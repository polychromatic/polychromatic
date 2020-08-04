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

    def get_device_all(self):
        """
        Returns a list containing every get_device() dictionary. Devices that
        encounter an error are skipped.
        """
        device_list = self.get_device_list()
        devices = []
        for device_item in device_list:
            device = self.get_device(device_item["backend"], device_item["uid"])
            if type(device) == dict:
                devices.append(device)
        return devices

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

    def _get_current_device_option(self, device):
        """
        Return the currently 'active' option, its parameter and colour(s), if applicable.
        Usually this would be an effect.

        Params:
            device          (dict)      middleman.get_device() object

        Returns list:
        [option_id, option_data, colour_hex]
        """
        option_id = None
        option_data = None
        colour_hex = []
        colour_count = 0
        found_option = None

        for zone in device["zone_options"].keys():
            for option in device["zone_options"][zone]:
                if not "active" in option.keys():
                    continue

                if not option["type"] == "effect":
                    continue

                if option["active"] == True:
                    found_option = option
                    option_id = option["id"]
                    colour_count = option["colours"]

                    try:
                        if len(option["parameters"]) == 0:
                            break
                        else:
                            for param in option["parameters"]:
                                if param["active"] == True:
                                    option_data = param["id"]
                                    colour_count = param["colours"]
                                    break
                    except KeyError:
                        # Toggle or slider do not have a 'parameters' key
                        pass

        for i in range(1, colour_count + 1):
            colour_hex.append(found_option["colour_" + str(i)])

        return [option_id, option_data, colour_hex]

    def set_device_colour_1(self, device, zone, hex_value):
        """
        Replays the currently selected effect (option_id) with the same parameters
        (option_data) but with a different primary colour.

        The return code is the same as set_device_state()
        """
        option_id, option_data, colour_hex = self._get_current_device_option(device)
        colour_hex[0] = hex_value
        return self.set_device_state(device["backend"], device["uid"], device["serial"], zone, option_id, option_data, colour_hex)

    def set_bulk_option(self, option_id, option_data, colours_needed):
        """
        The "Apply to All" function that will set all of the devices to the specified
        effect (option ID and option parameter), such as "breath" and "single", or
        "static" and None.

        The colour for the device will be re-used from a previous selection.

        Params:
            option_id           (str)
            option_data         (str)
            colours_needed      (int)

        Parameters may be determined by the common.get_bulk_apply_options() function.

        Return is null.
        """
        self._dbg.stdout("Setting all devices to '{0}' (parameter: {1})".format(option_id, option_data), self._dbg.action, 1)

        devices = self.get_device_all()
        for device in devices:
            name = device["name"]
            backend = device["backend"]
            uid = device["uid"]
            serial = device["serial"]
            colour_hex = []

            for zone in device["zone_options"].keys():
                # Skip if the device's zone/options doesn't support this request
                skip = True
                for option in device["zone_options"][zone]:
                    if option["id"] == option_id:
                        skip = False

                        for i in range(1, colours_needed + 1):
                            colour_hex.append(option["colour_" + str(i)])

                        break

                if skip:
                    continue

                self._dbg.stdout("- {0} [{1}]".format(name, zone), self._dbg.action, 1)
                result = self.set_device_state(backend, uid, serial, zone, option_id, option_data, colour_hex)
                if result == True:
                    self._dbg.stdout("Request OK", self._dbg.success, 1)
                elif result == False:
                    self._dbg.stdout("Bad request!", self._dbg.error, 1)
                else:
                    self._dbg.stdout("Error: " + str(result), self._dbg.error, 1)

    def set_bulk_colour(self, new_colour_hex):
        """
        The "Apply to All" function that will set all of the devices to the specified
        primary colour. Some devices may not be playing an effect that uses a colour
        (e.g. wave, spectrum) and as such, this will cause no effect.

        Params:
            new_colour_hex      (str)

        Return is null.
        """
        self._dbg.stdout("Setting all primary colours to {0}".format(new_colour_hex), self._dbg.action, 1)

        devices = self.get_device_all()
        for device in devices:
            option_id, option_data, colour_hex = self._get_current_device_option(device)
            name = device["name"]
            backend = device["backend"]
            uid = device["uid"]
            serial = device["serial"]

            for zone in device["zone_options"].keys():

                # Skip if the device's zone/options doesn't support this request
                skip = True
                for option in device["zone_options"][zone]:
                    if option["id"] == option_id:
                        skip = False
                        break

                if skip:
                    continue

                self._dbg.stdout("- {0} [{1}]".format(name, zone), self._dbg.action, 1)
                result = self.set_device_colour_1(device, zone, new_colour_hex)
                if result == True:
                    self._dbg.stdout("Request OK", self._dbg.success, 1)
                elif result == False:
                    self._dbg.stdout("Bad request!", self._dbg.error, 1)
                else:
                    self._dbg.stdout("Error: " + str(result), self._dbg.error, 1)
