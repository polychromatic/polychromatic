#!/bin/bash
#
# In event of new SVGs, use the 'svgcleaner' tool to optimise the SVGs by
# stripping non-essential data.
#
# This only applies to the "img" folder. The device maps should NOT be optimised
# as it will likely strip essential data.
#

if [ -z "$(which svgcleaner)" ]; then
    echo "'svgcleaner' not installed."
    exit 1
fi

cd "$(dirname $0)/../data/img/"

for f in $(find . -name "*.svg" -type f)
do
    echo -n "$f: "
    mv "$f" "$f.old.svg"
    svgcleaner --trim-colors=no "$f.old.svg" "$f"
done

find . -name "*.old.svg" -delete
