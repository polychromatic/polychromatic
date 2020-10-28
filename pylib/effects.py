#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2019-2020 Luke Horwell <code@horwell.me>
#
"""
This module manages, edits and renders custom effects.

Documentation: https://polychromatic.app/docs/config-effects/
"""

import glob
import os
import json
import hashlib
import importlib
import sys

from . import common
from . import locales
from . import preferences as pref
from . import procpid
from . import fx

# Also set in preferences.py
VERSION = 7

path = common.Paths()
dbg = common.Debugging()


def _read_file(filepath):
    """
    Read the effect from disk and return the content on success.
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        dbg.stdout("Failed to read effect metadata: " + filepath, dbg.error)
        dbg.stdout(common.get_exception_as_string(e) + "\n", dbg.error)
        return None


def _write_file(filepath, data):
    """
    Write the effect to disk.
    """
    try:
        with open(filepath, "w") as f:
            f.write(json.dumps(data, sort_keys=True, indent=4))
        return True
    except Exception as e:
        dbg.stdout("Failed to write effect: " + filepath, dbg.error)
        dbg.stdout(common.get_exception_as_string(e) + "\n", dbg.error)
        return False


def _get_i18n(data, key_name):
    """
    Returns localised keys for a dictionary if they exist.
    """
    pass
    return ""





def _get_icon_path(icon):
    """
    Returns an absolute path to the icon for the effect.
    """
    if os.path.exists(icon):
        return icon

    if icon.startswith("img/"):
        absolute_builtin_icon = os.path.join(path.data_dir, icon)
        if os.path.exists(absolute_builtin_icon):
            return absolute_builtin_icon

    return common.get_icon("effects", "layer-middle")


def _get_md5_checksum(path):
    """
    Returns the hash of a file.
    """
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_effect_list():
    """
    Prepares a list describing the effects currently stored on the filesystem.
    This will use translated strings if present in the file.

    Returns a list consisting of dictionaries:
    [
        {
            "filename": (str),
            "type": "scripted" or "keyframed",
            "name": (str),
            "icon": (str),          # Relative from 'data' or absolute path.
            "tampered": (bool)      # Checksum mismatch for scripted effect.
            "revision": (int)
        },
        { ... }
    ]
    """
    file_list_keyframed = glob.glob(path.effects_keyframed + "/*.json")
    file_list_scripted = glob.glob(path.effects_scripted + "/*.json")
    file_list = file_list_keyframed + file_list_scripted
    effect_list = []

    for filepath in file_list:
        data = _read_file(filepath)
        if not data:
            continue

        try:
            effect_list.append({
                "filepath": filepath,
                "type": data["type"],
                "name": _get_i18n(data, "name"),
                "icon": _get_icon_path(data["icon"]),
                "revision": data["revision"]
            })
        except KeyError as e:
            dbg.stdout("Invalid data for {0}: {1}".format(filepath, str(e)), dbg.error)

    return effect_list


def get_effect(filepath):
    """
    Returns a dictionary describing the effect (metadata) as well as the data
    necessary to read and modify the effect.

    The JSON is directly loaded into memory, with a 'ui' variable that holds
    some "rendered" variables in memory, such as effect type, and i18n values.

    Params:
        filepath        (str)   Full path to the effect.

    Returns:
        None        Effect cannot be found.
        False       Effect is invalid.
        (dict)      Effect successfully read.

    For all effects:
    {
        "name": (str)
        "summary": (str)
        "type": (str)                   # 'keyframed' or 'scripted'
        "author": (str)
        "icon": (str)                   # Absolute path (built-in icons are saved as a relative string)
        "save_format": -1               # Internal FX version. -1 will auto set to latest.
        "revision": 1                   # User's incremental revision number.
    }

    Processed in memory, not to be saved to disk:
    {
        "ui": {
            "name": (str),              # Using i18n key if used.
            "summary": (str),           # Using i18n key if used.
            "icon": (str),              # Absolute path to the icon
            "filepath": (str),          # Absolute path to the effect
        }
    }

    For keyframed effects only:
    {
        "optimised": {
            "form_factor": (str)
            "name": (str)               # Device Name
        },
        "data": [
            "frames": (int)             # Number of frames
            "layers": [
                {
                    "name": (str)
                    "type": (str)       # 'wave', 'spectrum', 'static', 'frames'
                    "single": (bool)    # True if the layer type specifies each frame.
                    "prop": {
                        "colours": (list)
                        "direction": (int)
                    }
                    "keyframes": [      # If 'single' is FALSE
                        "0,0"           # "x,y" values wrapped in string. 1-based.
                    ]
                    "frames": {
                        1: {            # Frame number. 1-based.
                            {
                                "x": (int),
                                "y": (int),
                                "colour": (str)
                            }
                        }
                    }
                }
            ]
        ]
    }

    For scripted effects only:
    {
        "depends": {
            "form_factor": (list)
            "OS": (list)
            "py_dependencies": (list)
        },
        "parameters": [
            {
                "var": (str)            # Internal variable name
                "label": (str)          # Label to show in interface. i18n supported.
                "type": "colour"        # "colour", "choice" or "text"
                "value": null           # Currently set value. Defaults to None.
                "default": (str)        # Default value.
            }
        ],
        "checksum_passed": (bool)         # MD5 checksum passes?
    }
    """
    data = _read_file(filepath)
    if not data:
        return None

    # Attributes in memory
    effect = data.copy()
    effect["ui"] = {}
    #effect["ui"]["name"] = _get_i18n(data, "name")
    #effect["ui"]["summary"] = _get_i18n(data, "summary")
    effect["ui"]["icon"] = _get_icon_path(data["icon"])
    effect["ui"]["filepath"] = filepath

    # Check internal FX version matches this version of the application.
    if effect["save_format"] == -1:
        data["save_format"] = VERSION
        _write_file(filepath, data)

    elif effect["save_format"] > VERSION:
        dbg.stdout("Warning: Effect was saved in a newer version of the application!", dbg.warning)
        dbg.stdout(filepath, dbg.warning)
        dbg.stdout("Saved: v{0}    Application: v{1}".format(effect["save_format"], VERSION), dbg.warning)

    # Validate that all required metadata exists.
    for required_key in ["name", "summary", "author", "icon", "save_format", "revision"]:
        if not required_key in data.keys():
            dbg.stdout("Effect missing required key: " + required_key, dbg.error)
            return False

    # Data specific to the type of effect
    if effect["type"] == "keyframed":
        try:
            effect["data"]["frames"]
            effect["data"]["layers"]
            effect["optimised"]["form_factor"]
            effect["optimised"]["name"]
        except KeyError as e:
            dbg.stdout("Missing keyframe data: " + filepath, dbg.error)
            dbg.stdout(common.get_exception_as_string(e), dbg.error)
            return False

    elif effect["type"] == "scripted":
        try:
            effect["depends"]["form_factor"]
            effect["depends"]["OS"]
            effect["depends"]["py_dependencies"]
            effect["parameters"]
        except KeyError as e:
            dbg.stdout("Missing script metadata: " + filepath, dbg.error)
            dbg.stdout(common.get_exception_as_string(e), dbg.error)
            return False

        script_path = filepath.replace(".json", ".py")

        if not os.path.exists(script_path):
            dbg.stdout("Missing effect Python script for: " + filepath, dbg.error)
            return False

        effect["ui"]["tampered"] = _get_md5_checksum(filepath) == data["checksum_md5"]

    return effect


def play_effect_hardware(filepath, backend, device_uid):
    """
    Play the effect directly onto a device that supports individual key lighting.
    This will spawn the 'helper' process, which will be dedicated to the processing
    of the effect.

    Returns:
        (bool)          Indicate whether execution succeeded or failed.

    Params:
        filepath        Name of the effect.
        backend         Device's backend ID
        device_uid      Backend ID for device
    """
    return procpid.start_component("helper", [
        "--play-custom-effect",
        "--filepath", filepath,
        "--device-backend", backend,
        "--device-uid", device_uid
    ])


def render_keyframes(filepath):
    """
    Generates a dictionary consisting of "flattened" matrixes for each frame.
    This merges layers and calculates the colours for each (key)frame.

    This will be cached to disk to prevent excessive calculations.

    Returns:
        (str)   Render successful. Path to cache file.
        None    Effect file does not exist or is unreadable.
        False   Render failed. Invalid or missing data.
    """
    effect = _read_file(filepath)
    if not effect:
        return None

    checksum = _get_md5_checksum(filepath)
    cache_path = os.path.join(path.effects_cache, checksum + ".json")

    if os.path.exists(cache_path):
        return cache_path

    # TODO: Stub!
    print("stub:render_keyframes")

    return cache_path

    """

    Params:
    """
    pass
def send_effect_frames(frames, fps, device):
    """
    Use the devuce object to send a series of frames to the hardware.
    This should be spawned by the helper process.

    Params:
        frames      (dict)  Dictionary containing the files
        fps         (int)   Desired number of frames per second.
        device      (str)   middleman.get_device_object() object
    """
    #fx_obj = fx.FX(device)
    #procpid.set_as_device_custom_fx(device["serial"]) # FIXME

    # FIXME: Stub!
    print("stub:send_effect_frames")


def send_effect_custom(script_path, device, params):
    """
    Use the device object and execute a custom effect script.
    This should be spawned by the helper process.

    Params:
        script_path (str)   Path to Python script
        device      (str)   middleman.get_device_object() object
    """
    #fx_obj = fx.FX(device)
    try:
        script_dir = os.path.dirname(script_path)
        script_name = os.path.basename(script_path).replace(".py", "")
        sys.path.append(script_dir)
        custom_script = importlib.import_module(script_name)
    except Exception as e:
        dbg.stdout("Failed to import custom effect script: " + script_path, dbg.error)
        dbg.stdout(common.get_exception_as_string(e), dbg.error)
        exit(1)

    try:
        #procpid.set_as_device_custom_fx(device["serial"]) # FIXME
        #custom_script.run(fx_obj, params)
        raise NotImplementedError
    except KeyboardInterrupt:
        exit(0)


def check_environment(effect, device):
    """
    Check this system's environment to ensure the scripted effect will run as intended.

    Scripted effects can be restricted by:
      - OS
      - Form Factors
      - Python Modules
      - Checksum Mismatch

    Params:
        effect          (dict)  Raw effect data
        device          (str)   middleman.get_device_object() object

    Returns
        True        Environment compatible.
        False       Incompatibility detected. Will be printed to stdout.
    """
    dbg.stdout("Checking environment...", dbg.action, 1)
    passed = True

    # Load effect dependency data
    form_factors = effect["depends"]["form_factor"]
    supported_os = effect["depends"]["OS"]
    py_dependencies = effect["depends"]["py_dependencies"]

    # Verify form factor
    form_factor = device["form_factor"]
    if form_factors != ["any"]:
        if not form_factor in form_factors:
            dbg.stdout("Effect only supported one these devices: " + ", ".join(form_factors), dbg.error)
            dbg.stdout("This device '{0}' is a '{1}'".format(device["name"], form_factor), dbg.warning)
            passed = False

    # Verify OS
    if supported_os != ["any"]:
        # TODO: OS detection unused
        # Stored as: ["linux", "windows", "osx"],
        # os.sys.platform() => linux, linux2, win32, cygwin, msys, darwin
        dbg.stdout("Skipping OS checking as unused.", dbg.warning)

    # Check Python dependencies are importable (without actually importing them)
    if len(py_dependencies) > 0:
        for module_name in py_dependencies:
            found = importlib.util.find_spec(module_name) is not None

            if not found:
                dbg.stdout("Python module cannot be imported: " + module_name, dbg.warning)
                passed = False

    # Check the checksum in the metadata matches that of the actual file.
    # This is a basic line of defense against external tampering.
    last_checksum = effect["checksum_md5"]
    current_checksum = _get_md5_checksum(effect["ui"]["filepath"].replace(".json", ".py"))

    if last_checksum != current_checksum:
        dbg.stdout("\nChecksum mismatch! Script was tampered externally.", dbg.warning)
        dbg.stdout("  As a precaution, this effect will not be run.", dbg.warning)
        dbg.stdout("  To fix this, open the script in the Controller, review the code and save.\n", dbg.warning)
        passed = False

    if passed:
        return True

    dbg.stdout("Failed to play scripted effect '{0}' due to one (or more) reasons:".format(effect["ui"]["name"]), dbg.error)
    dbg.stdout("- It is not designed to run with the requested device form factor.", dbg.error)
    dbg.stdout("- A required Python module is missing.", dbg.error)
    dbg.stdout("- It was externally modified.", dbg.error)
    return False


def compute_script_parameters(effect):
    """
    Validate the parameters for a scripted effect and return the parameters to use
    for this session.

    Params:
        effect      (dict)  Raw effect data

    Returns:
        (dict)      Parameter values for each key

    A parameter in the effect file consists of:

        "var": (str)            # Internal variable name
        "label": (str)          # Label to show in interface. i18n supported.
        "type": "colour"        # "colour", "list", "number" or "text"
        "value": null           # Currently set value.
        "default": (str)        # Default value.
        "options": (list)       # Options to show in the interface (list type only)

    """
    effect_params = effect["parameters"]
    computed_params = {}

    for param in effect_params:
        var = param["var"]
        ptype = param["type"]
        value = param["value"]
        default = param["default"]

        if not value:
            value = default

        # Valid data types
        if ptype == "colour":
            if len(value) not in [7, 4]: #RRGGBB or #RGB
                value = default

        elif ptype == "list":
            if value not in param["options"]:
                value = default

        elif ptype == "number":
            if type(value) != int:
                value = default

        elif ptype == "text":
            if type(value) != str:
                value = default

        else:
            dbg.stdout("Skipping unknown data type: " + ptype, dbg.warning)
            continue

        computed_params[var] = value

    return computed_params
