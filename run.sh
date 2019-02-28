#!/bin/bash

if [ ! -d env ] || [ $(grep VIRTUAL_ENV= env/bin/activate|cut -f2 -d'"') != "$PWD/env" ] ; then
	rm -rf env
	virtualenv -p python3 env
	. env/bin/activate
	pip install -r requirements.txt
fi

. env/bin/activate

if [ ! -f src/secrets.py ]; then
	echo "You need to change the configuration in src/secrets.py (see src/secrets.template.py)" >&2
	exit 1
fi

if [ "`grep USE_SSL src/secrets.py | grep True`" != "" ] && [ ! -f `grep SSL_KEY src/secrets.py | cut -f2 -d"'"` ]; then
	echo "SSL certificate not found. Configure one in src/secrets.py. You can generate it for localhost with ./ssl/generate.sh" >&2
	exit 1
fi

# warn: remove disk-saving options in production (only keep --dbpath)
mkdir -p data/mongo
mongod --nojournal --nssize=1 --noprealloc --smallfiles --dbpath data/mongo >/dev/null 2>&1 &

python src/server.py -debug

kill %%
