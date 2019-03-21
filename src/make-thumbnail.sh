#!/bin/bash

if [ $# != 2 ]; then
	echo "usage: $0 <source-image> <target-image.jpg>" >&2
	exit 1
fi

set -e -u -o pipefail

convert "$1" -resize 512x512^^ -gravity center -extent 512x512 -quality 65 "$2"
jhead -q -autorot -purejpg "$2"

exit 0
