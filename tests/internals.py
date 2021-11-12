import pylib.common as common
import pylib.controller as controller
import pylib.locales as locales
import pylib.preferences as preferences
import pylib.procpid as procpid

import os
import unittest


class TestInternals(unittest.TestCase):
    """
    Test the internals of Polychromatic.
    """
    @classmethod
    def setUpClass(self):
        pass

    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        self._ = locales.Locales("polychromatic").init()
        self.dbg = common.Debugging()
        self.paths = common.paths
        preferences.init(self._)

    def tearDown(self):
        pass

    def test_locales_can_be_set(self):
        i18n = locales.Locales("polychromatic", "de_DE")
        _ = i18n.init()
        self.assertEqual(i18n.get_current_locale(), "de_DE", "Could not set up a German locale")

    def test_locales_can_translate_strings(self):
        _ = locales.Locales("polychromatic", "de_DE").init()
        # EN: Breath | DE: Atem
        self.assertEqual(_("Breath"), "Atem", "Could not translate text in German")

    def test_locales_can_translate_colours(self):
        _ = locales.Locales("polychromatic", "de_DE").init()
        if os.path.exists(self.paths.colours):
            os.remove(self.paths.colours)
        preferences.init(_)
        colours = preferences.load_file(self.paths.colours)
        passed = False
        for item in colours:
            # EN: Green | DE: Grün
            if item["name"] == "Grün":
                passed = True
        self.assertTrue(passed, "Could not translate colour strings")

    def test_config_pref_read(self):
        data = preferences.load_file(self.paths.preferences)
        self.assertFalse(data["controller"]["system_qt_theme"], "Could not init or read preferences file")

    def test_config_pref_write(self):
        newdata = preferences.load_file(self.paths.preferences)
        newdata["controller"]["landing_tab"] = 2
        preferences.save_file(self.paths.preferences, newdata)

        data = preferences.load_file(self.paths.preferences)
        self.assertEqual(data["controller"]["landing_tab"], 2, "Could not write to preferences file")

    def test_config_pref_force_invalid_data(self):
        newdata = preferences.load_file(self.paths.preferences)
        newdata["controller"]["system_qt_theme"] = 123456
        preferences.save_file(self.paths.preferences, newdata)

        # load_file._validate() should correct this
        data = preferences.load_file(self.paths.preferences)
        self.assertFalse(data["controller"]["system_qt_theme"], "Invalid data was not corrected")

    def test_data_path(self):
        self.assertTrue(self.paths.data_dir.endswith("/data"), "Unexpected development data directory path")

    def test_get_form_factor(self):
        ff = common.get_form_factor(self._, "keyboard")
        self.assertEqual(list(ff.keys()), ["id", "icon", "label"], "Unexpected get_form_factor() output")

    def test_get_form_factor_all(self):
        for form_factor_id in common.FORM_FACTORS:
            ff = common.get_form_factor(self._, form_factor_id)
        self.assertTrue(True, "Got exception processing form factors")

    def test_get_green_shades(self):
        shades = common.get_green_shades(self._)
        passed = True
        for shade in shades:
            if shade["hex"][1:3] != "00" or shade["hex"][5:7] != "00":
                passed = False
        self.assertTrue(passed, "Non-green hex values in get_green_shades()")

    def test_tray_icon_kde(self):
        os.environ["XDG_CURRENT_DESKTOP"] = "KDE"
        os.environ["GTK_THEME"] = "Breeze"
        self.assertEqual(common.get_default_tray_icon(), "img/tray/light/breeze.svg", "Could not detect KDE desktop for tray icon")
        del(os.environ["XDG_CURRENT_DESKTOP"])
        del(os.environ["GTK_THEME"])

    def test_tray_icon_ubuntu(self):
        self.assertEqual(common.get_default_tray_icon(), "img/tray/light/polychromatic.svg", "Coul not retrieve default tray icon")

    def test_get_icon(self):
        self.assertIsNotNone(common.get_icon("general", "controller"), "Could not retrieve an icon")

    def test_colour_bitmap(self):
        self.assertIsNotNone(common.generate_colour_bitmap(self.dbg, "#00FF00"), "Could not generate a colour bitmap")

    def test_asset_bitmaps(self):
        icons = common.get_icon_styles(self.dbg, "general", "controller", "#FF0000", "#00FF00", "#0000FF", "#FFFFFF", "#000000", "#808080")
        self.assertEqual(len(icons), 4, "Could not generate icon bitmap")

    def test_rgb_to_hex(self):
        self.assertEqual(common.rgb_to_hex([0, 255, 0]), "#00FF00", "Could not convert RGB to hex")

    def test_hex_to_rgb(self):
        self.assertEqual(common.hex_to_rgb("#FF00FF"), [255, 0, 255], "Could not convert RGB to hex")

    def test_state_set_effect(self):
        state = procpid.DeviceSoftwareState("POLY000001")
        state.set_effect("Untitled Effect 1", "/path/to/icon", "/path/to/effect.json")
        self.assertEqual(state.get_effect()["name"], "Untitled Effect 1", "Could not set effect state")
        self.assertEqual(state.get_effect()["icon"], "/path/to/icon", "Could not set effect state")
        self.assertEqual(state.get_effect()["path"], "/path/to/effect.json", "Could not set effect state")

    def test_state_clear_effect(self):
        state = procpid.DeviceSoftwareState("POLY000001")
        state.clear_effect()
        self.assertEqual(state.get_effect(), None, "Could not clear effect state")

    def test_state_set_preset(self):
        state = procpid.DeviceSoftwareState("POLY000001")
        state.set_preset("Untitled Effect 1", "/path/to/icon", "/path/to/effect.json")
        self.assertEqual(state.get_preset()["name"], "Untitled Effect 1", "Could not set preset state")
        self.assertEqual(state.get_preset()["icon"], "/path/to/icon", "Could not set preset state")
        self.assertEqual(state.get_preset()["path"], "/path/to/effect.json", "Could not set preset state")

    def test_state_clear_preset(self):
        state = procpid.DeviceSoftwareState("POLY000001")
        state.clear_preset()
        self.assertEqual(state.get_preset(), None, "Could not clear preset state")
