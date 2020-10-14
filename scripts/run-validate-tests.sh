#!/bin/bash -x

cd "$(dirname "$0")/../"

./scripts/validate-scdoc.sh
./scripts/validate-json.py
./scripts/validate-scss.sh
./scripts/validate-py.sh
