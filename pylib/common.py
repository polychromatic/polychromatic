#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2021 Luke Horwell <code@horwell.me>
#
"""
Shared functions that are commonly used across Polychromatic's interfaces
and some backends.
"""

import colorama
import hashlib
import os
import sys
import subprocess
import grp
import time
import traceback
from threading import Thread

from . import locales

FORM_FACTORS = [
    "accessory",
    "keyboard",
    "mouse",
    "mousemat",
    "keypad",
    "headset",
    "gpu",
    "unrecognised"
]


class Paths(object):
    """
    Initialises the paths for data files, configuration and caches.
    """
    # Config/cache (XDG) directories
    try:
        config = os.path.join(os.environ["XDG_CONFIG_HOME"], ".config", "polychromatic")
    except KeyError:
        config = os.path.join(os.path.expanduser("~"), ".config", "polychromatic")

    try:
        cache = os.path.join(os.environ["XDG_CACHE_HOME"], ".cache", "polychromatic")
    except KeyError:
        cache = os.path.join(os.path.expanduser("~"), ".cache", "polychromatic")

    # Cached directories
    assets_cache = os.path.join(cache, "assets")
    effects_cache = os.path.join(cache, "effects")

    # Subdirectories
    effects = os.path.join(config, "effects")
    presets = os.path.join(config, "presets")
    custom_icons = os.path.join(config, "custom_icons")
    states = os.path.join(config, "states")

    # Files
    preferences = os.path.join(config, "preferences.json")
    colours = os.path.join(config, "colours.json")

    # Legacy (v0.3.12 and earlier)
    old_profiles = os.path.join(config, "profiles.json")
    old_profile_folder = os.path.join(config, "profiles")
    old_profile_backups = os.path.join(config, "backups")
    old_devicestate = os.path.join(config, "devicestate.json")

    # Create folders if they do not exist.
    for folder in [config, presets, custom_icons, states, effects,
                   cache, assets_cache, effects_cache]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Data directory
    # -- For developmen/opt, this is normally adjacent to the application executable.
    # -- For system-wide installs, this is generally /usr/share/polychromatic.
    module_path = __file__
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(module_path), "../data/"))):
        data_dir = os.path.abspath(os.path.join(os.path.dirname(module_path), "../data/"))
    elif os.path.exists("/usr/share/polychromatic/"):
        data_dir = "/usr/share/polychromatic/"
    else:
        print("Data directory cannot be located. Exiting.")
        exit(1)


class Debugging(object):
    """
    Outputs pretty debugging details to the terminal.
    """
    def __init__(self):
        self.verbose_level = 0
        colorama.init()

        # Colours for stdout
        self.error = colorama.Fore.LIGHTRED_EX
        self.success = colorama.Fore.LIGHTGREEN_EX
        self.warning = colorama.Fore.YELLOW
        self.action = colorama.Fore.LIGHTYELLOW_EX
        self.blue = colorama.Fore.BLUE
        self.magenta = colorama.Fore.MAGENTA
        self.debug = colorama.Fore.CYAN
        self.grey = colorama.Fore.LIGHTBLACK_EX
        self.normal = colorama.Fore.RESET

    def stdout(self, msg, colour_code=colorama.Fore.RESET, verbosity=0, overwritable=False):
        # msg           String containing message for stdout.
        # color         stdout code (e.g. '\033[92m')
        # verbosity     0 = Always shown
        #               1 = -v flag
        #               2 = -vv flag
        if overwritable:
            line_end = "\r"
        else:
            line_end = "\n"

        if self.verbose_level >= verbosity:
            # Only colourise output if running in a real terminal.
            if sys.stdout.isatty():
                print(colour_code + msg + '\033[0m', end=line_end)
            else:
                print(msg)


def get_exception_as_string(e):
    """
    For when things go wrong, convert an exception object into a human-readable
    output that is normally displayed via the GUI.
    """
    return traceback.format_exc().replace("'", '’').replace('"', '’')


def get_form_factor(_, form_factor_id):
    """
    Reads a string provided by a backend and returns data that is used to refer
    to the device ("form factor") throughout the application.

    Params:
        form_factor_id      (str)   One string from FORM_FACTORS.

    Returns:
        {id, icon, label}   A dictionary consisting of:
                                id          Form Factor ID
                                icon        Absolute path to icon
                                label       Human-readable name of form factor
    """
    if form_factor_id not in FORM_FACTORS:
        form_factor_id = "unrecognised"

    labels = {
        "accessory": _("USB Accessory"),
        "keyboard": _("Keyboard"),
        "mouse": _("Mouse"),
        "mousemat": _("Mousemat"),
        "keypad": _("Keypad"),
        "headset": _("Headset"),
        "gpu": _("External Graphics Enclosure"),
        "unrecognised": _("Unrecognised")
    }

    return {
        "id": form_factor_id,
        "icon": get_icon("devices", form_factor_id),
        "label": labels[form_factor_id]
    }


def get_green_shades(_):
    """
    Returns a custom colours.json for use with non-RGB keyboards,
    like the Razer BlackWidow Ultimate.
    """
    colours = []
    count = 0
    for shade in ["#00FF00", "#00E100", "#00C800", "#00AF00", "#009600", "#007D00", "#006400", "#004B00", "#003200"]:
        count += 1
        colours.append({
            "name": "{0} {1}".format(_("Green"), str(count)),
            "hex": shade
        })
    return colours


def get_default_tray_icon():
    """
    Determines which tray icon is best suited for the current desktop environment
    or theme.

    The path is intentionally relative as this is saved to preferences.json.
    A relative path will look up the icon in Polychromatic's data folders.
    """
    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP")
    theme_env = os.environ.get("GTK_THEME")

    # Default icon
    icon_value = "img/tray/light/polychromatic.svg"

    # TODO: Detect GTK dark theme.

    if desktop_env:
        if desktop_env == "KDE":
            icon_value = "img/tray/light/breeze.svg"

    elif theme_env:
        # Unity/Ubuntu MATE
        if theme_env.startswith("Ambiant") or theme_env.startswith("Ambiance"):
            icon_value = "img/tray/light/humanity.svg"

    return icon_value


def get_tray_icon(dbg, icon_value):
    """
    Returns the full path to the icon to use with the tray applet.

    Params:
        dbg             (obj)   Application's "dbg" object
        icon_value      (str)   Preference value of ["tray"]["icon"]
    """
    # Check if the icon is absolute -> a custom icon
    if os.path.exists(icon_value):
        return icon_value

    # Check if the icon is relative -> a built-in icon
    icon_builtin = os.path.join(paths.data_dir, icon_value)
    if os.path.exists(icon_builtin):
        return icon_builtin

    dbg.stdout("Tray icon missing: {0}\nUsing fallback icon.".format(icon_value), dbg.warning)
    return get_icon("tray/light", "polychromatic")


def get_icon(folder, name):
    """
    Returns the absolute path to a Polychromatic provided icon from the data
    folder.

    Example:
        ("general", "battery-75") returns "/usr/share/polychromatic/img/general/battery-75.svg"

    Returns:
        (str)       Absolute path to icon
        None        Icon does not exist
    """
    for ext in [".svg", ".png"]:
        icon_path = os.path.join(paths.data_dir, "img", folder, name + ext)
        if os.path.exists(icon_path):
            return icon_path
    return None


def generate_colour_bitmap(dbg, colour_hex, size="22x22"):
    """
    Generates a small bitmap of a colour and returns the path. Used for some UI controls
    that cannot use stylesheets.

    The file is cached to speed up future retrievals of the colour.
    """
    cache_name = hashlib.md5(str(colour_hex + size).encode("utf-8")).hexdigest()
    cache_path = os.path.join(paths.assets_cache, cache_name + ".png")

    if not os.path.exists(cache_path):
        dbg.stdout("Generating colour bitmap: " + colour_hex, dbg.action, 1)
        subprocess.call("convert -size {size} xc:{hex} {path}".format(hex=colour_hex, path=cache_path, size=size), shell=True)

    if not os.path.exists(cache_path):
        dbg.stdout("ERROR: Failed to generate bitmap: " + colour_hex, dbg.error)
        return None

    return cache_path


def get_icon_styles(dbg, folder, name, normal_colour, disabled_colour, active_colour, selected_colour, secondary_active, secondary_inactive):
    """
    Returns a list of icon paths to SVG assets for use with buttons and other
    Qt widgets in this order: ["normal", "disabled", "active", "selected"]. If
    the icon is missing, then None is returned.

    Paramaters are for get_icon() and the hex values to use. The secondary colour
    is used to recolour icons with a dual tone.

    The file is cached to speed up future retrievals of the asset.
    """
    original_icon = get_icon(folder, name)
    icons = []

    if not original_icon:
        return None

    for colour in [normal_colour, disabled_colour, active_colour, selected_colour]:
        cache_name = hashlib.md5(str(folder + name + colour).encode("utf-8")).hexdigest()
        cache_path = os.path.join(paths.assets_cache, cache_name + ".svg")

        if not os.path.exists(cache_path):
            dbg.stdout("Generating icon style: {0}/{1} ({2})".format(folder, name, colour), dbg.action, 1)
            with open(original_icon, "r") as f:
                data = f.readlines()
            newdata = []
            for line in data:
                secondary_colour = secondary_active if colour in [active_colour, selected_colour] else secondary_inactive
                newdata.append(line.replace("#00FF00", colour).replace("#00ff00", colour).replace("#008000", secondary_colour))
            with open(cache_path, "w") as f:
                f.writelines(newdata)

        icons.append(cache_path)

    return icons


def get_full_path_for_save_data_icon(icon_path):
    """
    Returns the full path to an icon specified in the save data for the UI to use.

    Polychromatic stores icon paths relatively. These paths are to be checked
    in this priority:
        - Custom Icons (~/.config/.../custom_icons/example.png)
        - Emblems/Tray (/usr/share/.../img/emblems/example.svg)

    If the icon no longer exists, a fallback will be provided.
    """
    possible_paths = [
        os.path.join(paths.custom_icons, icon_path),
        os.path.join(paths.data_dir, icon_path)
    ]

    if os.path.exists(icon_path):
        # Icon is already absolute!
        return icon_path

    # Try relative paths
    for path in possible_paths:
        if os.path.exists(path):
            return path

    return get_icon("devices", "unrecognised")


def execute_polychromatic_component(dbg, component, controller_open=None):
    """
    Starts a Polychromatic application relative to its location or system-wide
    if installed.

    Params:
        component           e.g. "controller" would run "polychromatic-controller"
        controller_open     (Optional - Controller only) Opens a specific tab/feature.
    """
    data_dir = paths.data_dir
    exec_name = "polychromatic-" + component

    possible_paths = [
        # Relative copy #1
        os.path.join(data_dir, "../" + exec_name),

        # Relative copy #2
        os.path.join(os.path.dirname(__file__), exec_name),

        # Relative system-wide (e.g. /usr/share/polychromatic)
        os.path.join(data_dir, "../../bin/" + exec_name),

        # Relative system-wide (e.g. /usr/share/polychromatic)
        os.path.join(os.path.dirname(__file__), "../" + exec_name),

        # Absolute system-wide
        "/usr/bin/" + exec_name
    ]

    for bin_path in possible_paths:
        args = [bin_path]

        if controller_open:
            args.append("--open")
            args.append(controller_open)

        if os.path.exists(bin_path):
            dbg.stdout("Executing: " + os.path.realpath(" ".join(args)), dbg.debug, 1)
            try:
                subprocess.Popen(args)
            except Exception:
                pass
            return True
    return False


def run_thread(target_function, args=()):
    """
    Executes a function that will run outside the main thread.

    target_function     Function to execute.
    args                (Optional) A tuple containing arguments.
    """
    thread = Thread(target=target_function, args=args)
    thread.daemon = True
    thread.start()
    return thread


def rgb_to_hex(rgb_list):
    """
    Converts [R,G,B] list to #RRGGBB string.
    Polychromatic stores and processes colours as hex values.
    """
    return "#{0:02X}{1:02X}{2:02X}".format(*rgb_list)


def hex_to_rgb(hex_string):
    """
    Converts "#RRGGBB" string to [R,G,B] list.
    Some backends/logic may expect colours to be individual RGB values.
    """
    hex_string = hex_string.lstrip("#")
    return list(int(hex_string[i:i+2], 16) for i in (0, 2 ,4))


def get_plural(integer, non_plural, plural):
    """
    Returns the correct plural or non-plural spelling based on an integer.
    """
    if integer == 1:
        return non_plural
    else:
        return plural


def get_bulk_apply_options(_, devices):
    """
    Return a dictionary describing a list of IDs for the interface to build
    buttons to quickly apply common options to all connected devices.

    The output is currently biased to OpenRazer IDs and should be
    reworked to work with other backends if they use different IDs. Currently,
    this will return options if at least one device supports them.

    Params:
        devices         (list)      List of get_device() dicts

    Returns:
    {
        "brightness", "effects": [
            {
                "option_id": "<id>"
                "option_data": <data>
                "required_colours": <int>
            }
        ]
    }
    """
    output = {"brightness": [], "effects": []}

    # Brightness
    for x in range(0, 125, 25):
        output["brightness"].append({
            "id": "brightness",
            "data": x,
            "label": "{0}%".format(str(x)),
            "icon": get_icon("options", str(x))
        })

    # Options
    effects = {
        "spectrum": False,
        "wave": False,
        "breath": False,
        "reactive": False,
        "static": False
    }

    effects_params = {
        "spectrum": None,
        "wave": 2,
        "breath": "single",
        "reactive": 2,
        "static": None
    }

    effects_colours = {
        "spectrum": 0,
        "wave": 0,
        "breath": 1,
        "reactive": 1,
        "static": 1
    }

    effects_labels = {
        "spectrum": _("Spectrum"),
        "wave": _("Wave"),
        "breath": _("Breath"),
        "reactive": _("Reactive"),
        "static": _("Static")
    }

    for option_id in effects.keys():
        for device in devices:
            for zone in device["zone_options"].keys():
                for option in device["zone_options"][zone]:
                    if option["id"] == option_id:
                        effects[option_id] = True

    for effect in effects.keys():
        output["effects"].append({
            "id": effect,
            "data": effects_params[effect],
            "label": effects_labels[effect],
            "required_colours": effects_colours[effect]
        })

    return output


def get_versions(base_version):
    """
    When running from a Git repository, return the development revision and
    Git commit "revision" as a tuple. Otherwise just the release version.

    This is intended to make debugging easier.
    """
    py_version = "{0}.{1}.{2}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)

    if os.path.exists(os.path.join(os.path.dirname(__file__), "..", ".git")):
        import subprocess
        os.chdir(os.path.dirname(__file__))
        git_version = subprocess.check_output(["git", "describe"]).strip().decode("UTF-8")[1:]
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("UTF-8")
        return (git_version, git_commit, py_version)

    # Production "installed" version
    return (base_version, None, py_version)


# Available to all modules
paths = Paths()
