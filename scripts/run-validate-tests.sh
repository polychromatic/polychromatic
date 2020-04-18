#!/bin/bash -x

cd "$(dirname "$0")/../"

./tests/validate-scdoc.sh
./tests/validate-json.py
./tests/validate-scss.sh
./tests/validate-js.sh
./tests/validate-py.sh
