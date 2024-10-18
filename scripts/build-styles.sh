#!/usr/bin/env bash
#
# Builds the styling for the controller application.
#
# Supported implementations:
#   - SASSC (sassc)
#   - Dart SASS (sass)
#

cd $(dirname "$0")/../sources/qt-theme/

# Find an implementation of SASS to use.
sassc=$(which sassc 2>/dev/null)
sass=$(which sass 2>/dev/null)

if [ -z "$sass" ] && [ -z "$sassc" ]; then
    echo "Please install a package that provides 'sassc' or 'sass' and try again."
    echo "Try: sassc (from your distro's repositories); sass (npm) or Dart SASS."
    exit 1
fi

# SASS cannot compile Qt gradients, so concatenate them
cp ./_misc.css ../../data/qt/style.qss

if [ ! -z "$sassc" ]; then
    echo -n "Compiling Qt theme using 'sassc'..."
    sassc ./stylesheet.scss ../../data/qt/style.css.tmp --sass --style compressed
    result=$?

elif [ ! -z "$sass" ]; then
    echo "Compiling Qt theme using 'sass'..."
    sass ./stylesheet.scss ../../data/qt/style.css.tmp --style=compressed --no-source-map
    result=$?
fi

if [ "$result" != 0 ]; then
    exit 1
fi

cat ../../data/qt/style.css.tmp >> ../../data/qt/style.qss
rm ../../data/qt/style.css.tmp

echo " done!"
