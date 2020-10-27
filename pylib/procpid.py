#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module is responsible for managing other Polychromatic processes.
"""

import glob
import json
import os
import signal
import shutil
from subprocess import Popen

from . import preferences as pref


def _get_pid_dir():
    """
    Returns the runtime directory for storing process PIDs.
    """
    try:
        pid_dir = os.path.join(os.environ["XDG_RUNTIME_DIR"], "polychromatic")
    except KeyError:
        pid_dir = "/tmp/polychromatic"

    if not os.path.exists(pid_dir):
        os.makedirs(pid_dir)

    return pid_dir


def _get_pid_file(component):
    """
    Returns the path to a PID file.
    """
    return os.path.join(_get_pid_dir(), component + ".pid")


def _is_polychromatic_process(component, pid):
    """
    Verify that the specified PID is actually an alive Polychromatic process.
    """
    cmdline_file = "/proc/{0}/cmdline".format(pid)

    if os.path.exists(cmdline_file):
        with open(cmdline_file, "r") as f:
            cmdline = f.readline()
    else:
        # No process running here!
        return False

    if cmdline.find("polychromatic-") != -1:
        return True

    # This PID is old and no longer belongs to Polychromatic
    pid_file = os.path.join(_get_pid_dir(), component + ".pid")
    os.remove(_get_pid_file(component))
    return False


def get_component_pid(component):
    """
    Returns the PID of a running Polychromatic process, which may be providing
    a feature (e.g. tray applet) or processing software effects for a device.

    Returns:
        (int)       Process ID
        None        Process is not running
    """
    pid_file = _get_pid_file(component)

    if not os.path.exists(pid_file):
        return None

    with open(pid_file, "r") as f:
        pid = int(f.read())

    if _is_polychromatic_process(component, pid):
        return pid

    return None


def get_component_pid_list():
    """
    Returns a list of all the components that currently have a PID file. This
    isn't validated and is presumed to be running and Polychromatic processes.
    """
    for component in glob.glob(_get_pid_dir() + "/*.pid"):
        os.path.basename(component.replace(".pid", ""))


def set_component_pid(component):
    """
    Assign the PID of the running process to a component or device, indicating
    a 'locked' state to avoid multiple instances.

    If the component is already running, it will be stopped.
    """
    pid_file = _get_pid_file(component)

    if os.path.exists(pid_file):
        stop_component(component)

    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    return True


def release_component_pid(component):
    """
    Unassign the PID of the running process from a component or device.
    """
    pid_file = _get_pid_file(component)
    pid = get_component_pid(component)
    if pid == os.getpid():
        os.remove(pid_file)


def is_another_instance_is_running(component):
    """
    Return a boolean to indicate whether this component is already running.
    """
    pid = get_component_pid(component)
    if pid:
        return True
    return False


def stop_component(component):
    """
    Unassign the PID to the running process, allowing it to be used by
    another Polychromatic process.

    This sends the USR2 signal.
    """
    pid_file = _get_pid_file(component)
    pid = get_component_pid(component)
    if pid:
        os.kill(pid, signal.SIGUSR2)


def restart_component(component):
    """
    Send a request to the process to reload itself.

    This sends the USR1 signal.
    """
    pid_file = _get_pid_file(component)
    pid = get_component_pid(component)
    if pid:
        # Already running, ask to restart self
        os.kill(pid, signal.SIGUSR1)
    else:
        # Not running, start!
        start_component(component)


def _get_component_exec_path(name):
    """
    Internally gets the path of a component, such as "tray-applet" or "controller".

    Returns:
        (str)   Path to exceutable, e.g. "/usr/bin/polychromatic-controller"
        None    Executable not found.
    """
    bin_filename = "polychromatic-" + name

    # __file__ = procpid.py
    path_relative = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", bin_filename))
    path_var = shutil.which(bin_filename)
    path_system = "/usr/bin/" + bin_filename

    for path in [path_relative, path_var, path_system]:
        if path and os.path.exists(path):
            return path

    return None


def start_component(name, parameters=[]):
    """
    Start a new Polychromatic process with 'name' being the suffix of the
    executable, e.g. 'tray-applet'

    Returns a boolean to indicate whether the process successfully spawned.
    """
    bin_path = _get_component_exec_path(name)

    try:
        bin_arguments = [bin_path]
        bin_arguments += parameters
        Popen(bin_arguments)
        return True
    except Exception as e:
        print("Failed to start process: " + " ".join(bin_arguments))
        print(str(e))
        return False

    print("Could not locate executable: polychromatic-" + name)
    return False


def is_component_installed(name):
    """
    Checks whether another Polychromatic component is installed. This could be
    because of modular packaging, where a user installs the tray applet, but
    not the Controller, for example.

    Returns a boolean to indicate it is launchable.
    """
    if _get_component_exec_path(name):
        return True
    return False


def restart_self(exec_path, exec_args):
    """
    Immediately restart the current execution.
    """
    os.execv(exec_path, exec_args)


def restart_all():
    """
    Restart all tasks, excluding the current one.
    """
    for pid_file in get_component_pid_list():
        restart_component(pid_file)


class DeviceSoftwareState(object):
    """
    Tracks the active custom software effect or preset for a specified device,
    such as when a custom effect is currently being played and/or a preset is
    currently in use.

    This is metadata for the user interface. It may also be used to resume a
    custom effect or preset state at login.

    The "state" is stored as a JSON file named after the device's serial number.
    {
        "effect": {
            "name": "Human readable name",
            "icon": "<absolute path>",
            "path": "<path to effect JSON>"
        },
        "preset": {
            "name": "Human readable name",
            "icon": "<absolute path>",
            "path": "<path to preset JSON>"
        }
    }
    """
    def __init__(self, serial):
        self.serial = serial
        self.state = {}
        self.state_path = os.path.join(pref.path.states, serial + ".json")

        if not os.path.exists(self.state_path):
            with open(self.state_path, "w") as f:
                f.write("{}")

        self._read_state()

    def _read_state(self):
        with open(self.state_path) as f:
            self.state = json.load(f)

    def _write_state(self):
        with open(self.state_path, "w") as f:
            f.write(json.dumps(self.state))

    def get_preset(self):
        """
        Returns the metadata of the preset that is currently representing this
        device's current status.

        If no preset is set, this will return None.
        """
        try:
            return {
                "name": self.state["preset"]["name"],
                "icon": self.state["preset"]["icon"],
                "path": self.state["preset"]["path"]
            }
        except KeyError:
            return None

    def set_preset(self, name, icon, path):
        """
        This device is now set to the properties of a saved preset.
        """
        self.state["preset"] = {}
        self.state["preset"]["name"] = name
        self.state["preset"]["icon"] = icon
        self.state["preset"]["path"] = path
        self._write_state()

    def clear_preset(self):
        """
        This device no longer matches the preset state.
        """
        try:
            del(self.state["preset"])
            self._write_state()
        except KeyError:
            # Does not exist.
            pass

    def get_effect(self, ignore_pid=False):
        """
        Returns the metadata of the effect that is currently playing on this
        device. This only applies to custom software effects and not any
        backend or hardware effects.

        If no effect is running, this will return None.
        """
        pid = get_component_pid(self.serial)
        if not pid and not ignore_pid:
            return None

        try:
            return {
                "name": self.state["effect"]["name"],
                "icon": self.state["effect"]["icon"],
                "path": self.state["effect"]["path"]
            }
        except KeyError:
            return None

    def set_effect(self, name, icon, path):
        """
        This device is now running under a software effect.
        """
        self.state["effect"] = {}
        self.state["effect"]["name"] = name
        self.state["effect"]["icon"] = icon
        self.state["effect"]["path"] = path
        self._write_state()

    def clear_effect(self):
        """
        This device is no longer running under a software effect.
        """
        try:
            del(self.state["effect"])
            self._write_state()
        except KeyError:
            # Does not exist.
            pass
