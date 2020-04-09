#!/bin/bash
#
# Validates Python files for errors. Uses 'pylint'.
#

if [ -z "$(which pylint)" ]; then
    echo "'pylint' not installed."
    exit 1
fi

errors=false
function check_status() {
    if [ $? != 0 ]; then
        errors=true
    fi
}

options="relative-beyond-top-level"

pylint --errors-only --disable "$options" polychromatic-controller
check_status $?

pylint --errors-only --disable "$options" polychromatic-tray-applet
check_status $?

pylint --errors-only --disable "$options" polychromatic-cli
check_status $?

cd pylib/
find . -name "*.py" | xargs pylint --disable "$options" --errors-only
check_status $?

if [ $errors == true ]; then
    exit 1
fi
