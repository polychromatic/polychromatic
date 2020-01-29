#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2020 Luke Horwell <code@horwell.me>
#
"""
Shared functions that are commonly used across Polychromatic's interfaces.
"""

import os
import sys
import gettext
import subprocess
import grp
import time
import traceback
from threading import Thread

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class Debugging(object):
    """
    Outputs pretty debugging details to the terminal.
    """
    def __init__(self):
        self.verbose_level = 0

        # Colours for stdout
        self.error = '\033[91m'
        self.success = '\033[92m'
        self.warning = '\033[93m'
        self.action = '\033[93m'
        self.debug = '\033[96m'
        self.normal = '\033[0m'

    def stdout(self, msg, colour_code='\033[0m', verbosity=0, overwritable=False):
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


def get_data_dir_path():
    """
    Returns the path for the data directory.

    For development, this is normally adjacent to the application executable.
    For system-wide installs, this is generally /usr/share/polychromatic.
    """
    module_path = __file__

    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(module_path), "../data/"))):
        path = os.path.abspath(os.path.join(os.path.dirname(module_path), "../data/"))
    elif os.path.exists("/usr/share/polychromatic/"):
        path = "/usr/share/polychromatic/"
    else:
        dbg.stdout("Data directory cannot be located. Exiting.", dbg.error)
        exit(1)

    return path


def setup_translations(bin_path, i18n_app, locale_override=None):
    """
    Initalises translations for the application.

    bin_path = __file__ of the application that is being executed.
    i18n_app = Name of the application's locales.

    Returns a gettext object used for performing translations.
    """
    whereami = os.path.abspath(os.path.join(os.path.dirname(bin_path)))

    if os.path.exists(os.path.join(whereami, 'locale/')):
        # Using relative path
        locale_path = os.path.join(whereami, 'locale/')
    else:
        # Using system path or en_US if none found
        locale_path = '/usr/share/locale/'

    if locale_override:
        t = gettext.translation(i18n_app, localedir=locale_path, fallback=True, languages=[locale_override])
    else:
        t = gettext.translation(i18n_app, localedir=locale_path, fallback=True)

    # This is set as the app's global variable: _
    return t.gettext


def get_form_factor(device_type):
    """
    Reads a string provided by a backend and returns data that is used to refer
    to the device ("form factor") throughout the application.

    Params:
        device_type         String from a backend (e.g. OpenRazer)

    Returns:
        {id, icon, label}   A dictionary consisting of:
                                id          The resulting 'form factor'
                                icon        Absolute path to form factor icon
                                label       Human-readable name of form factor
    """
    type_to_form_factor = {
        # Razer
        "firefly": "mousemat",
        "tartarus": "keypad",
        "core": "gpu",
        "mug": "accessory",

        # Generic
        "keyboard": "keyboard",
        "mouse": "mouse",
        "mousemat": "mousemat",
        "keypad": "keypad",
        "headset": "headset",
        "unrecognised": "unrecognised",
    }

    form_factor_labels = {
        "accessory": _("USB Accessory"),
        "keyboard": _("Keyboard"),
        "mouse": _("Mouse"),
        "mousemat": _("Mousemat"),
        "keypad": _("Keypad"),
        "headset": _("Headset"),
        "gpu": _("External Graphics Enclosure"),
        "unrecognised": _("Unrecognised")
    }

    try:
        form_factor = type_to_form_factor[device_type]
    except KeyError:
        form_factor = "accessory"

    return {
        "id": form_factor,
        "icon": os.path.abspath(os.path.join(DATA_PATH, "ui/img/devices/" + form_factor + ".svg")),
        "label": form_factor_labels[form_factor]
    }


def get_zone_metadata(zones, device_name):
    """
    Returns human readable strings and icons for a device's lighting areas.

    For example, "logo" could refer to the hex ring on a Razer Hex.
    """
    zone_names = {}
    zone_icons = {}

    zones_to_string = {
        "main": _("Main"),
        "logo": _("Logo"),
        "scroll": _("Scroll Wheel"),
        "backlight": _("Backlight"),
        "left": _("Left"),
        "right": _("Right")
    }

    for zone in zones:
        try:
            name = zones_to_string[zone]
            icon = zone
        except KeyError:
            dbg.stdout("Unimplemented zone name '{0}' (used by device '{1}')".format(zone, device_name), dbg.warning)
            name = zone
            icon = "unknown"

        if zone == "logo" and device_name == "Razer Nex":
            name = _("Hex Ring")
            icon = "naga-hex-ring"

        if zone == "logo" and device_name.startswith("Razer Blade"):
            name = _("Laptop Lid")
            icon = "blade-logo"

        icon_path = os.path.abspath(os.path.join(DATA_PATH, "ui/img/zones/" + icon + ".svg"))

        if not os.path.exists(icon_path):
            icon_path = os.path.abspath(os.path.join(DATA_PATH, "ui/img/devices/unrecognised.svg"))

        zone_names[zone] = name
        zone_icons[zone] = icon_path

    return {
        "names": zone_names,
        "icons": zone_icons
    }


def get_wave_direction(form_factor_id):
    """
    Returns a list of localised direction strings according to the device.
    """
    if form_factor_id == "mouse":
        left = _("Down")
        right = _("Up")
    elif form_factor_id == "mousemat":
        left = _("Clockwise")
        right = _("Anti-clockwise")
    else:
        left = _("Left")
        right = _("Right")

    return [left, right]


def get_green_shades():
    """
    Returns a custom colours.json for use with non-RGB keyboards,
    like the Razer BlackWidow Ultimate.
    """
    return [
        {"name": _("Green") + " 1", "hex": "#00FF00"},
        {"name": _("Green") + " 2", "hex": "#00E100"},
        {"name": _("Green") + " 3", "hex": "#00C800"},
        {"name": _("Green") + " 4", "hex": "#00AF00"},
        {"name": _("Green") + " 5", "hex": "#009600"},
        {"name": _("Green") + " 6", "hex": "#007D00"},
        {"name": _("Green") + " 7", "hex": "#006400"},
        {"name": _("Green") + " 8", "hex": "#004B00"},
        {"name": _("Green") + " 9", "hex": "#003200"}
    ]


def set_default_tray_icon(pref):
    """
    Determines which tray icon is best suited for the current desktop environment.
    """
    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP")
    pref.set("tray_icon", "type", "builtin")

    if desktop_env == "KDE":
        pref.set("tray_icon", "value", "0")
    else:
        # MATE/Unity/Others
        pref.set("tray_icon", "value", "0")


def get_tray_icon(dbg, pref):
    """
    Returns the full path to the icon to use with the tray applet.
    """

    # If it's the first time loading, set default icon to desktop environment.
    if not pref.exists("tray_icon", "type"):
        set_default_tray_icon(pref)

    icon_type = pref.get("tray_icon", "type", "builtin")
    icon_fallback = os.path.join(DATA_PATH, "tray", "humanity-light.svg")

    try:
        if icon_type == "builtin":
            icon_id = pref.get("tray_icon", "icon_id")
            icon_index = pref.load_file(os.path.join(DATA_PATH, "tray/icons.json"))
            return os.path.join(DATA_PATH, "tray", icon_index[icon_id]["path"])

        elif icon_type == "custom":
            icon_path = pref.get("tray_icon", "custom_image_path")
            if os.path.exists(icon_path):
                return icon_path
            else:
                dbg.stdout("Icon missing: " + icon_path, dbg.error)
                dbg.stdout("Using fallback!", dbg.error)
                return icon_path

        elif icon_type == "gtk":
            icon_gtk = pref.get("tray_icon", "gtk_icon_name")
            return get_path_from_gtk_icon_name(icon_gtk)

        else:
            return icon_fallback

    except Exception:
        dbg.stdout("Error whlie loading icon, using fallback.", dbg.error)
        return icon_fallback


def execute_polychromatic_component(dbg, suffix, current_bin_path, data_source, jump_to):
    """
    Starts a Polychromatic application relative to its location or system-wide
    if installed.

    Params:
        suffix              e.g. "controller" would run "polychromatic-controller"
        current_bin_path    Application's __file__
        data_source         Data directory, e.g. /usr/share/polychromatic
        jump_to             (Optional - Controller only) Opens a specific tab.
    """
    possible_paths = [
        os.path.join(data_source, "../polychromatic-" + suffix),
        os.path.join(os.path.dirname(current_bin_path), "polychromatic-" + suffix),
        "/usr/bin/polychromatic-" + suffix
    ]

    for bin_path in possible_paths:
        if os.path.exists(bin_path):
            dbg.stdout("Executing: " + os.path.realpath(bin_path), dbg.debug, 1)
            try:
                subprocess.Popen(bin_path) # Add jump_to here
            except Exception:
                pass
            return True
    return False


def restart_tray_applet(dbg, current_bin_path, data_source):
    """
    Restarts the tray applet if an instance is running in the background.
    Returns True/False depending on success.

    Params:
        dbg                 Debugging() object
        current_bin_path    Application's __file__
        data_source         Data directory, e.g. /usr/share/polychromatic
    """
    dbg.stdout("Restarting tray applet...", dbg.action, 1)

    try:
        pid = int(subprocess.check_output(["pidof", "polychromatic-tray-applet"]))
        os.kill(pid, 9)
    except Exception:
        dbg.stdout("Tray applet PID not found.", dbg.warning, 1)
        return False

    result = execute_polychromatic_component(dbg, "tray-applet", current_bin_path, data_source)
    return result


def restart_openrazer_daemon(dbg, devman):
    """
    Restarts the OpenRazer daemon.
    Returns True/False depending on success.
    """
    dbg.stdout("Restarting OpenRazer daemon...", dbg.action, 1)

    # Try gracefully via OpenRazer Python library.
    try:
        dbg.stdout("-- Stopping via DeviceManager...", dbg.action, 1)
        devman.stop_daemon()
        dbg.stdout("-- OK!", dbg.success, 1)
    except Exception as e:
        dbg.stdout("-- Error!", dbg.error, 1)

    # Check process is still running
    try:
        daemon_pid = int(subprocess.check_output(["pidof", "openrazer-daemon"]))
        still_running = True
    except subprocess.CalledProcessError:
        # Returns 1 if
        still_running = False

    # Kill the daemon if still not ended
    if still_running:
        dbg.stdout("-- Killing process PID {0}...".format(str(daemon_pid)), dbg.action, 1)
        os.kill(daemon_pid, 9)

    # Ensure a clean log
    dbg.stdout("-- Archiving razer.log...", dbg.action, 1)
    log_path = os.path.join(os.path.expanduser("~"), ".local/share/openrazer/razer.log")
    log_bak = os.path.join(os.path.expanduser("~"), ".local/share/openrazer/razer.log.bak")
    if os.path.exists(log_path):
        os.rename(log_path, log_bak)

    # Wait for daemon to start again
    dbg.stdout("-- Starting openrazer-daemon...", dbg.action, 1)
    subprocess.Popen("openrazer-daemon", shell=True)

    # Running application must restart.
    os.execv(__file__, sys.argv)


def get_path_from_gtk_icon_name(icon_name):
    """
    Returns an image path determined by a GTK icon name, if there is one.
    """
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
    Polychromatic stores and presents colours as hex values.
    """
    return "#{0:02X}{1:02X}{2:02X}".format(*rgb_list)


def hex_to_rgb(hex_string):
    """
    Converts "#RRGGBB" string to [R,G,B] list.
    The daemon expects parameters with individual RGB values.
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


# Module Initalization
_ = setup_translations(__file__, "polychromatic")
DATA_PATH = get_data_dir_path()
PID_FILE_TRAY = os.path.join("/run/user/", str(os.getuid()), "polychromatic-tray-applet.pid")

