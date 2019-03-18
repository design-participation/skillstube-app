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

timestamp=`date '+%Y-%m-%d_%H:%M:%S'`
mkdir -p data/mongo logs

# warn: remove disk-saving options in production (only keep --dbpath)
mongod --nojournal --nssize=1 --noprealloc --smallfiles --dbpath data/mongo --port `grep DB_URL src/secrets.py | cut -f2 -d"'" | awk -F: '{print $(NF)}'` > "logs/db_$timestamp.txt" 2>&1 &

python -u src/server.py $* 2>&1 | tee "logs/server_$timestamp.txt"

kill %%
