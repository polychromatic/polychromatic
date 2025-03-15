#!/usr/bin/env bash
#
# Updates the device index of known OpenRazer devices. For development use,
# to be run after OpenRazer releases a new version.
#

# Verify path exists
if [[ ! -d "${OPENRAZER_SRC}" ]]; then
    echo "Please set the OPENRAZER_SRC environment variable to the OpenRazer source code:"
    echo -e "\n  export OPENRAZER_SRC=/path/to/repo\n"
    exit 1
fi

POLYCHROMATIC_ROOT="$(dirname "$0")/../../"
POLYCHROMATIC_ROOT="$(realpath "${POLYCHROMATIC_ROOT}")"
DEVICE_JSON="$(realpath "${POLYCHROMATIC_ROOT}/data/devices/openrazer.json")"
DAEMON_LIB="$(realpath "${OPENRAZER_SRC}/daemon")"
DAEMON_PYLIB="$(realpath "${OPENRAZER_SRC}/pylib")"

echo "Setting up fake environment..."
cd "${OPENRAZER_SRC}"
export HOME=/tmp
export PYTHONPATH="${POLYCHROMATIC_ROOT}:${DAEMON_PYLIB}:${DAEMON_LIB}"

# Set up all fake devices
test_dir="/tmp/daemon_test/"
run_dir="/tmp/daemon_run/"
log_dir="/tmp/daemon_logs/"
"${OPENRAZER_SRC}/scripts/create_fake_device.py" --dest "${test_dir}" --non-interactive --all &
sleep 1

# Spawn daemon under fake conditions
openrazer-daemon -s
"${OPENRAZER_SRC}/daemon/run_openrazer_daemon.py" -F --run-dir "${run_dir}" --log-dir "${log_dir}" --test-dir "${test_dir}" &
sleep 2

# Use OpenRazer Python library to discover new devices
echo -ne "\nDiscovering new devices "
python3 <<EOF
from polychromatic.base import PolychromaticBase
from polychromatic.backends.openrazer import OpenRazerBackend
import json

def _(d): return d

base = PolychromaticBase()
openrazer = OpenRazerBackend(base)
openrazer.init()
print("for OpenRazer", openrazer.version, "...")

with open("${DEVICE_JSON}") as f:
    index = json.load(f)

for device in openrazer.get_devices():
    vidpid = f"{device.vid}:{device.pid}"

    if vidpid not in index.keys():
        print(f"Discovered {vidpid} | {device.name}")
        index[vidpid] = {
            "name": device.name,
            "form_factor": device.form_factor["id"],
            "matrix": f"{device.matrix.cols},{device.matrix.rows}" if device.matrix else None,
            "since": openrazer.version,
        }

with open("${DEVICE_JSON}", "w") as f:
    index = f.write(json.dumps(index, sort_keys=True, indent=4) + "\n")

EOF
echo -e "... done!\n"

# Clean up
kill $(jobs -p)
