#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2020 Luke Horwell <code@horwell.me>
#
"""
This module abstracts data from the OpenRazer Python library (and daemon)
and parses this for Polychromatic to use.

Project URL: https://github.com/openrazer/openrazer
"""

import os
import subprocess
import grp

# Imported on demand:
# import requests       _get_device_image() for retrieving device image URLs

from . import _backend

from openrazer import client as rclient


class Backend(_backend.Backend):
    """
    Bindings for the OpenRazer 2.x Python library.
    """
    def __init__(self, dbg, common):
        super().__init__(dbg, common)
        self.backend_id = "openrazer"
        self.logo = "openrazer.svg"
        self.version = rclient.__version__
        self.project_url = "https://openrazer.github.io"
        self.bug_url = "https://github.com/openrazer/openrazer/issues"
        self.releases_url = "https://github.com/openrazer/openrazer/releases"
        self.license = "GPLv2"

        # Variables for OpenRazer
        self.devman = None
        self.devices = None
        self.allow_image_download = True
        self.ripple_speed = 0.01
        self.starlight_speed = 0.01

    def _reinit_device_manager(self):
        """
        OpenRazer uses a "Device Manager" containing devices connected. It needs
        to be refreshed when devices are connected/disconnected.
        """
        self.debug("Initalising Device Manager...")
        try:
            self.devman = rclient.DeviceManager()
            self.devman.sync_effects = False
            self.devices = self.devman.devices
            return True
        except Exception as e:
            return self.common.get_exception_as_string(e)

    def get_device_list(self):
        """
        See _backend.get_device_list()
        """
        devices = []
        uid = -1

        if not self.devices:
            success = self._reinit_device_manager()
            if success != True:
                return success

        for rdevice in self.devices:
            uid += 1

            devices.append({
                "backend": self.backend_id,
                "uid": uid,
                "name": rdevice.name,
                "serial": str(rdevice.serial),
                "form_factor": self._get_form_factor(rdevice.type),
                "real_image": self._get_device_image(rdevice),
                "zones": self._get_supported_zones(rdevice)
            })

        return devices

    def get_unsupported_devices(self):
        """
        See _backend.get_unsupported_devices()

        Connected Razer hardware not bound to the daemon likely means the driver/daemon
        isn't set up correctly or the hardware isn't supported yet.
        """
        devices = []
        unknown_list = self._get_filtered_lsusb_list()
        form_factor = self._get_form_factor("unrecognised")

        for vid, pid in unknown_list:
            devices.append({
                "backend": self.backend_id,
                "name": "{0}:{1}".format(vid, pid),
                "form_factor": form_factor,
            })

        return devices

    def get_device(self, uid):
        """
        See _backend.get_device()
        """
        try:
            success = self._reinit_device_manager()
            if success != True:
                return success
            rdevice = self.devman.devices[uid]
        except IndexError:
            return None
        except Exception as e:
            return self.common.get_exception_as_string(e)

        form_factor = self._get_form_factor(rdevice.type)
        real_image = self._get_device_image(rdevice)

        _vid_pid = self._get_device_vid_pid(rdevice)
        vid = _vid_pid.get("pid")
        pid = _vid_pid.get("vid")

        # Determine device variables
        firmware_version = None
        keyboard_layout = None
        monochromatic = self._is_device_monochromatic(rdevice)
        macros = False              # Supports key rebinding
        game_mode = None            # Keyboards only
        matrix = False              # Supports custom effects (per-key lighting)
        battery_charging = False
        battery_level = None
        matrix_rows = None
        matrix_cols = None
        dpi_x = None
        dpi_y = None
        dpi_min = None
        dpi_max = None
        dpi_single = False          # E.g. DeathAdder 3.5G only inputs X, Y = -1
        dpi_ranges = []
        poll_rate = None
        poll_rate_ranges = [125, 500, 1000] # Cannot be changed

        # Retrieve device variables
        if rdevice.has("name"):
            name = rdevice.name
        else:
            self.debug("Device {0} doesn't have a name!".format(uid))
            name = "Device " + str(uid)

        if rdevice.has("serial"):
            serial = str(rdevice.serial)
            if not type(serial) == str or len(serial) <= 2:
                self.debug("Got bad serial for {0}!".format(name))
                serial = "0"
        else:
            self.debug("Device {0} doesn't have a valid serial!".format(uid))
            name = "invalid_device_" + str(uid)

        if rdevice.has("firmware_version"):
            firmware_version = rdevice.firmware_version

        if rdevice.has("keyboard_layout"):
            keyboard_layout = rdevice.keyboard_layout

        if rdevice.has("lighting_led_matrix"):
            matrix = True
            matrix_rows = rdevice.fx.advanced.rows
            matrix_cols = rdevice.fx.advanced.cols

        if rdevice.has("dpi"):
            dpi_x = rdevice.dpi[0]
            dpi_y = rdevice.dpi[1]
            dpi_min = 100
            dpi_max = rdevice.max_dpi

            default_ranges = {
                16000: [200, 800, 1800, 4500, 9000, 16000],
                8200: [200, 800, 1800, 4800, 6400, 8200]
            }

            # Generate a range if a default isn't known
            try:
                dpi_ranges = default_ranges[dpi_max]
            except KeyError:
                dpi_ranges = [200,
                    int(dpi_max / 10),
                    int(dpi_max / 8),
                    int(dpi_max / 4),
                    int(dpi_max / 2),
                    int(dpi_max)
                ]

            # DeathAdder 3.5G only supports DPI X (#209)
            if rdevice.has("available_dpi"):
                dpi_single = True

        if rdevice.has("poll_rate"):
            poll_rate = rdevice.poll_rate

        if rdevice.has("battery"):
            battery_level = rdevice.battery_level
            battery_charging = rdevice.is_charging

        # Build an index of zones, parameters and what's currently set.
        _zones = self._get_supported_zones(rdevice)
        zone_icons = self._get_zone_icons(_zones, name)
        zone_options = {}

        def _device_has_zone_capability(capability):
            return self._device_has_zone_capability(rdevice, zone, capability)

        for zone in _zones:
            options = []
            rzone = self._get_zone_as_object(rdevice, zone)

            # Brightness - toggle or slider?
            brightness_parent, brightness_type = self._get_device_brightness(rdevice, zone)

            if brightness_type == int:
                options.append({
                    "id": "brightness",
                    "type": "slider",
                    "value": round(brightness_parent.brightness),
                    "min": 0,
                    "max": 100,
                    "step": 5,
                    "suffix": "%",
                    "colours": [] # n/a
                })

            elif brightness_type == bool:
                options.append({
                    "id": "brightness",
                    "type": "toggle",
                    "active": True if brightness_parent.active else False,
                    "colours": [] # n/a
                })

            # Hardware Effects
            current_state = self._read_persistence_storage(rdevice, zone)

            for effect in ["spectrum", "wave", "reactive", "ripple", "static", "pulsate", "blinking"]:
                if _device_has_zone_capability(effect):
                    effect_option = {
                        "id": effect,
                        "type": "effect",
                        "parameters": [],
                        "colours": [],
                        "active": current_state["effect"].startswith(effect)
                    }

                    # Add parameters and determine what is in use
                    if effect == "wave":
                        # Change label IDs depending on orientation.
                        direction_1 = "right"
                        direction_2 = "left"

                        if rdevice.type == "mouse":
                            direction_1 = "up"
                            direction_2 = "down"

                        elif rdevice.type == "mousemat":
                            direction_1 = "anticlock"
                            direction_2 = "clock"

                        effect_option["parameters"] = [
                            {
                                "id": direction_2,
                                "data": 2,
                                "active": current_state["wave_dir"] == 2,
                                "colours": []
                            },
                            {
                                "id": direction_1,
                                "data": 1,
                                "active": current_state["wave_dir"] == 1,
                                "colours": []
                            }
                        ]

                    elif effect == "ripple":
                        if _device_has_zone_capability("ripple_random"):
                            effect_option["parameters"].append({
                                "id": "random",
                                "data": "random",
                                "active": current_state["effect"] == "rippleRandomColour",
                                "colours": []
                            })

                        if _device_has_zone_capability("ripple"):
                            effect_option["parameters"].append({
                                "id": "single",
                                "data": "single",
                                "active": current_state["effect"] == "ripple",
                                "colours": [current_state["colour_1"]]
                            })

                    elif effect == "reactive":
                        effect_option["parameters"] = [
                            {
                                "id": "fast",
                                "data": 1,
                                "active": current_state["speed"] == 1,
                                "colours": [current_state["colour_1"]]
                            },
                            {
                                "id": "medium",
                                "data": 2,
                                "active": current_state["speed"] == 2,
                                "colours": [current_state["colour_1"]]
                            },
                            {
                                "id": "slow",
                                "data": 3,
                                "active": current_state["speed"] == 3,
                                "colours": [current_state["colour_1"]]
                            },
                            {
                                "id": "vslow",
                                "data": 4,
                                "active": current_state["speed"] == 4,
                                "colours": [current_state["colour_1"]]
                            }
                        ]

                    elif effect in "static":
                        effect_option["colours"] = [current_state["colour_1"]]

                    effect_option["active"] = True if current_state["effect"].startswith(effect) else False

                    options.append(effect_option)

            # There is no 'lighting_breath' or 'lighting_starlight' in the capabilities list
            def _get_multi_effect_parameters(effect):
                effect_option = {
                    "id": effect,
                    "type": "effect",
                    "parameters": [],
                    "colours": [],
                    "active": current_state["effect"].startswith(effect)
                }

                for _colour_count, param in enumerate(["random", "single", "dual", "triple"]):
                    if _device_has_zone_capability(effect + "_" + param):
                        _colour_list = []
                        for c in range(1, _colour_count + 1):
                            _colour_list.append(current_state["colour_" + str(c)])
                        param_key = {
                            "id": param,
                            "data": param,
                            "active": current_state["effect"].endswith(param.capitalize()),
                            "colours": _colour_list
                        }
                        effect_option["parameters"].append(param_key)

                return effect_option

            if True in [_device_has_zone_capability("breath_random"),
                        _device_has_zone_capability("breath_single"),
                        _device_has_zone_capability("breath_dual"),
                        _device_has_zone_capability("breath_triple")]:
                options.append(_get_multi_effect_parameters("breath"))

            if True in [_device_has_zone_capability("starlight_random"),
                        _device_has_zone_capability("starlight_single"),
                        _device_has_zone_capability("starlight_dual")]:
                options.append(_get_multi_effect_parameters("starlight"))

            # DPI is a special control, variables have been populated earlier.

            # Finished building options list
            zone_options[zone] = options

        # Other hardware features
        def _init_main_if_empty():
            if "main" not in zone_options.keys():
                zone_options["main"] = []

        if rdevice.has("game_mode_led"):
            _init_main_if_empty()
            zone_options["main"].append({
                "id": "game_mode",
                "type": "toggle",
                "active": True if rdevice.game_mode_led else False,
                "colours": [] # n/a
            })

        if rdevice.has("poll_rate"):
            _init_main_if_empty()
            params = []
            for rate in poll_rate_ranges:
                params.append({
                    "id": "{0}Hz".format(rate),
                    "data": rate,
                    "active": poll_rate == rate,
                    "colours": [] # n/a
                })
            zone_options["main"].append({
                "id": "poll_rate",
                "type": "multichoice",
                "parameters": params,
                "active": True,         # Always a poll rate
                "colours": [] # n/a
            })

        # Prepare summary of device.
        summary = []
        _multiple_zones = len(_zones) > 1

        # -- Gather current states for effects/brightness.
        # -- If all zones are the same, show that status, otherwise state (Multiple)
        # -- Not all statuses are shown at once since this can be crowded for some devices.
        _effects = []
        _brightness = []
        for zone in zone_options:
            for option in zone_options[zone]:
                if option["type"] == "effect" and option["active"] == True:
                    _effects.append(option["id"])

                if option["id"] == "brightness" and "value" in option.keys():
                    _brightness.append(option["value"])

                if option["id"] == "brightness" and "active" in option.keys():
                     _brightness.append(option["active"])

        def is_same(items):
            return all(x == items[0] for x in items)

        # -- Effects
        if len(_effects) > 0:
            if is_same(_effects):
                summary.append({
                    "icon": self.common.get_icon("options", _effects[0]),
                    "string_id": _effects[0]
                })
            else:
                summary.append({
                    "icon": self.common.get_icon("options", "static"),
                    "string_id": "multiple"
                })

        # -- Brightness
        if len(_brightness) > 0:
            # Only show % suffix for integers
            if not is_same(_brightness):
                summary.append({
                    "icon": self.common.get_icon("options", "75"),
                    "string_id": "multiple"
                })
            elif _brightness[0] == True:
                summary.append({
                    "icon": self.common.get_icon("options", "100"),
                    "string_id": "on"
                })
            elif _brightness[0] in [False, 0]:
                summary.append({
                    "icon": self.common.get_icon("options", "50"),
                    "string_id": "off"
                })
            elif type(_brightness[0]) in [int, float]:
                summary.append({
                    "icon": self.common.get_icon("options", "100"),
                    "string": "{0}%".format(_brightness[0])
                })

        # -- Game Mode
        if game_mode:
            summary.append({
                "icon": self.common.get_icon("options", "game_mode"),
                "string_id": "game_mode"
            })

        # -- DPI
        if dpi_x or dpi_y:
            if dpi_x == dpi_y or dpi_single:
                summary.append({
                    "icon": self.common.get_icon("general", "dpi"),
                    "string": "{0} DPI".format(dpi_x)
                })
            else:
                summary.append({
                    "icon": self.common.get_icon("general", "dpi"),
                    "string": "{0}, {1} DPI".format(dpi_x, dpi_y)
                })

        # -- Poll Rate
        if poll_rate:
            summary.append({
                "icon": self.common.get_icon("options", "poll_rate"),
                "string": "{0} Hz".format(poll_rate)
            })

        # -- Battery Status
        if battery_level:
            if battery_charging:
                icon = "battery-charging"
            else:
                if battery_level < 10:
                    icon = "battery-0"
                elif battery_level < 30:
                    icon = "battery-25"
                elif battery_level < 55:
                    icon = "battery-50"
                elif battery_level < 90:
                    icon = "battery-75"
                else:
                    icon = "battery-100"

            summary.append({
                "icon": self.common.get_icon("general", icon),
                "string": "{0}%".format(battery_level)
            })

        return {
            "backend": self.backend_id,
            "uid": uid,
            "name": name,
            "form_factor": form_factor,
            "real_image": real_image,
            "serial": serial,
            "monochromatic": monochromatic,
            "vid": vid,
            "pid": pid,
            "firmware_version": firmware_version,
            "keyboard_layout": keyboard_layout,
            "summary": summary,
            "dpi_x": dpi_x,
            "dpi_y": dpi_y,
            "dpi_single": dpi_single,
            "dpi_ranges": dpi_ranges,
            "dpi_min": dpi_min,
            "dpi_max": dpi_max,
            "matrix": matrix,
            "matrix_rows": matrix_rows,
            "matrix_cols": matrix_cols,
            "zone_icons": zone_icons,
            "zone_options": zone_options
        }

    def set_device_state(self, uid, zone, option_id, option_data, colours=[]):
        """
        See _backend.set_device_state()
        """
        try:
            success = self._reinit_device_manager()
            if success != True:
                return success
            rdevice = self.devman.devices[uid]
        except IndexError:
            return None
        except Exception as e:
            return self.common.get_exception_as_string(e)

        # DPI may not associated with a zone (CLI only)
        if not zone:
            zone = "main"

        rzone = self._get_zone_as_object(rdevice, zone)

        # Hardware effects require up to 3 colours. Daemon uses RGB integers (0-255)
        colour_hex = colours
        colour_1 = [0, 255, 0]
        colour_2 = [255, 0, 0]
        colour_3 = [0, 0, 255]

        if colours:
            try:
                if colours[0]:
                    colour_1 = self.common.hex_to_rgb(colours[0])
                if colours[1]:
                    colour_2 = self.common.hex_to_rgb(colours[1])
                if colours[2]:
                    colour_3 = self.common.hex_to_rgb(colours[2])
            except IndexError:
                # Expected, as not all colours may be needed. Use default.
                pass

        try:
            # Brightness or active?
            brightness_parent, brightness_type = self._get_device_brightness(rdevice, zone)

            if option_id == "brightness":
                # Slider value or CLI string
                if brightness_type in [int, str]:
                    brightness_parent.brightness = int(option_data)

                elif brightness_type == bool:
                    brightness_parent.active = option_data

            # Effects and their parameters
            elif option_id == "spectrum":
                rzone.spectrum()
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "spectrum")

            elif option_id == "wave":
                # Params: <direction 1-2>
                rzone.wave(int(option_data))
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "wave")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "wave_dir", option_data)

            elif option_id == "reactive":
                # Params: <red> <green> <blue> <speed 1-4>
                rzone.reactive(colour_1[0], colour_1[1], colour_1[2], int(option_data))
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "reactive")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "speed", option_data)
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])

            elif option_id == "blinking":
                # Params: <red> <green> <blue>
                rzone.blinking(colour_1[0], colour_1[1], colour_1[2])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "blinking")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])

            elif option_id == "breath" and option_data == "random":
                rzone.breath_random()
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "breathRandom")

            elif option_id == "breath" and option_data == "single":
                # Params: <red> <green> <blue>
                rzone.breath_single(colour_1[0], colour_1[1], colour_1[2])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "breathSingle")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])

            elif option_id == "breath" and option_data == "dual":
                # Params: <red1> <green1> <blue1> <red2> <green2> <blue2>
                rzone.breath_dual(colour_1[0], colour_1[1], colour_1[2],
                    colour_2[0], colour_2[1], colour_2[2])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "breathDual")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_2", colour_hex[1])

            elif option_id == "breath" and option_data == "triple":
                # Params: <red1> <green1> <blue1> <red2> <green2> <blue2> <red3> <green3> <blue3>
                rzone.breath_triple(colour_1[0], colour_1[1], colour_1[2],
                    colour_2[0], colour_2[1], colour_2[2],
                    colour_3[0], colour_3[1], colour_3[2])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "breathTriple")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_2", colour_hex[1])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_3", colour_hex[2])

            elif option_id == "pulsate":
                # Params: <red> <green> <blue>
                rzone.pulsate(colour_1[0], colour_1[1], colour_1[2])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "pulsate")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])

            elif option_id == "ripple" and option_data == "single":
                # Params: <red> <green> <blue> <speed>
                rzone.ripple(colour_1[0], colour_1[1], colour_1[2], self.ripple_speed)
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "ripple")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])

            elif option_id == "ripple" and option_data == "random":
                # Params: <speed>
                rzone.ripple_random(self.ripple_speed)
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "rippleRandomColour")

            elif option_id == "starlight" and option_data == "single":
                # Params: <red> <green> <blue> <speed>
                rzone.starlight_single(colour_1[0], colour_1[1], colour_1[2], self.starlight_speed)
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "starlightSingle")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "speed", option_data)
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])

            elif option_id == "starlight" and option_data == "dual":
                # Params: <red1> <green1> <blue1> <red2> <green2> <blue2> <speed>
                rzone.starlight_dual(colour_1[0], colour_1[1], colour_1[2],
                    colour_2[0], colour_2[1], colour_2[2], self.starlight_speed)
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "starlightDual")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "speed", option_data)
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_2", colour_hex[1])

            elif option_id == "starlight" and option_data == "random":
                # Params: <speed>
                rzone.starlight_random(self.starlight_speed)
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "starlightRandom")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "speed", option_data)

            elif option_id == "static":
                # Params: <red> <green> <blue>
                rzone.static(colour_1[0], colour_1[1], colour_1[2])
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "effect", "static")
                self._write_persistence_storage_fallback(rdevice, zone, rzone, "colour_1", colour_hex[0])

            # Other
            elif option_id == "game_mode":
                # Params: <true/false>
                rdevice.game_mode_led = option_data

            elif option_id == "dpi":
                # Params: <dpi X> <dpi Y>
                # DeathAdder 3.5G only supports DPI X (#209)
                if rdevice.has("available_dpi"):
                    rdevice.dpi = (int(option_data[0]), -1)
                else:
                    rdevice.dpi = (int(option_data[0]), int(option_data[1]))

            elif option_id == "poll_rate":
                # Params: (int)
                rdevice.poll_rate = int(option_data)

            else:
                return False

        except Exception as e:
            return self.common.get_exception_as_string(e)

        return True

    def _get_form_factor(self, device_type):
        """
        Convert the device type returned by OpenRazer to match one used within Polychromatic.
        """
        openrazer_to_poly = {
            "firefly": "mousemat",
            "tartarus": "keypad",
            "core": "gpu",
            "mug": "accessory"
        }

        try:
            form_factor_id = openrazer_to_poly[device_type]
        except KeyError:
            form_factor_id = device_type

        return self.common.get_form_factor(form_factor_id)

    def _get_zone_as_object(self, rdevice, zone):
        """
        Returns an object that directly references this device's "zone".
        """
        zone_to_device = {
            "main": rdevice.fx,
            "logo": rdevice.fx.misc.logo,
            "scroll": rdevice.fx.misc.scroll_wheel,
            "backlight": rdevice.fx.misc.backlight
        }

        # Ignore missing left/right classes, most devices do not support these.
        try:
            zone_to_device["left"] = rdevice.fx.misc.left
            zone_to_device["right"] = rdevice.fx.misc.right
        except Exception:
            pass

        return zone_to_device[zone]

    def _device_has_zone_capability(self, rdevice, zone, capability):
        """
        Returns a boolean whether the capability is available for the specified zone.

        For example, "active" for zone "logo" will check "lighting_logo_active"
        """
        zone_to_capability = {
            "main": "lighting",
            "logo": "lighting_logo",
            "scroll": "lighting_scroll",
            "backlight": "lighting_backlight",
            "left": "lighting_left",
            "right": "lighting_right"
        }
        return rdevice.has(zone_to_capability[zone] + "_" + capability)

    def _get_supported_zones(self, rdevice):
        """
        Returns a list of zones that are supported by the device.
        """
        zones = []

        if rdevice.has("lighting"):
            zones.append("main")
        if rdevice.has("lighting_logo") or rdevice.has("lighting_logo_active"):
            zones.append("logo")
        if rdevice.has("lighting_scroll") or rdevice.has("lighting_scroll_active"):
            zones.append("scroll")
        if rdevice.has("lighting_left"):
            zones.append("left")
        if rdevice.has("lighting_right"):
            zones.append("right")
        if rdevice.has("lighting_backlight"):
            zones.append("backlight")

        return zones

    def _get_zone_icons(self, zones, device_name):
        """
        Returns the name of icons for a device's lighting areas.

        For example, on a Razer Hex mouse, "logo" would be hex ring buttons.
        """
        zone_icons = {}

        for zone in zones:
            if zone == "logo" and device_name.startswith("Razer Nex"):
                icon = self.common.get_icon("zones", "naga-hex-ring")
            elif zone == "logo" and device_name.startswith("Razer Blade"):
                icon = self.common.get_icon("zones", "blade-logo")
            else:
                icon = self.common.get_icon("zones", zone)

            zone_icons[zone] = icon

        return zone_icons

    def _get_filtered_lsusb_list(self):
        """
        Scans 'lsusb' for incompatible Razer devices. As the daemon doesn't recognise them,
        they can be listed, but cannot be interacted with. Excludes already connected devices.
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
        if self.devices:
            for device in self.devices:
                vidpid = self._get_device_vid_pid(device)
                reg_ids.append([vidpid.get("vid"), vidpid.get("pid")])

        # Identify Razer VIDs that are not registered in the daemon
        for usb in all_usb_ids:
            if usb[0] != "1532":
                continue

            if usb in reg_ids:
                continue

            unreg_ids.append(usb)

        return unreg_ids

    def _get_device_vid_pid(self, rdevice):
        """
        Extracts VID:PID from the daemon's device object in list format: [VID,PID]

        In the event OpenRazer's _vid and _pid is inaccessible, then 0000 is returned.

        Returns:
            {vid, pid}      Success: A dictionary consisting of the VID and PID.
        """
        try:
            vid = str(hex(rdevice._vid))[2:].upper().rjust(4, '0')
            pid = str(hex(rdevice._pid))[2:].upper().rjust(4, '0')
        except Exception:
            self.debug("VID PID unavailable for " + rdevice.name + ". Using dummy ID.")
            vid = "0000"
            pid = "0000"

        return {
            "vid": vid,
            "pid": pid
        }

    def _is_user_in_plugdev_group(self):
        """
        Check the groups of the currently logged in user to identify if it is
        missing 'plugdev' as required by the daemon.
        """
        if "plugdev" in [grp.getgrgid(g).gr_name for g in os.getgroups()]:
            return True
        else:
            return False

    def _get_device_image(self, rdevice):
        """
        OpenRazer doesn't store device images, they are referenced by a URL.

        This function will download a copy of the image for caching purposes.
        """
        if not self.allow_image_download:
            return ""

        import requests

        try:
            # OpenRazer 2.9.0 onwards (#1127)
            image_url = rdevice.device_image
        except AttributeError:
            # OpenRazer 2.8.0 but is backwards compatible
            image_url = rdevice.razer_urls["top_img"]
        except KeyError:
            return ""

        # Save images in Polychromatic's config directory under "device_images"
        try:
            device_images_dir = os.path.join(os.environ["XDG_CONFIG_HOME"], ".config", "polychromatic", "backends", "openrazer", "images")
        except KeyError:
            device_images_dir = os.path.join(os.path.expanduser("~"), ".config", "polychromatic", "backends", "openrazer", "images")

        if not os.path.exists(device_images_dir):
            self.debug("Creating folder for device images: " + device_images_dir)
            os.makedirs(device_images_dir)

        image_path = os.path.join(device_images_dir, rdevice.name + "." + image_url.split(".")[-1])

        # Image already cached?
        if os.path.exists(image_path) and os.stat(image_path).st_size > 8:
            return image_path

        # No image?
        if not image_url:
            self.debug("No device image specified for " + rdevice.name)
            return ""

        self.debug("Retrieving device image for " + rdevice.name)
        self.debug("URL: " + image_url)

        try:
            r = requests.get(image_url)
            if r.status_code == 200:
                open(image_path, "wb").write(r.content)
                self.debug("Success!")
                return image_path
            self.debug("Error: Got status code {0} for '{1}'".format(rdevice.name, str(r.status_code)))
        except Exception as e:
            self.debug("Error: Got exception while retrieving image for '{0}'...".format(rdevice.name))
            self.debug(str(e) + '\n')

        return ""

    def _is_device_monochromatic(self, device):
        """
        Returns a boolean to state whether the device supports per-lighting but
        only works with the 'green' value from RGB.
        """
        if str(device.name).find("Ultimate") != -1:
            return True

        return False

    def _get_device_brightness(self, rdevice, zone):
        """
        Returns both the object and data type required for setting the brightness
        of the specified zone.

        OpenRazer has two kinds of adjusting lighting:
            .brightness = a variable between 0 and 100.
            .active = an on/off state.

        Returns None if brightness is unsupported for the zone.

        Returns a list:
            (object)        The parent object to reference 'brightness' or 'active'
            (data type)     The data type expected by this object.

        Example returns:
            - [a.fx, int]               for main 'brightness'
            - [a.fx.misc.logo, bool]    for logo 'active'
        """
        # -- Device uses a variable (0-100) and it's 'main' so use the root element
        if rdevice.has("brightness") and zone == "main":
            return [rdevice, int]

        rzone = self._get_zone_as_object(rdevice, zone)

        # -- Device is a 'brightness' nested under the zone object
        if self._device_has_zone_capability(rdevice, zone, "brightness"):
            return [rzone, int]

        # -- Device uses an on/off state (zones only)
        if self._device_has_zone_capability(rdevice, zone, "active"):
            return [rzone, bool]

        # -- Device does not support brightness/toggle options
        return [None, None]

    def _convert_colour_bytes(self, raw):
        """
        Convert the daemon's '.colors' function to a string hex.
        """
        input_hex = str(raw.hex())
        primary_hex = "#000000"
        secondary_hex = "#000000"
        tertiary_hex = "#000000"

        if len(input_hex) >= 6:
            primary_hex = input_hex[:6]

        if len(input_hex) >= 12:
            secondary_hex = input_hex[6:12]

        if len(input_hex) >= 18:
            tertiary_hex = input_hex[12:18]

        return {
            "primary": "#" + primary_hex,
            "secondary": "#" + secondary_hex,
            "tertiary": "#" + tertiary_hex
        }

    def _read_persistence_storage(self, rdevice, zone):
        """
        OpenRazer 2.9.0+ uses persistence storage (#1149) to track
        the last effect, colours and parameters. If this version does not have
        this or fails, proceed with a file-based fallback.
        """
        try:
            rzone = self._get_zone_as_object(rdevice, zone)
            colours = self._convert_colour_bytes(rzone.colors)

            return {
                "effect": str(rzone.effect),
                "colour_1": colours["primary"],
                "colour_2": colours["secondary"],
                "colour_3": colours["tertiary"],
                "wave_dir": int(rzone.wave_dir),
                "speed": int(rzone.speed)
            }
        except Exception as e:
            self.debug("Persistence storage not available, falling back!")
            return self._read_persistence_storage_fallback(rdevice, zone)

    def _get_persistence_storage_fallback_path(self):
        """
        Prepare the 'fallback' persistence storage if the daemon's is unavailable.
        """
        try:
            storage_dir = os.path.join(os.environ["XDG_CONFIG_HOME"], "polychromatic", "backends", "openrazer", "persistence")
        except KeyError:
            storage_dir = os.path.join(os.path.expanduser("~"), ".config", "polychromatic", "backends", "openrazer", "persistence")

        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

        return storage_dir

    def _read_persistence_storage_fallback(self, rdevice, zone):
        """
        In case the daemon's persistence storage is unavailable, use flat files
        stored on the filesystem.
        """
        storage_dir = self._get_persistence_storage_fallback_path()
        key_name_suffix = "{0}_{1}".format(rdevice.serial, zone)

        def _get_data(data_name, data_type, default_value):
            file_path = os.path.join(storage_dir, key_name_suffix + "_" + data_name)
            if not os.path.exists(file_path):
                return default_value
            with open(file_path) as f:
                return data_type(f.readline())

        return {
            "effect": _get_data("effect", str, "spectrum"),
            "colour_1": _get_data("colour_1", str, "#00FF00"),
            "colour_2": _get_data("colour_2", str, "#FF0000"),
            "colour_3": _get_data("colour_3", str, "#0000FF"),
            "wave_dir": _get_data("wave_dir", int, 1),
            "speed":  _get_data("speed", int, 2)
        }

    def _write_persistence_storage_fallback(self, rdevice, zone, rzone, key, value):
        """
        If the daemon does not support persistence storage (e.g. old version)
        then write to files instead.
        """
        if hasattr(rzone, "effect"):
            # No need, daemon supports persistence
            return

        storage_dir = self._get_persistence_storage_fallback_path()
        key_name_suffix = "{0}_{1}_{2}".format(rdevice.serial, zone, key)
        file_path = os.path.join(storage_dir, key_name_suffix)
        with open(file_path, "w") as f:
            f.write(str(value))

    def get_device_object(self, uid):
        """
        See _backend.get_device_object()
        """
        try:
            success = self._reinit_device_manager()
            if success != True:
                return success
            rdevice = self.devman.devices[uid]
        except IndexError:
            return None
        except Exception as e:
            return self.common.get_exception_as_string(e)

        if not rdevice.has("lighting_led_matrix"):
            return "Device does not support 'lighting_led_matrix'"

        class OpenRazerCustomFX(object):
            def __init__(self, rdevice, backend_id, name, rows, cols, serial, form_factor):
                self._rdevice = rdevice

                self.backend = backend_id
                self.name = name
                self.rows = rows
                self.cols = cols
                self.serial = serial
                self.form_factor = form_factor

            def set(self, x, y, red, green, blue):
                self._rdevice.fx.advanced.matrix[x,y] = (red, green, blue)

            def draw(self):
                self._rdevice.fx.advanced.draw()

            def clear(self):
                self._rdevice.fx.advanced.matrix.reset()

            def brightness(self, percent):
                self._rdevice.brightness = percent

        return OpenRazerCustomFX(rdevice,
                                 self.backend_id,
                                 str(rdevice.name),
                                 int(rdevice.fx.advanced.rows),
                                 int(rdevice.fx.advanced.cols),
                                 str(rdevice.serial),
                                 self._get_form_factor(rdevice.type)["id"])

    def restart(self):
        """
        Immediately restart the daemon process.
        """
        import time

        # Stop any process running
        self.debug("Running: openrazer-daemon -s")
        os.system("openrazer-daemon -s")

        # Give chance to stop, but kill to be sure.
        self.debug("Waiting for openrazer-daemon to stop (2s)...")
        time.sleep(2)
        os.system("killall openrazer-daemon")

        # Start again
        self.debug("Running: openrazer-daemon")
        os.system("openrazer-daemon")

        self.debug("Waiting for openrazer-daemon to start (2s)...")
        time.sleep(2)
