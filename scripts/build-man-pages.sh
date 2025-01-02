#!/usr/bin/env bash
#
# Compiles the man pages from scd files.
#

cd $(dirname "$0")/../man/

scdoc="$(type -P scdoc 2>/dev/null)"

if [[ -z "${scdoc}" ]]; then
    echo "Please install 'scdoc', which was not found in your PATH."
    exit 1
fi

for input in *.scd; do
    output="${input%.*}"
    scdoc < "${input}" > "${output}"
    if [[ "${?}" != 0 ]]; then
        exit 1
    fi
done
