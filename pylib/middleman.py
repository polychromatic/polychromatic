#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module collates data from installed backends for supported devices.
Polychromatic's applications will process this data.

Each backend is stored in its own module adjacent to this file. These are
written by inheriting the "Backend" class below and added accordingly.

Refer to the online documentation for more details:
https://polychromatic.app/docs/
"""

from . import procpid

BACKEND_ID_NAMES = {
#   "backend ID": "human readable string"
    "openrazer": "OpenRazer"
}

class Middleman(object):
    """
    The 'middleman' that processes the data between Polychromatic's applications
    by blending all the backends together.
    """
    def __init__(self, dbg, common):
        """
        Stores variables for the sessions.
        """
        self._dbg = dbg
        self._common = common

        # List of initalised Backend() objects.
        self.backends = []

        # List of IDs for modules that are not present.
        self.not_installed = []

        # Keys containing human readable strings for modules that failed to import.
        self.import_errors = {}

    def init(self):
        """
        Imports the modules and initalises the backend objects.
        """
        try:
            from .backends import openrazer as openrazer
            self.backends.append(openrazer.Backend(self._dbg, self._common))
        except (ImportError, ModuleNotFoundError):
            self.not_installed.append("openrazer")
        except Exception as e:
            self.import_errors["openrazer"] = self._common.get_exception_as_string(e)

    def get_backends(self):
        """
        Returns a list of backend IDs that are currently running.
        """
        backends = []
        for module in self.backends:
            backends.append(module.backend_id)
        return backends

    def get_versions(self):
        """
        Return a dictionary of versions for each running backend.
        """
        versions = {}
        for module in self.backends:
            versions[module.backend_id] = module.version
        return versions

    def get_device_list(self):
        """
        Returns a list of connected devices.
        """
        devices = []
        for module in self.backends:
            m_devices = module.get_device_list()
            if type(m_devices) == list:
                devices = devices + m_devices
        return devices

    def get_filtered_device_list(self, form_factor):
        """
        Returns a list of connected devices filtered by a form factor.
        """
        new_list = []
        devices = self.get_device_list()
        for device in devices:
            if device["form_factor"]["id"] == form_factor:
                new_list.append(device)
        return new_list

    def get_unsupported_devices(self):
        """
        Returns a list of connected devices that cannot be controlled by their backend.
        """
        devices = []
        for module in self.backends:
            m_devices = module.get_unsupported_devices()
            if type(m_devices) == list:
                devices = devices + m_devices
        return devices

    def get_device(self, backend, uid):
        """
        Returns a dictionary describing the state of a device.

        In event of an error, an error string is returned to inform the user.
        """
        device = None

        for module in self.backends:
            if module.backend_id == backend:
                device = module.get_device(uid)

        # In case of error, return immediately
        if type(device) in [None, str]:
            return device

        # Append state data
        device["custom_effect_busy"] = procpid.is_custom_effect_in_use(device["serial"])
        device["custom_effect"] = procpid.get_effect_state(device["serial"])
        device["preset"] = procpid.get_preset_state(device["serial"])

        return device

    def set_device_state(self, backend, uid, serial, zone, option_id, option_data, colour_hex):
        """
        Sends a request to the the device, like setting the brightness, the hardware
        effect or a hardware property (such as DPI).

        See _backend.Backend.set_device_state() for parameters and data types.
        """
        # Stop Polychromatic software effect helper for this device if changing an effect
        if option_id == "effect":
            procpid.stop_device_custom_fx(serial)
            procpid.reset_preset_state(serial)

        for module in self.backends:
            if module.backend_id == backend:
                return module.set_device_state(uid, zone, option_id, option_data, colour_hex)

    def get_device_object(self, backend, uid):
        """
        Returns a 'device' object that can be used for drawing frames to a device
        that supports individual addressable LEDs ("matrix")
        """
        for module in self.backends:
            if module.backend_id == backend:
                return module.get_device_object(uid)

    def troubleshoot(self, backend):
        """
        Performs a series of troubleshooting steps to identify possible
        reasons why a particular backend is non-functional.
        """
        for module in self.backends:
            if module.backend_id == backend:
                return module.troubleshoot()

    def restart(self, backend):
        """
        Restarts a specific backend.
        """
        for module in self.backends:
            if module.backend_id == backend:
                return module.restart()
