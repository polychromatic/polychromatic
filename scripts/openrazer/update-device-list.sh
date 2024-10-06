#!/bin/bash
#
# Updates the device index of known OpenRazer devices. For development use,
# to be run after OpenRazer releases a new version.
#

POLYCHROMATIC_ROOT="$(dirname "$0")/../../"
DEVICE_JSON="$(realpath "$POLYCHROMATIC_ROOT/data/devices/openrazer.json")"
export PYTHONPATH="$(realpath "$POLYCHROMATIC_ROOT")"
export HOME=/tmp

# Verify path exists
if [ ! -d "$OPENRAZER_SRC" ]; then
    echo "Please set the OPENRAZER_SRC environment variable to the OpenRazer source code:"
    echo -e "\n  export OPENRAZER_SRC=/path/to/repo\n"
    exit 1
fi

echo "Setting up fake environment..."
cd "$OPENRAZER_SRC"
export PYTHONPATH="$(realpath pylib)"

# Set up all fake devices
test_dir="/tmp/daemon_test/"
run_dir="/tmp/daemon_run/"
log_dir="/tmp/daemon_logs/"
$OPENRAZER_SRC/scripts/create_fake_device.py --dest "$test_dir" --non-interactive --all &
sleep 1

# Spawn daemon under fake conditions
openrazer-daemon -s
$OPENRAZER_SRC/daemon/run_openrazer_daemon.py -F --run-dir "$run_dir" --log-dir "$log_dir" --test-dir "$test_dir" &
sleep 2

# Use OpenRazer Python library to discover new devices
echo "Discovering new devices..."
python3 <<EOF
from polychromatic.base import PolychromaticBase
from polychromatic.backends.openrazer import OpenRazerBackend
import json

def _(d): return d

base = PolychromaticBase()
openrazer = OpenRazerBackend(base)
openrazer.init()
devices = openrazer.get_devices()
version = openrazer.version

with open("$DEVICE_JSON") as f:
    index = json.load(f)

for device in devices:
    vidpid = f"{device.vid}:{device.pid}"

    if vidpid not in index.keys():
        print(f"Discovered {vidpid} | {device.name}")
        index[vidpid] = {
            "name": device.name,
            "form_factor": device.form_factor["id"],
            "matrix": f"{device.matrix.cols},{device.matrix.rows}" if device.matrix else None,
            "since": version,
        }

with open("$DEVICE_JSON", "w") as f:
    index = f.write(json.dumps(index, sort_keys=True, indent=4) + "\n")

EOF

# Clean up
kill $(jobs -p)
