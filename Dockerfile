# Use an small Python runtime as a parent image
FROM jfloff/alpine-python:3.7-slim

# Setup access to 'community' packages
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.8/community' >> /etc/apk/repositories

# Install mongodb and runtime dependencies
RUN apk --update --no-cache add mongodb openssl jpeg libffi

# Install packages specified in requirements.txt and build deps
COPY requirements.txt /tmp/
RUN apk add --no-cache --virtual .build-deps gcc musl-dev make libffi-dev openssl-dev libffi jpeg-dev ;\
	  pip install --trusted-host pypi.python.org -r /tmp/requirements.txt ;\
		# cleanup
		apk del --no-cache --purge .build-deps ;\
		rm -rf /var/cache/apk/*

# Add user for running the app
RUN adduser -D -h /app appuser
WORKDIR /app/
USER appuser

# Copy current directory contents into the container at /app
COPY run.sh /app
COPY src /app/src
COPY static /app/static
COPY templates /app/templates
# Only needed if you are going to run in debug mode
COPY debug-data /app/debug-data

# Setup data and configuration from host directories 
VOLUME /app/data
VOLUME /app/src/secret.py
VOLUME /app/ssl/key
VOLUME /app/ssl/crt

# Setup environment
ENV HOST "0.0.0.0"
ENV PORT 8787

# Expose App port to host
EXPOSE 8787
# Expose mongodb port to host
EXPOSE 27018 

# Run server when the container launches
# Note: this replaces the entrypoint from base image
ENTRYPOINT ["/bin/bash", "/app/run.sh"]

