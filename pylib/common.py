#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2019 Luke Horwell <code@horwell.me>
#
"""
This module contains shared functions that are used across Polychromatic's interfaces.
"""

import os
import sys
import gettext
import subprocess
import grp
import time
from threading import Thread

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# PID file used to restart tray applet
tray_pid_file = os.path.join("/run/user/", str(os.getuid()), "polychromatic-tray-applet.pid")


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


def parse_html(html):
    """
    Returns a string that is HTML safe for jQuery to use.
    """
    return html.strip().replace('\n', '')


def setup_translations(bin_path, i18n_app, locale_override=None):
    """
    Initalises translations for the application.

    bin_path = __file__ of the application that is being executed.
    i18n_app = Name of the application's locales.

    Returns
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


def get_all_device_types():
    """
    Returns a list of all the known device types in Polychromatic.
    We refer to these as "form factors".
    """
    return [
        "keyboard",
        "mouse",
        "mousemat",
        "keypad",
        "mug",
        "headset",
        "core",
        "mug"
    ]


def get_device_type_pretty(device_type):
    """
    Returns a human-readable, translatable string for a device type.
    """
    strings = {
        "keyboard": _("Keyboard"),
        "mouse": _("Mouse"),
        "mousemat": _("Mousemat"),
        "keypad": _("Keypad"),
        "mug": _("Mug"),
        "headset": _("Headset"),
        "core": _("External Graphics Enclosure"),
        "mug": _("Mug Holder")
    }

    try:
        return strings[device_type]
    except KeyError:
        return device_type



def get_device_type(device_obj):
    """
    Convert the daemon's device type string to what Polychromatic identifies as "form factor".
    This is used for determining icons and filtering a list of device objects.
    """
    form_factor = device_obj.type

    if form_factor == "firefly":
        form_factor = "mousemat"
    elif form_factor == "tartarus":
        form_factor = "keypad"

    return(form_factor)


def get_device_list_by_type(device_obj_list, filtered_type):
    """
    Returns a list of device objects filtered to the desired form factor of device.
    """
    filtered_list = []
    for device_obj in device_obj_list:
        formfactor = get_device_type(device_obj)
        if formfactor == filtered_type:
            filtered_list.append(device_obj)
    return filtered_list


def get_device_list_by_serial(device_obj_list, expected_serial):
    """
    Returns the device object based on serial number.
    """
    for device_obj in device_obj_list:
        if device_obj.serial == expected_serial:
            return device_obj
    return None


def get_device_image(device, data_source, relative_path=False):
    """
    Gets a Polychromatic image of the current device.
    """
    return get_device_image_by_type(device.type, data_source, relative_path)


def get_device_image_by_type(device_type, data_source, relative_path=False):
    """
    Gets a Polychromatic image that represents a device's form factor.
    """
    image_path = "ui/img/devices/{0}.svg".format(device_type)

    if not os.path.exists(os.path.join(data_source, image_path)):
        image_path = "ui/img/devices/unknown.svg"

    if relative_path:
        return image_path
    else:
        return os.path.join(data_source, image_path)


def get_real_device_image(device):
    """
    Returns the device image provided via the daemon if available.
    """
    # TODO: In future, this variable will just be DEVICE_IMAGE
    try:
        return device.razer_urls["top_img"]
    except KeyError:
        return get_device_image(device)


def get_supported_lighting_sources(device_obj):
    """
    Returns a list of supported lighting sources (may also be referred to as "targets")
    """
    supported_sources = []

    if device_obj.has("lighting"):
        supported_sources.append("main")

    if device_obj.has("lighting_backlight"):
        supported_sources.append("backlight")

    if device_obj.has("lighting_logo"):
        supported_sources.append("logo")

    if device_obj.has("lighting_scroll"):
        supported_sources.append("scroll")

    return supported_sources


def has_multiple_sources(device):
    """
    Returns True or False to determine whether a device has multiple light sources.
    """
    source_list = get_supported_lighting_sources(device)
    if len(source_list) > 1:
        return True
    else:
        return False


def get_source_name(source, device):
    """
    Returns a human readable string for a device's lighting source.

    E.g. "logo" on a Razer Hex refers to the hex ring.
    """
    if source == "logo" and device.name == "Razer Nex":
        return _("Hex Ring")

    source_names = {
        "main": _("Main"),
        "logo": _("Logo"),
        "scroll": _("Scroll Wheel"),
        "backlight": _("Backlight")
    }

    try:
        return source_names[source]
    except NameError:
        return source


def get_effect_state_string(string):
    """
    Function to retrieve the current device effect as a human-readable string.
    """
    if string == 'spectrum':
        return _("Spectrum")
    elif string == 'wave':
        return _("Wave")
    elif string == 'reactive':
        return _("Reactive")
    elif string == 'breath':
        return _("Breath")
    elif string == 'ripple':
        return _("Ripple")
    elif string == 'starlight':
        return _("Starlight")
    elif string == 'static':
        return ("Static")
    elif string == 'none':
        return ("None")
    elif string == 'profile':
        return _("Profile")
    elif string == 'blinking':
        return _("Blinking")
    elif string == 'pulsate':
        return _("Pulsate")
    elif string == 'unknown':
        return _("Try one...")
    else:
        return string


def set_lighting_effect(pref, device_object, source, effect, fx_params=None, primary_colours=None, secondary_colours=None):
    """
    Function to set a effect for a specific area of the device.

    device_object = Device to apply effect to.
    source =        Lighting source labelled by Polychromatic.
                        e.g. main / scroll / wheel
    effect =        Effect name identified by Polychromatic.
                        e.g. wave / spectrum / static
    params =        (Optional) Any parameters for the effect, seperated by '?'.
                        e.g. 255?255?255?2
    primary_colours   = (Optional) Use specified HEX instead of default primary colour.
    secondary_colours = (Optional) As above, but secondary colours.
    """
    serial = device_object.serial

    # For remembering current device state
    def remember_params(params):
        pref.set_device_state(serial, source, "effect_params", params)

    if fx_params:
        params = str(fx_params).split('?')
        remember_params(fx_params)
    else:
        params = None

    # Determine source function
    if source == "main":
        fx = device_object.fx

    elif source == "backlight":
        fx = device_object.fx.misc.backlight

    elif source == "logo":
        fx = device_object.fx.misc.logo

    elif source == "scroll":
        fx = device_object.fx.misc.scroll_wheel

    # Determine colours, if unspecified, use previously set colours.
    if not primary_colours:
        primary_colours = pref.get_device_state(serial, source, "colour_primary")

    if not secondary_colours:
        secondary_colours = pref.get_device_state(serial, source, "colour_secondary")

    # Convert colours to R,G,B to pass to the daemon.
    # If device hasn't previously specified colours, use default colours.
    if primary_colours:
        if type(primary_colours) == str:
            rgb = hex_to_rgb(primary_colours)
        elif type(primary_colours) == list:
            rgb = primary_colours
    else:
        rgb = hex_to_rgb(pref.get("colours", "primary", "#00FF00"))

    primary_red = rgb[0]
    primary_green = rgb[1]
    primary_blue = rgb[2]

    if secondary_colours:
        if type(secondary_colours) == str:
            rgb = hex_to_rgb(secondary_colours)
        elif type(secondary_colours) == list:
            rgb = secondary_colours
    else:
        rgb = hex_to_rgb(pref.get("colours", "primary", "#00FFFF"))

    secondary_red = rgb[0]
    secondary_green = rgb[1]
    secondary_blue = rgb[2]

    # Execute function (only if source is known)
    success = False
    params_to_set = None

    if fx:
        if effect == "none":
            success = fx.none()

        elif effect == "spectrum":
            success = fx.spectrum()

        elif effect == "wave":
            # Params:  <direction 1-2>
            if params:
                success = fx.wave(int(params[0]))
            else:
                success = fx.wave(1)
                params_to_set = 1

        elif effect == "reactive":
            # Params:  <speed 1-4>
            if params:
                success = fx.reactive(primary_red, primary_green, primary_blue, int(params[0]))
            else:
                success = fx.reactive(primary_red, primary_green, primary_blue, 2)
                params_to_set = 2

        elif effect == "blinking":
            if params:
                success = fx.blinking(primary_red, primary_green, primary_blue)
            else:
                success = fx.blinking(primary_red, primary_green, primary_blue)

        elif effect == "breath":
            # Params: <type>
            if params:
                if params[0] == 'random':
                    success = fx.breath_random()
                    params_to_set = 'random'

                elif params[0] == 'single':
                    success = fx.breath_single(primary_red, primary_green, primary_blue)

                elif params[0] == 'dual':
                    success = fx.breath_dual(primary_red, primary_green, primary_blue,
                                   secondary_red, secondary_green, secondary_blue)

                # TODO: Add triple breath support

            else:
                success = fx.breath_random()
                params_to_set = 'random'

        elif effect == "pulsate":
            success = fx.pulsate(primary_red, primary_green, primary_blue)

        elif effect == "ripple":
            # Params: <type>
            if params:
                if params[0] == 'single':
                    success = fx.ripple(primary_red, primary_green, primary_blue, 0.01)

                elif params[0] == 'random':
                    success = fx.ripple_random(0.01)

            else:
                success = fx.ripple_random()
                params_to_set = 'random'

        elif effect == "starlight":
            # Params: <type> [speed 1-3]
            # TODO: Add option to set speed. Requires re-structure.
            speed = 2 # Normal

            if params:
                if params[0] == 'single':
                    success = fx.starlight_single(primary_red, primary_green, primary_blue, speed)

                elif params[0] == 'dual':
                    success = fx.starlight_dual(primary_red, primary_green, primary_blue,
                                      secondary_red, secondary_green, secondary_blue, speed)

                elif params[0] == 'random':
                    success = fx.starlight_random(speed)
            else:
                success = fx.starlight_random(speed)
                params_to_set = 'random'

        elif effect == "static":
            success = fx.static(primary_red, primary_green, primary_blue)

        else:
            print("Unrecognised effect {}! FX not applied.".format(effect))

    else:
        print("Unrecognised source! FX not applied.")

    # Daemon returns True/False whether effect was successful.
    # Only save state if the operation was successful
    if success:
        pref.set_device_state(device_object.serial, source, "effect", effect)

        if params_to_set:
            remember_params(params_to_set)

    # Some devices may throw a DBUS error, so returning function should be
    # prepared for that too.
    return(success)


def get_brightness(device_object, source):
    """
    Returns an integer of the brightness for a specified light source
    or a boolean for devices that can only toggle their brightness.
    """
    if source == "main":
        # Only integers are supported
        if device_object.has("brightness"):
            return int(device_object.brightness)

    elif source == "logo":
        if device_object.has("lighting_logo_active"):
            return int(device_object.fx.misc.logo.brightness) == 1
        elif device_object.has("lighting_logo_brightness"):
            return int(device_object.fx.misc.logo.brightness)

    elif source == "scroll":
        if device_object.has("lighting_scroll_active"):
            return int(device_object.fx.misc.scroll_wheel.brightness) == 1
        elif device_object.has("lighting_scroll_brightness"):
            return int(device_object.fx.misc.scroll_wheel.brightness)

    elif source == "backlight":
        if device_object.has("lighting_backlight_active"):
            return int(device_object.fx.misc.backlight.brightness) == 1
        elif device_object.has("lighting_backlight_brightness"):
            return int(device_object.fx.misc.backlight.brightness)

    return None


def set_brightness(pref, device_object, source, value):
    """
    Function to set the brightness level or turn it on/off
    for a specific area of the device.

    pref            Preferences object (for updating devicestate)
    device_object   Daemon device object
    source          Lighting source to use, e.g. "main" or "logo"
    value           Integer of the value. For "toggle" hardware, >0 will turn on,
                    0 will turn off.
    """
    device_fn = None

    if source == "main":
        if device_object.has("brightness"):
            device_fn = device_object

    elif source == "backlight":
        if device_object.has("lighting_backlight") or device_object.has("lighting_backlight_active"):
            device_fn = device_object.fx.misc.backlight

    elif source == "logo":
        if device_object.has("lighting_logo_brightness") or device_object.has("lighting_logo_active"):
            device_fn = device_object.fx.misc.logo

    elif source == "scroll":
        if device_object.has("lighting_scroll_brightness") or device_object.has("lighting_scroll_active"):
            device_fn = device_object.fx.misc.scroll_wheel

    if not device_fn:
        return None

    # For devices that only turn on/off.
    if is_brightness_toggled(device_object, source):
        if float(value) > 0:
            device_fn.active = True
        else:
            device_fn.active = False

    # For devices that use a brightness level.
    else:
        device_fn.brightness = float(value)

    # Update devicestate
    pref.set_device_state(device_object.serial, source, "brightness", int(value))


def is_brightness_toggled(device_object, source):
    """
    Determines if a device toggles its brightness on/off.

    Returns True if specified source is on/off.
    Returns False if specified source is variable.
    """
    if source == "main" and device_object.has("lighting_active"):
        return True

    if source == "backlight" and device_object.has("lighting_backlight_active"):
        return True

    if source == "logo" and device_object.has("lighting_logo_active"):
        return True

    if source == "scroll" and device_object.has("lighting_scroll_active"):
        return True

    return False


def get_source_icon(device_object, source):
    """
    Returns a path (excluding data source) to an icon that matches the context
    of the device and the lighting source.

    For example:
        - Mice show a mouse graphic with highlighted logo/scroll wheel
        - Naga Hex shows the 'rings' for 'main'.
        - Blade Stealth show clamshell logo for 'logo'.
    """
    # Defaults
    graphics = {
        "main": "img/effects/brightness.svg",
        "logo": "img/sources/logo.svg",
        "scroll": "img/sources/scroll.svg",
        "backlight": "img/fa/lightbulb.svg"
    }

    path = graphics[source]

    if device_object.name in ["Razer Naga Hex", "Razer Naga Hex V2", "Razer Naga Hex (Red)"]:
        path = "img/sources/naga-hex-ring.svg"

    if device_object.name.find("Blade") != -1 and source == "logo":
        path = "img/sources/blade-logo.svg"

    return path


def get_wave_direction(device):
    """
    Returns a list of localised direction strings according to the device.
    """
    if get_device_type(device) == "mouse":
        left = _("Down")
        right = _("Up")
    elif get_device_type(device) == "mousemat":
        left = _("Clockwise")
        right = _("Anti-clockwise")
    else:
        left = _("Left")
        right = _("Right")

    return [left, right]


def get_dpi_range(device):
    """
    Returns a list of default DPI values determined by the mouse's DPI range.
    """
    max_dpi = device.max_dpi

    if max_dpi == 16000:
        return [200, 800, 1800, 4500, 9000, 16000]

    elif max_dpi == 8200:
        return [200, 800, 1800, 4800, 6400, 8200]

    else:
        return [200,
            int(max_dpi / 10),
            int(max_dpi / 8),
            int(max_dpi / 4),
            int(max_dpi / 2),
            int(max_dpi)
        ]


def repeat_last_effect(pref, device_object):
    """
    Function to "replay" the last effect, for example, if the colour was changed.

    This affects all effects the device supports.
    """
    serial = device_object.serial

    def replay_source(source, capability):
        if device_object.has(capability):
            effect = pref.get_device_state(serial, source, "effect")
            effect_params = pref.get_device_state(serial, source, "effect_params")
            set_lighting_effect(pref, device_object, source, effect, effect_params)

    replay_source("main", "lighting")
    replay_source("backlight", "lighting_backlight")
    replay_source("logo", "lighting_logo")
    replay_source("scroll", "lighting_scroll")


def save_colours_to_all_sources(pref, device_object, colour_name, colour_hex):
    """
    Function to bulk save a colour for all light sources the device supports, e.g.
    logo, scroll, etc.

    The tray applet uses this as it sets colour across the entire device.

    colour_name     String as used in devicestate, e.g. "colour_primary"
    colour_hex      Colour hex, e.g. "#00FF00"
    """
    serial = device_object.serial

    def save_colour(source, capability):
        if device_object.has(capability):
            pref.set_device_state(serial, source, colour_name, colour_hex)

    save_colour("main", "lighting")
    save_colour("backlight", "lighting_backlight")
    save_colour("logo", "lighting_logo")
    save_colour("scroll", "lighting_scroll")


def is_device_fixed_colour(device):
    """
    Returns True if the device does not support RGB (e.g. can only turn LEDs on/off)
    """
    if not device.has("lighting_led_matrix"):
        return True

    return False


def is_device_greenscale(device):
    """
    Determines whether a Chroma-enabled device is "greenscale" - meaning
    it only has green LEDs (no RGB).

    This allows non-RGB keyboards to show green variants instead of full RGB
    for devices like the Razer BlackWidow Ultimate.
    """
    if not device.has("lighting_led_matrix") or device.name.find("Ultimate") != -1:
        return True

    return False


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


def get_tray_icon(dbg, pref, path):
    """
    Returns the full path to the icon to use with the tray applet.
    """

    # If it's the first time loading, set default icon to desktop environment.
    if not pref.exists("tray_icon", "type"):
        set_default_tray_icon(pref)

    icon_type = pref.get("tray_icon", "type", "builtin")
    icon_fallback = os.path.join(path.data_source, "tray", "humanity-light.svg")

    try:
        if icon_type == "builtin":
            icon_id = pref.get("tray_icon", "icon_id")
            icon_index = pref.load_file(os.path.join(path.data_source, "tray/icons.json"))
            return os.path.join(path.data_source, "tray", icon_index[icon_id]["path"])

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


def devicestate_monitor_start(callback_function, file_path):
    """
    Watches the devicestate.json file for changes, so different instances
    of Polychromatic (e.g. tray applet / controller) can refresh.

    callback_function   =   Function to call when there is a change.
    file_path           =   Full path to devicestate.json
    """
    run_thread(devicestate_monitor_thread, (callback_function, file_path))


def devicestate_monitor_thread(callback_function, file_path):
    """
    Main thread for monitoring devicestate.json changes.
    See devicestate_monitor_start() for reference.
    """
    def _init_devicestate_file():
        if not os.path.exists(file_path):
            with open(file_path, "a") as f:
                f.write("{}")

    while True:
        try:
            before = os.stat(file_path).st_mtime
            time.sleep(1)
            after = os.stat(file_path).st_mtime
            if before != after:
                 callback_function()
        except FileNotFoundError:
            _init_devicestate_file()


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


def is_any_razer_device_connected(dbg):
    """
    Scan 'lsusb' for Razer devices. Used for diagnostics to check whether a device is incompatible with daemon.

    Returns:
    None        Cannot be determined.
    True        Razer device was found
    False       Could not find a Razer device
    """
    try:
        lsusb = str(subprocess.Popen("lsusb", stdout=subprocess.PIPE).communicate()[0])
    except FileNotFoundError:
        dbg.stdout("'lsusb' not available, unable to determine if product is connected.", dbg.error, 1)
        return None

    if lsusb.find("ID 1532") == -1:
        return False
    else:
        return True


def get_device_vid_pid(device):
    """
    Extracts VID:PID from the daemon's device object in list format: [VID,PID]
    """
    vid = str(hex(device._vid))[2:].upper().rjust(4, '0')
    pid = str(hex(device._pid))[2:].upper().rjust(4, '0')
    return [vid, pid]


def get_incompatible_device_list(dbg, devices):
    """
    Scans 'lsusb' for incompatible Razer devices. As the daemon doesn't recognise them,
    they can be listed, but cannot be interacted with. Excludes already connected devices.

    Returns a list in format: [[vid1, pid1], [vid2, pid2]]
    Returns None if an error occurs (e.g. 'lsusb' not installed)
    """
    all_usb_ids = []
    reg_ids = []
    unreg_ids = []

    # Strip lsusb to just get VIDs and PIDs
    try:
        lsusb = subprocess.Popen("lsusb", stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
    except FileNotFoundError:
        dbg.stdout("'lsusb' not available, unable to determine if product is connected.", dbg.error, 1)
        return None

    for usb in lsusb.split("\n"):
        if len(usb) > 0:
            try:
                vidpid = usb.split(" ")[5].split(":")
                all_usb_ids.append([vidpid[0].upper(), vidpid[1].upper()])
            except AttributeError:
                pass

    # Get VIDs and PIDs of current devices to exclude them.
    for device in devices:
        vidpid = get_device_vid_pid(device)
        reg_ids.append([vidpid[0], vidpid[1]])

    # Identify Razer VIDs that are not registered in the daemon
    for usb in all_usb_ids:
        if usb[0] != "1532":
            continue

        if usb in reg_ids:
            continue

        unreg_ids.append(usb)

    return unreg_ids


def is_user_in_plugdev_group():
    """
    Check the groups of the currently logged in user to identify if it is
    missing 'plugdev' as required by the daemon.
    """
    if "plugdev" in [grp.getgrgid(g).gr_name for g in os.getgroups()]:
        return True
    else:
        return False


def get_plural(integer, non_plural, plural):
    """
    Returns the correct plural or non-plural spelling based on an integer.
    """
    if integer == 1:
        return non_plural
    else:
        return plural


def generate_uuid():
    return(str(int(time.time() * 1000000)))


def get_locale_pretty(locale):
    """
    Returns a 'prettier' string to show in UI for localized (if known)
    """
    try:
        locales = {
            "en_US": _("US"),
            "pt_BR": _("Brazilian Portuguese"),
            "en_GB": _("British")
        }
        return locales[locale]
    except KeyError:
        return locale


# Module Initalization
_ = setup_translations(__file__, "polychromatic")
