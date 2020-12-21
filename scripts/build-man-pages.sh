#!/bin/bash
#
# Compiles the man pages from scd files.
#

cd $(dirname "$0")/../man/

which=$(which scdoc)
if [ $? != 0 ]; then
    echo "Please install 'scdoc', which was not found in your PATH."
    exit 1
fi

for input in $(ls *.scd); do
    output="${input%.*}"
    scdoc < $input > $output
    if [ $? != 0 ]; then
        exit 1
    fi
done
