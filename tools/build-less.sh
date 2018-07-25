#!/bin/bash
#
# Builds the LESS files for local development.
#

cmd=$(which lessc)
if [ -z "$cmd" ]; then
    echo "LESSC is needed to compile the styling, but it is missing."
    echo "Please install 'lessc' (node-less) and try again."
    exit 1
fi

cd $(dirname "$0")/../source/less/

for source in $(find . -name "*.less" -type f); do
    filename=$(basename -- "$source")
    extension="${filename##*.}"
    output="${filename%.*}"
    lessc "$source" "../../data/pages/css/$output.css"
done

