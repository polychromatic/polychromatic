#!/bin/bash
#
# Watches for SASS files during development of the controller application.
#

cmd=$(which sass)
if [ -z "$cmd" ]; then
    echo "Please install the command for 'sass' and try again."
    exit 1
fi

cd $(dirname "$0")/sass/

sass --watch .:../../data/ui/ --sourcemap=none --scss --style=compressed

