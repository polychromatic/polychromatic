#!/bin/bash
#
# Generates and merges all locales into one template.
#

cd "$(dirname $0)"/../

echo "Generating pots..."

pygettext -d polychromatic-controller       polychromatic-controller
pygettext -d polychromatic-tray-applet      polychromatic-tray-applet
pygettext -d polychromatic-common           pylib/common.py
pygettext -d polychromatic-page-error       pylib/screens/error.py
pygettext -d polychromatic-page-loading     pylib/screens/loading.py
pygettext -d polychromatic-page-devices     pylib/screens/main/devices.py
pygettext -d polychromatic-page-preferences pylib/screens/main/preferences.py
pygettext -d polychromatic-page-profiles    pylib/screens/main/profiles.py

for file in $(ls pylib/screens/*.py); do
    if [ "$(basename "$file")" == "__init__.py" ]; then
        continue
    fi
    pygettext -d polychromatic-$(basename "$file") "$file"
done

msgcat *.pot --use-first > ./locale/polychromatic.pot
rm ./*.pot

echo "New pot files generated."

