#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2020 Luke Horwell <code@horwell.me>
#
"""
Shared functions that are commonly used across Polychromatic's interfaces
and some backends.
"""

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
        print("Data directory cannot be located. Exiting.")
        exit(1)

    return path


def get_form_factor(form_factor_id):
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

    return {
        "id": form_factor_id,
        "icon": os.path.abspath(os.path.join(DATA_PATH, "ui/img/devices/" + form_factor_id + ".svg")),
        "label": locales.get(form_factor_id)
    }


def get_wave_direction(form_factor_id):
    """
    Returns a list of localised direction strings according to the device.
    """
    if form_factor_id == "mouse":
        return [locales.get("down"), locales.get("up")]

    elif form_factor_id == "mousemat":
        return [locales.get("clock"), locales.get("anticlock")]

    return [locales.get("left"), locales.get("right")]


def get_green_shades():
    """
    Returns a custom colours.json for use with non-RGB keyboards,
    like the Razer BlackWidow Ultimate.
    """
    colours = []
    count = 0
    for shade in ["#00FF00", "#00E100", "#00C800", "#00AF00", "#009600", "#007D00", "#006400", "#004B00", "#003200"]:
        count += 1
        colours.append({
            "name": "{0} {1}".format(locales.get("green"), str(count)),
            "hex": shade
        })
    return colours


def set_default_tray_icon(pref):
    """
    Determines which tray icon is best suited for the current desktop environment
    or theme.
    """
    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP")
    theme_env = os.environ.get("GTK_THEME")

    # Default icon
    icon_value = "ui/img/tray/light/polychromatic.svg"

    # TODO: Detect GTK dark theme.

    if desktop_env == "KDE":
        icon_value = "ui/img/tray/light/breeze.svg"

    # Unity/Ubuntu MATE
    elif theme_env.startswith("Ambiant") or theme_env.startswith("Ambiance"):
        icon_value = "ui/img/tray/light/humanity.svg"

    pref.set("tray", "icon", icon_value)


def get_tray_icon(dbg, pref):
    """
    Returns the full path to the icon to use with the tray applet.
    """
    icon_value = pref.get("tray", "icon")

    # Check if the icon is absolute - a custom icon
    if os.path.exists(icon_value):
        return icon_value

    # Check if the icon is relative - a built-in icon
    icon_builtin = os.path.join(get_data_dir_path(), icon_value)
    if os.path.exists(icon_builtin):
        return icon_builtin

    dbg.stdout("Tray icon missing: {0}\nUsing fallback icon.".format(icon_value), dbg.warning)
    return os.path.join(get_data_dir_path(), "ui/img/tray/light/polychromatic.svg")


def execute_polychromatic_component(dbg, component, tab=None):
    """
    Starts a Polychromatic application relative to its location or system-wide
    if installed.

    Params:
        component   e.g. "controller" would run "polychromatic-controller"
        tab         (Optional - Controller only) Opens a specific tab.
    """
    data_dir = get_data_dir_path()
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

        if tab:
            args.append("--tab")
            args.append(tab)

        if os.path.exists(bin_path):
            dbg.stdout("Executing: " + os.path.realpath(" ".join(args)), dbg.debug, 1)
            try:
                subprocess.Popen(args)
            except Exception:
                pass
            return True
    return False


def restart_tray_applet(dbg, current_bin_path): #TODO: restart_polychromatic_component
    """
    Restarts the tray applet if an instance is running in the background.
    Returns True/False depending on success.

    Params:
        dbg                 Debugging() object
        current_bin_path    Application's __file__
    """
    dbg.stdout("Restarting tray applet...", dbg.action, 1)

    try:
        pid = int(subprocess.check_output(["pidof", "polychromatic-tray-applet"]))
        os.kill(pid, 9)
    except Exception:
        dbg.stdout("Tray applet PID not found.", dbg.warning, 1)
        return False

    return execute_polychromatic_component(dbg, "tray-applet")


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
DATA_PATH = get_data_dir_path()
