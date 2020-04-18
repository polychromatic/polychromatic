#!/bin/bash
#
# Generates and merges all locales into one template.
#

cd "$(dirname $0)"/../

echo "Generating pots..."

count=0
for file in "polychromatic-controller" \
            "polychromatic-tray-applet" \
            "pylib/common.py" \
            "pylib/locales.py" \
            "pylib/preferences.py"
do
    count=$(( count + 1 ))
    pygettext -d "polychromatic-$count" "$file"
done

msgcat *.pot --use-first > ./locale/polychromatic.pot
rm ./*.pot

echo "New pot files generated."

