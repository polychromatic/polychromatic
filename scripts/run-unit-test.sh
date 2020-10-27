#!/bin/bash
#
# Runs a unit test with the environment variables correctly set.
#
# Usage: ./run-unit-test.sh <test_name>
#
# Test name should NOT have the .py extension.
#

test_name="$1.py"

cd "$(dirname $0)/../"
export PATH=$(realpath .):$PATH
export PYTHONPATH="$(realpath .)"

if [ -z "$test_name" ]; then
    echo "Please enter the name of the test:"
    cd tests/
    for test in $(ls --ignore _*); do
        echo "  - ${test/.*}"
    done
    exit 1
fi

if [ ! -f "tests/$test_name" ]; then
    echo "Test script does not exist: $test_name"
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
python3 tests/$test_name
result=$?

# Clean up temporary home
rm -rf "$temp_home"

exit $result
