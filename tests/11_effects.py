#!/usr/bin/python3
#
# Working directory should be the repository root.
#

import pylib.common as common
import pylib.locales as locales
import pylib.preferences as preferences
import pylib.effects as effects

import glob
import json
import os
import unittest


class PolychromaticTests(unittest.TestCase):
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
            if not type(item["filename"]) == str:
                passed = False
            if not type(item["rows"]) == int:
                passed = False
            if not type(item["cols"]) == int:
                passed = False
            if not type(item["locale"]) in [str, None]:
                passed = False

        self.assertEqual(passed, True, "Invalid data found in maps.json")

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


if __name__ == '__main__':
    unittest.main()
