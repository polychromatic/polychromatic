#!/usr/bin/python3
#
# Validates the integrity of JSON files and (if applicable) the paths for
# the files exist.
#

import glob
import os
import json
import sys

files = glob.glob("data/**/*.json", recursive=True)
passed = True

for path in files:
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("Invalid JSON: " + path)
        print(str(e))
        passed = False
        continue

    if path.endswith("icons.json"):
        for icon in data:
            if not os.path.exists(os.path.join("data", icon)):
                print("Icon does not exist: " + icon)
                passed = False

if passed:
    sys.exit(0)
else:
    sys.exit(1)
