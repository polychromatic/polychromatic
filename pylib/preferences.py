#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2015-2020 Luke Horwell <code@horwell.me>
#
"""
This module is responsible for loading/saving persistent data used by Polychromatic's frontends.
"""

import os
import json
import shutil
from . import common
from . import locales

# Also set in effects.py
VERSION = 7

dbg = common.Debugging()


class Paths(object):
    # Config/cache (XDG) directories
    try:
        root = os.path.join(os.environ["XDG_CONFIG_HOME"], ".config", "polychromatic")
    except KeyError:
        root = os.path.join(os.path.expanduser("~"), ".config", "polychromatic")

    try:
        cache = os.path.join(os.environ["XDG_CACHE_HOME"], ".cache", "polychromatic")
    except KeyError:
        cache = os.path.join(os.path.expanduser("~"), ".cache", "polychromatic")

    # Subdirectories
    effects = os.path.join(root, "effects")
    effects_keyframed = os.path.join(effects, "keyframed")
    effects_scripted = os.path.join(effects, "scripted")
    effects_cache = os.path.join(cache, "effects")
    presets = os.path.join(root, "presets")
    custom_icons = os.path.join(root, "custom_icons")

    # Files
    preferences = os.path.join(root, "preferences.json")
    colours = os.path.join(root, "colours.json")

    # Legacy (v0.3.12 and earlier)
    old_profiles = os.path.join(root, "profiles.json")
    old_profile_folder = os.path.join(root, "profiles")
    old_profile_backups = os.path.join(root, "backups")
    old_devicestate = os.path.join(root, "devicestate.json")


def load_file(filepath):
    """
    Loads a JSON file from disk. If empty, it will be created.

    Params:
        filepath            String from the Path() object.

    Returns:
        {}                  Data (dictionary object)
    """
    if not os.path.exists(filepath):
        init_config(filepath)
        data = {}

    try:
        with open(filepath) as stream:
            data = json.load(stream)
    except Exception as e:
        dbg.stdout(filepath + ": Read error!", dbg.error)
        dbg.stdout("Exception:\n" + common.get_exception_as_string(e), dbg.error)
        init_config(filepath)
        data = {}

    # Check preferences contain valid data and defaults.
    def _validate(group, item, data_type, default_value):
        try:
            data[group]
        except KeyError:
            data[group] = {}

        try:
            data[group][item]
        except KeyError:
            data[group][item] = default_value
            save_file(path.preferences, data)

        if type(data[group][item]) != data_type:
            data[group][item] = default_value
            save_file(path.preferences, data)

    if filepath == path.preferences:
        _validate("colours", "primary", str, "#00FF00")
        _validate("colours", "secondary", str, "#FF0000")
        _validate("effects", "live_preview", bool, True)
        _validate("controller", "landing_tab", int, 0)
        _validate("controller", "show_menu_bar", bool, True)
        _validate("controller", "system_qt_theme", bool, False)
        _validate("tray", "mode", int, 0)
        _validate("tray", "icon", str, "ui/img/tray/light/polychromatic.svg")

    return(data)


def save_file(filepath, newdata):
    """
    Commit data to the disk.

    Params:
        filepath            String from the Path() object.
        newdata             Data (dictionary object)

    Returns:
        True                Save successful.
        False               Save failed.
    """
    # The preferences file always stores the configuration version.
    if filepath == path.preferences:
        newdata["config_version"] = VERSION

    if not os.path.exists(filepath):
        open(filepath, "w").close()

    if os.access(filepath, os.W_OK):
        f = open(filepath, "w+")
        f.write(json.dumps(newdata, sort_keys=True, indent=4))
        f.close()
        return True
    else:
        return False


def init_config(filepath):
    """
    Prepares a configuration file for the first time.
    """
    try:
        # Backup if the JSON was invalid.
        if os.path.exists(filepath):
            dbg.stdout(filepath + ": JSON corrupt or unreadable. It will backed up then recreated.", dbg.error)
            os.rename(filepath, filepath + ".bak")

        # Touch new file
        save_file(filepath, {})
        dbg.stdout(filepath + ": New configuration written.", dbg.success)

    except Exception as e:
        # Couldn't create the default configuration.
        dbg.stdout(filepath + ": Init write error!", dbg.error)
        dbg.stdout("Exception: ", str(e), dbg.error)


def upgrade_old_pref():
    """
    Checks and updates the configuration from previous revisions.
    """
    try:
        with open(path.preferences, "r") as f:
            data = json.load(f)
        config_version = int(data["config_version"])
    except Exception:
        # Never mind, the parent function should fix this later.
        return

    # Is the configuration version already up-to-date?
    if VERSION == config_version:
        return

    # Is the config newer then the software? Wicked time travelling!
    if config_version > VERSION:
        dbg.stdout("\nWARNING: Your preferences file is newer then the application!", dbg.error)
        dbg.stdout("It's likely you're running an older version. This is unsupported.", dbg.error)
        dbg.stdout("     Current Config Version:   v." + str(config_version), dbg.error)
        dbg.stdout("     Installed Config Version: v." + str(VERSION), dbg.error)
        dbg.stdout("")
        return

    dbg.stdout("Upgrading configuration from v{0} to v{1}...".format(config_version, VERSION), dbg.action)

    # v0.3.12
    if config_version < 5:
        # Ensure preferences.json is clean.
        data = load_file(path.preferences)
        for key in ["activate_on_save", "live_switch", "live_preview"]:
            try:
                value = data["editor"][key]
                if type(value) == str:
                    if value in ['true', 'True']:
                        data["editor"][key] = True
                    else:
                        data["editor"][key] = False
            except Exception:
                pass

        save_file(path.preferences, data)

    # v0.4.0 (dev)
    if config_version == 6:
        # The configuration will be reset.
        dbg.stdout("Development configuration detected. Preferences have been reset.", dbg.warning)
        for filepath in [path.preferences, path.colours, path.old_devicestate]:
            if os.path.exists(filepath):
                os.remove(filepath)
        return

    # v0.5.0 (dev)
    if config_version < 7:
        # Migrate preferences.json to new keys
        old_data = load_file(path.preferences)

        # -- Tray icon is now one key (a relative or absolute path)
        new_tray_value = ""

        def get_path_from_gtk_icon_name(icon_name):
            """
            Returns an image path determined by a GTK icon name, if there is one.

            This is a legacy feature as the tray icon is a relative/absolute path,
            but remains so users upgrading from v0.3.12.
            """
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk

            theme = Gtk.IconTheme.get_default()
            info = theme.lookup_icon(icon_name, 22, 0)
            try:
                filename = info.get_filename()
            except Exception:
                filename= None

            if filename:
                return filename
            else:
                return ""

        try:
            old_type = old_data["tray_icon"]["type"]
            if old_type == "gtk":
                new_tray_value = get_path_from_gtk_icon_name(old_data["tray_icon"]["value"])
            elif old_type == "custom":
                new_tray_value = old_data["tray_icon"]["value"]
            elif old_type == "builtin":
                try:
                    mapping = {
                        "0": "ui/img/tray/light/humanity.svg",
                        "1": "ui/img/tray/dark/humanity.svg",
                        "2": "ui/img/tray/animated/chroma.gif",
                        "3": "ui/img/tray/light/breeze.svg",
                        "4": "ui/img/tray/dark/breeze.svg"
                    }
                    new_tray_value = mapping[old_data["tray_icon"]["value"]]
                except KeyError:
                    # Invalid data, discard.
                    pass
        except KeyError:
            # Invalid data, discard.
            pass

        try:
            old_live_preview = old_data["editor"]["live_preview"]
        except KeyError:
            old_live_preview = False

        new_data = {
            "colours": {
                "primary": "#00FF00",               # New
                "secondary": "#00FFFF"              # New
            },
            "effects": {
                "live_preview": old_live_preview    # Changed
            },
            "tray": {
                "icon": new_tray_value              # Changed
            }
        }

        os.remove(path.preferences)
        save_file(path.preferences, new_data)

        # devicestate.json now obsolete
        if os.path.exists(path.old_devicestate):
            os.remove(path.old_devicestate)

        # If the colours were unchanged from v0.3.12, reset to new ones.
        old_colours = load_file(path.colours)
        old_colour_json = {
            "1": {"name": "White", "col": [255, 255, 255]},
            "2": {"name": "Red", "col": [255, 0, 0]},
            "3": {"name": "Orange", "col": [255, 165, 0]},
            "4": {"name": "Yellow", "col": [255, 255, 0]},
            "5": {"name": "Signature Green", "col": [0, 255, 0]},
            "6": {"name": "Aqua", "col": [0, 255, 255]},
            "7": {"name": "Blue", "col": [0, 0, 255]},
            "8": {"name": "Purple", "col": [128, 0, 128]},
            "9": {"name": "Pink", "col": [255, 0, 255]}
        }

        if old_colours == old_colour_json:
            os.remove(path.colours)
        else:
            # Migrate colours from RGB lists to hex strings.
            new_colours = []
            if type(old_colours) != list:
                old_ids = list(old_colours.keys())
                old_ids.sort()
                for uuid in old_ids:
                    new_name = old_colours[uuid]["name"]
                    new_hex = common.rgb_to_hex(old_colours[uuid]["col"])
                    new_colours.append({"name": new_name, "hex": new_hex})

                save_file(path.colours, new_colours)



    # Write new version number.
    data = load_file(path.preferences)
    data["config_version"] = VERSION
    save_file(path.preferences, data)

    dbg.stdout("Configuration successfully upgraded.", dbg.success)


def get_custom_icons():
    """
    Returns a list of all the icons currently stored in the user's "custom icons"
    folder. This is used by the icon picker. Save data will reference images
    by a relative file name.
    """
    return os.listdir(path.custom_icons)


def start_initalization():
    """
    Prepares the preferences module.
    """
    # Create folders if they do not exist.
    for folder in [path.root, path.effects, path.effects_keyframed, path.effects_scripted, path.effects_cache, path.presets, path.cache, path.custom_icons]:
        if not os.path.exists(folder):
            dbg.stdout("Configuration folder does not exist. Creating: " + folder, dbg.action)
            os.makedirs(folder)

    # Create preferences if non-existent.
    for json_path in [path.preferences]:
        if not os.path.exists(json_path):
            init_config(json_path)

    # Check the configuration and software version matches.
    upgrade_old_pref()

    # Validate preferences with defaults if non-existant.
    data = load_file(path.preferences)

    # Generate colours with defaults if non-existant.
    data = load_file(path.colours)
    if len(data) <= 2:
        default_data = [
            {"name": locales.get("white"), "hex": "#FFFFFF"},
            {"name": locales.get("red"), "hex": "#FF0000"},
            {"name": locales.get("green"), "hex": "#00FF00"},
            {"name": locales.get("blue"), "hex": "#0000FF"},
            {"name": locales.get("aqua"), "hex": "#00FFFF"},
            {"name": locales.get("orange"), "hex": "#FFA500"},
            {"name": locales.get("pink"), "hex": "#FF00FF"},
            {"name": locales.get("purple"), "hex": "#8000FF"},
            {"name": locales.get("yellow"), "hex": "#FFFF00"},
            {"name": locales.get("grey-light"), "hex": "#C0C0C0"},
            {"name": locales.get("grey-dark"), "hex": "#7F7F7F"},
            {"name": locales.get("black"), "hex": "#000000"}
        ]
        save_file(path.colours, default_data)


# Module Initalization
path = Paths()
start_initalization()
