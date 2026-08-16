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

# Check the translated pages can be assembled and compiled too.
if [[ -z "$(type -P po4a)" ]]; then
    echo "'po4a' not installed. Skipping translated manual pages."
else
    rm -rf .build
    po4a --no-update po4a.cfg
    if [[ "${?}" != 0 ]]; then
        errors=true
    fi

    for file in .build/*/*.scd
    do
        temp_file="$(mktemp)"
        scdoc < "${file}" > "${temp_file}"
        if [[ "${?}" != 0 ]]; then
            errors=true
        fi
        rm "${temp_file}"
    done
    rm -rf .build
fi

if [[ "${errors}" == true ]]; then
    exit 1
fi
