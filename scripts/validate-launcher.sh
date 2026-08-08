#!/usr/bin/env bash
#
# Validate XDG *.desktop launcher files
#

if [[ -z "$(type -P desktop-file-validate)" ]]; then
    echo "desktop-file-validate not found. Try installing 'desktop-file-utils'."
    exit 1
fi

cd "$(dirname "$0")/../"
desktop-file-validate ./sources/launchers/*.desktop
result="${?}"

exit "${?}"
