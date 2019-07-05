#!/bin/bash

set -e -u -o pipefail

dir=`dirname "$0"`

if [ ! -d "$dir/node_modules" ]; then
  if ! which npm > /dev/null 2>&1; then
    echo "npm is required for installing babel" >&2
    exit 1
  fi
  cd "$dir"
  npm install @babel/core @babel/cli
  cd -
fi

$dir/node_modules/.bin/babel $*
