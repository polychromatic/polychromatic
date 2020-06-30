#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module is responsible for managing other Polychromatic processes.
"""

import os
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


def _is_polychromatic_process(pid):
    """
    Verify that the specified PID is actually a Polychromatic process.
    """
    cmdline_file = "/proc/{0}/cmdline".format(pid)

    if os.path.exists(cmdline_file):
        with open(cmdline_file, "r") as f:
            cmdline = f.readline()
    else:
        # No process running here.
        return False

    if cmdline.find("polychromatic-") != -1:
        return True

    # Old PID that is no longer a Polychromatic one.
    return False


def _get_lock_pid(component):
    """
    Returns the PID of a process that has 'locked' a component.

    Returns:
        (int)       Integer to the process.
        None        No lock is in place.
    """
    pid_file = os.path.join(_get_pid_dir(), component + ".pid")

    if not os.path.exists(pid_file):
        return None

    with open(pid_file, "r") as f:
        return int(f.read())


def _set_lock_pid(component):
    """
    Assign the PID of the running process to a component, indicating a 'locked'
    state to avoid multiple instances.
    """
    pid_path = os.path.join(_get_pid_dir(), component + ".pid")

    with open(pid_path, "w") as f:
        f.write(str(os.getpid()))

    return True


def _terminate_process_pid(pid, component):
    """
    Stops the execution of another Polychromatic process.

    Returns:
        True        Process was terminated.
        False       Process does not exist or cannot be terminated.
    """
    if _is_polychromatic_process(pid):
        os.kill(pid, 9)

        pid_path = os.path.join(_get_pid_dir(), component + ".pid")
        os.remove(pid_path)

        return True
    return False


def is_another_instance_running(component):
    """
    Returns the PID of a process if the specified component is running in another
    instance.

    Returns:
        (int)       Process PID (if applicable)
        False       Process not running
    """
    existing_pid = _get_lock_pid(component)
    if existing_pid:
        return existing_pid
    return False


def set_as_device_custom_fx(serial):
    """
    The current process PID will play custom effects for this device. This
    will stop the other process (if necessary) so only one device is controlled
    by one process at a time.
    """
    existing_pid = _get_lock_pid(serial)
    if existing_pid:
        success = _terminate_process_pid(existing_pid, serial)

        if not success:
            return False

    _set_lock_pid(serial)
    return True


def stop_device_custom_fx(serial):
    """
    Stop the process playing custom effects for this device. This may happen if
    the user changes the current effect to a hardware one.
    """
    pid = _get_lock_pid(serial)

    if pid:
        _terminate_process_pid(pid, serial)


def start_component(name, parameters=[]):
    """
    Start a new Polychromatic process with 'name' being the suffix of the
    executable, e.g. 'tray-applet'

    Returns a boolean to indicate whether the process successfully spawned.
    """
    bin_filename = "polychromatic-" + name

    # this __file__ = pylib folder
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


def is_custom_effect_in_use(serial):
    """
    Returns a boolean to indicate if the specified device is 'locked' for custom effects.
    """
    pid = _get_lock_pid(serial)

    if pid:
        if _is_polychromatic_process(pid):
            return True

    return False


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
