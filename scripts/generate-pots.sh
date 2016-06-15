#!/bin/bash
whereami=$(dirname "$0")
cd "$whereami"/../

echo "Generating pots..."

pygettext -d polychromatic-controller   polychromatic-controller
pygettext -d polychromatic-tray-applet  polychromatic-tray-applet

mv polychromatic-controller.pot locale/
mv polychromatic-tray-applet.pot locale/

echo "New pot files generated."
