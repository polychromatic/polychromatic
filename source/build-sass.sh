#!/bin/bash
#
# Builds the styling for the controller application.
#

cmd=$(which sass)
if [ -z "$cmd" ]; then
    echo "SASS is needed to compile the controller theming, but it is missing."
    echo "Please install the command for 'sass' and try again."
    exit 1
fi

cd $(dirname "$0")/sass/

$cmd ./dark.scss ../../data/ui/theme/dark.css --scss --style compressed

