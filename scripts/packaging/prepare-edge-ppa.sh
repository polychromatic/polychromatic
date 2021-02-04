#!/bin/bash
#
# This script prepares the Edge PPA containing the latest builds for Ubuntu.
#
# Expected to be run by CI system.
# Parameters: <path to src code>
#

REPO_ROOT="$(realpath "$1")"

for codename in "focal" "groovy" "hirsute"
do
    echo -e "\n$codename"
    echo -e "===================="
    TEMP_DIR="$(mktemp -d)"
    git clone "$REPO_ROOT" "$TEMP_DIR/src"
    cd "$TEMP_DIR/src"
    ./scripts/packaging/generate-edge-debian-changelog.py $codename
    debuild -S
    debsign -k 49D6E0C94C9832E63FDBD50BEAF6D6A2C65D1D85 ../*.changes
    dput ppa:polychromatic/edge ../*.changes
done
