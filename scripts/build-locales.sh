#!/bin/bash
#
# Prepares a structure so locales can be tested without installing the
# application.
#
# Parameters:
#   $1      Path to generate locales (.mo files)
#

cd "$(dirname "$0")"/../locale
output_path="$1"

if [ -z "$(which msgfmt)" ]; then
    echo "Command for 'msgfmt' not found. Locales will not be compiled."
    exit 1
fi

if [ -z "$output_path" ]; then
    echo "Missing parameter: Path to generate locales"
    exit 1
fi

if [ -d "$output_path" ]; then
    rm -r "$output_path"
fi

mkdir "$output_path"

echo -n "Compiling locales using 'msgfmt'..."
for file in $(ls *.po)
do
    locale=${file%.*}
    mkdir -p "$output_path/$locale/LC_MESSAGES/"
    msgfmt $locale.po -o "$output_path/$locale/LC_MESSAGES/polychromatic.mo"
done
echo " done!"
