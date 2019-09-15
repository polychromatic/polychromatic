#!/bin/bash
#
# Builds the styling for the controller application.
#
# Supported implementations:
#   - SASSC (sassc)
#   - Dart SASS (sass)
#

cd $(dirname "$0")/sass/

# Find an implementation of SASS to use.
sassc=$(which sassc 2>/dev/null)
sass=$(which sass 2>/dev/null)

if [ -z "$sass" ] && [ -z "$sassc" ]; then
    echo "Please install a package that provides 'sassc' or 'sass' and try again."
    echo "Try: sassc (from your distro's repositories); sass (npm) or Dart SASS."
    exit 1
fi

if [ ! -z "$sassc" ]; then
    echo "Compiling styling... (sassc)"
    sassc ./controller.scss ../../data/ui/controller.css --sass --style compressed

elif [ ! -z "$sass" ]; then
    echo "Compiling styling... (sass)"
    sass ./controller.scss ../../data/ui/controller.css --style=compressed --no-source-map
fi
