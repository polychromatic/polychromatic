#!/bin/bash
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
    if [ -z "$(which $1)" ]; then
        echo "Command for '$1' not found."
        missing_tool=true
    fi
}

check_for_tool "intltool-extract"
check_for_tool "xgettext"
check_for_tool "msgcat"
check_for_tool "msgmerge"

if [ "$missing_tool" == true ]; then
    echo -e "\nSome tools are missing. Please install them and run this script again.\n"
    exit 1
fi

# Create a temporary folder where POT files will be assembled
repo_root="$(realpath ../)"
temp_dir=$(realpath "./tmp/")

if [ -d "$temp_dir" ]; then
    rm -r "$temp_dir"
fi
mkdir "$temp_dir"

# Extract strings from Qt Designer (.ui) files
echo -e "\nGenerating locales from Qt Designer files...\n"
cd "$repo_root/data/qt/"
for ui_file in $(ls *.ui); do
    intltool-extract --type="gettext/qtdesigner" $ui_file
    xgettext -a -c --qt $ui_file.h -o $ui_file.pot
    rm $ui_file.h
    mv $ui_file.pot "$temp_dir/"
done

# Extract strings from Python (.py) files
echo -ne "\nGenerating locales from source code...\n"
cd "$repo_root"
for py_file in $(find . -name "*.py"); do
    echo -n "."
    if [ "$(basename $py_file)" == "__init__.py" ]; then
        continue
    fi
    # Some files have the same basename, so keep them unique
    output=$(echo $py_file | sed "s#\/#-#g" | sed "s#\.\-##g")
    xgettext --language=Python "$py_file" -o "$temp_dir/$output.pot"
done
echo " done."

# Concatenate pots into one file
cd "$temp_dir"
msgcat *.pot --use-first > "$repo_root/locale/polychromatic.pot"

# Update existing translations
echo -e "\nUpdating existing locales...\n"
cd "$repo_root/locale/"
for po_file in $(ls *.po); do
    msgmerge $po_file polychromatic.pot -o $po_file.new
    mv $po_file.new $po_file
done

# Clean up
rm -rf "$temp_dir"

echo -e "\nGeneration complete.\n"
