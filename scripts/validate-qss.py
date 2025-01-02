#!/usr/bin/env python3
#
# Perform basic validation on the Qt stylesheet (QSS) for errors.
#
import os
import sys

REPO_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
QSS_FILE = os.path.join(REPO_ROOT, "data", "qt", "style.qss")

if not os.path.exists(QSS_FILE):
    print(f"Error: File not found: {QSS_FILE}")
    sys.exit(1)

with open(QSS_FILE, "r", encoding="utf-8") as file:
    content = file.read()

    # Check for unclosed braces
    if content.count('{') != content.count('}'):
        print(f"Error: Mismatched braces in {QSS_FILE}")
        print(f"    Open braces: {content.count('{')}")
        print(f"    Close braces: {content.count('}')}")
        sys.exit(1)

sys.exit(0)
