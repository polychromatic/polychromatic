#!/bin/bash
#
# Prepares a structure so locales can be tested without installing the
# application.
#
# Parameters:
#   $1      Optional. Path to generate locales (e.g. en_GB/LC_MESSAGES/polychromatic.mo files)
#

cd "$(dirname "$0")"/../locale
output_path="$1"

if [ -z "$(which msgfmt)" ]; then
    echo "Command for 'msgfmt' not found. Locales will not be compiled."
    exit 1
fi

# Path to locales optional. Use development repository otherwise.
if [ -z "$output_path" ]; then
    output_path="$(pwd)"
fi

if [ ! -d "$output_path" ]; then
    mkdir "$output_path"
fi

echo -n "Compiling locales using 'msgfmt'..."
for file in $(ls *.po)
do
    locale=${file%.*}
    locale_path="$output_path/$locale/LC_MESSAGES/"
    if [ -d "$locale_path" ]; then
        rm -r "$locale_path"
    fi
    mkdir -p "$locale_path"
    msgfmt $locale.po -o "$locale_path/polychromatic.mo"
done
echo " done!"
