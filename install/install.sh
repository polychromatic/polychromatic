#!/bin/bash
#
# Polychromatic Controller is free software: you can redistribute it and/or modify
# it under the temms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Polychromatic Controller is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2016 Luke Horwell <lukehorwell37+code@gmail.com>
#
############################################################################
# This script manually installs the Polychromatic Controller and Python
# libraries.
############################################################################

# Paths
TARGET="/usr/share/polychromatic/"
MODULES="/usr/lib/python3/dist-packages/polychromatic/"
SOURCE=$(dirname "$0")/..


# Are we root?
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root." 1>&2
   exec sudo "$0"
   exit
fi

# Check for existing installation.
if [ -d "$TARGET" ]; then
    echo "An installation already exists. Removing first..."
    $(dirname "$0")/uninstall.sh
    if [ -d "$TARGET" ]; then
        echo "Uninstall failed. Aborting."
        exit 1
    fi
fi

# Check if the Razer Python modules are present.
razer_path='/usr/lib/python3/dist-packages/razer/'
if [ ! -d "$razer_lib" ]; then
    echo "*************************"
    echo "The razer-chroma-drivers Python modules are missing!"
    echo "Please install them from http://pez2001.github.io/razer_chroma_drivers/"
    echo -e "It could be possible that they are in a different path to '$razer_path'"
    echo "*************************"
    read -p "Continue anyway? [y] " action
    if [ ! "$action" == 'y' ]; then
        echo "Install Aborted."
        exit 1
    fi
fi

# Create directories
mkdir "$TARGET"
mkdir "$MODULES"

# Copy data files.
cp -r "$SOURCE/data/" "$TARGET/data/"
cp    "$SOURCE/controller.py" "$TARGET/controller.py"
cp    "$SOURCE/tray_applet.py" "$TARGET/tray_applet.py"

# Copy Python modules
cp -r "$SOURCE/pylib/"* "$MODULES/"

# Copy desktop launchers
cp "$SOURCE/install/polychromatic-controller.desktop" /usr/share/applications/
cp "$SOURCE/install/polychromatic-tray.desktop" /usr/share/applications/

# Success!
echo "Installation Success!"
exit 0

