#!/usr/bin/python3
#
# Assumes run_daemon.sh is running.
#
# The tests target the latest version of OpenRazer from the 'master' branch.
#
import os
import random
import unittest

# Polychromatic Modules
from pylib import base
from pylib.backends._backend import Backend
from pylib.backends.openrazer import OpenRazerBackend, OpenRazerPersistence, OpenRazerPersistenceFallback

# External
import openrazer.client


class OpenRazerMiddlemanTest(unittest.TestCase):
    """
    Test OpenRazerBackend against a "fake driver" instance of the OpenRazer daemon,
    using all the supported devices for testing the class is implemented correctly.
    """
    @classmethod
    def setUpClass(self):
        self.base = base.PolychromaticBase()
        self.base.init_base("", [])
        self.openrazer = OpenRazerBackend(self.base)

    @classmethod
    def get_rdevice(self, name):
        """
        Directly get an OpenRazer device for testing.
        """
        for rdevice in self.openrazer.devman.devices:
            if rdevice.name == name:
                return rdevice

    @classmethod
    def get_option(self, device, option_uid, zone_id):
        """
        Returns a specific option from a zone.
        """
        for zone in device.zones:
            if zone.zone_id == zone_id:
                for option in zone.options:
                    if option.uid == option_uid:
                        return option
        raise ValueError(f"Could not find option '{option_uid}' in zone '{zone_id}' for {device.name}")

    @classmethod
    def get_device(self, name):
        """
        Returns a specific device by its name.
        """
        device = self.openrazer.get_device_by_name(name)
        if not device:
            raise ValueError("Could not find device: " + name)
        if not isinstance(device, self.openrazer.DeviceItem):
            raise ValueError(f"Could not get device: {name} due to this error:\n{device}")
        return device

    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        # Never allow device images to be downloaded
        self.allow_image_download = False

    def tearDown(self):
        pass

    def test_backend_init(self):
        self.assertTrue(self.openrazer.init(), "OpenRazerBackend could not init")

    def test_client_override(self):
        ripple_override_path = os.path.join(self.openrazer.get_backend_storage_path(), "ripple_refresh_rate")

        # Perform what the GUI would do
        with open(ripple_override_path, "w") as f:
            f.write("1")

        # Does it load correctly?
        self.openrazer.load_client_overrides()
        self.assertEqual(self.openrazer.ripple_refresh_rate, 1, "Failed to override a client setting")

    def test_empty_unrecog_list(self):
        self.assertEqual(self.openrazer.get_unsupported_devices(), [], "Unexpected 'unrecognised device' found")

    def test_get_devices(self):
        self.assertGreater(len(self.openrazer.get_devices()), 140, "Failed to get devices")

    def test_get_device_by_name(self):
        device = self.get_device("Razer BlackWidow Chroma")
        self.assertEqual(device.name, "Razer BlackWidow Chroma", "Failed to get a device by name")

    def test_get_device_by_serial(self):
        # XX0000000203 == razerblackwidowchroma.cfg
        device = self.openrazer.get_device_by_serial("XX0000000203")
        self.assertIsNotNone(device, "Failed to get a device by serial")

    def test_device_dpi_max(self):
        device = self.get_device("Razer Mamba Elite")
        self.assertEqual(device.dpi.max, 16000, "Incorrect Max DPI")

    def test_device_dpi_has_stages(self):
        device = self.get_device("Razer Mamba Elite")
        self.assertEqual(len(device.dpi.stages), 5, "Failed to list five DPI stages")

    def test_device_dpi_set_get(self):
        device = self.get_device("Razer DeathAdder V2")
        device.dpi.set(20000, 20000)
        device.dpi.refresh()
        self.assertEqual(device.dpi.x, 20000, "Failed to set or get DPI")

    def test_device_dpi_set_get_deathadder35G(self):
        # In <openrazer>/daemon/openrazer_daemon/hardware/mouse.py:
        # AVAILABLE_DPI = [450, 900, 1800, 3500]
        device = self.get_device("Razer DeathAdder 3.5G")
        option = self.get_option(device, "fixed_dpi", "main")

        if not option:
            raise RuntimeError("Expected a FixedDPIOption object")

        option.apply(900)
        option.refresh()

        # The second parameter should now be selected
        self.assertTrue(option.parameters[1].active, "Failed to set or get for a fixed DPI X device")

    def test_device_matrix(self):
        device = self.get_device("Razer BlackWidow Chroma V2")
        if device.matrix.rows != 6:
            raise ValueError("Unexpected rows: " + str(device.matrix.rows))
        if device.matrix.cols != 22:
            raise ValueError("Unexpected columns: " + str(device.matrix.cols))
        device.matrix.set(0, 0, 255, 0, 0)
        device.matrix.set(1, 0, 0, 255, 0)
        device.matrix.set(2, 0, 0, 0, 255)
        device.matrix.draw()
        device.matrix.clear()
        device.matrix.set(0, 1, 255, 255, 255)

    def test_device_matrix_deathstalker(self):
        # This device normally has 12 columns, but we have a virtual one of 6 due to its quirks.
        device = self.get_device("Razer DeathStalker Chroma")
        self.assertEqual(device.matrix.cols, 6, "Failed to create virtual matrix for Razer DeathStalker Chroma")

    def test_device_matrix_deathstalker_apply(self):
        device = self.get_device("Razer DeathStalker Chroma")
        device.matrix.clear()
        device.matrix.set(0, 0, 255, 0, 0)
        device.matrix.draw()

    def test_device_matrix_name(self):
        device = self.get_device("Razer BlackWidow Ultimate 2016")
        self.assertEqual(device.matrix.name, "Razer BlackWidow Ultimate 2016")

    def test_device_matrix_form_factor_id(self):
        device = self.get_device("Razer BlackWidow Chroma")
        self.assertEqual(device.matrix.form_factor_id, "keyboard")

    def test_zone_logo_laptop(self):
        # The second zone (logo) for some Blade models are the laptop lid
        device = self.get_device("Razer Blade Stealth (Late 2016)")
        self.assertEqual(device.zones[1].label, "Laptop Lid", "Failed to set custom zone label")

    def test_form_factor_stand(self):
        device = self.get_device("Razer Base Station Chroma")
        self.assertEqual(device.form_factor["id"], "stand", "Unexpected form factor ID")

    def test_vid_pid(self):
        device = self.get_device("Razer Mamba Tournament Edition")
        self.assertTrue(device.vid == "1532" and device.pid == "0046", "Failed to get VID:PID values")

    def test_monochromatic_keyboard(self):
        device = self.get_device("Razer BlackWidow Ultimate 2016")
        self.assertTrue(device.monochromatic == True, "Device incorrectly reporting monochromatic status")

    def test_non_monochromatic_headset(self):
        device = self.get_device("Razer Kraken Ultimate")
        self.assertTrue(device.monochromatic == False, "Device incorrectly reporting monochromatic status")

    def test_capability_main(self):
        rdevice = self.get_rdevice("Razer Mamba Tournament Edition")
        zone = OpenRazerBackend.DeviceItem.Zone()
        zone.zone_id = "main"
        self.assertTrue(self.openrazer._has_zone_capability(rdevice, zone, "brightness"), "Capability incorrectly reported")

    def test_capability_logo(self):
        rdevice = self.get_rdevice("Razer Abyssus Essential")
        zone = OpenRazerBackend.DeviceItem.Zone()
        zone.zone_id = "logo"
        self.assertTrue(self.openrazer._has_zone_capability(rdevice, zone, "reactive"), "Capability incorrectly reported")

    def test_capability_scroll(self):
        rdevice = self.get_rdevice("Razer Taipan")
        zone = OpenRazerBackend.DeviceItem.Zone()
        zone.zone_id = "scroll"
        self.assertTrue(self.openrazer._has_zone_capability(rdevice, zone, "active"), "Capability incorrectly reported")

    def test_capability_backlight(self):
        rdevice = self.get_rdevice("Razer Naga 2012")
        zone = OpenRazerBackend.DeviceItem.Zone()
        zone.zone_id = "backlight"
        self.assertTrue(self.openrazer._has_zone_capability(rdevice, zone, "active"), "Capability incorrectly reported")

    def test_capability_left(self):
        rdevice = self.get_rdevice("Razer Mamba Elite")
        zone = OpenRazerBackend.DeviceItem.Zone()
        zone.zone_id = "left"
        self.assertTrue(self.openrazer._has_zone_capability(rdevice, zone, "spectrum"), "Capability incorrectly reported")

    def test_capability_right(self):
        rdevice = self.get_rdevice("Razer Naga Left-Handed Edition 2020")
        zone = OpenRazerBackend.DeviceItem.Zone()
        zone.zone_id = "right"
        self.assertTrue(self.openrazer._has_zone_capability(rdevice, zone, "static"), "Capability incorrectly reported")

    def test_capability_charging(self):
        rdevice = self.get_rdevice("Razer Charging Pad Chroma")
        zone = OpenRazerBackend.DeviceItem.Zone()
        zone.zone_id = "charging"
        self.assertTrue(self.openrazer._has_zone_capability(rdevice, zone, "breath_random"), "Capability incorrectly reported")

    def test_capability_fast_charging(self):
        rdevice = self.get_rdevice("Razer Charging Pad Chroma")
        zone = OpenRazerBackend.DeviceItem.Zone()
        zone.zone_id = "fast_charging"
        self.assertTrue(self.openrazer._has_zone_capability(rdevice, zone, "brightness"), "Capability incorrectly reported")

    def test_capability_fully_charged(self):
        rdevice = self.get_rdevice("Razer Charging Pad Chroma")
        zone = OpenRazerBackend.DeviceItem.Zone()
        zone.zone_id = "fully_charged"
        self.assertTrue(self.openrazer._has_zone_capability(rdevice, zone, "wave"), "Capability incorrectly reported")

    def test_option_colours_persist(self):
        device = self.get_device("Razer Mamba Tournament Edition")
        static = self.get_option(device, "static", "main")
        static.colours[0] = "#123456"
        static.apply()
        static.colours[0] = "#000000"
        device.refresh()
        self.assertTrue(static.colours[0] == "#123456", "Persistence did not read/write as expected.")

    def test_option_brightness_main(self):
        device = self.get_device("Razer Mamba Tournament Edition")
        brightness = self.get_option(device, "brightness", "main")
        brightness.apply(24)
        brightness.refresh()
        self.assertTrue(brightness.value == 24, "Could not set 'variable' brightness correctly")

    def test_option_brightness_logo(self):
        device = self.get_device("Razer Mamba Elite")
        brightness = self.get_option(device, "brightness", "logo")
        brightness.apply(48)
        brightness.refresh()
        self.assertTrue(brightness.value == 48, "Could not set 'variable' brightness correctly")

    def test_option_brightness_right(self):
        device = self.get_device("Razer Lancehead (Wired)")
        brightness = self.get_option(device, "brightness", "right")
        brightness.apply(72)
        brightness.refresh()
        self.assertTrue(brightness.value == 72, "Could not set 'variable' brightness correctly")

    def test_option_active_logo(self):
        device = self.get_device("Razer Taipan")
        brightness = self.get_option(device, "brightness", "logo")
        brightness.apply(False)
        brightness.refresh()
        self.assertTrue(brightness.active == False, "Could not set 'toggle' brightness correctly")

    def test_option_active_scroll(self):
        device = self.get_device("Razer DeathAdder 3.5G")
        brightness = self.get_option(device, "brightness", "scroll")
        brightness.apply(True)
        brightness.refresh()
        self.assertTrue(brightness.active == True, "Could not set 'toggle' brightness correctly")

    def test_option_effect_change(self):
        device = self.get_device("Razer BlackWidow Chroma")
        none = self.get_option(device, "none", "main")
        static = self.get_option(device, "static", "main")
        none.apply()
        static.apply()
        none.refresh()
        device.refresh()
        self.assertTrue(none.active == False and static.active == True, "Could not set effect active state")

    def test_option_effect_none(self):
        device = self.get_device("Razer BlackWidow Lite")
        effect = self.get_option(device, "none", "main")
        effect.apply()

    def test_option_effect_spectrum(self):
        device = self.get_device("Razer Blade Pro (2019)")
        effect = self.get_option(device, "spectrum", "main")
        effect.apply()

    def test_option_effect_wave(self):
        device = self.get_device("Razer Blade (Late 2016)")
        effect = self.get_option(device, "wave", "main")
        effect.apply(effect.parameters[0].data)

    def test_option_effect_wave_label_mouse(self):
        device = self.get_device("Razer Mamba (Wireless)")
        effect = self.get_option(device, "wave", "main")
        self.assertTrue(effect.parameters[1].label == "Up", "Unexpected wave label for mouse")

    def test_option_effect_wave_label_mousemat(self):
        device = self.get_device("Razer Firefly V2")
        effect = self.get_option(device, "wave", "main")
        self.assertTrue(effect.parameters[1].label == "Clockwise", "Unexpected wave label for mousemat")

    def test_option_effect_ripple(self):
        device = self.get_device("Razer BlackWidow Chroma")
        effect = self.get_option(device, "ripple", "main")
        effect.apply(effect.parameters[0].data)

    def test_option_effect_reactive(self):
        device = self.get_device("Razer BlackWidow V3")
        effect = self.get_option(device, "reactive", "main")
        effect.apply(effect.parameters[0].data)

    def test_option_effect_static(self):
        device = self.get_device("Razer BlackWidow Chroma")
        effect = self.get_option(device, "static", "main")
        effect.apply()

    def test_option_effect_breath(self):
        device = self.get_device("Razer BlackWidow 2019")
        effect = self.get_option(device, "breath", "main")
        effect.apply(effect.parameters[0].data)

    def test_option_effect_breath_triple(self):
        device = self.get_device("Razer Kraken Ultimate")
        effect = self.get_option(device, "breath", "main")
        # Expects: [single, dual, triple]
        effect.apply(effect.parameters[2].data)

    def test_option_effect_starlight(self):
        device = self.get_device("Razer BlackWidow X Ultimate")
        effect = self.get_option(device, "starlight", "main")
        effect.apply(effect.parameters[-1].data)

    def test_workaround_bw2013_pulsate(self):
        device = self.get_device("Razer Deathstalker Expert")
        effect = self.get_option(device, "pulsate", "main")
        effect.apply()

    def test_workaround_bw2013_static(self):
        device = self.get_device("Razer BlackWidow Ultimate 2013")
        effect = self.get_option(device, "static", "main")
        effect.apply()

    def test_poll_rate_set(self):
        device = self.get_device("Razer Taipan")
        poll_rate = self.get_option(device, "poll_rate", "main")
        poll_rate.apply(500)

    def test_poll_rate_set_hyper(self):
        device = self.get_device("Razer Basilisk X HyperSpeed")
        poll_rate = self.get_option(device, "poll_rate", "main")
        poll_rate.apply(8000)

    def test_game_mode_set(self):
        device = self.get_device("Razer BlackWidow Chroma")
        game_mode = self.get_option(device, "game_mode", "main")
        game_mode.apply(True)

    def test_battery_idle_time_set_only(self):
        device = self.get_device("Razer Ouroboros")
        idle_time = self.get_option(device, "idle_time", "main")
        idle_time.apply(10)
        # 'get' is powered by fallback persistence
        device.refresh()
        idle_time.refresh()
        self.assertEqual(idle_time.value, 10, "Could not set or get idle_time (device = set only)")

    def test_battery_low_power_set_only(self):
        device = self.get_device("Razer Ouroboros")
        low_bat_thres = self.get_option(device, "low_battery_threshold", "main")
        low_bat_thres.apply(50)
        # 'get' is powered by fallback persistence
        device.refresh()
        low_bat_thres.refresh()
        self.assertEqual(low_bat_thres.value, 50, "Could not set or get low_battery_threshold (device = set only)")

    def test_battery_idle_time_set_get(self):
        device = self.get_device("Razer Basilisk X HyperSpeed")
        idle_time = self.get_option(device, "idle_time", "main")
        idle_time.apply(10)
        # 'get' is retrieved from device
        device.refresh()
        idle_time.refresh()
        self.assertEqual(idle_time.value, 10, "Could not set or get idle_time (device = get/set)")

    def test_battery_low_power_set_get(self):
        device = self.get_device("Razer Basilisk X HyperSpeed")
        low_bat_thres = self.get_option(device, "low_battery_threshold", "main")
        low_bat_thres.apply(50)
        # 'get' is retrieved from device
        device.refresh()
        low_bat_thres.refresh()
        self.assertEqual(low_bat_thres.value, 50, "Could not set or get low_battery_threshold (device = get/set)")

    def test_all_options_no_duplicates(self):
        for device in self.openrazer.get_devices():
            all_options = []
            for zone in device.zones:
                all_options += [zone.zone_id + "-" + option.uid for option in zone.options]

            filtered_options = set(all_options)
            if len(filtered_options) < len(all_options):
                raise KeyError("Duplicate option UIDs for " + device.name + \
                    f"! {len(all_options)} UIDs but only {len(filtered_options)} unique: {str(all_options)}")

    def test_all_devices_refresh(self):
        for device in self.openrazer.get_devices():
            device.refresh()

    def test_all_options_refresh(self):
        for device in self.openrazer.get_devices():
            for zone in device.zones:
                for option in zone.options:
                    option.refresh()

    def test_all_options_apply(self):
        for device in self.openrazer.get_devices():
            device.refresh()
            for zone in device.zones:
                for option in zone.options:
                    if isinstance(option, Backend.EffectOption):
                        if option.parameters:
                            option.apply(random.choices(option.parameters)[0].data)
                        else:
                            option.apply()
                    elif isinstance(option, Backend.ToggleOption):
                        option.apply(False)
                        option.apply(True)
                    elif isinstance(option, Backend.SliderOption):
                        option.apply(random.choices(range(option.min, option.max, option.step))[0])
                    elif isinstance(option, Backend.MultipleChoiceOption):
                        option.apply(random.choices(option.parameters)[0].data)
                    elif isinstance(option, Backend.ButtonOption):
                        option.apply()
                    option.refresh()

    def test_persistence_colour_bytes(self):
        rdevice = self.get_rdevice("Razer Mamba Tournament Edition")
        persistence = OpenRazerPersistence(rdevice.fx)
        persistence._convert_colour_bytes(rdevice.fx)

    def test_persistence_refresh(self):
        rdevice = self.get_rdevice("Razer Mamba Tournament Edition")
        persistence = OpenRazerPersistence(rdevice.fx)
        persistence.refresh()

    def test_persistence_fallback_read(self):
        rdevice = self.get_rdevice("Razer Mamba Tournament Edition")
        persistence = OpenRazerPersistenceFallback("main", rdevice.serial, self.openrazer.persistence_fallback_path)
        persistence.refresh()

    def test_persistence_fallback_write(self):
        rdevice = self.get_rdevice("Razer Mamba Tournament Edition")
        persistence = OpenRazerPersistenceFallback("main", rdevice.serial, self.openrazer.persistence_fallback_path)
        persistence.save("effect", "static")


if __name__ == '__main__':
    unittest.main()
