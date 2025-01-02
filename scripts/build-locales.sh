#!/usr/bin/env bash
#
# Step 2: After locales have been created and translated, generate compiled
#         locales for the application to use, such as
#         /usr/share/locale/en_GB/LC_MESSAGES/polychromatic.mo
#
# Requires "msgfmt" to be installed (usually provided in the 'gettext' package)
#
# To update locales from the source code, run ./create-locales.sh instead.
#
# Parameters:
#   $1      Optional. Path to save compiled locales
#

cd "$(dirname "$0")"/../locale
output_path="$1"

# Check all the required tools are present
if [[ -z "$(type -P msgfmt)" ]]; then
    echo "Command for 'msgfmt' not found. Locales will not be compiled."
    echo "Try installing a 'gettext' package for your distribution."
    exit 1
fi

# A parameter to the script can optionally override where the place the output.
if [[ -z "${output_path}" ]]; then
    output_path="$(pwd)"
fi

if [[ ! -d "${output_path}" ]]; then
    mkdir "${output_path}"
fi

# Compile locales
echo -n "Compiling locales using 'msgfmt'..."
for file in *.po
do
    locale="${file%.*}"
    locale_path="$output_path/${locale}/LC_MESSAGES/"
    if [[ -d "${locale_path}" ]]; then
        rm -r "${locale_path}"
    fi
    mkdir -p "${locale_path}"
    msgfmt "${locale}.po" -o "${locale_path}/polychromatic.mo"
done
echo " done!"
