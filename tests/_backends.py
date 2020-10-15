#!/usr/bin/python3

import os
import subprocess
import glob
import shutil
import time
import unittest

import openrazer.client

class OpenRazerTest(object):
    """
    This class contains the steps to start and end testing against OpenRazer 2.x
    The OpenRazer driver provides 'fake devices' which are used for testing against.

    - Requires OpenRazer to be installed.
    - The path to the source code needs to be specified as the OPENRAZER_SRC environment variable.
    """
    def __init__(self):
        self.src_path = None
        self.process_fake_driver = None
        self.process_daemon = None

    def start_daemon(self):
        # Check the source code exists.
        try:
            self.src_path = os.environ["OPENRAZER_SRC"]

            if not os.path.exists(os.path.join(self.src_path, "scripts")):
                raise KeyError

        except KeyError:
            print(" ")
            print("Please set the OPENRAZER_SRC environment variable to the OpenRazer source code.")
            print(" ")
            print("  export OPENRAZER_SRC=/path/to/repo")
            print(" ")
            exit(1)

        # Check the scripts are in place.
        if not os.path.exists(os.path.join(self.src_path, "scripts/create_fake_device.py")):
            print("Cannot start the test! create_fake_device.py no longer exists?")
            exit(1)

        # Stop any existing daemon running
        subprocess.call(["openrazer-daemon", "-s"])

        # Test all 'fake' devices
        device_files = glob.glob(self.src_path + "/pylib/openrazer/_fake_driver/*.cfg")
        test_dir = "/tmp/daemon_test/"
        run_dir = "/tmp/daemon_run/"
        log_dir = "/tmp/daemon_logs/"
        devices = []

        for path in device_files:
            devices.append(os.path.basename(path).replace(".cfg", ""))

        for path in [test_dir, run_dir, log_dir]:
            if os.path.exists(path):
                shutil.rmtree(path)
            os.makedirs(path)

        cmd_fake_driver = [self.src_path + "/scripts/create_fake_device.py", "--dest", test_dir, "--non-interactive"] + devices
        self.process_fake_driver = subprocess.Popen(cmd_fake_driver, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        cmd_daemon = ["openrazer-daemon", "-F", "--run-dir", run_dir, "--log-dir", log_dir, "--test-dir", test_dir]
        self.process_daemon = subprocess.Popen(cmd_daemon, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Wait a moment for the daemon to be ready.
        print("Waiting for daemon to be ready...")
        time.sleep(2)
        devman = openrazer.client.DeviceManager()
        devices = devman.devices
        print("Daemon ready.")

        if len(devices) == 0:
            print("No devices loaded!")
            raise Exception

    def stop_daemon(self):
        if self.process_daemon:
            self.process_daemon.kill()

        if self.process_fake_driver:
            self.process_fake_driver.kill()
