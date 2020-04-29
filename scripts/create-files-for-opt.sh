#!/bin/bash
#
# Creates a distro-agnostic set of files that allows Polychromatic to run
# relatively without installation or with additional sources.
#
# This could be installed to /opt.
#
# Dependencies must be installed to use the application. See README for details.
#
# Parameters: <install path>
#

if [ -z "$1" ]; then
    echo "Please specify the directory to place files."
    exit 1
fi

SOURCE="`realpath $(dirname "$0")/../`"
DEST="$1"

# Prerequisites
cd "$SOURCE"
./scripts/build-styles.sh

if [ ! -d "$DEST" ]; then
    mkdir "$DEST"
fi

# Copy required files
cd "$DEST"
cp -vr "$SOURCE/data" "$DEST/data"
cp -vr "$SOURCE/locale" "$DEST/locale"
cp -vr "$SOURCE/pylib" "$DEST/pylib"
cp -vr "$SOURCE/LICENSE" "$DEST/"
cp -vr "$SOURCE/polychromatic-"* "$DEST/"
rm "$DEST/polychromatic-controller-dev"
