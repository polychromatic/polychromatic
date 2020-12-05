#!/bin/bash
#
# Creates a distro-agnostic set of files that allows Polychromatic to run
# relatively without installation or with additional sources.
#
# This could be installed to /opt.
#
# Dependencies must be installed to use the application. See README for details.
#
# Parameters: <install path> [--overwrite]
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

# Prepare destination directory
if [ -d "$DEST" ] && [ "$2" != "--overwrite" ]; then
    echo "Output directory already exists! Pass --overwrite as second parameter to delete."
    exit 1
fi

if [ "$2" == "--overwrite" ]; then
    rm -rf "$DEST"
fi

mkdir "$DEST"

# Copy required files
cd "$DEST"
cp -vr "$SOURCE/data" "$DEST/data"
cp -vr "$SOURCE/pylib" "$DEST/pylib"
cp -vr "$SOURCE/LICENSE" "$DEST/"
cp -vr "$SOURCE/polychromatic-"* "$DEST/"
rm "$DEST/polychromatic-controller-dev"

# Build locales
"$SOURCE/scripts/build-locales.sh" "$DEST/locale/"

# Clean up
find "$DEST" -name "__pycache__" -type d -exec rm -rf {} +
