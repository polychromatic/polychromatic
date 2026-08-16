#!/usr/bin/env bash
#
# Compiles the man pages from scd files.
#
# Translated pages are assembled from the message catalogues in man/po/ and
# compiled the same way. This step needs 'po4a' and is skipped when it is
# missing, leaving the English pages alone.
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

po4a="$(type -P po4a 2>/dev/null)"

if [[ -z "${po4a}" ]]; then
    echo "Skipping translated man pages, as 'po4a' was not found in your PATH."
    exit 0
fi

# Refresh the catalogues and write a translated scd file per language.
rm -rf .build
"${po4a}" po4a.cfg
if [[ "${?}" != 0 ]]; then
    exit 1
fi

for lang_dir in .build/*/; do
    lang="$(basename "${lang_dir}")"
    mkdir -p "${lang}"
    for input in "${lang_dir}"*.scd; do
        output="${lang}/$(basename "${input%.*}")"
        scdoc < "${input}" > "${output}"
        if [[ "${?}" != 0 ]]; then
            exit 1
        fi
    done
done

rm -rf .build
