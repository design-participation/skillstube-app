VERSION:=0.1
SSL_KEY:=$(PWD)/ssl/localhost.key
SSL_CRT:=$(PWD)/ssl/localhost.crt
DATA:=$(PWD)/data
CONFIG:=$(PWD)/src/secrets.py

build: Dockerfile
	./tools/babel.sh src -d static
	docker build -t benob/skillstube:$(VERSION) . 

run: 
	docker run --volume "$(CONFIG)":/app/src/secrets.py \
		--volume "$(SSL_KEY)":/app/ssl/localhost.key \
		--volume "$(SSL_CRT)":/app/ssl/localhost.crt \
		--volume "$(DATA)":/app/data \
		--expose 8787 \
		--network host \
		benob/skillstube:$(VERSION)

export:
	docker save benob/skillstube:$(VERSION) | gzip > benob-skillstube-$(VERSION).tgz 
