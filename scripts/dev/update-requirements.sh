#!/bin/bash -x

cd "$(dirname "$0")/../../"
python -m venv /tmp/venv
source /tmp/venv/bin/activate
pip install pip-tools
pip-compile -U
