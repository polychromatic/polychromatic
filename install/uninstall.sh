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
# This script manually deletes the Polychromatic and Python
# libraries from the system.
############################################################################

# Paths
TARGET="/usr/share/polychromatic/"
MODULES="/usr/lib/python3/dist-packages/polychromatic/"

# Are we root?
if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root." 1>&2
   exec sudo "$0"
   exit
fi

# Deleting files
rm -rfv "$TARGET"
rm -rfv "$MODULES"
rm -rfv /usr/share/applications/polychromatic-controller.desktop
rm -rfv /usr/share/applications/polychromatic-tray.desktop

# Success!
echo "Uninstall Success!"
exit 0
