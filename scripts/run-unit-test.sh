#!/bin/bash
#
# Runs a unit test isolated from the user's actual configuration.
#
# Usage: ./run-unit-test.sh <path>
#

test_path="$1"

cd "$(dirname $0)/../"
export PATH=$(realpath .):$PATH
export PYTHONPATH="$(realpath .)"

if [ -z "$test_path" ]; then
    echo "Usage: $(basename "$0") <path>"
    exit 1
fi

if [ ! -f "$test_path" ]; then
    echo "Does not exist: $test_path"
    exit 1
fi

# Use an isolated, clean home directory (for config and caches)
temp_home="$(mktemp -d)"
export HOME="$temp_home"
mkdir $HOME/.config $HOME/.cache

# (OpenRazer) Disallow device images from being downloaded
mkdir -p $HOME/.config/polychromatic/backends/openrazer
echo -e '0' > $HOME/.config/polychromatic/backends/openrazer/allow_image_download

# Run the test!
python3 "$test_path"
result=$?

# Clean up temporary home
rm -rf "$temp_home"

exit $result
