#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2021 Luke Horwell <code@horwell.me>
#
"""
Handles the processing of custom software effects and device mapping.
"""

import json
import os
import shutil

from . import common
from . import fileman

# Effect Types
TYPE_LAYERED = 1
TYPE_SCRIPTED = 2
TYPE_SEQUENCE = 3

# Layer Types
LAYER_STATIC = 10
LAYER_GRADIENT = 11
LAYER_PULSING = 12
LAYER_WAVE = 13
LAYER_SPECTRUM = 14
LAYER_CYCLE = 15
LAYER_SCRIPT = 16


class EffectFileManagement(fileman.FlatFileManagement):
    """
    Provides common functions for parsing the custom effects.
    """
    def __init__(self, i18n, _, dbg):
        """
        Store variables for the session.
        """
        super().__init__(i18n, _, dbg)
        self.feature = "effects"
        self.factory_path = os.path.join(common.paths.data_dir, "effects")
        self.local_path = common.paths.effects

    def get_item(self, path):
        """
        Load the effect into memory and validate the data is consistent and in
        accordance to the type of effect it is.

        Returns:
            {}          Data (and its effect type specific data) as defined by the documentation.
            ERROR_*     One of ERROR_* variables from the fileman module.
        """
        data = self._load_file(path)
        if not data:
            return fileman.ERROR_MISSING_FILE

        # Check the format and upgrade if necessary.
        try:
            save_format = data["save_format"]
            if save_format > fileman.VERSION:
                self.dbg.stdout("Refusing to load the effect '{0}' as it was created in a newer version of the application.".format(data["name"]), self.dbg.error)
                return fileman.ERROR_NEWER_FORMAT
            elif fileman.VERSION > save_format:
                data = self.upgrade_item(data)
                self.dbg.stdout("Effect upgraded (in memory) to version {0}: {1}".format(fileman.VERSION, path), self.dbg.success)
        except KeyError:
            self.dbg.stdout("Invalid Effect: Unspecified save format!", self.dbg.error)
            return fileman.ERROR_BAD_DATA

        # Validate common metadata
        if not self._validate_key(data, "type", int):
            self.dbg.stdout("Invalid Effect: Unspecified type!", self.dbg.error)
            return fileman.ERROR_BAD_DATA

        results = [
            self._validate_key(data, "name", str),
            self._validate_key(data, "type", int),
            self._validate_key(data, "author", str),
            self._validate_key(data, "author_url", str),
            self._validate_key(data, "icon", str),
            self._validate_key(data, "summary", str),
            self._validate_key(data, "map_device", str),
            self._validate_key(data, "map_device_icon", str),
            self._validate_key(data, "map_graphic", str),
            self._validate_key(data, "map_cols", int),
            self._validate_key(data, "map_rows", int),
            self._validate_key(data, "save_format", int),
            self._validate_key(data, "revision", int)
        ]

        # Validate specific data
        effect_type = data["type"]

        if effect_type == TYPE_LAYERED:
            results.append(self._validate_key(data, "layers", list))
            try:
                for layer in data["layers"]:
                    results.append(self._validate_key(layer, "name", str))
                    results.append(self._validate_key(layer, "type", int))
                    results.append(self._validate_key(layer, "positions", list))
                    results.append(self._validate_key(layer, "properties", dict))
            except KeyError:
                results.append(False)

        elif effect_type == TYPE_SCRIPTED:
            script_path = os.path.join(os.path.dirname(path), os.path.basename(path).replace(".json", ".py"))
            if not os.path.exists(script_path):
                self.dbg.stdout("Effect script does not exist: " + script_path, self.dbg.warning, 1)

            results.append(self._validate_key(data, "required_os", list))
            results.append(self._validate_key(data, "parameters", list))
            results.append(self._validate_key(data, "designed_for", list))
            results.append(self._validate_key(data, "optimised_for", list))
            try:
                for param in data["parameters"]:
                    results.append(self._validate_key(param, "var", str))
                    results.append(self._validate_key(param, "label", str))
                    results.append(self._validate_key(param, "type", str))
            except KeyError:
                results.append(False)

        elif effect_type == TYPE_SEQUENCE:
            results.append(self._validate_key(data, "fps", int))
            results.append(self._validate_key(data, "loop", bool))
            results.append(self._validate_key(data, "frames", list))

        # Was validation successful?
        if False in results:
            self.dbg.stdout("The effect '{0}' contains invalid data.".format(path), self.dbg.error)
            if not self.dbg.verbose_level >= 1:
                self.dbg.stdout("Run this application in the Terminal with the -v parameter for details.", self.dbg.warning)
            return fileman.ERROR_BAD_DATA

        # Append "parsed" key (used by the UI, but not saved)
        data["parsed"] = self._get_parsed_keys(data, path)

        return data

    def init_data(self, effect_name, effect_type):
        """
        Creates new effect data, ready for editing by the editor.

        Returns (dict) containing new data.
        """
        data = {}

        # Common for all effects
        data["name"] = effect_name
        data["type"] = effect_type
        data["author"] = ""
        data["author_url"] = ""
        data["icon"] = "img/general/effects.svg"
        data["summary"] = ""
        data["map_device"] = ""
        data["map_device_icon"] = ""
        data["map_graphic"] = ""
        data["map_cols"] = 0
        data["map_rows"] = 0
        data["save_format"] = fileman.VERSION
        data["revision"] = 1

        if effect_type == TYPE_LAYERED:
            data["layers"] = [
                {
                    "name": self._("Layer 1"),
                    "type": LAYER_STATIC,
                    "positions": [],
                    "properties": {}
                }
            ]

        elif effect_type == TYPE_SCRIPTED:
            data["required_os"] = []
            data["parameters"] = []
            data["designed_for"] = []
            data["optimised_for"] = []

        elif effect_type == TYPE_SEQUENCE:
            data["fps"] = 10
            data["loop"] = True
            data["frames"] = []

        return data

    def upgrade_item(self, data):
        """
        Upgrades the data for an effect if it was saved in a older version
        of the application.

        Returns the new data.
        """
        old_ver = data["save_format"]

        # Version 8: First! Nothing new yet.

        data["save_format"] = fileman.VERSION
        return data

    def delete_item(self, path):
        """
        In addition to the usual deletion of an item, also delete the
        effect's accompanying script (if a scripted effect)
        """
        data = self._load_file(path)
        if data["type"] == TYPE_SCRIPTED:
            py_path = path.replace(".json", ".py")
            if os.path.exists(py_path):
                os.remove(py_path)
            self.dbg.stdout("Deleted: " + path, self.dbg.success, 1)

        return super().delete_item(path)

    def clone_item(self, path):
        """
        In addition to the usual duplication of an item, also copy
        the effect's accompanying script (if a scripted effect)

        Returns:
            (str)           Success: Path to the new effect
            None            Failed to clone effect
        """
        new_path = super().clone_item(path)

        if new_path:
            data = self._load_file(new_path)

            if data["type"] == TYPE_SCRIPTED:
                src_script = path.replace(".json", ".py")
                dest_script = new_path.replace(".json", ".py")

                if not os.path.exists(src_script):
                    return False

                shutil.copy(src_script, dest_script)
                self.dbg.stdout("Clone OK: " + dest_script, self.dbg.success)

            return new_path

        return None


class DeviceMapGraphics(object):
    """
    Responsible for populating the list of device graphics and generating SVG
    graphics of a grid if a specific device is unavailable (or by request).
    """
    def __init__(self, appdata):
        self.appdata = appdata
        self.map_index = os.path.join(common.paths.data_dir, "devicemaps", "maps.json")
        self.map_dir = os.path.join(common.paths.data_dir, "devicemaps")
        self.cache_dir = common.paths.assets_cache

    def get_graphic_list(self):
        """
        Returns a list of dictionaries referencing graphics:
        {
            "Human readable name": {
                "filename": "some_device_graphic_en_GB.svg",
                "rows": 1,
                "cols": 2,
                "locale": "en_GB"
            }, { ... }
        }
        """
        with open(self.map_index) as f:
            original_svg =  json.load(f)

        parsed_svg = {}

        for name in original_svg:
            graphic_path = self.get_graphic_path(original_svg[name]["filename"])
            if not os.path.exists(graphic_path):
                self.appdata.dbg.stdout("Graphic missing: " + graphic_path, self.appdata.dbg.warning)
                continue
            parsed_svg[name] = original_svg[name]

        return parsed_svg

    def get_graphic_path(self, filename):
        """
        Returns an absolute path to the graphic.
        For use with metadata editor UI which loads via file.
        """
        return os.path.join(self.map_dir, filename)

    def get_grid_path(self, cols, rows):
        """
        Returns an absolute path to the grid SVG.
        For use with metadata editor UI which loads via file.
        """
        svg = self.get_svg_grid(cols, rows)
        svg_path = os.path.join(self.cache_dir, "grid-{0}-{1}.svg".format(cols, rows))
        with open(svg_path, "w") as f:
            f.writelines(svg)
        return svg_path

    def get_graphic_name_from_filename(self, filename):
        """
        Return the human friendly name from the specified filename. If there
        isn't an entry, the filename will be returned.
        """
        maps = self.get_graphic_list()
        for name in maps.keys():
            if maps[name]["filename"] == filename:
                return name
        return filename

    def get_svg_graphic(self, filename):
        """
        Loads the SVG of a device to visually map.

        Returns:
            (str)       SVG Data
            None        File Missing
        """
        # Verify the device map exists, then load it
        graphic_path = os.path.join(self.map_dir, filename)

        if not os.path.exists(graphic_path):
            return None

        with open(os.path.join(self.map_dir, filename)) as f:
            return str(f.readlines()).replace("\n", "")

    def get_svg_grid(self, cols, rows):
        """
        Returns the SVG of the device's matrix represented as a 'pretty' graphic.
        """
        svg = []

        # How large is each grid?
        square_px = 50
        margin_px = 1
        fill_colour = "#00ff00"
        stroke_colour = "#008000"
        stroke_width = 1
        total_X_blocks = cols
        total_Y_blocks = rows

        svg.append('<svg width="{width}px" height="{height}px"> version="1.1" viewBox="0px 0px {width}px {height}px" xmlns="http://www.w3.org/2000/svg">'.format(
            width = total_X_blocks * square_px + (margin_px * total_X_blocks),
            height = total_Y_blocks * square_px + (margin_px * total_X_blocks)
        ))

        for x in range(0, total_X_blocks):
            for y in range(0, total_Y_blocks):
                x_pos = x * square_px + (x * margin_px + 1)
                y_pos = y * square_px + (y * margin_px + 1)
                svg.append('<g id="x{x}-y{y}" class="LED"><rect x="{x_pos}px" y="{y_pos}px" width="{square_px}px" height="{square_px}px" style="fill:{fill_colour};paint-order:markers fill stroke;stroke-linecap:round;stroke-width:{stroke_width};stroke:{stroke_colour}"/></g>'.format(
                    x = x,
                    y = y,
                    x_pos = x_pos,
                    y_pos = y_pos,
                    square_px = square_px,
                    fill_colour = fill_colour,
                    stroke_colour = stroke_colour,
                    stroke_width = stroke_width
                ))

        svg.append("</svg>")
        return "".join(svg)
