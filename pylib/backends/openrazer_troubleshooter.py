#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module is dedicated to resolving common driver/daemon installation issues
with the OpenRazer project.
"""

import os
import subprocess
import shutil

try:
    import openrazer.client as rclient
    PYTHON_LIB_PRESENT = True
except Exception:
    PYTHON_LIB_PRESENT = False


def troubleshoot():
    """
    See: middleman.troubleshoot()
    """
    results = {"success": False}

    # In a future version of OpenRazer (3.0?), most of the troubleshooting is irrelevant as it should be all userspace.

    try:
        # Troubleshooting only supported on Linux.
        uname = os.uname()
        if uname.sysname != "Linux":
            return {"success": False}

        # Gather info about OpenRazer Daemon
        try:
            daemon_pid_file = os.path.join(os.environ["XDG_RUNTIME_DIR"], "openrazer-daemon.pid")
        except KeyError:
            daemon_pid_file = os.path.join("/run/user/", str(os.getuid()), "openrazer-daemon.pid")

        # Can openrazer-daemon be found?
        results["daemon_found"] = True if shutil.which("openrazer-daemon") != None else False

        # Is openrazer-daemon running?
        results["daemon_running"] = False
        if os.path.exists(daemon_pid_file):
            with open(daemon_pid_file) as f:
                daemon_pid = int(f.readline())
            if os.path.exists("/proc/" + str(daemon_pid)):
                results["daemon_running"] = True

        # Are the Python libraries working?
        results["pylib_present"] = PYTHON_LIB_PRESENT

        # Gather info about DKMS
        if PYTHON_LIB_PRESENT:
            dkms_version = rclient.__version__
            kernel_version = uname.release
            expected_dkms_src = "/var/lib/dkms/openrazer-driver/{0}".format(dkms_version)
            expected_dkms_build = "/var/lib/dkms/openrazer-driver/kernel-{0}-{1}".format(uname.release, uname.machine)

            # Is the OpenRazer DKMS module installed?
            results["dkms_installed_src"] = True if os.path.exists(expected_dkms_src) else False
            results["dkms_installed_built"] = True if os.path.exists(expected_dkms_build) else False
        else:
            # Cannot automatically check unless we know the version of the modules.
            results["dkms_installed_src"] = None
            results["dkms_installed_built"] = None

        # Can the DKMS module be loaded?
        modprobe = subprocess.Popen(["modprobe", "-n", "razerkbd"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output = modprobe.communicate()[0].decode("utf-8")
        code = modprobe.returncode
        results["dkms_loaded"] = False
        if code == 0:
            results["dkms_loaded"] = True

        # Is a Razer DKMS module loaded right now?
        lsmod = subprocess.Popen(["lsmod"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output = lsmod.communicate()[0].decode("utf-8")
        if output.find("razer") != -1:
            results["dkms_active"] = True
        else:
            results["dkms_active"] = False

        # Is secure boot the problem?
        if os.path.exists("/sys/firmware/efi"):
            if output.find("Required key") != -1:
                results["secure_boot"] = False
            else:
                results["secure_boot"] = True

        # Is user in plugdev group?
        groups = subprocess.Popen(["groups"], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
        results["plugdev"] = False
        if groups.find("plugdev") != -1:
            results["plugdev"] = True

        # Does plugdev have permission to read the files in /sys/?
        log_path = os.path.join(os.path.expanduser("~"), ".local/share/openrazer/logs/razer.log")
        if os.path.exists(log_path):
            with open(log_path) as f:
                log = f.readlines()
            if "".join(log).find("Could not access /sys/") == -1:
                results["plugdev_perms"] = True
            else:
                results["plugdev_perms"] = False

        # Supported device in lsusb?
        try:
            devman = rclient.DeviceManager()
            rdevices = devman.devices
            devices = _get_incompatible_device_list(rdevices)
            if devices != None:
                results["all_supported"] = True
                if len(devices) > 0:
                    results["all_supported"] = False
        except Exception:
            pass

    except Exception as e:
        print("Troubleshooter did not complete:")
        raise e
        return results

    results["success"] = True
    return results
