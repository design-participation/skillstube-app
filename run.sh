#!/bin/bash

trap 'kill -TERM $(jobs -p)' SIGTERM

timestamp=`date '+%Y-%m-%d_%H:%M:%S'`
mkdir -p data/mongo data/pictures data/qrcodes data/export data/logs

if [ ! -r src/secrets.py ]; then
	echo "ERROR: you must provide a secrets.py configuration file. Here is a template:"
	echo "--------- 8< ---------"
	cat src/secrets.template.py
	echo "--------- >8 ---------"
	exit 1
fi

# warn: remove disk-saving options in production (only keep --dbpath)
mongod --dbpath data/mongo --port `grep DB_URL src/secrets.py | cut -f2 -d"'" | awk -F: '{print $(NF)}'` > "data/logs/db_$timestamp.txt" 2>&1 &

python -u src/server.py $* 2>&1 | tee "data/logs/server_$timestamp.txt"

kill -TERM $(jobs -p)
