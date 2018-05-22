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
# Copyright (C) 2016-2017 Luke Horwell <luke@ubuntu-mate.org>
#
############################################################################
# This script manually installs the Polychromatic and Python
# libraries.
############################################################################

## Assign Global Install Variables
# Function Definition
function assign() {
    var=$1
    val=$2
    eval ${var^^}=$( [ ${!var} ] && echo ${!var} || echo $val )
}

# Global Variables
assign PREFIX /usr/local
# assign EPREFIX $PREFIX
# assign BINDIR $EPREFIX/bin
# assign SBINDIR $EPREFIX/sbin
# assign LIBEXECDIR $EPREFIX/libexec
# assign SYSCONFDIR $PREFIX/etc
# assign SHAREDSTATEDIR $PREFIX/com
# assign LOCALSTATEDIR $PREFIX/var
# assign RUNSTATEDIR $LOCALSTATEDIR/run
# assign LIBDIR $EPREFIX/lib
# assign INCLUDEDIR $PREFIX/include
# assign OLDINCLUDEDIR /usr/include
assign DATAROOTDIR $PREFIX/share
assign DATADIR $DATAROOTDIR
assign INFODIR $DATADIR/info
assign LOCALEDIR $DATADIR/locale
assign MANDIR $DATADIR/man
assign DOCDIR $DATADIR/doc/polychromatic

# Paths
target_data="$DATADIR/polychromatic"
# target_bin="$BINDIR"
target_icon="$DATADIR/icons"
target_apps="$DATADIR/applications"
target_man="$MANDIR/man1"
python_path=$(python3 -c "import sys; print(sys.path[-1])")
polyc_modules="$python_path/polychromatic"
razer_modules="$python_path/razer/"
# locale_dir="$LOCALEDIR"
source=$(dirname "$0")/..
dependencies_apt="gir1.2-webkit2-4.0 python3-gi python3-setproctitle python3-requests gir1.2-appindicator3-0.1 imagemagick node-less"
dependencies_pacman="webkitgtk python-gobject python-setproctitle python-requests libappindicator imagemagick nodejs-less"

# Pretty colours!
bold="$(tput bold)"
black="$(tput setaf 0)"
red="$(tput setaf 1)"
green="$(tput setaf 2)"
yellow="$(tput setaf 3)"
blue="$(tput setaf 4)"
magenta="$(tput setaf 5)"
cyan="$(tput setaf 6)"
white="$(tput setaf 7)"
reset="$(tput sgr0)"

function printg() {
    echo "${green}$*${reset}"
}

function printr() {
    echo "${red}$*${reset}"
}

function printy() {
    echo "${yellow}$*${reset}"
}

# Are we root?
if [ "$(id -u)" != "0" ]; then
    echo "To install, this script must be run as root." 1>&2
    exec sudo "$0"
    exit
fi

# Check for existing installation.
if [ -d "$target_data" ]; then
    printy "An installation already exists. Removing first..."
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
    printy "Dependencies: $dependencies_apt"
    printg "Installing dependencies..."
    sudo apt install --yes $dependencies_apt
    echo

elif [ "$distro" == "arch" ] || [ "$distro" == "manjaro" ]; then
    printy "Dependencies: $dependencies_pacman"
    read -p "Install dependencies with pacman? [y/n] | " choice
    if [ "${choice,,}" == "y" ] || [ "${choice,,} == "yes" ]; then
        printg "Installing dependencies..."
        sudo pacman -Sy $dependencies_pacman
    fi
    echo

else
    echo "**************************************************"
    printy "Dependencies cannot be automatically installed on this distro."
    echo "Please see the README before using the application."
    echo "**************************************************"
fi

# Check if the Razer Python modules are present.
printy "Checking if Razer modules are present..."
if [ ! -d "$razer_modules" ]; then
    echo "**************************************************"
    printr "The OpenRazer Python libraries are missing!"
    echo "Please install them from ${yellow}http://openrazer.github.io${reset}"
    echo "They are expected to be installed in ${yellow}$razer_modules${reset}"
    echo "**************************************************"
    read -p "Continue anyway? [y] " action
    if [ ! "$action" == 'y' ]; then
        printr "Polychromatic was not installed."
        exit 1
    fi
fi

# Create directories
printg "Creating new directories..."
mkdir "$target_data"
mkdir "$polyc_modules"

# Copy bin files.
printg "Copying to $BINDIR..."
cp "$source/polychromatic-controller" "$BINDIR/"
chmod +x "$BINDIR/polychromatic-controller"
cp "$source/polychromatic-tray-applet" "$BINDIR/"
chmod +x "$BINDIR/polychromatic-tray-applet"

# Copy data files.
printg "Copying to $target_data..."
cp -r "$source/data/"* "$target_data/"

# Copy Python modules
printg "Copying to $polyc_modules..."
cp -r "$source/pylib/"* "$polyc_modules/"

# Copy icons
printg "Copying to $target_icon..."
cp -r "$source/install/hicolor/"* "$target_icon/hicolor/"

# Copy man
printg "Copying to $target_man..."
cp "$source/man/polychromatic-controller.1" "$target_man/"
cp "$source/man/polychromatic-tray-applet.1" "$target_man/"

# Copy locales
printg "Copying to $LOCALEDIR..."
rsync -rlpt --exclude=*.pot --exclude=*.po "$source/locale/" "$LOCALEDIR"

# Copy desktop launchers
printg "Copying to $target_apps..."
cp "$source/install/polychromatic-controller.desktop" "$target_apps/"
cp "$source/install/polychromatic-tray-applet.desktop" "$target_apps/"

# Keep a copy of the uninstall script for manual removal later.
cp "$source/install/uninstall.sh" "$target_data/uninstall-polychromatic.sh"

# Create an autostart entry for tray applet.
printg "Creating start-up entry in /etc/xdg/autostart/ ..."
cp "$source/install/polychromatic-tray-applet.desktop" /etc/xdg/autostart/

# Compile source files
printg "Compiling LESS..."
lessc "$source/data/controller.less" "$target_data/pages/controller.css"

# Post installation
printg "Updating icon cache..."
update-icon-caches $target_icon/hicolor/

# Success!
printg "\nPolychromatic Installed!"
echo "----------------------------"
echo "To manually remove the software from your system cleanly later, run:"
printy "$target_data/uninstall-polychromatic.sh"
echo "----------------------------"
echo "To manually update, run:"
printy "$(pwd)/update.sh"
echo -e "----------------------------"
exit 0
