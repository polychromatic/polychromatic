#!/bin/bash
#
# Builds the SASS files for UI styling.
#

cmd=$(which sass)
if [ -z "$cmd" ]; then
    echo "SASS is needed to compile the styling, but it is missing."
    echo "Please install the command for 'sass' and try again."
    exit 1
fi

cd $(dirname "$0")/../source/sass/

for source in $(find . -maxdepth 1 -name "*.scss"); do
    filename=$(basename -- "$source")
    extension="${filename##*.}"
    output="${filename%.*}"
    dest="../../data/ui/css/$output.css"
    $cmd "$source" "$dest" --sourcemap=none
    if [ ! $? == 0 ]; then
        rm "$dest"
    fi
done
