#!/bin/bash
#
# Validates Python files for errors. Uses 'pylint'.
#

# Try 'pylint3' (Ubuntu 18.04) otherwise 'pylint' (Ubuntu 20.04, Arch, etc)
pylint=""
for bin in "pylint3" "pylint"; do
    if [ ! -z "$(command -v $bin)" ]; then
        pylint="$bin"
        continue
    fi
done

if [ -z "$pylint" ]; then
    echo "'pylint' not installed."
    exit 1
fi

$pylint --errors-only \
    --disable="relative-beyond-top-level" \
    --disable="no-name-in-module" \
    polychromatic-cli \
    polychromatic-controller \
    polychromatic-helper \
    polychromatic-tray-applet \
    pylib/*/*.py \
    pylib/*.py

if [ $? != 0 ]; then
    exit 1
fi
