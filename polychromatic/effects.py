# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
"""
Handles the processing of custom software effects and device mapping.
"""

import importlib
import json
import os
import shutil
import platform

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
    def __init__(self):
        self.feature = "effects"
        self.factory_path = os.path.join(self.paths.data_dir, "effects")
        self.local_path = self.paths.effects

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
                self.dbg.stdout("Effect upgraded (in memory) from v{0} to v{1}: {2}".format(save_format, fileman.VERSION, path), self.dbg.success, 1)
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
                    results.append(self._validate_key(param, "value"))
                    results.append(self._validate_key(param, "default"))
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
            else:
                self.dbg.stdout("Accompanying script file no longer exists: " + path, self.dbg.warning, 1)

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
            return " ".join(f.readlines()).replace("\\", "\\\\").replace("\n", "")

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


class ScriptedEffectHandler(object):
    """
    Parses scripted effects to verify dependencies, the environment and parse parameters.
    """
    def __init__(self, fileman, path):
        self.fileman = fileman
        self.path = path
        self.script_path = self.path.replace(".json", ".py")
        self.data = fileman.get_item(path)

    def _load_script(self):
        """
        Return the contents of the script file for parsing.
        None is returned if the file does not exist.
        """
        if not os.path.exists(self.script_path):
            return None

        with open(self.script_path, "r") as f:
            return f.readlines()

    def get_integrity_check(self):
        """
        Returns a boolean to indicate whether the script contains the required
        code to function as a Polychromatic scripted effect.
        """
        lines = self._load_script()
        if not lines:
            return False

        for line in lines:
            if line.strip() == "def play(fx, params=[]):":
                return True

        return False

    def get_modules(self):
        """
        Parses the Python script and gathers a list of modules.

        Returns:
            (list)      List of modules
            None        File error or detected unsupported import mechanism
        """
        lines = self._load_script()
        if not lines:
            return None

        modules = []
        for line in lines:
            line = line.strip()

            # Only permit 'import' - no 'from' to keep namespace clear.
            if line.startswith("from "):
                return None

            # For security and transparency, prevent importlib for sly imports.
            if line.find("importlib") != -1:
                return None

            if line[:6] == "import":
                modules.append(line.split(" ")[1])

        return modules

    @staticmethod
    def _simulate_import(module):
        """
        Tests if a module is importable, without actually importing it.
        """
        try:
            # Python >= 3.4
            if importlib.util.find_spec(module):
                return True
        except AttributeError:
            # Python <= 3.3
            if importlib.find_loader(module):
                return True
        return False

    def can_find_modules(self):
        """
        Returns a boolean to indicate whether all the script's imports
        can be found.
        """
        modules = self.get_modules()
        if not modules:
            return False

        for module in modules:
            if not self._simulate_import(module):
                return False

        return True

    def can_run_on_platform(self):
        """
        Returns a boolean to indicate whether the script is designed to run
        on this operating system.
        """
        required_os = self.data["required_os"]
        if not required_os:
            return True

        host_os = platform.system()
        for system in required_os:
            if host_os == system:
                return True

        return False

    def get_import_results(self):
        """
        Returns a dictionary with booleans to indicate which modules could
        be imported. Missing modules indicate a dependency is
        not installed or in the PATH.
        """
        modules = self.get_modules()
        if not modules:
            return modules

        results = {}
        for name in modules:
            results[name] = self._simulate_import(name)
        return results

    def is_device_compatible(self, device):
        """
        Reads a Backend.DeviceItem() and returns a boolean to indicate whether
        it is supported.
        """
        # Effect isn't restricted to specific device form factors
        if not self.data["designed_for"]:
            return True

        # Effect 'certifies' a specific device
        if device.name in self.data["optimised_for"]:
            return True

        # Effect is designed to run on this form factor
        if device.form_factor["id"] in self.data["designed_for"]:
            return True

        return False

    def get_parameters(self):
        """
        Returns a dictionary of processed parameters for use with this effect.

        To ensure the effect has a value, invalid or missing parameters will be
        replaced by its default value.
        """
        parameters = {}

        for param in self.data["parameters"]:
            key = param["var"]
            value = param["default"]
            param_type = param["type"]

            # Value already saved?
            if "value" in param.keys():
                value = param["value"]

            # Use default if no value specified or is invalid
            if not value:
                value = param["default"]

            types = {
                "colour": str,
                "str": str,
                "int": int
            }

            if param_type in types and type(value) != types[param_type]:
                value = param["default"]

            # Retrieve saved value
            if param_type == "list":
                found_match = False
                for option in param["options"]:
                    if param["options"][option] == value:
                        found_match = True
                if not found_match:
                    value = param["default"]

            elif param_type == "colour":
                if value[0] != "#" or len(value) not in [4, 7]:
                    value = param["default"]

            elif param_type == "str":
                value = str(value)

            elif param_type == "int":
                value = int(value)

            parameters[key] = value

        return parameters
