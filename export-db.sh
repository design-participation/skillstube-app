#!/bin/bash

if [ $# != 1 ]; then
	echo "usage: $0 <output.xlsx>" >&1
	exit 1
fi

output=$1

set -e -u -o pipefail

. env/bin/activate

python src/export.py "$output"
