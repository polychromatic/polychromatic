#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
Troubleshooter for OpenRazer 2.x.

Users occasionally may end up with installation problems due to the nature of
having a driver module and requirement of being in the 'plugdev' group.

Troubleshooting this aims to inform the user and prompt some guidelines to
get the system up and running again.

The future of OpenRazer (3.0) aims to move to userspace, which will eliminate
a lot of these issues.
"""

import os
import subprocess
import shutil

try:
    import openrazer.client as rclient
    PYTHON_LIB_PRESENT = True
except Exception:
    PYTHON_LIB_PRESENT = False

def troubleshoot(_):
    """
    See: _backend.Backend.troubleshoot()
    """
    results = []

    try:
        # Troubleshooting only supported on Linux.
        uname = os.uname()
        if uname.sysname != "Linux":
            return None

        # Gather info about OpenRazer Daemon
        try:
            daemon_pid_file = os.path.join(os.environ["XDG_RUNTIME_DIR"], "openrazer-daemon.pid")
        except KeyError:
            daemon_pid_file = os.path.join("/run/user/", str(os.getuid()), "openrazer-daemon.pid")

        # Can openrazer-daemon be found?
        results.append({
            "test_name": _("Check the daemon is installed"),
            "suggestion": _("Install the 'openrazer-meta' package for your distribution."),
            "passed": True if shutil.which("openrazer-daemon") != None else False
        })

        # Is openrazer-daemon running?
        daemon_running = False
        if os.path.exists(daemon_pid_file):
            with open(daemon_pid_file) as f:
                daemon_pid = int(f.readline())
            if os.path.exists("/proc/" + str(daemon_pid)):
                daemon_running = True

        results.append({
            "test_name": _("Check the daemon is running"),
            "suggestion": _("Start the daemon from the terminal. Look out for any errors: $ openrazer-daemon -Fv"),
            "passed": daemon_running
        })

        # Are the Python libraries working?
        results.append({
            "test_name": _("Check the Python library is installed"),
            "suggestion": _("Install the 'python3-openrazer' package for your distribution, or check your PYTHONPATH is correct."),
            "passed": PYTHON_LIB_PRESENT
        })

        # Gather info about DKMS
        if PYTHON_LIB_PRESENT:
            dkms_version = rclient.__version__
            kernel_version = uname.release
            expected_dkms_src = "/var/lib/dkms/openrazer-driver/{0}".format(dkms_version)
            expected_dkms_build = "/var/lib/dkms/openrazer-driver/kernel-{0}-{1}".format(uname.release, uname.machine)

            # Is the OpenRazer DKMS module installed?
            dkms_installed_src = True if os.path.exists(expected_dkms_src) else False
            dkms_installed_built = True if os.path.exists(expected_dkms_build) else False
        else:
            # Cannot automatically check unless we know the version of the modules.
            dkms_installed_src = None
            dkms_installed_built = None

        results.append({
            "test_name": _("Check the DKMS sources are installed"),
            "suggestion": _("Install the 'openrazer-meta' package for your distribution."),
            "passed": dkms_installed_src
        })

        results.append({
            "test_name": _("Check the DKMS module has been built for this kernel version"),
            "suggestion": _("Ensure the correct Linux kernel headers are installed, and try re-installing the DKMS module (replacing 2.x.x with the version of OpenRazer installed) $ sudo dkms install -m openrazer-driver/2.x.x"),
            "passed": dkms_installed_built
        })

        # Can the DKMS module be loaded?
        modprobe = subprocess.Popen(["modprobe", "-n", "razerkbd"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output = modprobe.communicate()[0].decode("utf-8")
        code = modprobe.returncode

        results.append({
            "test_name": _("Check the DKMS module can be loaded"),
            "suggestion": _("For full error details, run $ sudo modprobe razerkbd"),
            "passed": True if code == 0 else False
        })

        # Is a Razer DKMS module loaded right now?
        lsmod = subprocess.Popen(["lsmod"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output = lsmod.communicate()[0].decode("utf-8")

        results.append({
            "test_name": _("Check the DKMS module is currently loaded"),
            "suggestion": _("For full error details, run $ sudo modprobe razerkbd"),
            "passed": True if output.find("razer") != -1 else False
        })

        # Is secure boot the problem?
        if os.path.exists("/sys/firmware/efi"):
            results.append({
                "test_name": _("Check whether secure boot is preventing the module from loading"),
                "suggestion": _("OpenRazer's kernel modules are unsigned, so they will not load at boot. Either disable secure boot in the EFI firmware settings, or sign the modules yourself."),
                "passed": True if output.find("Required key") != -1 else False
            })

        # Is user in plugdev group?
        groups = subprocess.Popen(["groups"], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
        results.append({
            "test_name": _("Check the user account has been added to 'plugdev' group"),
            "suggestion": _("If you've recently installed, you may need to restart the computer. Otherwise, run this command, log out, then log back in to the computer: $ sudo gpasswd -a $USER plugdev"),
            "passed": True if groups.find("plugdev") != -1 else False
        })

        # Does plugdev have permission to read the files in /sys/?
        log_path = os.path.join(os.path.expanduser("~"), ".local/share/openrazer/logs/razer.log")
        if os.path.exists(log_path):
            with open(log_path) as f:
                log = f.readlines()

            results.append({
                "test_name": _("Check the OpenRazer log for plugdev permission errors"),
                "suggestion": _("Restarting (or replugging) usually fixes the problem. Clear the log to reset this message."),
                "passed": True if "".join(log).find("Could not access /sys/") == -1 else False
            })

        # Supported device in lsusb?
        def _get_filtered_lsusb_list():
            """
            A copy of pylib/backends/openrazer._get_filtered_lsusb_list so the troubleshooter
            can run independently.

            Uses 'lsusb' to parse the devices and identify VID:PIDs that are not registered
            by the daemon, usually because they are not compatible yet.
            """
            all_usb_ids = []
            reg_ids = []
            unreg_ids = []

            # Strip lsusb to just get VIDs and PIDs
            try:
                lsusb = subprocess.Popen("lsusb", stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
            except FileNotFoundError:
                self.debug("'lsusb' not available, unable to determine if product is connected.")
                return None

            for usb in lsusb.split("\n"):
                if len(usb) > 0:
                    try:
                        vidpid = usb.split(" ")[5].split(":")
                        all_usb_ids.append([vidpid[0].upper(), vidpid[1].upper()])
                    except AttributeError:
                        pass

            # Get VIDs and PIDs of current devices to exclude them.
            devices = rclient.DeviceManager().devices
            for device in devices:
                try:
                    vid = str(hex(device._vid))[2:].upper().rjust(4, '0')
                    pid = str(hex(device._pid))[2:].upper().rjust(4, '0')
                except Exception as e:
                    print("Got exception parsing VID/PID: " + str(e))
                    continue

                reg_ids.append([vid, pid])

            # Identify Razer VIDs that are not registered in the daemon
            for usb in all_usb_ids:
                if usb[0] != "1532":
                    continue

                if usb in reg_ids:
                    continue

                unreg_ids.append(usb)

            return unreg_ids

        found_unsupported_device = None

        if PYTHON_LIB_PRESENT:
            unsupported_devices = _get_filtered_lsusb_list()
            if len(unsupported_devices) > 0:
                found_unsupported_device = True
            else:
                found_unsupported_device

        results.append({
            "test_name": _("Check for unsupported hardware"),
            "suggestion": _("Check the OpenRazer project (and stable/master branches) to confirm your device is supported."),
            "passed": found_unsupported_device == False
        })

    except Exception as e:
        print("Troubleshooter failed to complete!")
        raise e

    return results
