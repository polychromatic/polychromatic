#!/bin/bash
#
# Validates SCSS files can be compiled. Uses 'sassc'.
#

if [ -z "$(which sassc)" ]; then
    echo "'sassc' not installed."
    exit 1
fi

temp_file=$(mktemp)

sassc source/sass/qt-style.scss $temp_file --sass --style compressed
if [ $? != 0 ]; then
    exit 1
fi
rm $temp_file
