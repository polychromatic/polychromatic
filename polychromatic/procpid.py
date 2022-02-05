# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
"""
This module is responsible for managing other Polychromatic processes.
"""

import glob
import json
import os
import signal
import shutil
import subprocess

from . import common


class ProcessManager():
    """
    Stores functions for controlling other Polychromatic processes, which may
    be handling a feature (e.g. tray applet) or playing an effect.

    Other Polychromatic processes may send (and be expected to receive) the
    following signals:

    - USR1 "Reload"
      |- Controller           Refresh current device and/or device list.
      |- Tray                 Reload, device list changed.
      |- Helper (FX)          Reload, current effect data changed.
      |- Helper (Triggers)    Reload, trigger data changed.

    - USR2 "Stop"
      |- Controller           (n/a)
      |- Tray                 Exit tray applet
      |- Helper (FX)          Stop playing effect
      |- Helper (Triggers)    Stop monitoring triggers
    """
    def __init__(self, component=None):
        self.pid_dir = self._get_pid_dir()
        self.component = component
        self.components = ["controller", "tray-applet", "helper"]

    def _get_pid_dir(self):
        """
        Returns the runtime directory for storing process PIDs.
        """
        pid_dir = common.paths.pid_dir

        if not os.path.exists(pid_dir):
            os.makedirs(pid_dir)

        return pid_dir

    def _get_pid_file(self):
        """
        Returns the path to a PID file.
        """
        return os.path.join(self.pid_dir, self.component + ".pid")

    def _is_polychromatic_process(self, component, pid):
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
        pid_file = os.path.join(self.pid_dir, component + ".pid")
        os.remove(self._get_pid_file())
        return False

    def _get_component_pid(self):
        """
        Returns the PID of a running Polychromatic process, which may be providing
        a feature (e.g. tray applet) or processing software effects for a device.

        Returns:
            (int)       Process ID
            None        Process is not running
        """
        pid_file = self._get_pid_file()

        if not os.path.exists(pid_file):
            return None

        if os.path.getsize(pid_file) == 0:
            return None

        with open(pid_file, "r") as f:
            pid = int(f.read())

        if self._is_polychromatic_process(self.component, pid):
            return pid

        return None

    def _get_component_pid_list(self):
        """
        Returns a list of all the components that currently have a PID file. This
        isn't validated and is presumed to be running and is a Polychromatic process.
        """
        pids = []
        for component in glob.glob(self.pid_dir + "/*.pid"):
            pids.append(os.path.basename(component.replace(".pid", "")))

        return pids

    def set_component_pid(self):
        """
        Assign the PID of the running process to a component or device, indicating
        a 'locked' state to avoid multiple instances.

        If the component is already running, it will be stopped.
        """
        pid_file = self._get_pid_file()

        if os.path.exists(pid_file):
            self.stop()

        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))

        return True

    def release_component_pid(self):
        """
        Unassign the PID of the running process from a component or device.
        """
        pid_file = self._get_pid_file()
        pid = self._get_component_pid()
        if pid == os.getpid():
            os.remove(pid_file)

    def is_another_instance_is_running(self):
        """
        Return a boolean to indicate whether this component is already running.
        """
        pid = self._get_component_pid()
        if pid:
            return True
        return False

    def stop(self):
        """
        Send the USR2 signal to the process to ask this component to stop.
        The PID will be unassigned, allowing it to be used by another
        Polychromatic process.
        """
        pid = self._get_component_pid()
        if pid:
            os.kill(pid, signal.SIGUSR2)

    def reload(self, pid_file=None):
        """
        Send the USR1 signal to reload or restart the component. The PID is
        expected to be reassigned to the new process.
        """
        if not pid_file:
            pid_file = self._get_pid_file()

        pid = self._get_component_pid()
        if pid:
            # Already running, ask to restart self
            os.kill(pid, signal.SIGUSR1)
        else:
            # Not running, start!
            self.start_component()

    def _get_component_exec_path(self, name):
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

    def start_component(self, parameters=[]):
        """
        Start a new Polychromatic process with 'name' being the suffix of the
        executable, e.g. 'tray-applet'

        Returns a boolean to indicate whether the process successfully spawned.
        """
        if self.component not in self.components:
            return False

        bin_path = self._get_component_exec_path(self.component)

        try:
            bin_arguments = [bin_path]
            bin_arguments += parameters
            subprocess.Popen(bin_arguments, env=dict(os.environ))
            return True
        except Exception as e:
            print("Failed to start process: " + " ".join(bin_arguments))
            print(str(e))
            return False

        print("Could not locate executable: polychromatic-" + self.component)
        return False

    def is_component_installed(self, name):
        """
        Checks whether another Polychromatic component is installed. This could be
        because of modular packaging, where a user installs the tray applet, but
        not the Controller, for example.

        Returns a boolean to indicate it is launchable.
        """
        if self._get_component_exec_path(name):
            return True
        return False

    def restart_self(self, exec_path, exec_args):
        """
        Immediately restart the current execution.
        """
        os.execv(exec_path, exec_args)

    def restart_all(self):
        """
        Restart all tasks, excluding the current process.
        """
        for pid_file in self._get_component_pid_list():
            procmgr = ProcessManager(pid_file)
            procmgr.reload(pid_file)


class DeviceSoftwareState(object):
    """
    Tracks the active custom software effect or preset for a specified device,
    such as when a custom effect is currently being played and/or a preset is
    currently in use.

    This is metadata presented to the user and internally to know the last
    effect or preset (when autostarting)

    The "state" is stored in a JSON file named after the device's serial number.
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
        self.state_path = os.path.join(common.paths.states, serial + ".json")

        if not os.path.exists(self.state_path):
            with open(self.state_path, "w") as f:
                f.write("{}")

        self._read_state()

    def _read_state(self):
        with open(self.state_path) as f:
            try:
                self.state = json.load(f)
            except Exception:
                # Bad JSON or filesystem error. Ignore and start afresh.
                print("Ignoring bad data: ", self.state_path)
                self.state = {}

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
        This device is now aligned to the properties of a saved preset.
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

    def get_effect(self):
        """
        Returns the metadata of the effect that is currently playing on this
        device. This only applies to custom software effects and not any
        backend or hardware effects.

        If no effect is running, this will return None.
        """
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
        This device is no longer under software control.
        """
        try:
            del(self.state["effect"])
            self._write_state()
        except KeyError:
            # Does not exist.
            pass
