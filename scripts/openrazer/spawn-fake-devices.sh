#!/usr/bin/env bash
#
# Shortcut to test a handful of different kinds of OpenRazer devices
#

export HOME=/tmp

# Verify path exists
if [[ ! -d "${OPENRAZER_SRC}" ]]; then
    echo "Please set the OPENRAZER_SRC environment variable to the OpenRazer source code:"
    echo -e "\n  export OPENRAZER_SRC=/path/to/repo\n"
    exit 1
fi

mkdir -p ~/.config/polychromatic/backends/openrazer
echo -n "0" > ~/.config/polychromatic/backends/openrazer/allow_image_download

config_dir="/tmp/daemon_config/"
test_dir="/tmp/daemon_test"
devices="razerabyssus1800 razerbasilisk razerblackwidowstealth razerblackwidowxchroma razerblade152019advanced razerbladelate2016 razercore razerfireflyv2 razerhuntsmanelite razerkraken7.1chroma razerkrakenkittyedition razernagahex razernommochroma razerorbweaver razerviper"

cd "${OPENRAZER_SRC}"
openrazer-daemon -s

./scripts/create_fake_device.py --dest "${test_dir}" --non-interactive ${devices} &
sleep 1

./daemon/run_openrazer_daemon.py --verbose -F --run-dir "${config_dir}/data" --log-dir "${config_dir}/logs" --test-dir "${test_dir}"
