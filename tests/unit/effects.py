#!/usr/bin/python3
#
# Working directory should be the repository root.
#

import pylib.common as common
import pylib.locales as locales
import pylib.preferences as preferences
import pylib.effects as effects
import pylib.fileman as fileman

import glob
import json
import os
import unittest


class TestEffects(unittest.TestCase):
    """
    Test the internals of Polychromatic.
    """
    @classmethod
    def setUpClass(self):
        self.i18n = locales.Locales("polychromatic")
        self._ = self.i18n.init()
        self.dbg = common.Debugging()
        self.paths = common.paths
        preferences.init(self._)

        self.fileman = effects.EffectFileManagement(self.i18n, self._, self.dbg)

        # Dummy content
        self.fileman.save_item(self.fileman.init_data("Test 1", effects.TYPE_LAYERED))
        self.fileman.save_item(self.fileman.init_data("Test 2", effects.TYPE_LAYERED))
        self.fileman.save_item(self.fileman.init_data("Test 3", effects.TYPE_LAYERED))

        # Unit test resources
        self.res_path = os.path.join(os.path.dirname(__file__), "files")

    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_layered_effect(self):
        data1 = self.fileman.init_data("My Layered Effect", effects.TYPE_LAYERED)
        success, path = self.fileman.save_item(data1)
        data2 = self.fileman.get_item(path)
        self.assertEqual(type(data2), dict, "Could not create a layered effect")

    def test_create_scripted_effect(self):
        data1 = self.fileman.init_data("My Scripted Effect", effects.TYPE_SCRIPTED)
        success, path = self.fileman.save_item(data1)
        data2 = self.fileman.get_item(path)
        self.assertEqual(type(data2), dict, "Could not create a scripted effect")

    def test_create_sequence_effect(self):
        data1 = self.fileman.init_data("My Sequence Effect", effects.TYPE_SEQUENCE)
        success, path = self.fileman.save_item(data1)
        data2 = self.fileman.get_item(path)
        self.assertEqual(type(data2), dict, "Could not create a sequence effect")

    def test_illegal_unix_filename(self):
        data = self.fileman.init_data("Game / Application & More", effects.TYPE_LAYERED)
        success, path = self.fileman.save_item(data)
        self.assertTrue(os.path.exists(path), "Failed to strip illegal Unix filename characters")

    def test_unicode_characters(self):
        data = self.fileman.init_data("Game: What? Who! Where: ƀƁƂƃƄƅƆƇƈƉƊƌƍƎƏƐƑƒ 😁", effects.TYPE_LAYERED)
        success, path = self.fileman.save_item(data)
        self.assertTrue(os.path.exists(path), "Failed to process Unicode characters")

    def test_get_effect_list(self):
        items = self.fileman.get_item_list()
        self.assertGreaterEqual(len(items), 3, "Could not get a list of effects")

    def test_get_effect(self):
        items = self.fileman.get_item_list()
        data = self.fileman.get_item(items[0]["path"])
        self.assertEqual(type(data["name"]), str, "Could not get an effect")

    def test_delete_effect(self):
        items = self.fileman.get_item_list()
        data = self.fileman.get_item(items[0]["path"])
        path_to_delete = data["parsed"]["path"]
        self.fileman.delete_item(path_to_delete)
        self.assertEqual(os.path.exists(path_to_delete), False, "Could not delete an effect")

    def test_clone_effect(self):
        items = self.fileman.get_item_list()
        data = self.fileman.get_item(items[0]["path"])
        source_path = data["parsed"]["path"]
        cloned_path = self.fileman.clone_item(source_path)
        self.assertEqual(os.path.exists(source_path), os.path.exists(cloned_path), "Could not clone an effect")

    def test_rename_effect(self):
        items = self.fileman.get_item_list()
        data = self.fileman.get_item(items[0]["path"])
        orig_path = data["parsed"]["path"]
        data["name"] = "NEW NAME"
        self.fileman.save_item(data, orig_path)
        self.assertEqual(os.path.exists(orig_path), False, "Could not rename an effect")

    def test_saving_duplicate_name(self):
        items = self.fileman.get_item_list()
        data = self.fileman.get_item(items[0]["path"])
        orig_path = data["parsed"]["path"]
        success, new_path = self.fileman.save_item(data)
        self.assertNotEqual(orig_path, new_path, "Could not save an effect with a duplicate filename")

    def test_devicemap_map_json(self):
        passed = True
        with open("data/devicemaps/maps.json") as f:
            data = json.load(f)
        for name in data.keys():
            item = data[name]
            keys = list(item.keys())
            if False in [
                "filename" in keys,
                "rows" in keys,
                "cols" in keys,
                "locale" in keys,
                "scancode" in keys
            ]:
                passed = False

        self.assertEqual(passed, True, "Item(s) missing keys in maps.json")

    def test_devicemap_valid_json(self):
        passed = True
        for svg_file in glob.glob("data/devicemaps/*.json"):
            with open(svg_file) as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(svg_file, str(e))
                    passed = False

        self.assertEqual(passed, True, "Invalid JSON: " + svg_file)

    def test_devicemap_map_exists(self):
        passed = True
        with open("data/devicemaps/maps.json") as f:
            data = json.load(f)
        for name in data.keys():
            if not os.path.exists("data/devicemaps/" + data[name]["filename"]):
                passed = False

        self.assertEqual(passed, True, "maps.json referenced SVG files that do not exist")

    def test_devicemap_map_xy_check(self):
        for svg_file in glob.glob("data/devicemaps/*.svg"):
            with open(svg_file) as f:
                data = " ".join(f.readlines())

                # SVGs should have at least one "LED" class.
                if data.find("LED") == -1:
                    self.assertTrue(False, "Device map {0} does not specify an LED class!".format(os.path.basename(svg_file)))
                found_an_ID = False
                for x in range(0, 50):
                    for y in range(0, 50):
                        if data.find("x{0}-y{1}".format(str(x), str(y))) != -1:
                            found_an_ID = True

                # SVGs should have at least one "x0-y0" ID.
                if not found_an_ID:
                    self.assertTrue(False, "Device map {0} does not specify IDs!".format(os.path.basename(svg_file)))

        self.assertEqual(True, True)

    def test_script_handler_init(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")

    def test_script_integrity(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        self.assertEqual(handler.get_integrity_check(), True, "Failed to validate effect script integrity!")

    def test_script_integrity_bad(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_bad.json")
        self.assertEqual(handler.get_integrity_check(), False, "Improperly validated a bad effect script!")

    def test_script_modules(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        self.assertEqual(handler.get_modules(), ["math", "time"], "Unexpected modules from effect script!")

    def test_script_modules_bad(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_bad.json")
        self.assertEqual(handler.get_modules(), None, "Improperly listing modules for a bad effect script!")

    def test_script_can_find_modules(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        self.assertEqual(handler.can_find_modules(), True, "Could not find modules for effect script!")

    def test_script_can_find_modules_bad(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_bad.json")
        self.assertEqual(handler.can_find_modules(), False, "Found non-existant modules for effect script!")

    def test_script_can_run_on_platform(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        self.assertEqual(handler.can_run_on_platform(), True, "Could not determine OS for effect script!")

    def test_script_import_results(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        results = handler.get_import_results()
        self.assertTrue(results["math"], "Failed to get module status for effect script!")

    def test_script_is_device_compatible_1(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        # This effect was written specifically for this hardware
        device = {
            "name": "Razer BlackWidow Chroma",
            "form_factor": {
                "id": "keyboard"
            }
        }
        self.assertTrue(handler.is_device_compatible(device), "Miscategorised a device as incompatible for effect script!")

    def test_script_is_device_compatible_2(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        # This effect works on any keyboards
        device = {
            "name": "Razer BlackWidow Ultimate 2016",
            "form_factor": {
                "id": "keyboard"
            }
        }
        self.assertTrue(handler.is_device_compatible(device), "Miscategorised a device as incompatible for effect script!")

    def test_script_is_device_compatible_3(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        # This effect is not designed for mice
        device = {
            "name": "Razer Mamba",
            "form_factor": {
                "id": "mouse"
            }
        }
        self.assertFalse(handler.is_device_compatible(device), "Miscategorised a device as compatible for effect script!")

    def test_script_parameters_default(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        params = handler.get_parameters()
        # Colour: Value not set, should return default.
        self.assertEqual(params["test_colour"], "#00FF00", "Script parameter returned incorrect default!")

    def test_script_parameters_list(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        params = handler.get_parameters()
        # List: Value set, should be returned.
        self.assertEqual(params["test_list"], 2, "Script parameter returned incorrect value!")

    def test_script_parameters_str(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        params = handler.get_parameters()
        # String: Value set, should be returned.
        self.assertEqual(params["test_text"], "My Text", "Script parameter returned incorrect value!")

    def test_script_parameters_int(self):
        handler = effects.ScriptedEffectHandler(self.fileman, self.res_path + "/script_good.json")
        params = handler.get_parameters()
        # Number: Value not set, should return default.
        self.assertEqual(params["test_number"], 48, "Script parameter returned incorrect value!")


if __name__ == '__main__':
    unittest.main()
