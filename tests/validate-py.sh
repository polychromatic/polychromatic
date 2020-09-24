#!/bin/bash
#
# Validates Python files for errors. Uses 'pylint'.
#

# Package used by CI (Ubuntu 18.04) is still the python2 version.
pylint="pylint"
if [ "$1" == "--ubuntu" ]; then
    pylint="pylint3"
fi

if [ -z "$(which $pylint)" ]; then
    echo "'$pylint' not installed."
    exit 1
fi

errors=false
function check_status() {
    if [ $? != 0 ]; then
        errors=true
    fi
}

$pylint --errors-only \
    --disable="relative-beyond-top-level" \
    --disable="no-name-in-module" \
    polychromatic-cli \
    polychromatic-controller \
    polychromatic-helper \
    polychromatic-tray-applet \
    pylib/*.py \
    pylib/backends/*.py

check_status $?

if [ $errors == true ]; then
    exit 1
fi
