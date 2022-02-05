#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2022 Luke Horwell <code@horwell.me>
#
"""
This module abstracts data from the OpenRazer Python library (and daemon)
and parses this for Polychromatic to use.

Project URL: https://github.com/openrazer/openrazer
"""

import glob
import os
import requests

from openrazer import client as rclient

from ._backend import Backend as Backend
from .. import fx
from .. import common


class OpenRazerBackend(Backend):
    """
    Integration with the OpenRazer 3.x Python library.

    Thoughout the module:
    - 'rdevice' refers to an openrazer.client.devices.RazerDevice object.
    - 'rzone' refers to an openrazer.client.fx.RazerFX (main) or
                           openrazer.client.fx.SingleLed object (e.g. logo)
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.backend_id = "openrazer"
        self.name = "OpenRazer"
        self.logo = "openrazer.svg"
        self.version = rclient.__version__
        self.project_url = "https://openrazer.github.io"
        self.bug_url = "https://github.com/openrazer/openrazer/issues"
        self.releases_url = "https://github.com/openrazer/openrazer/releases"
        self.license = "GPLv2"

        # Variables for OpenRazer
        self.devman = None
        self.persistence_supported = True
        self.persistence_fallback_path = os.path.join(self.get_backend_storage_path(), "persistence")

        # Client Settings
        # FIXME: Move image download to Controller only!
        self.allow_image_download = False
        self.ripple_refresh_rate = 0.05
        self.load_client_overrides()

    def _reload_device_manager(self):
        """
        Returns a new instance of the OpenRazer Device Manager client. This
        establishes a connection to the daemon via D-Bus. The devices list will
        be up-to-date.

        If the daemon "service" is not running, this will usually start it.
        """
        self.debug("Connecting to daemon...")
        self.devman = rclient.DeviceManager()
        self.devman.sync_effects = False

    def init(self):
        """
        Summons the OpenRazer DeviceManager() daemon.
        """
        try:
            self._reload_device_manager()
            return True
        except Exception as e:
            self.debug("Failed: Got an exception initialising device manager!")
            return self.get_exception_as_string(e)

        # Persistence API was introduced in OpenRazer 3.0.0
        if int(self.version.split(".")[0]) <= 3:
            self.persistence_supported = False

        if self.persistence_supported:
            if not os.path.exists(self.persistence_fallback_path):
                os.makedirs(self.persistence_fallback_path)

    def load_client_overrides(self):
        """
        Load any user-defined client settings that Polychromatic should use
        interfacing with the daemon. These are stored as individual files inside
        ~/.config/polychromatic/backends/openrazer/
        """
        def _get_override(filename, data_type, default):
            path = os.path.join(self.get_backend_storage_path(), filename)
            if not os.path.exists(path):
                return default

            with open(path, "r") as f:
                data = str(f.readline()).strip()

            try:
                output = data_type(data)
                self.debug("Setting client setting: {0} to {1}".format(filename, output))
                return output
            except ValueError:
                return default

        self.ripple_refresh_rate = _get_override("ripple_refresh_rate", float, 0.05)

    def get_unsupported_devices(self):
        """
        See Backend.get_unsupported_devices() and Backend.UnknownDeviceItem()

        Returns a list of PIDs of Razer hardware that is physically plugged in,
        but inaccessible by the daemon. Usually indicating the installation is
        incomplete or the device is not supported by the driver.
        """
        all_usb_pids = self.helpers.get_usb_pids_by_vid("1532")
        reg_pids = []
        unreg_pids = []

        # Get VIDs and PIDs from daemon to exclude later.
        for rdevice in self.devman.devices:
            vidpid = self._get_device_vid_pid(rdevice)
            reg_pids.append(vidpid.get("pid"))

        # Determine Razer PIDs that are not listed in the daemon
        for pid in all_usb_pids:
            if pid in reg_pids:
                continue

            # Ignore Kitty headphones duplicate: 1532:0521 [Headset], 1532:0F19 [Chroma] (#328)
            if pid == "0521":
                continue

            # Ignore Razer Seiren X. No RGB support (openrazer/openrazer#1058)
            elif pid == "0511":
                continue

            device = Backend.UnknownDeviceItem()
            device.name = "{0}:{1}".format("1532", pid)
            device.form_factor = self.get_form_factor()
            unreg_pids.append(device)

        return unreg_pids

    def get_devices(self):
        """
        See Backend.get_devices() and Backend.DeviceItem()
        """
        devices = []
        self._reload_device_manager()
        for rdevice in self.devman.devices:
            devices.append(self._get_device(rdevice))
        return devices

    def get_device_by_name(self, name):
        """
        See Backend.get_device_by_name()
        """
        try:
            for rdevice in self.devman.devices:
                if rdevice.name == name:
                    return self._get_device(rdevice)
        except Exception as e:
            return self.get_exception_as_string(e)

    def get_device_by_serial(self, serial):
        """
        See Backend.get_device_by_serial()
        """
        try:
            for rdevice in self.devman.devices:
                if not rdevice.has("serial"):
                    continue
                if rdevice.serial == serial:
                    return self._get_device(rdevice)
        except Exception as e:
            return self.get_exception_as_string(e)

    def _get_device(self, rdevice):
        """
        Returns a Backend.DeviceItem() from OpenRazer's device object.
        """
        # A valid serial number is essential
        serial = ""
        if rdevice.has("serial"):
            serial = str(rdevice.serial)
        if len(serial) <= 2:
            serial = "".join(c for c in rdevice.name if c.isalnum()).upper()
            self.debug("Got bad serial for {0}! Using dummy serial: {1}".format(rdevice.name, serial))

        # Device details
        class OpenRazerDeviceItem(Backend.DeviceItem):
            def refresh(self):
                for zone in self.zones:
                    zone._persistence.refresh()
                    for option in zone.options:
                        option.refresh()
                if self.dpi:
                    self.dpi.refresh()

        device = OpenRazerDeviceItem()
        device._rdevice = rdevice
        device.name = str(rdevice.name)
        device.form_factor = self._get_form_factor(rdevice)
        device.real_image = self._get_device_image(rdevice)
        device.serial = serial
        device.monochromatic = self._is_device_monochromatic(rdevice)

        _vid_pid = self._get_device_vid_pid(rdevice)
        device.vid = _vid_pid.get("vid")
        device.pid = _vid_pid.get("pid")

        if rdevice.has("firmware_version"):
            device.firmware_version = str(rdevice.firmware_version)

        if rdevice.has("keyboard_layout"):
            device.keyboard_layout = str(rdevice.keyboard_layout)

        if rdevice.has("dpi") and not rdevice.has("available_dpi"):
            device.dpi = self._get_dpi_object(rdevice)

        if rdevice.has("lighting_led_matrix"):
            device.matrix = self._get_matrix_object(rdevice, device)

        # Initialize zones
        device.zones = self._get_zone_objects(rdevice)
        main_zone = device.zones[0]

        # Add brightness & effects (per zone)
        for zone in device.zones:
            zone._persistence = self._get_persistence(self._map_zone_id_to_rzone(rdevice, zone), zone, serial)

            brightness = self._get_brightness_option(rdevice, zone)
            if brightness:
                zone.options.append(brightness)

            effects = self._get_effect_options(rdevice, zone)
            if effects:
                zone.options += effects

        workarounds = self._get_workaround_options(rdevice)
        if workarounds:
            main_zone.options = workarounds

        # Add other "main" options
        if rdevice.has("available_dpi"):
            device.dpi = None
            main_zone.options.append(self._get_dpi_fixed_object(rdevice))


        if rdevice.has("poll_rate"):
            main_zone.options.append(self._get_poll_rate_option(rdevice))

        if rdevice.has("game_mode_led"):
            main_zone.options.append(self._get_game_mode_option(rdevice))

        if rdevice.has("battery"):
            main_zone.options += self._get_battery_options(rdevice)

        if rdevice.has("macro_mode_led_effect") and rdevice.type == "keyboard":
            main_zone.options.append(self._get_macro_option(rdevice))

        if rdevice.type in ["keyboard", "keypad"]:
            main_zone.options.append(self._get_key_remapping_option(rdevice))

        return device

    def _get_persistence(self, rzone, zone, serial):
        """
        Returns OpenRazerPersistence() or OpenRazerPersistenceFallback()
        depending on this running version of OpenRazer.
        """
        if self.persistence_supported:
            return OpenRazerPersistence(rzone)

        return OpenRazerPersistenceFallback(zone.zone_id, serial, self.persistence_fallback_path)

    def _get_dpi_object(self, rdevice):
        """
        Returns a Backend.DeviceItem.DPI object.
        This is for standard use of the .dpi function (X/Y axis support). If the
        device has "available_dpi", use _get_fixed_dpi_object() instead.
        """
        class DPI(Backend.DeviceItem.DPI):
            def __init__(self, rdevice):
                super().__init__()
                self._rdevice = rdevice
                self.min = 100
                self.max = int(rdevice.max_dpi)

            def refresh(self):
                self.x = self._rdevice.dpi[0]
                self.y = self._rdevice.dpi[1]

            def set(self, x, y):
                self._rdevice.dpi = (int(x), int(y))

        dpi = DPI(rdevice)

        # Determine DPI stages, or generate them if not known
        default_stages = {
            16000: [800, 1800, 4500, 9000, 16000],
            8200: [800, 1800, 4800, 6400, 8200]
        }

        try:
            dpi.stages = default_stages[dpi.max]
        except KeyError:
            dpi.stages = [
                int(dpi.max / 10),
                int(dpi.max / 8),
                int(dpi.max / 4),
                int(dpi.max / 2),
                int(dpi.max)
            ]

        return dpi

    def _get_dpi_fixed_object(self, rdevice):
        """
        Returns a Backend.MultipleChoiceOption object as an alternate for DPI.
        This is used for devices that have a fixed DPI and do not support the
        'variable' slider.
        """
        current_dpi = int(rdevice.dpi[0])
        parameters = []

        for index, dpi in enumerate(list(rdevice.available_dpi)):
            param = Backend.Option.Parameter()
            param.data = int(dpi)
            param.label = "{0} Hz".format(dpi)
            param.active = True if dpi == current_dpi else False
            param.default = True if index == 0 else False
            parameters.append(param)

        class FixedDPIOption(Backend.MultipleChoiceOption):
            def __init__(self, rdevice, parameters):
                super().__init__()
                self._rdevice = rdevice
                self.uid = "fixed_dpi"
                self.parameters = parameters

            def refresh(self):
                current_dpi = int(self._rdevice.dpi[0])
                for param in self.parameters:
                    # Round up internally just in case DPI is not an exact value
                    param.active = True if round(param.data, -1) == round(current_dpi, -1) else False

            def apply(self, new_value):
                # Device only supports fixed DPI X values, such as DeathAdder 3.5G (#209)
                self._rdevice.dpi = (int(new_value), 0)

        fixed_dpi = FixedDPIOption(rdevice, parameters)
        fixed_dpi.label = self._("DPI")
        fixed_dpi.icon = self.get_icon("general", "dpi")

        return fixed_dpi

    def _get_dpi_sync_option(self, rdevice):
        """
        Returns a Backend.Option derivative object used for syncing DPI stages
        to the hardware. This is a firmware feature. Most devices don't support this
        and require a software implementation to listen to the buttons.
        """
        return Backend.Option()

    def _get_matrix_object(self, rdevice, device):
        """
        Returns a Backend.DeviceItem.Matrix object.
        """
        class OpenRazerMatrix(Backend.DeviceItem.Matrix):
            def __init__(self, rdevice):
                self._rdevice = rdevice
                self.name = device.name
                self.form_factor_id = device.form_factor["id"]
                self.rows = int(rdevice.fx.advanced.rows)
                self.cols = int(rdevice.fx.advanced.cols)

            def set(self, x, y, red, green, blue):
                self._rdevice.fx.advanced.matrix[y, x] = (red, green, blue)

            def draw(self):
                self._rdevice.fx.advanced.draw()

            def clear(self):
                self._rdevice.fx.advanced.matrix.reset()

            def brightness(self):
                print("todo:stub:_get_matrix_object.brightness")

        class DeathStalkerMatrix(OpenRazerMatrix):
            """
            Alternate matrix implementation for Razer DeathStalker Chroma, which
            has a matrix of 12x1, but every second LED [2,4,6,8,10,12]
            physically blends with its previous LED [1,3,5,7,9,11], which messes
            up the lighting colours (#335)

            This matrix is virtual. It'll stretch LEDs by two for each one. Example:
                Virtual     Physical
                0       ->  0, 1
                5       ->  10, 11
            """
            def __init__(self, rdevice):
                super().__init__(rdevice)
                self.cols = 6

            def set(self, x, y, red, green, blue):
                self._rdevice.fx.advanced.matrix[y, (x * 2)] = (red, green, blue)
                self._rdevice.fx.advanced.matrix[y, (x * 2) + 1] = (red, green, blue)

        # OpenRazer changed this matrix after 3.1 (6 => 12)
        if rdevice.name == "Razer DeathStalker Chroma" and rdevice.fx.advanced.cols == 12:
            return DeathStalkerMatrix(rdevice)

        return OpenRazerMatrix(rdevice)

    def _get_zone_objects(self, rdevice):
        """
        Returns a list of Backend.DeviceItem.Zone objects.
        """
        zones = []
        device_name = str(rdevice.name)

        def _add_zone(zone_id, label):
            zone = Backend.DeviceItem.Zone()
            zone.zone_id = zone_id
            zone.label = label
            zone.icon = self.get_icon("zones", zone_id)
            zones.append(zone)

        # All devices have a 'main' base zone
        form_factor = self._get_form_factor(rdevice)
        zone = Backend.DeviceItem.Zone()
        zone.zone_id = "main"
        zone.label = form_factor["label"]
        zone.icon = form_factor["icon"]
        zones.append(zone)

        if rdevice.has("lighting_scroll") or rdevice.has("lighting_scroll_active"):
            _add_zone("scroll", self._("Scroll Wheel"))

        if rdevice.has("lighting_logo") or rdevice.has("lighting_logo_active"):
            # This zone may be more personalized for some devices
            zone = Backend.DeviceItem.Zone()
            zone.zone_id = "logo"
            zone.label = self._("Logo")
            zone.icon = self.get_icon("zones", "logo")

            if device_name.startswith("Razer Nex"):
                zone.label = self._("Hex Ring")
                zone.icon = self.get_icon("zones", "naga-hex-ring")

            if device_name.startswith("Razer Blade"):
                zone.label = self._("Laptop Lid")
                zone.icon = self.get_icon("zones", "blade-logo")

            zones.append(zone)

        if rdevice.has("lighting_left"):
            _add_zone("left", self._("Left"))
        if rdevice.has("lighting_right"):
            _add_zone("right", self._("Right"))
        if rdevice.has("lighting_backlight"):
            _add_zone("backlight", self._("Backlight"))
        if rdevice.has("lighting_charging"):
            _add_zone("charging", self._("Charging"))
        if rdevice.has("lighting_fast_charging"):
            _add_zone("fast_charging", self._("Fast Charging"))
        if rdevice.has("lighting_fully_charged"):
            _add_zone("fully_charged", self._("Fully Charging"))

        return zones

    def _get_form_factor(self, rdevice):
        """
        Convert the device type returned by OpenRazer to match one used within Polychromatic.
        """
        device_name = rdevice.name
        device_type = rdevice.type

        # Some of these 'device types' originate from legacy OpenRazer versions
        openrazer_to_poly = {
            "firefly": "mousemat",
            "tartarus": "keypad",
            "core": "gpu",
            "mug": "accessory"
        }

        if device_type in openrazer_to_poly:
            form_factor_id = openrazer_to_poly[device_type]
        else:
            form_factor_id = device_type

        if device_name.find("Base Station") != -1:
            form_factor_id = "stand"
        elif device_name.find("Blade") != -1:
            form_factor_id = "laptop"
        elif device_name.find("Core") != -1:
            form_factor_id = "gpu"
        elif device_name.find("Nommo") != -1:
            form_factor_id = "speaker"
        elif device_name.find("Raptor") != -1:
            form_factor_id = "display"

        return self.get_form_factor(form_factor_id)

    def _get_device_image(self, rdevice):
        """
        OpenRazer doesn't store device images, they are referenced by a URL.

        This function will download a copy of the image for caching purposes,
        unless disabled by the user.
        """
        if not self.allow_image_download:
            return ""

        try:
            # OpenRazer >= 2.9.0 (openrazer/openrazer#1127)
            image_url = rdevice.device_image
        except AttributeError:
            # Backwards compatiblity with OpenRazer <= 2.8.0
            image_url = rdevice.razer_urls["top_img"]
        except KeyError:
            return ""

        image_dir = os.path.join(self.get_backend_storage_path(), "images")

        if not os.path.exists(image_dir):
            self.debug("Creating folder for device images: " + image_dir)
            os.makedirs(image_dir)

        image_path = os.path.join(image_dir, rdevice.name + "." + image_url.split(".")[-1])

        # Image already cached?
        if os.path.exists(image_path) and os.stat(image_path).st_size > 8:
            return image_path

        # No image?
        if not image_url:
            self.debug("{0} does not have an image.".format(rdevice.name))
            return ""

        self.debug("Downloading device image for {0}...".format(rdevice.name))
        self.debug("URL: " + image_url)

        try:
            r = requests.get(image_url)
            if r.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(r.content)
                self.debug("Success!")
                return image_path

            self.debug("Error: Got status code {0} for '{1}'".format(rdevice.name, str(r.status_code)))
        except Exception as e:
            self.debug("Error: Got exception while retrieving image for '{0}'...".format(rdevice.name))
            self.debug(str(e) + '\n')

        return ""

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

    def _is_device_monochromatic(self, device):
        """
        Returns a boolean to state whether the device supports per-lighting but
        only works with the 'green' value from RGB.
        """
        # Razer BlackWidow Ultimate keyboards only output "green" RGB
        if str(device.name).find("Ultimate") != -1 and device.type == "keyboard":
            return True

        return False

    def _map_zone_id_to_rzone(self, rdevice, zone):
        """
        Returns an object that directly references the OpenRazer's device "zone".
        """
        zone_to_device = {
            "main": rdevice.fx,
            "logo": rdevice.fx.misc.logo,
            "scroll": rdevice.fx.misc.scroll_wheel,
            "backlight": rdevice.fx.misc.backlight
        }

        # Introduced in OpenRazer 2.6.0, but not all devices list these.
        try:
            zone_to_device["left"] = rdevice.fx.misc.left
            zone_to_device["right"] = rdevice.fx.misc.right
        except KeyError:
            pass

        # Introduced in OpenRazer 3.0.0, but not all devices list these.
        try:
            zone_to_device["charging"] = rdevice.fx.misc.charging
            zone_to_device["fully_charged"] = rdevice.fx.misc.fully_charged
            zone_to_device["fast_charging"] = rdevice.fx.misc.fast_charging
        except KeyError:
            pass

        return zone_to_device[zone.zone_id]

    def _has_zone_capability(self, rdevice, zone, capability):
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
            "right": "lighting_right",
            "charging": "lighting_charging",
            "fast_charging": "lighting_fast_charging",
            "fully_charged": "lighting_fully_charged",
        }

        # Brightness for the "root" (main) zone does not use the "lighting_" prefix.
        if capability == "brightness" and zone.zone_id == "main" and rdevice.has("brightness"):
            return True

        return rdevice.has(zone_to_capability[zone.zone_id] + "_" + capability)

    def _get_brightness_option(self, rdevice, zone):
        """
        Returns a Backend.Option derivative object based on the type of
        brightness for the specified zone and device.

        OpenRazer has two kinds of lighting:
            .brightness = a variable between 0 and 100.
            .active = an on/off state.

        Returns None if brightness is unsupported for the zone.
        """
        if rdevice.has("brightness") and zone.zone_id == "main":
            # This is provided in the root element, not .fx
            rzone = rdevice
        else:
            rzone = self._map_zone_id_to_rzone(rdevice, zone)

        # Device is a 'brightness' % variable
        if self._has_zone_capability(rdevice, zone, "brightness"):
            class BrightnessSlider(Backend.SliderOption):
                def __init__(self, rzone):
                    super().__init__()
                    self._rzone = rzone
                    self.uid = "brightness"
                    self.min = 0
                    self.max = 100
                    self.step = 5
                    self.suffix = "%"
                    self.suffix_plural = "%"

                def refresh(self):
                    self.value = int(round(self._rzone.brightness))

                def apply(self, new_value):
                    self._rzone.brightness = float(new_value)

            slider = BrightnessSlider(rzone)
            slider.label = self._("Brightness")
            slider.icon = self.get_icon("options", "brightness")
            return slider

        # Device uses an on/off state
        if self._has_zone_capability(rdevice, zone, "active"):
            class BrightnessToggle(Backend.ToggleOption):
                def __init__(self, rzone):
                    super().__init__()
                    self._rzone = rzone
                    self.uid = "brightness"

                def refresh(self):
                    self.active = True if self._rzone.active else False

                def apply(self, enabled):
                    self._rzone.active = enabled

            toggle = BrightnessToggle(rzone)
            toggle.label = self._("Brightness")
            toggle.icon = self.get_icon("options", "brightness")
            toggle.icon_enable = self.get_icon("params", "100")
            toggle.icon_disable = self.get_icon("params", "0")
            toggle.label_enable = self._("On")
            toggle.label_disable = self._("Off")
            toggle.label_toggle = self._("Enabled")
            return toggle

        # Device does not support this option
        return None

    def _get_effect_options(self, rdevice, zone):
        """
        Returns list of Backend.EffectOption objects by determining
        which options/parameters are available for this device and zone.
        """
        rzone = self._map_zone_id_to_rzone(rdevice, zone)
        options = []

        has_ripple = self._has_zone_capability(rdevice, zone, "ripple")
        has_ripple_random = self._has_zone_capability(rdevice, zone, "ripple_random")

        # There isn't a single 'lighting_breath' in the capabilities list
        has_breath_random = self._has_zone_capability(rdevice, zone, "breath_random")
        has_breath_single = self._has_zone_capability(rdevice, zone, "breath_single")
        has_breath_dual = self._has_zone_capability(rdevice, zone, "breath_dual")
        has_breath_triple = self._has_zone_capability(rdevice, zone, "breath_triple")

        # There isn't a single 'lighting_starlight' in the capabilities list
        has_starlight_random = self._has_zone_capability(rdevice, zone, "starlight_random")
        has_starlight_single = self._has_zone_capability(rdevice, zone, "starlight_single")
        has_starlight_dual = self._has_zone_capability(rdevice, zone, "starlight_dual")

        if self._has_zone_capability(rdevice, zone, "none"):
            class NoneOption(Backend.EffectOption):
                def __init__(self, rzone, persistence):
                    super().__init__()
                    self._rzone = rzone
                    self._persistence = persistence
                    self.uid = "none"

                def refresh(self):
                    self.active = True if self._persistence.state["effect"] == "none" else False

                def apply(self, param=None):
                    self._rzone.none()
                    self._persistence.save("effect", "none")

            option = NoneOption(rzone, zone._persistence)
            option.label = self._("None")
            option.icon = self.get_icon("options", "none")
            options.append(option)

        if self._has_zone_capability(rdevice, zone, "spectrum"):
            class SpectrumOption(Backend.EffectOption):
                def __init__(self, rzone, persistence):
                    super().__init__()
                    self._rzone = rzone
                    self._persistence = persistence
                    self.uid = "spectrum"

                def refresh(self):
                    self.active = True if self._persistence.state["effect"] == "spectrum" else False

                def apply(self, param=None):
                    self._rzone.spectrum()
                    self._persistence.save("effect", "spectrum")

            option = SpectrumOption(rzone, zone._persistence)
            option.label = self._("Spectrum")
            option.icon = self.get_icon("options", "spectrum")
            options.append(option)

        if self._has_zone_capability(rdevice, zone, "wave"):
            class WaveOption(Backend.EffectOption):
                def __init__(self, rzone, persistence):
                    super().__init__()
                    self._rzone = rzone
                    self._persistence = persistence
                    self.uid = "wave"

                def refresh(self):
                    self.active = True if self._persistence.state["effect"] == "wave" else False
                    for param in self.parameters:
                        param.active = True if self._persistence.state["wave_dir"] == param.data else False

                def apply(self, direction):
                    # direction: 1 or 2
                    self._rzone.wave(int(direction))
                    self._persistence.save("effect", "wave")
                    self._persistence.save("wave_dir", str(direction))

            option = WaveOption(rzone, zone._persistence)
            option.label = self._("Wave")
            option.icon = self.get_icon("options", "wave")

            direction_1 = Backend.Option.Parameter()
            direction_1.data = 1

            direction_2 = Backend.Option.Parameter()
            direction_2.data = 2
            direction_2.default = True

            # Change parameter labels depending on orientation/device
            if rdevice.type == "mouse":
                direction_1.label = self._("Up")
                direction_1.icon  = self.get_icon("params", "up")
                direction_2.label = self._("Down")
                direction_2.icon  = self.get_icon("params", "down")

            elif rdevice.type == "mousemat":
                direction_1.label = self._("Clockwise")
                direction_1.icon  = self.get_icon("params", "clock")
                direction_2.label = self._("Anti-clockwise")
                direction_2.icon  = self.get_icon("params", "anticlock")

            else:
                direction_1.label = self._("Right")
                direction_1.icon = self.get_icon("params", "right")
                direction_2.label = self._("Left")
                direction_2.icon = self.get_icon("params", "left")

            option.parameters = [direction_2, direction_1]
            options.append(option)

        if has_ripple or has_ripple_random:
            class RippleOption(Backend.EffectOption):
                def __init__(self, rzone, persistence):
                    super().__init__()
                    self._rzone = rzone
                    self._persistence = persistence
                    self.uid = "ripple"
                    self.colours = persistence.state["colours"]

                def refresh(self):
                    current_effect = self._persistence.state["effect"]
                    self.active = True if current_effect in ["ripple", "rippleRandomColour"] else False
                    for param in self.parameters:
                        if param.data == "random":
                            param.active = True if current_effect == "rippleRandomColour" else False
                        elif param.data == "single":
                            param.active = True if current_effect == "ripple" else False
                    self.colours = self._persistence.state["colours"]

                def apply(self, ripple_type):
                    if str(ripple_type) == "random":
                        self._rzone.ripple_random()
                        self._persistence.save("effect", "rippleRandomColour")
                    elif str(ripple_type) == "single":
                        rgb = common.hex_to_rgb(self.colours[0])
                        self._rzone.ripple(rgb[0], rgb[1], rgb[2])
                        self._persistence.save("effect", "ripple")
                        self._persistence.save("colour_1", self.colours[0])

            option = RippleOption(rzone, zone._persistence)
            option.label = self._("Ripple")
            option.icon = self.get_icon("options", "ripple")

            if has_ripple_random:
                random = Backend.Option.Parameter()
                random.data = "random"
                random.label = self._("Random")
                random.icon = self.get_icon("params", "random")
                option.parameters.append(random)

            if has_ripple:
                single = Backend.Option.Parameter()
                single.data = "single"
                single.label = self._("Single")
                single.icon = self.get_icon("params", "single")
                single.colours_required = 1
                single.default = True
                option.parameters.append(single)

            options.append(option)

        if self._has_zone_capability(rdevice, zone, "reactive"):
            class ReactiveOption(Backend.EffectOption):
                def __init__(self, rzone, persistence):
                    super().__init__()
                    self._rzone = rzone
                    self._persistence = persistence
                    self.uid = "reactive"
                    self.colours_required = 1
                    self.colours = self._persistence.state["colours"]

                def refresh(self):
                    self.active = True if self._persistence.state["effect"] == "reactive" else False
                    for param in self.parameters:
                        param.active = True if self._persistence.state["speed"] == param.data else False
                    self.colours = self._persistence.state["colours"]

                def apply(self, speed):
                    rgb = common.hex_to_rgb(self.colours[0])
                    self._rzone.reactive(rgb[0], rgb[1], rgb[2], int(speed))
                    self._persistence.save("effect", "reactive")
                    self._persistence.save("speed", str(speed))
                    self._persistence.save("colour_1", self.colours[0])

            option = ReactiveOption(rzone, zone._persistence)
            option.label = self._("Reactive")
            option.icon = self.get_icon("options", "reactive")

            fast = Backend.Option.Parameter()
            fast.data = 1
            fast.label = self._("Fast (0.5s)")
            fast.icon = self.get_icon("params", "fast")

            medium = Backend.Option.Parameter()
            medium.data = 2
            medium.label = self._("Medium (1s)")
            medium.default = True

            slow = Backend.Option.Parameter()
            slow.data = 3
            slow.label = self._("Slow (1.5s)")

            vslow = Backend.Option.Parameter()
            vslow.data = 4
            vslow.label = self._("Very Slow (2s)")
            vslow.icon = self.get_icon("params", "slow")

            for param in [fast, medium, slow, vslow]:
                option.parameters.append(param)

            options.append(option)

        if self._has_zone_capability(rdevice, zone, "blinking"):
            # Buggy and pretty much unused!
            # - API only exposes for 'logo' and 'scroll' zones.
            # - Only the Chroma Mug Holder supports this (as of 3.2.0)
            class BlinkingOption(Backend.EffectOption):
                def __init__(self, rzone, persistence):
                    super().__init__()
                    self._rzone = rzone
                    self._persistence = persistence
                    self.uid = "blinking"
                    self.colours_required = 1
                    self.colours = self._persistence.state["colours"]

                def refresh(self):
                    self.active = True if self._persistence.state["colours"] == "blinking" else False
                    self.colours = self._persistence.state["colours"]

                def apply(self, param=None):
                    rgb = common.hex_to_rgb(self.colours[0])
                    self._rzone.blinking(rgb[0], rgb[1], rgb[2])
                    self._persistence.save("effect", "blinking")
                    self._persistence.save("colour_1", self.colours[0])

            option = BlinkingOption(rzone, zone._persistence)
            option.label = self._("Blinking")
            option.icon = self.get_icon("options", "blinking")
            options.append(option)

        if self._has_zone_capability(rdevice, zone, "static"):
            class StaticOption(Backend.EffectOption):
                def __init__(self, rzone, persistence):
                    super().__init__()
                    self._rzone = rzone
                    self._persistence = persistence
                    self.uid = "static"
                    self.colours_required = 1
                    self.colours = self._persistence.state["colours"]

                def refresh(self):
                    self.active = True if self._persistence.state["effect"] == "static" else False
                    self.colours = self._persistence.state["colours"]

                def apply(self, param=None):
                    rgb = common.hex_to_rgb(self.colours[0])
                    self._rzone.static(rgb[0], rgb[1], rgb[2])
                    self._persistence.save("effect", "static")
                    self._persistence.save("colour_1", self.colours[0])

            option = StaticOption(rzone, zone._persistence)
            option.label = self._("Static")
            option.icon = self.get_icon("options", "static")
            options.append(option)

        if has_breath_random or has_breath_single or has_breath_dual or has_breath_triple:
            class BreathOption(Backend.EffectOption):
                def __init__(self, rzone, persistence):
                    super().__init__()
                    self._rzone = rzone
                    self._persistence = persistence
                    self.uid = "breath"
                    self.colours = self._persistence.state["colours"]

                def refresh(self):
                    current_effect = self._persistence.state["effect"]
                    if not current_effect.startswith("breath"):
                        self.active = False
                        return
                    self.active = True
                    current_breath_type = current_effect.split("breath")[1].lower()
                    for param in self.parameters:
                        param.active = True if current_breath_type == param.data else False
                    self.colours = self._persistence.state["colours"]

                def apply(self, breath_type):
                    rgb = []
                    for colour in self.colours:
                        rgb.append(common.hex_to_rgb(colour))

                    if breath_type == "random":
                        self._rzone.breath_random()
                        self._persistence.save("effect", "breathRandom")
                    elif breath_type == "single":
                        self._rzone.breath_single(rgb[0][0], rgb[0][1], rgb[0][2])
                        self._persistence.save("effect", "breathSingle")
                        self._persistence.save("colour_1", self.colours[0])
                    elif breath_type == "dual":
                        self._rzone.breath_dual(rgb[0][0], rgb[0][1], rgb[0][2],
                                                rgb[1][0], rgb[1][1], rgb[1][2])
                        self._persistence.save("effect", "breathDual")
                        self._persistence.save("colour_1", self.colours[0])
                        self._persistence.save("colour_2", self.colours[1])
                    elif breath_type == "triple":
                        self._rzone.breath_triple(rgb[0][0], rgb[0][1], rgb[0][2],
                                                  rgb[1][0], rgb[1][1], rgb[1][2],
                                                  rgb[2][0], rgb[2][1], rgb[2][2])
                        self._persistence.save("effect", "breathTriple")
                        self._persistence.save("colour_1", self.colours[0])
                        self._persistence.save("colour_2", self.colours[1])
                        self._persistence.save("colour_3", self.colours[2])
                    else:
                        raise KeyError("Unknown breath type: " + breath_type)

            option = BreathOption(rzone, zone._persistence)
            option.label = self._("Breath")
            option.icon = self.get_icon("options", "breath")

            if has_breath_random:
                random = Backend.Option.Parameter()
                random.data = "random"
                random.label = self._("Random")
                random.icon = self.get_icon("params", "random")
                option.parameters.append(random)

            if has_breath_single:
                single = Backend.Option.Parameter()
                single.data = "single"
                single.label = self._("Single")
                single.icon = self.get_icon("params", "single")
                single.colours_required = 1
                single.default = True
                option.parameters.append(single)

            if has_breath_dual:
                dual = Backend.Option.Parameter()
                dual.data = "dual"
                dual.label = self._("Dual")
                dual.icon = self.get_icon("params", "dual")
                dual.colours_required = 2
                option.parameters.append(dual)

            if has_breath_triple:
                triple = Backend.Option.Parameter()
                triple.data = "triple"
                triple.label = self._("Triple")
                triple.icon = self.get_icon("params", "triple")
                triple.colours_required = 3
                option.parameters.append(triple)

            options.append(option)

        if has_starlight_random or has_starlight_single or has_starlight_dual:
            class StarlightOption(Backend.EffectOption):
                def __init__(self, rzone, persistence):
                    super().__init__()
                    self._rzone = rzone
                    self._persistence = persistence
                    self.uid = "starlight"
                    self.colours = self._persistence.state["colours"]

                def refresh(self):
                    current_effect = self._persistence.state["effect"]
                    if not current_effect.startswith("starlight"):
                        self.active = False
                        return
                    self.active = True
                    current_starlight = current_effect.split("starlight")[1].lower()
                    current_speed = self._persistence.state["speed"]
                    self.active = True if current_effect.startswith("starlight") else False
                    for param in self.parameters:
                        param.active = False
                        starlight_type, starlight_speed = param.data.split(":")
                        if current_starlight == starlight_type and str(current_speed) == starlight_speed:
                            param.active = True
                    self.colours = self._persistence.state["colours"]

                def apply(self, data):
                    # Param Example: "random:2" for a Medium (2) Random Starlight
                    starlight_type = data.split(":")[0]
                    starlight_speed = int(data.split(":")[1])

                    rgb = []
                    for colour in self.colours:
                        rgb.append(common.hex_to_rgb(colour))

                    if starlight_type == "random":
                        self._rzone.starlight_random(starlight_speed)
                        self._persistence.save("effect", "starlightRandom")
                    elif starlight_type == "single":
                        self._rzone.starlight_single(rgb[0][0], rgb[0][1], rgb[0][2], starlight_speed)
                        self._persistence.save("colour_1", self.colours[0])
                        self._persistence.save("effect", "starlightSingle")
                    elif starlight_type == "dual":
                        self._rzone.starlight_dual(rgb[0][0], rgb[0][1], rgb[0][2],
                                                   rgb[1][0], rgb[1][1], rgb[1][2], starlight_speed)
                        self._persistence.save("colour_1", self.colours[0])
                        self._persistence.save("colour_2", self.colours[1])
                        self._persistence.save("effect", "starlightDual")
                    else:
                        raise KeyError("Unknown starlight parameter:" + str(data))

            option = StarlightOption(rzone, zone._persistence)
            option.label = self._("Starlight")
            option.icon = self.get_icon("options", "starlight")

            speeds = {
                1: self._("Fast"),
                2: self._("Medium"),
                3: self._("Slow"),
            }

            if has_starlight_random:
                for speed in speeds.keys():
                    random = Backend.Option.Parameter()
                    random.data = "random:" + str(speed)
                    random._speed = speed
                    random.label = "{0} ({1})".format(self._("Random"), speeds[speed])
                    random.icon = self.get_icon("params", "random")
                    option.parameters.append(random)

            if has_starlight_single:
                for speed in speeds.keys():
                    single = Backend.Option.Parameter()
                    single.data = "single:" + str(speed)
                    single._speed = speed
                    single.label = "{0} ({1})".format(self._("Single"), speeds[speed])
                    single.icon = self.get_icon("params", "single")
                    single.colours_required = 1
                    single.default = True
                    option.parameters.append(single)

            if has_starlight_dual:
                for speed in speeds.keys():
                    dual = Backend.Option.Parameter()
                    dual.data = "dual:" + str(speed)
                    dual._speed = speed
                    dual.label = "{0} ({1})".format(self._("Dual"), speeds[speed])
                    dual.icon = self.get_icon("params", "dual")
                    dual.colours_required = 2
                    option.parameters.append(dual)

            options.append(option)

        return options

    def _get_workaround_options(self, rdevice):
        """
        If applicable, return a list of option objects that workaround the
        OpenRazer Python library due to bugs in the API.

        #1: Devices speaking the "BW2013" protocol can't set pulsate or static.
            - The latter doesn't appear as a capability either. These devices do not
            accept parameters or colours.
            - As a workaround, bypass the pylib and echo directly to the sysfs driver.
            - See also: #345, openrazer/openrazer#1575
        """
        try:
            if "razer.device.lighting.bw2013" in rdevice._available_features.keys():
                vidpid = self._get_device_vid_pid(rdevice)
                persistence = OpenRazerPersistenceFallback("main", rdevice.serial, self.persistence_fallback_path)

                try:
                    matrix_file_pulsate = glob.glob("/sys/bus/hid/drivers/razer*/*{0}:{1}*/matrix_effect_pulsate".format(vidpid["vid"], vidpid["pid"]), recursive=True)[0]
                    matrix_file_static = glob.glob("/sys/bus/hid/drivers/razer*/*{0}:{1}*/matrix_effect_static".format(vidpid["vid"], vidpid["pid"]), recursive=True)[0]
                except IndexError:
                    # Check the fake driver instead
                    matrix_file_pulsate = glob.glob("/tmp/**/*{0}:{1}*/matrix_effect_pulsate".format(vidpid["vid"], vidpid["pid"]), recursive=True)[0]
                    matrix_file_static = glob.glob("/tmp/**/*{0}:{1}*/matrix_effect_static".format(vidpid["vid"], vidpid["pid"]), recursive=True)[0]

                class PulsateOptionBW2013(Backend.EffectOption):
                    def __init__(self, persistence, sysfs_path):
                        super().__init__()
                        self._persistence = persistence
                        self.sysfs_path = sysfs_path
                        self.uid = "pulsate"

                    def refresh(self):
                        self.active = True if self._persistence.state["effect"] == "pulsate" else False

                    def apply(self, param=None):
                        with open(self.sysfs_path, "w") as f:
                            f.write("1")
                        self._persistence.save("effect", "pulsate")

                class StaticOptionBW2013(Backend.EffectOption):
                    def __init__(self, persistence, sysfs_path):
                        super().__init__()
                        self.sysfs_path = sysfs_path
                        self._persistence = persistence
                        self.uid = "static"

                    def refresh(self):
                        self.active = True if self._persistence.state["effect"] == "static" else False

                    def apply(self, param=None):
                        with open(self.sysfs_path, "w") as f:
                            f.write("1")
                        self._persistence.save("effect", "static")

                pulsate = PulsateOptionBW2013(persistence, matrix_file_pulsate)
                pulsate.label = self._("Pulsate")
                pulsate.icon = self.get_icon("options", "pulsate")

                static = StaticOptionBW2013(persistence, matrix_file_static)
                static.label = self._("Static")
                static.icon = self.get_icon("options", "static")

                self.debug("Using sysfs workaround for Pulsate/Static")
                return [pulsate, static]

        except AttributeError:
            self.debug("Can't check _available_features as not supported by library. Omitting any workarounds.")

        return None

    def _get_poll_rate_option(self, rdevice):
        """
        Returns a Backend.Option derivative object for setting a mouse's poll rate.
        """
        current_rate = int(rdevice.poll_rate)
        parameters = []

        # OpenRazer <= 3.1.0 were hardcoded (not exposed via API)
        supported_poll_rates = [125, 500, 1000]

        # OpenRazer >= 3.2.0 provides the list
        if rdevice.has("supported_poll_rates"):
            supported_poll_rates = rdevice.supported_poll_rates

        for rate in supported_poll_rates:
            param = Backend.Option.Parameter()
            param.data = rate
            param.active = True if current_rate == rate else False

            # 500 Hz  = 2 millisecond latency
            # 1000 Hz = 1 millisecond latency
            # 2000 Hz = 0.5 millisecond latency
            msecs = float(1000 / rate)
            param.label = self._("X Hz (Y msec latency)").replace("X", str(rate)).replace("Y", str(int(msecs) if msecs.is_integer() else msecs))

            if rate > 1000:
                param.icon = self.get_icon("params", "poll_hyper")
            elif rate > 500:
                param.icon = self.get_icon("params", "poll_high")
            elif rate < 500:
                param.icon = self.get_icon("params", "poll_low")
            else:
                param.icon = self.get_icon("params", "poll_mid")

            parameters.append(param)

        class PollRateOption(Backend.MultipleChoiceOption):
            def __init__(self, rdevice, parameters):
                super().__init__()
                self._rdevice = rdevice
                self.uid = "poll_rate"
                self.parameters = parameters

            def refresh(self):
                current_rate = int(self._rdevice.poll_rate)
                for param in self.parameters:
                    param.active = True if param.data == current_rate else False

            def apply(self, new_value):
                self._rdevice.poll_rate = int(new_value)

        poll_rate = PollRateOption(rdevice, parameters)
        poll_rate.label = self._("Poll Rate")
        poll_rate.icon = self.get_icon("options", "poll_rate")
        return poll_rate

    def _get_game_mode_option(self, rdevice):
        """
        Returns a Backend.Option derivative object for the hardware's game mode feature.
        """
        class GameModeOption(Backend.ToggleOption):
            def __init__(self, rdevice):
                super().__init__()
                self._rdevice = rdevice
                self.uid = "game_mode"

            def refresh(self):
                self.active = True if rdevice.game_mode_led else False

            def apply(self, enabled):
                self._rdevice.game_mode_led = enabled

        option = GameModeOption(rdevice)
        option.label =  self._("Game Mode")
        option.label_toggle = self._("Disable Alt+Tab, Alt+F4 and Win keys")
        option.icon = self.get_icon("options", "game_mode")
        option.icon_enable = self.get_icon("options", "game_mode")
        option.icon_disable = self.get_icon("options", "game_mode_off")
        return option

    def _get_battery_options(self, rdevice):
        """
        Returns a list of Backend.Option derivative objects for power saving features.

        In OpenRazer >= 3.2.0, low power and sleep mode are exposed as individual capabilities.
        """
        options = []
        persistence = OpenRazerPersistenceFallback("main", rdevice.serial, self.persistence_fallback_path)

        # This is the amount of time before the device enters "sleep mode"
        if rdevice.has("get_idle_time") or rdevice.has("set_idle_time"):
            class IdleTimeOptionSetOnly(Backend.SliderOption):
                def __init__(self, rdevice, persistence):
                    # Device stores idle time in seconds. Present as minutes.
                    super().__init__()
                    self._rdevice = rdevice
                    self._persistence = persistence
                    self.uid = "idle_time"
                    self.min = 1
                    self.max = 15

                def refresh(self):
                    self.value = int(int(self._persistence.get("idle_time")) / 60)

                def apply(self, new_value):
                    self._rdevice.set_idle_time(int(new_value) * 60)
                    self._persistence.save("idle_time", int(new_value) * 60)

            class IdleTimeOptionSetGet(IdleTimeOptionSetOnly):
                def refresh(self):
                    self.value = int(self._rdevice.get_idle_time() / 60)

            if rdevice.has("get_idle_time"):
                idle_time = IdleTimeOptionSetGet(rdevice, persistence)
            else:
                idle_time = IdleTimeOptionSetOnly(rdevice, persistence)

            idle_time.label = self._("Sleep mode after")
            idle_time.icon = self.get_icon("options", "sleep")
            idle_time.suffix = ' ' + self._("minute")
            idle_time.suffix_plural = ' ' + self._("minutes")
            options.append(idle_time)

        # This is the battery percentage before the device enters a low power mode.
        if rdevice.has("get_low_battery_threshold") or rdevice.has("set_low_battery_threshold"):
            class LowBatteryThresholdOptionSetOnly(Backend.SliderOption):
                def __init__(self, rdevice, persistence):
                    super().__init__()
                    self._rdevice = rdevice
                    self._persistence = persistence
                    self.uid = "low_battery_threshold"
                    self.min = 1
                    self.max = 100
                    self.suffix = "%"
                    self.suffix_plural = "%"

                def refresh(self):
                    self.value = int(self._persistence.get("low_battery_threshold"))

                def apply(self, new_value):
                    self._rdevice.set_low_battery_threshold(int(new_value))
                    self._persistence.save("low_battery_threshold", int(new_value))

            class LowBatteryThresholdOptionSetGet(LowBatteryThresholdOptionSetOnly):
                def refresh(self):
                    self.value = int(self._rdevice.get_low_battery_threshold())

            if rdevice.has("get_low_battery_threshold"):
                low_power = LowBatteryThresholdOptionSetGet(rdevice, persistence)
            else:
                low_power = LowBatteryThresholdOptionSetOnly(rdevice, persistence)

            low_power.label = self._("Low Power Mode")
            low_power.icon = self.get_icon("options", "low_battery")
            options.append(low_power)

        return options

    def _get_macro_option(self, rdevice):
        """
        Returns a Backend.Option derivative object to explain macro support.
        """
        option = Backend.DialogOption()
        option.uid = "info_macros"
        option.label = self._("Macros")
        option.icon = self.get_icon("general", "info")
        option.button_label = self._("About Macro Recording")
        option.message = self._("The OpenRazer daemon provides a simple on-the-fly macro recording feature. To use:\n\n" + \
            "1. Press FN+[M] to enter macro mode.\n" + \
            "2. Press the macro key to assign to. Only M1-M5 are supported.\n" + \
            "3. Press the keys in sequence to record.\n" + \
            "4. Press FN+[M] to exit macro mode.\n\n" + \
            "Macros are retained in memory until the daemon is stopped. The replay speed will be instantaneous.\n\n" + \
            "This is not a Polychromatic feature and could disappear in future. This application intends to integrate a key rebinding feature in a future version.")
        return option

    def _get_key_remapping_option(self, rdevice):
        """
        Returns a Backend.Option derivative object to explain key remapping support.
        """
        option = Backend.DialogOption()
        option.uid = "info_mapping"
        option.label = self._("Key Mapping")
        option.icon = self.get_icon("general", "info")
        option.button_label = self._("About Key Mapping")
        option.message = self._("Currently, OpenRazer and Polychromatic do not support a convenient key rebinding feature. " + \
            "Polychromatic intends to integrate a key mapping solution in a future version.\n\n" + \
            "In the meantime, there are third party projects which provide key remapping agnostic to any input device.\n\nFor more information, visit:\n" + \
            "https://polychromatic.app/permalink/keymapping/")
        return option

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


class OpenRazerPersistence(object):
    """
    Use OpenRazer's persistence API introduced in v3.0.0. Each 'fx' zone contains
    variables that the daemon uses for storing the last effect, parameters and colours.

    Due to a daemon bug, there is no way to tell if a device does not support/need
    persistence, so we must fail gracefully (#294, openrazer/openrazer#1380)
    """
    state = {
        "effect": "spectrum",
        "colours": ["#00FF00", "#FF0000", "#0000FF"],
        "wave_dir": 1,
        "speed": 2,
    }

    def __init__(self, rzone):
        self.rzone = rzone

    def _convert_colour_bytes(self, rzone):
        """
        Convert the daemon's '.colors' hex output to a list consisting of #RRGGBB strings.
        """
        input_hex = rzone.colors.hex()

        if len(input_hex) >= 6:
            primary_hex = input_hex[:6]

        if len(input_hex) >= 12:
            secondary_hex = input_hex[6:12]

        if len(input_hex) >= 18:
            tertiary_hex = input_hex[12:18]

        return [
            "#" + primary_hex,
            "#" + secondary_hex,
            "#" + tertiary_hex
        ]

    def refresh(self):
        try:
            self.state["effect"] = str(self.rzone.effect)
            self.state["wave_dir"] = int(self.rzone.wave_dir)
            self.state["speed"] = int(self.rzone.speed)
            self.state["colours"] = self._convert_colour_bytes(self.rzone)
        except Exception:
            pass

    def save(self, key, value):
        # Not applicable. The daemon is taking care of storing persistence.
        return


class OpenRazerPersistenceFallback(OpenRazerPersistence):
    """
    Use a file-based persistence for backwards compatibility (<= 2.9.0)
    """
    def __init__(self, zone_id, serial, path):
        self.zone_id = zone_id
        self.serial = serial
        self.persistence_path = path

        # "colours" will be saved as separate files
        self.state["colour_1"] = self.state["colours"][0]
        self.state["colour_2"] = self.state["colours"][1]
        self.state["colour_3"] = self.state["colours"][2]

    def _get_key_path(self, key):
        return os.path.join(self.persistence_path, f"{self.serial}_{self.zone_id}_{key}")

    def _get_data(self, key, data_type):
        file_path = self._get_key_path(key)
        if os.path.exists(file_path):
            with open(file_path) as f:
                self.state[key] = data_type(f.readline())

    def refresh(self):
        self._get_data("effect", str)
        self._get_data("wave_dir", int)
        self._get_data("speed", int)
        self._get_data("colour_1", str)
        self._get_data("colour_2", str)
        self._get_data("colour_3", str)
        self.state["colours"] = [
            self.state["colour_1"],
            self.state["colour_2"],
            self.state["colour_3"],
        ]

    def get(self, key):
        file_path = self._get_key_path(key)
        if os.path.exists(file_path):
            with open(file_path) as f:
                return str(f.readline())
        return "0"

    def save(self, key, value):
        if not os.path.exists(self.persistence_path):
            os.makedirs(self.persistence_path)
        with open(self._get_key_path(key), "w") as f:
            f.write(str(value))
