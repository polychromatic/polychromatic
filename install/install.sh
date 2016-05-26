#!/bin/bash
#
# Polychromatic is free software: you can redistribute it and/or modify
# it under the temms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Polychromatic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Polychromatic. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2016 Luke Horwell <lukehorwell37+code@gmail.com>
#
############################################################################
# This script manually installs the Polychromatic and Python
# libraries.
############################################################################

# Paths
target_data="/usr/share/polychromatic"
target_bin="/usr/bin"
target_icon="/usr/share/icons"
modules="/usr/lib/python3/dist-packages/polychromatic"
source=$(dirname "$0")/..
dependencies_apt="gir1.2-webkit2-4.0 python3-gi gir1.2-appindicator3-0.1"

# Are we root?
if [ "$(id -u)" != "0" ]; then
    echo "To install, this script must be run as root." 1>&2
    exec sudo "$0"
    exit
fi

# Check for existing installation.
if [ -d "$target_data" ]; then
    echo "An installation already exists. Removing first..."
    $(dirname "$0")/uninstall.sh
    if [ -d "$target_data" ]; then
        echo "Uninstall failed. Aborting."
        exit 1
    fi
fi

# Install dependencies on Ubuntu/Debian
function get_distro() {
    . /etc/os-release
    echo "$ID"
}

distro=`get_distro`
if [ "$distro" == "debian" ] || [ "$distro" == "ubuntu" ]; then
    echo -e "Installing dependencies...\n"
    sudo apt install $dependencies_apt
    echo -e ''
else
    echo "*************************"
    echo "Dependencies cannot be automatically installed on this distro."
    echo "Please see the README before using the application."
    echo "*************************"
fi

# Check if the Razer Python modules are present.
echo "Checking if Razer modules are present..."
razer_path='/usr/lib/python3/dist-packages/razer/'
if [ ! -d "$razer_path" ]; then
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
echo "Copying files..."
mkdir "$target_data"
mkdir "$modules"

# Copy bin files.
cp "$source/polychromatic-controller" "$target_bin/"
cp "$source/polychromatic-tray-applet" "$target_bin/"
chmod +x "$target_bin/polychromatic-controller"
chmod +x "$target_bin/polychromatic-tray-applet"

# Copy data files.
cp -r "$source/data/"* "$target_data/"

# Copy Python modules
cp -r "$source/pylib/"* "$modules/"

# Copy icons
cp "$source/install/hicolor/scalable/apps/polychromatic.svg" "$target_icon/hicolor/scalable/apps/polychromatic.svg"

# Copy desktop launchers
cp "$source/install/polychromatic-controller.desktop" /usr/share/applications/
cp "$source/install/polychromatic-tray.desktop" /usr/share/applications/

# Keep a copy of the uninstall script for manual removal later.
cp "$source/install/uninstall.sh" "$target_data/uninstall-polychromatic.sh"

# Post installation
echo "Updating icon cache..."
update-icon-caches /usr/share/icons/hicolor/

# Success!
echo "Installation Success!"
echo "----------------------------"
echo "To manually remove the software from your system cleanly later, run:"
echo "$target_data/uninstall-polychromatic.sh"
exit 0

