#!/bin/bash
#
# Validate AppStream metainfo
#

if [ -z "$(which appstreamcli)" ]; then
    echo "appstreamcli not found. Try installing 'appstream'."
    exit 1
fi

cd "$(dirname "$0")"/../sources/
appstreamcli validate *.xml
result=$?

exit $?
