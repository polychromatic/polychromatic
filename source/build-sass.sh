#!/bin/bash
#
# Builds the styling for the controller application.
#

cmd=$(which sass)
if [ -z "$cmd" ]; then
    echo "SASS is needed to compile the controller theming, but it is missing."
    echo "Please install the command for 'sass' and try again."
    exit 1
fi

cd $(dirname "$0")/sass/

for source in $(find themes/ -maxdepth 1 -name "*.scss"); do
    filename=$(basename -- "$source")
    extension="${filename##*.}"
    output="${filename%.*}"
    dest="../../data/ui/theme/$output.css"
    $cmd "$source" "$dest" --sourcemap=none --scss --style compressed
    if [ ! $? == 0 ]; then
        rm "$dest"
    fi
done

