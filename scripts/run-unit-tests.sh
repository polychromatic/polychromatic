#!/bin/bash
#
# Runs all Polychromatic's unit tests, excluding backends.
#

cd "$(dirname $0)/../"
errors=false

for test in $(ls tests/unit/*.py); do
    ./scripts/run-unit-test.sh "$test"

    if [ $? != 0 ]; then
        errors=true
    fi
done

if [ "$errors" == true ]; then
    echo "Failed to pass all tests."
    exit 1
fi
