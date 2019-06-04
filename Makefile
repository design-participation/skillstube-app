VERSION:=0.1
SSL_KEY:=$(PWD)/ssl/localhost.key
SSL_CRT:=$(PWD)/ssl/localhost.crt
DATA:=$(PWD)/data
CONFIG:=$(PWD)/src/secrets.py

build: Dockerfile
	docker build -t benob/howtoapp:$(VERSION) . 

run: 
	docker run --volume "$(CONFIG)":/app/src/secrets.py \
		--volume "$(SSL_KEY)":/app/ssl/localhost.key \
		--volume "$(SSL_CRT)":/app/ssl/localhost.crt \
		--volume "$(DATA)":/app/data \
		--expose 8787 \
		--network host \
		benob/howtoapp:$(VERSION)

export:
	docker save benob/howtoapp:$(VERSION) | gzip > benob-howtoapp-$(VERSION).tgz 
