#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2015-2021 Luke Horwell <code@horwell.me>
#
"""
This module is responsible for loading/saving persistent data used by Polychromatic's frontends.
"""

import os
import json
import shutil
from . import common
from . import locales

VERSION = 7

dbg = common.Debugging()
path = common.paths

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
        _validate("editor", "live_preview", bool, True)
        _validate("editor", "system_cursors", bool, False)
        _validate("editor", "suppress_confirm_dialog", bool, False)
        _validate("controller", "landing_tab", int, 0)
        _validate("controller", "show_menu_bar", bool, True)
        _validate("controller", "system_qt_theme", bool, False)
        _validate("controller", "window_behaviour", int, 0)
        _validate("tray", "autostart", bool, True)
        _validate("tray", "mode", int, 0)
        _validate("tray", "icon", str, common.get_default_tray_icon())
        _validate("tray", "autostart_delay", int, 0)

        for prefix in ["main", "editor"]:
            _validate("geometry", prefix + "_window_pos_x", int, 0)
            _validate("geometry", prefix + "_window_pos_y", int, 0)
            _validate("geometry", prefix + "_window_size_x", int, 1000)
            _validate("geometry", prefix + "_window_size_y", int, 600)

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
        with open(filepath, "w+") as f:
            f.write(json.dumps(newdata, sort_keys=True, indent=4))
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
        dbg.stdout(filepath + ": New configuration written.", dbg.success, 1)

    except Exception as e:
        # Couldn't create the default configuration.
        dbg.stdout(filepath + ": Init write error!", dbg.error)
        dbg.stdout("Exception: " + str(e), dbg.error)


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

    # Always clear cache when configuration is updated
    if os.path.exists(path.cache):
        shutil.rmtree(path.cache)
        os.makedirs(path.cache)
        dbg.stdout("Cache cleared.", dbg.success, 1)

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
        dbg.stdout("Unsupported v0.4.0 configuration detected. Preferences reset.", dbg.warning)
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
                        "0": "img/tray/light/humanity.svg",
                        "1": "img/tray/dark/humanity.svg",
                        "2": "img/tray/animated/chroma.gif",
                        "3": "img/tray/light/breeze.svg",
                        "4": "img/tray/dark/breeze.svg"
                    }
                    new_tray_value = mapping[old_data["tray_icon"]["value"]]
                except KeyError:
                    # Invalid data, discard.
                    pass
        except ImportError:
            dbg.stdout("GTK not installed. Tray icon cannot be migrated.", dbg.error)
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
            "editor": {
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


def init(_):
    """
    Prepares the preferences module.
    """
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
            {"name": _("White"), "hex": "#FFFFFF"},
            {"name": _("Red"), "hex": "#FF0000"},
            {"name": _("Green"), "hex": "#00FF00"},
            {"name": _("Blue"), "hex": "#0000FF"},
            {"name": _("Aqua"), "hex": "#00FFFF"},
            {"name": _("Orange"), "hex": "#FFA500"},
            {"name": _("Pink"), "hex": "#FF00FF"},
            {"name": _("Purple"), "hex": "#8000FF"},
            {"name": _("Yellow"), "hex": "#FFFF00"},
            {"name": _("Light Grey"), "hex": "#C0C0C0"},
            {"name": _("Dark Grey"), "hex": "#7F7F7F"},
            {"name": _("Black"), "hex": "#000000"}
        ]
        save_file(path.colours, default_data)
