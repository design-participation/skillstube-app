# Use an small Python runtime as a parent image
FROM jfloff/alpine-python:3.7-slim

# Set the working directory to /app
WORKDIR /app

# Install mongodb and build deps
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.8/community' >> /etc/apk/repositories
RUN apk upgrade --update
RUN apk add --no-cache mongodb gcc musl-dev make libffi-dev openssl-dev libffi openssl

# Install any needed packages specified in requirements.txt
COPY requirements.txt run.sh /app/
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Cleanup build dependencies
RUN apk del --no-cache gcc musl-dev make libffi-dev openssl-dev

# Make port 8787 available to the world outside this container
EXPOSE 8787

# Setup environment
ENV HOST "0.0.0.0"
ENV PORT 8787

# Copy the current directory contents into the container at /app
COPY src /app/src
COPY static /app/static
COPY templates /app/templates

# Setup data and configuration from host directories 
VOLUME /app/data
VOLUME /app/src/secret.py
VOLUME /app/ssl/key
VOLUME /app/ssl/crt

# Run server when the container launches
CMD "/app/run.sh"
