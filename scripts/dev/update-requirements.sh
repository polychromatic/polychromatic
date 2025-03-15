#!/bin/bash -xe
#
# Updates the repository's requirements.txt file, which is for use with
# the CI's virtual environment.
#
cd "$(dirname "$0")/../../"

TEMP_DIR="$(mktemp -d)"

python -m venv "${TEMP_DIR}"
source "${TEMP_DIR}/bin/activate"

pip install pip-tools
pip-compile -U

git add requirements.txt
git commit -m "CI: Update requirements.txt"
