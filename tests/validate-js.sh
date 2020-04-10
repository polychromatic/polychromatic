#!/bin/bash
#
# Validates JavaScript files. Uses 'jshint' from NPM.
#

if [ -z "$(which jshint)" ]; then
    echo "'jshint' not installed."
    exit 1
fi

errors=false

for file in $(ls data/ui/*.js)
do
    jshint -c "`realpath $(dirname "$0")/_jshint.json`" $file
    if [ $? != 0 ]; then
        errors=true
    fi
done

if [ $errors == true ]; then
    exit 1
fi
