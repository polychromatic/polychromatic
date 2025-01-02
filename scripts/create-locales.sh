#!/usr/bin/env bash
#
# Step 1: Extract strings from the application and sync for new changes.
#
# Requires these commands/packages:
#
#   Command             Package Hint
#   ------------------  --------------
#   intltool-extract    intltool
#   xgettext            gettext
#   msgcat              gettext
#   msgmerge            gettext
#
# To test locales, run ./polychromatic-controller-dev instead.
#

cd "$(dirname "$0")"/../locale

# Check all the required tools are present
missing_tool=false
function check_for_tool() {
    if [[ -z "$(type -P "${1}")" ]]; then
        echo "Command for '$1' not found."
        missing_tool=true
    fi
}

check_for_tool "intltool-extract"
check_for_tool "xgettext"
check_for_tool "msgcat"
check_for_tool "msgmerge"

if [[ "${missing_tool}" == true ]]; then
    echo -e "\nSome tools are missing. Please install them and run this script again.\n"
    exit 1
fi

# Create a temporary folder where POT files will be assembled
repo_root="$(realpath ../)"
temp_dir=$(realpath "./tmp/")

if [[ -d "${temp_dir}" ]]; then
    rm -r "${temp_dir}"
fi
mkdir "${temp_dir}"

# Extract strings from Qt Designer (.ui) files
# .ui (XML) --> .h (C) --> .pot
echo -e "\nGenerating locales from Qt Designer files...\n"
cd "${repo_root}/data/qt/" || exit 1
for ui_file in *.ui; do
    intltool-extract --type="gettext/qtdesigner" "${ui_file}"
    xgettext --extract-all --add-comments --qt "${ui_file}.h" -o "${ui_file}.pot"
    rm "${ui_file}.h"

    if [[ -f "${ui_file}.pot" ]]; then
        # intltool-extract caused some characters to escape
        sed -i 's/\&amp\;/\&/g' "${ui_file}.pot"
        sed -i 's/\&quot;/\\\"/g' "${ui_file}.pot"

        # intltool-extract lost whitespace for spinners suffixes, but the code
        # will accommodate this case.

        # File is ready to concatenate later
        mv "${ui_file}.pot" "${temp_dir}/"
    fi
done

# Extract strings from Python (.py) files
echo -ne "\nGenerating locales from source code...\n"
cd "${repo_root}" || exit 1
for py_file in $(find . -name "*.py") "polychromatic-controller" "polychromatic-tray-applet" "polychromatic-cli"; do
    echo -n "."
    if [[ "$(basename ${py_file})" == "__init__.py" ]]; then
        continue
    fi
    # Some files have the same basename, so keep them unique
    output="$(echo "${py_file}" | sed "s#\/#-#g" | sed "s#\.\-##g")"
    xgettext --language=Python "${py_file}" -o "${temp_dir}/${output}.pot"
done
echo " done."

# Concatenate pots into one POT file
cd "${temp_dir}" || exit 1
msgcat *.pot > "${repo_root}/locale/polychromatic.pot"

# Append a string so the source language is set correctly
sed -i '15 i "X-Source-Language: en_GB\\n"' "${repo_root}/locale/polychromatic.pot"

# Update existing translations
echo -e "\nMerging with existing locales...\n"
cd "${repo_root}/locale/" || exit 1
for po_file in $(ls *.po); do
    msgmerge "${po_file}" polychromatic.pot -o "${po_file}.new"
    mv "${po_file}.new" "${po_file}"
done

# Clean up
rm -rf "${temp_dir}"

echo -e "\nGeneration complete.\n"
