#!/usr/bin/env bash
#
# Checks the scdocs can be compiled.
#

if [[ -z "$(type -P scdoc)" ]]; then
    echo "'scdoc' not installed."
    exit 1
fi

errors=false

cd man || exit 1
for file in *.scd
do
    temp_file="$(mktemp)"
    scdoc < "${file}" > "${temp_file}"
    if [[ "${?}" != 0 ]]; then
        errors=true
    fi
    rm "${temp_file}"
done

if [[ "${errors}" == true ]]; then
    exit 1
fi
