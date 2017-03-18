#!/bin/bash
whereami=$(dirname "$0")
cd "$whereami"/../

echo "Generating pots..."

pygettext -d polychromatic-controller   polychromatic-controller
pygettext -d polychromatic-tray-applet  polychromatic-tray-applet
pygettext -d polychromatic-common       pylib/common.py

mv polychromatic-controller.pot locale/
mv polychromatic-tray-applet.pot locale/
mv polychromatic-common.pot locale/

echo "New pot files generated."
