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
# This script updates the repository and installs the latest
# Polychromatic version.
############################################################################

# Repository location
repo_url="https://github.com/lah7/polychromatic.git"
repo_root=$(dirname "$0")/../

# Check if git is installed
command -v git >/dev/null 2>&1 || { echo "Please install 'git' to update using this script." >&2; exit 1; }

# Check if the repository was cloned
if [ ! -d "$repo_root/.git" ]; then
    echo "The Polychromatic repository was not cloned and is unable to update itself."
    echo "Please delete '$repo_root' and run:"
    echo "  $ git clone $repo_url"
    exit 1
fi

# Get hash of current program
old_hash=$(md5sum $repo_root/polychromatic-controller)

# Ask user which branch to use.
echo "Which branch would you like to use?"
echo "(s) Stable"
echo "(d) Development"
read -p "Choice : " choice

if [ "$choice" == "s" ]; then
    branch='stable'
elif [ "$choice" == "d" ]; then
    branch='master'
else
    echo "I didn't understand that."
    exit 1
fi

# Pull the latest changes
git reset --hard &>/dev/null
git pull --rebase $repo_url $branch

# Anything new?
new_hash=$(md5sum $repo_root/polychromatic-controller)

if [ "$old_hash" == "$new_hash" ]; then
    echo "You have the latest Polychromatic Controller."
else
    # Offer to update the version installed on the system, if applicable.
    if [ -f "/usr/bin/polychromatic-controller" ]; then
        echo "New changes detected. Would you like to update? [y/n]"
        read -p " Update? | " choice
        if [ "$choice" == "y" ]; then
          "$repo_root/install/install.sh"
        fi
    else
        echo "Your copy of Polychromatic is now up-to-date."
    fi
fi

