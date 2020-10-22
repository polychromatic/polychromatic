#!/bin/bash
#
# This script starts the OpenRazer daemon with fake drivers and performs the
# unit test. This allows the test to be completed on a headless CI server.
#
# This script expects the OPENRAZER_SRC variable to be set pointing to
# the root of the OpenRazer repository, or as the first parameter.
#

POLYCHROMATIC="$(dirname $0)/../"
POLYCHROMATIC="$(realpath $POLYCHROMATIC)"

if [ ! -z "$1" ]; then
    OPENRAZER_SRC="$1"
fi

# Verify path exists
if [ ! -d "$OPENRAZER_SRC" ]; then
    echo "Please set the OPENRAZER_SRC environment variable to the OpenRazer source code:"
    echo -e "\n  export OPENRAZER_SRC=/path/to/repo\n"
    exit 1
fi

if [ ! -f "$OPENRAZER_SRC/scripts/create_fake_device.py" ]; then
    echo "Cannot start the test! create_fake_device.py no longer exists?"
    exit 1
fi

if [ -z "$(which openrazer-daemon)" ]; then
    echo "openrazer-daemon is not installed."
    exit 1
fi

# Stop the daemon if it is running
openrazer-daemon -s

# Start fake driver
test_dir="/tmp/daemon_test/"
run_dir="/tmp/daemon_run/"
log_dir="/tmp/daemon_logs/"
for directory in "$test_dir" "$run_dir" "$log_dir"; do
    if [ -d "$directory" ]; then
        rm -r "$directory"
    fi
    mkdir "$directory"
done

$OPENRAZER_SRC/scripts/create_fake_device.py --dest "$test_dir" --non-interactive --all &
sleep 1

# Start daemon with fake devices
if [ ! -z "$GITHUB_WORKSPACE" ]; then
    # Only CI (GitHub Actions) must run as root due to lack of user groups.
    openrazer-daemon -F --run-dir "$run_dir" --log-dir "$log_dir" --test-dir "$test_dir" --as-root &
else
    # Local testing, should be already part of plugdev group.
    openrazer-daemon -F --run-dir "$run_dir" --log-dir "$log_dir" --test-dir "$test_dir" &
fi
sleep 2

# Perform the test!
cd "$POLYCHROMATIC"
$POLYCHROMATIC/scripts/run-unit-test.sh "21_openrazer"
result=$?

# Stop fake driver / daemon
kill $(jobs -p)

exit $result
