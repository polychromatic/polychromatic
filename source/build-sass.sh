#!/bin/bash
#
# Builds the styling for the controller application.
#

cmd=$(which sass)
if [ -z "$cmd" ]; then
    echo "Please install the command for 'sass' and try again."
    exit 1
fi

cd $(dirname "$0")/sass/

sass ./controller.scss ../../data/ui/controller.css --scss --style=compressed --sourcemap=none

