#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module is responsible for managing other Polychromatic processes.
"""

import os
import signal
from subprocess import Popen


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
    Returns the PID of either a running Polychromatic process, or the process
    that has 'locked' the device.

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


def start_component(name, parameters=[]):
    """
    Start a new Polychromatic process with 'name' being the suffix of the
    executable, e.g. 'tray-applet'

    Returns a boolean to indicate whether the process successfully spawned.
    """
    bin_filename = "polychromatic-" + name

    # __file__ = procpid.py
    path_relative = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", bin_filename))
    path_system = "/usr/bin/" + bin_filename

    for path in [path_relative, path_system]:
        if os.path.exists(path):
            try:
                bin_arguments = [path]
                bin_arguments += parameters
                Popen(bin_arguments)
                return True
            except Exception as e:
                print("Failed to start process: " + " ".join(bin_arguments))
                print(str(e))
                return False

    print("Could not locate a suitable executable: " + bin_filename)
    print("Tried:")
    print(" - " + path_relative)
    print(" - " + path_system)
    return False


def restart_self(exec_path, exec_args):
    """
    Immediately restart the current execution.
    """
    os.execv(exec_path, exec_args)




def get_preset_state(serial):
    """
    Returns the name of the preset that represents this device's current status.

    This will return None if a preset is not responsible for the device's state.
    """
    tmp_file = os.path.join(_get_pid_dir(), serial + "-preset")

    if os.path.exists(tmp_file):
        with open(tmp_file, "r") as f:
            return str(f.readline().strip())

    return None


def reset_preset_state(serial):
    """
    This device is no longer under the control of a preset.
    """
    tmp_file = os.path.join(_get_pid_dir(), serial + "-preset")

    if os.path.exists(tmp_file):
        os.remove(tmp_file)


def set_preset_state(serial, preset_name):
    """
    Set the name of the preset that is now representing this device's state.
    This is to inform the user that this preset caused the current conditions.
    """
    tmp_file = os.path.join(_get_pid_dir(), serial + "-preset")

    with open(tmp_file, "w") as f:
        f.write(preset_name)


def get_effect_state(serial):
    """
    Get the name and icon of the custom effect that is controlling this device,
    if applicable.

    Returns dict: {name, icon} if applicable, otherwise None.
    """
    name_file = os.path.join(_get_pid_dir(), serial + "-custom-fx-name")
    icon_file = os.path.join(_get_pid_dir(), serial + "-custom-fx-icon")
    name = None
    icon = None

    if os.path.exists(name_file):
        with open(name_file, "r") as f:
            name = str(f.readline().strip())

    if os.path.exists(icon_file):
        with open(icon_file, "r") as f:
            icon = str(f.readline().strip())

        if not os.path.exists(icon):
            icon = None

    if name:
        return {
            "name": name,
            "icon": icon
        }

    return None


def set_effect_state(serial, effect_name, effect_icon):
    """
    Set the name and icon of the custom effect that is controlling this device.
    This is to inform the user.
    """
    fx_name = os.path.join(_get_pid_dir(), serial + "-custom-fx-name")
    fx_icon = os.path.join(_get_pid_dir(), serial + "-custom-fx-icon")

    with open(fx_name, "w") as f:
        f.write(effect_name)

    with open(fx_icon, "w") as f:
        f.write(effect_icon)
