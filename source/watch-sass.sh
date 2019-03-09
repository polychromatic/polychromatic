#!/bin/bash
#
# Watches the 'sass' folder during development and rebuilds styles
# for the controller application.
#

cd $(dirname "$0")/sass/

cmd=$(which sass)
if [ -z "$cmd" ]; then
    echo "SASS is needed to compile the controller theming, but it is missing."
    echo "Please install the command for 'sass' and try again."
    exit 1
fi

sass --watch .:../../data/ui/themes/ --sourcemap=none --scss --style compressed

