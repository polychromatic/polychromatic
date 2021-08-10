#!/usr/bin/python3
#
# This script is used by the CI system to produce changelogs for automated
# Debian/Ubuntu builds.
#
# Parameters: <codename>
#

import datetime
import os
import subprocess
import sys

CODENAME = sys.argv[1]
CHANGELOG = os.path.join(os.path.dirname(__file__), "../../debian/changelog")
PKG_VERSION = "0.0.0"


def run_command(cmd):
    cmd = cmd.split(" ")
    return str(subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode("UTF-8")).strip()


# Determine package version
ver_raw = run_command("git describe --tags")[1:]
ver_parts = ver_raw.split("-")
if len(ver_parts) == 3:
    # Example: 0.6.0-41-g59319b6
    PKG_VERSION = "{0}-{1}~{2}".format(ver_parts[0], ver_parts[1], ver_parts[2])
    START_TAG = "v" + ver_parts[0]
else:
    # Example: 1.0.0
    PKG_VERSION = ver_raw
    START_TAG = "v" + ver_raw


# Generate a changelog to describe latest changes
LOG = run_command("git log {0}..HEAD --oneline".format(START_TAG)).strip()
SIGN_DATE = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S")

def get_changelog():
    lines = []
    lines.append("polychromatic ({0}~{1}) {1}; urgency=low\n\n".format(PKG_VERSION, CODENAME))
    lines.append("  This package was automatically generated.\n\n")
    if len(LOG.split("\n")) > 1:
        lines.append("  Commit changes (newest first):\n\n")
        for line in LOG.split("\n"):
            lines.append("  * " + line + "\n")
    lines.append("\n -- Polychromatic Builder <bot@polychromatic.app>  {0} +0000\n\n".format(SIGN_DATE))

    return "".join(lines)


# Generate and upload each package
with open(CHANGELOG, "w") as f:
    f.writelines(get_changelog())
