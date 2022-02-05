# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
"""
Troubleshooter for OpenRazer >2.0 and 3.x series.

Users occasionally may end up with installation problems due to the nature of
having a driver module and requirement of being in the 'plugdev' group.

Troubleshooting this aims to inform the user and prompt some guidelines to
get the system up and running again.

The future of OpenRazer aims to move to userspace, which will eliminate
a lot of the common driver issues.
"""

import glob
import grp
import requests
import os
import subprocess
import shutil
import sys

from .. import common
from ..backends import _backend

try:
    from openrazer import client as rclient
    PYTHON_LIB_PRESENT = True
except Exception:
    PYTHON_LIB_PRESENT = False

OPENRAZER_MODULES = ["razerkbd", "razermouse", "razeraccessory", "razerkraken"]

def __get_razer_usb_pids():
    razer_usb_pids = []
    vendor_files = glob.glob("/sys/bus/usb/devices/*/idVendor")
    for vendor in vendor_files:
        with open(vendor, "r") as f:
            vid = str(f.read()).strip().upper()
            if vid == "1532":
                with open(os.path.dirname(vendor) + "/idProduct") as f:
                    pid = str(f.read()).strip().upper()
                    razer_usb_pids.append(pid)
    return razer_usb_pids


def _is_daemon_installed(_):
    return {
        "test_name": _("Daemon is installed"),
        "suggestions": [
            _("Install the 'openrazer-meta' package for your distribution.")
        ],
        "passed": True if shutil.which("openrazer-daemon") != None else False
    }


def _is_daemon_running(_):
    try:
        daemon_pid_file = os.path.join(os.environ["XDG_RUNTIME_DIR"], "openrazer-daemon.pid")
    except KeyError:
        daemon_pid_file = os.path.join("/run/user/", str(os.getuid()), "openrazer-daemon.pid")

    daemon_running = False
    if os.path.exists(daemon_pid_file):
        with open(daemon_pid_file) as f:
            daemon_pid = int(f.readline())
        if os.path.exists("/proc/" + str(daemon_pid)):
            daemon_running = True

    return {
        "test_name": _("Daemon is running"),
        "suggestions": [
            _("Start the daemon from the terminal. Run this command and look for errors:"),
            "$ openrazer-daemon -Fv",
        ],
        "passed": daemon_running
    }


def _is_pylib_installed(_):
    py_version = sys.version.split(" ")[0]
    suggestions = [_("Install 'python-openrazer' or 'python3-openrazer' for your distribution.")]

    if sys.executable.startswith("/usr/bin"):
        suggestions.append(_("Make sure the modules are installed for the correct Python version. Try re-installing."))
    else:
        suggestions.append(_("Your Python installation looks custom. Check your PATH and PYTHONPATH."))

    suggestions.append(_("Currently running Python 3.10.0 from /usr/bin/python3").replace("3.10.0", py_version).replace("/usr/bin/python3", sys.executable))

    for path in sys.path:
        suggestions.append("  -- " + _("Tried path:") + " " + path)

    return {
        "test_name": _("Python library is installed"),
        "suggestions": suggestions,
        "passed": PYTHON_LIB_PRESENT
    }


def _is_driver_src_installed(_):
    if not PYTHON_LIB_PRESENT:
        return {
            "test_name": _("Kernel module sources are installed for DKMS"),
            "suggestions": [
                _("Unable to check because the Python library is not installed.")
            ],
            "passed": None
        }

    if not os.path.exists("/var/lib/dkms"):
        return {
            "test_name": _("Kernel module sources are installed for DKMS"),
            "suggestions": [
                _("OpenRazer is a kernel module, typically built using DKMS."),
                _("Install the 'openrazer-driver-dkms' package for your distribution."),
                _("Some distributions (like Gentoo) may use an alternate system to DKMS."),
            ],
            "passed": None
        }

    driver_version = rclient.__version__
    expected_src_path = "/var/lib/dkms/openrazer-driver/{0}".format(driver_version)

    return {
        "test_name": _("Kernel module sources are installed for DKMS"),
        "suggestions": [
            _("OpenRazer is a kernel module, typically built using DKMS."),
            _("Install the 'openrazer-driver-dkms' package for your distribution."),
        ],
        "passed": True if os.path.exists(expected_src_path) else False
    }


def _is_driver_built(_):
    uname = os.uname()
    kernel_version = uname.release
    driver_version = "<version>"

    if PYTHON_LIB_PRESENT:
        driver_version = rclient.__version__

    modules = glob.glob("/lib/modules/{0}/**/razer*.ko*".format(kernel_version), recursive=True)
    modules += glob.glob("/usr/lib/{0}/**/razer*.ko*".format(kernel_version), recursive=True)

    return {
        "test_name": _("Kernel module has been built for this kernel"),
        "suggestions": [
            _("Ensure you have the correct Linux kernel headers package installed for your distribution."),
            _("Your distro's package system might not have rebuilt the module for this kernel. Try running:"),
            "$ sudo dkms install -m openrazer-driver/x.x.x".replace("x.x.x", driver_version),
        ],
        "passed": len(modules) >= len(OPENRAZER_MODULES)
    }


def _can_driver_be_probed(_):
    try:
        results = []
        for module in OPENRAZER_MODULES:
            modprobe = subprocess.Popen(["modprobe", "-n", module], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            output = modprobe.communicate()[0].decode("utf-8")
            results.append(True if modprobe.returncode == 0 else False)

        return {
            "test_name": _("Kernel module can be probed"),
            "suggestions": [
                "{0} {1}".format(_("OpenRazer uses these modules:"), ", ".join(OPENRAZER_MODULES)),
                _("For full error details, run this and substitute 'razerkbd' as necessary:"),
                "$ sudo modprobe razerkbd",
                _("No output from this command indicates success."),
            ],
            "passed": True if True in results else False
        }
    except FileNotFoundError:
        return {
            "test_name": _("Kernel module can be probed"),
            "suggestions": [
                _("Could not check as '[]' is not installed.").replace("[]", "modprobe"),
                "{0} {1}".format(_("OpenRazer uses these modules:"), ", ".join(OPENRAZER_MODULES)),
            ],
            "passed": None
        }


def _is_driver_loaded(_):
    try:
        lsmod = subprocess.Popen(["lsmod"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output = lsmod.communicate()[0].decode("utf-8")
    except FileNotFoundError:
        return {
            "test_name": _("Kernel module is loaded"),
            "suggestions": [
                "{0} {1}".format(_("OpenRazer uses these modules:"), ", ".join(OPENRAZER_MODULES)),
                _("Could not check as '[]' is not installed.").replace("[]", "lsmod"),
            ],
            "passed": None
        }

    return {
        "test_name": _("Kernel module is loaded"),
        "suggestions": [
            "{0} {1}".format(_("OpenRazer uses these modules:"), ", ".join(OPENRAZER_MODULES)),
            _("For full error details, run this and substitute 'razerkbd' as necessary:"),
            "$ sudo modprobe razerkbd",
            _("No output from this command indicates success."),
            _("If you've just installed, it is recommended to restart the computer."),
        ],
        "passed": True if output.find("razer") != -1 else False
    }


def _is_secure_boot_enabled(_):
    sb_sysfile = glob.glob("/sys/firmware/efi/efivars/SecureBoot*")
    sb_reason = _("Secure Boot prevents the driver from loading, as OpenRazer's kernel modules built by DKMS are usually unsigned.")

    if len(sb_sysfile) > 0:
        # The last digit of this sysfs file indicates whether secure boot is enabled
        secureboot = subprocess.Popen(["od", "--address-radix=n", "--format=u1", sb_sysfile[0]], stdout=subprocess.PIPE)
        status = secureboot.communicate()[0].decode("utf-8").split(" ")[-1].strip()

        return {
            "test_name": _("Check Secure Boot (EFI) status"),
            "suggestions": [
                _("Secure boot is enabled. Turn it off in the system's EFI settings or sign the modules yourself."),
                sb_reason,
            ],
            "passed": True if int(status) == 0 else False
        }

    # Possibly "invalid argument". Can't be sure if it's on or off.
    return {
        "test_name": _("Check Secure Boot (EFI) status"),
        "suggestions": [
            _("Unable to automatically check. If it's enabled, turn it off in the system's EFI settings or sign the modules yourself."),
            sb_reason,
        ],
        "passed": None
    }


def _is_user_in_plugdev_group(_):
    return {
        "test_name": _("User account has been added to the 'plugdev' group"),
        "suggestions": [
            _("Run this command, log out, then log back in to the computer:"),
            "$ sudo gpasswd -a $USER plugdev",
            _("If you've just installed, it is recommended to restart the computer."),
            _("This is required so that your user account (and daemon) has permission to access the driver files in /sys/bus/hid/drivers"),
        ],
        "passed": _backend.BackendHelpers().is_user_in_group("plugdev")
    }


def _is_sysfs_plugdev_permissions_ok(_):
    if not os.path.exists("/sys/bus/hid/drivers/"):
        return {
            "test_name": _("Device can be accessed using plugdev permissions"),
            "suggestions": [
                _("Unable to check as the drivers sysfs path for this Linux kernel is non-standard."),
            ],
            "passed": None
        }

    razer_modules = glob.glob("/sys/bus/hid/drivers/razer*")
    if not razer_modules:
        return {
            "test_name": _("Device can be accessed using plugdev permissions"),
            "suggestions": [
                _("Unable to check because OpenRazer's modules are not loaded."),
            ],
            "passed": None
        }

    # Gather file list
    sysfs_files = []
    for driver in razer_modules:
        for prefix in ["device_", "matrix_"]:
            sysfs_files += glob.glob("{0}/*/{1}*".format(driver, prefix))

    # Check sample of sysfs files have the correct group permission
    results = []
    for sysfile in sysfs_files:
        gid = os.stat(sysfile).st_gid
        group_name = grp.getgrgid(gid)[0]
        results.append(True if group_name == "plugdev" else False)

    return {
        "test_name": _("Device can be accessed using plugdev permissions"),
        "suggestions": [
            _("Permissions for OpenRazer's device files (/sys/bus/hid/drivers) are not set correctly. They should be owned as root:plugdev (owner/group)"),
            _("Replugging the hardware and then restarting the daemon usually fixes the problem."),
            _("Alternately, improperly configured udev rules (such as a missing PID) may cause this to happen."),
        ],
        "passed": False if False in results else True
    }


def _is_razer_device_connected(_):
    razer_usb_pids = __get_razer_usb_pids()

    return {
        "test_name": _("Razer hardware is present for kernel"),
        "suggestions": [
            _("The Linux kernel does not see hardware with a VID of 1532."),
            _("Check the device and USB port is working. Try a different port."),
        ],
        "passed": len(razer_usb_pids) > 0
    }


def _check_device_support_list(_):
    remote_get_url = "https://openrazer.github.io/api/devices.json"
    remote_device_list = None
    missing_pids = []

    try:
        request = requests.get(remote_get_url)
        remote_device_list = request.json()
    except Exception as e:
        # Gracefully ignore connection errors
        print("Could not retrieve OpenRazer data: {0}\n{1}".format(remote_get_url, str(e)))

    def _remote_failed():
        return {
            "test_name": _("Check device compatibility"),
            "suggestions": [
                _("Unable to retrieve this data from OpenRazer's website."),
                _("Check the OpenRazer website to confirm your device is listed as supported."),
                _("If you're checking OpenRazer's GitHub repository, check the 'stable' branch."),
            ],
            "passed": None
        }

    if not remote_device_list:
        return _remote_failed()

    # Get list of USB VIDs and PIDs plugged into the system.
    razer_usb_pids = __get_razer_usb_pids()

    # Check Razer PIDs against remote device list
    try:
        remote_pids = []
        for device in remote_device_list:
            remote_pids.append(device["pid"])
    except KeyError as e:
        print("Remote device list contains invalid data: " + remote_get_url)
        return _remote_failed()

    for pid in razer_usb_pids:
        if not pid in remote_pids:
            missing_pids.append("1532:" + pid)

    return {
        "test_name": _("Check device compatibility"),
        "suggestions": [
            _("The following PIDs are not supported in the latest stable release of OpenRazer:"),
            ", ".join(missing_pids),
            _("Check OpenRazer's issues and pull requests to see the status for your device. Create an issue if necessary."),
        ],
        "passed": len(missing_pids) == 0
    }


def _is_openrazer_up_to_date(_):
    if PYTHON_LIB_PRESENT:
        local_version = rclient.__version__
        remote_version = None
        remote_get_url = "https://openrazer.github.io/api/latest_version.txt"
        try:
            request = requests.get(remote_get_url)

            # Response should be 3 digits, e.g. 3.0.1
            if request.status_code == 200 and len(request.text.strip().split(".")) == 3:
                remote_version = request.text.strip()
        except Exception as e:
            # Gracefully ignore connection errors
            print("Could not retrieve OpenRazer data: {0}\n{1}".format(remote_get_url, str(e)))
            request = None

        def _is_version_newer_then(verA, verB):
            verA = verA.split(".")
            verB = verB.split(".")
            is_new = False

            if int(verA[0]) > int(verB[0]):
                is_new = True

            if float(verA[1] + '.' + verA[2]) > float(verB[1] + '.' + verB[2]):
                is_new = True

            return is_new

        if remote_version:
            return {
                "test_name": _("OpenRazer is the latest version"),
                "suggestions": [
                    _("There is a new version of OpenRazer available."),
                    _("New versions add support for more devices and address device-specific issues."),
                    _("Your version: 0.0.0").replace("0.0.0", local_version),
                    _("Latest version: 0.0.0").replace("0.0.0", remote_version),
                ],
                "passed": _is_version_newer_then(remote_version, local_version) is not True
            }

        return {
            "test_name": _("OpenRazer is the latest version"),
            "suggestions": [
                _("Unable to retrieve this data from OpenRazer's website."),
                _("Check the OpenRazer website to confirm your device is listed as supported."),
                _("If you're checking OpenRazer's GitHub repository, check the 'stable' branch."),
            ],
            "passed": None
        }

    return {
        "test_name": _("OpenRazer is the latest version"),
        "suggestions": [
            _("Unable to check because the Python library is not installed.")
        ],
        "passed": None
    }


def troubleshoot(_, fn_progress_set_max, fn_progress_advance):
    """
    See: _backend.Backend.troubleshoot()
    """
    results = []
    fn_progress_set_max(10)

    # Abort if running on a non-Linux system. Troubleshooting was written for Linux.
    if os.uname().sysname != "Linux":
        return None

    try:
        # Perform the checks in a logical order
        for test in [_is_daemon_installed,
                     _is_pylib_installed,
                     _is_driver_src_installed,
                     _is_driver_built,
                     _can_driver_be_probed,
                     _is_driver_loaded,
                     _is_daemon_running]:
            results.append(test(_))
            fn_progress_advance()

        # EFI systems only
        if os.path.exists("/sys/firmware/efi"):
            results.append(_is_secure_boot_enabled(_))
        fn_progress_advance()

        for test in [_is_razer_device_connected,
                     _is_user_in_plugdev_group,
                     _is_sysfs_plugdev_permissions_ok,
                     _check_device_support_list,
                     _is_openrazer_up_to_date]:
            results.append(test(_))
            fn_progress_advance()

    except Exception as e:
        exception = common.get_exception_as_string(e)
        print("Failed to run OpenRazer troubleshooter!\n" + exception)
        return exception

    return results
