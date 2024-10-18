#!/usr/bin/env -S bash -e
#
# Use pylint to validate Python files for errors.
#

# When running in CI, use virtual environment
if [ -d venv ]; then
    source venv/bin/activate
fi

pylint --errors-only \
    --disable="relative-beyond-top-level" \
    --disable="no-name-in-module" \
    --disable="possibly-used-before-assignment" \
    polychromatic-cli \
    polychromatic-controller \
    polychromatic-helper \
    polychromatic-tray-applet \
    polychromatic/*/*.py \
    polychromatic/*.py
