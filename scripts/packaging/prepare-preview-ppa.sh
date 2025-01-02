#!/usr/bin/env bash
#
# This script prepares the Preview PPA containing the latest builds for Ubuntu.
#
# Expected to be run by CI system.
# Parameters: <path to src code>
#

REPO_ROOT="$(realpath "$1")"

function process_release() {
    release="$1"
    codename="$2"

    echo -e "\n${codename}"
    echo -e "===================="
    TEMP_DIR="$(mktemp -d)"
    git clone "${REPO_ROOT}" "${TEMP_DIR}/src"
    cd "${TEMP_DIR}/src"
    ./scripts/packaging/generate-debian-changelog.py "${release}" "${codename}"
    debuild -S
    debsign -k 49D6E0C94C9832E63FDBD50BEAF6D6A2C65D1D85 ../*.changes
    dput ppa:polychromatic/preview ../*.changes
}

process_release "24.04" "noble"     # LTS
process_release "24.10" "oracular"
process_release "25.04" "plucky"
