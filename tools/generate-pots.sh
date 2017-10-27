#!/bin/bash
#
# Generates and merges all locales into one template.
#

cd "$(dirname $0)"/../

echo "Generating pots..."

pygettext -d polychromatic-controller   polychromatic-controller
pygettext -d polychromatic-tray-applet  polychromatic-tray-applet
pygettext -d polychromatic-common       pylib/common.py
for file in $(ls pylib/screens/*.py); do
    if [ "$(basename "$file")" == "__init__.py" ]; then
        continue
    fi
    pygettext -d polychromatic-$(basename "$file") "$file"
done

msgcat *.pot --use-first > ./locale/polychromatic.pot
rm ./*.pot

echo "New pot files generated."

