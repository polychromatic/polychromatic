#!/bin/bash
#
# Prepares a structure so locales can be tested without installing the
# application.
#
cd "$(dirname "$0")"/../locale

if [ -z "$(which msgfmt)" ]; then
    echo "Command for 'msgfmt' not found. Locales will not be compiled."
    exit 1
fi

if [ -d "testing/" ]; then
    rm -r testing
fi

mkdir testing

for file in $(ls *.po)
do
    locale=${file%.*}
    mkdir -p "testing/$locale/LC_MESSAGES/"
    msgfmt $locale.po -o "testing/$locale/LC_MESSAGES/polychromatic.mo"
done
