#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2018 Luke Horwell <code@horwell.me>
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
gi.require_version('Gtk', '3.0')
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


def get_device_image(device, data_dir):
    """
    Gets a generic Polychromatic image of the current device.
    """
    image_path = "{0}/ui/img/devices/{1}.svg".format(data_dir, get_device_type(device))
    if os.path.exists(image_path):
        return image_path
    else:
        return "{0}/ui/img/devices/unknown.svg".format(data_dir)


def get_real_device_image(device, angle="top"):
    """
    Returns the device image provided via the daemon if available.

    angle = top
            side
            perspective
    """
    try:
        if angle == "top":
            return device.razer_urls["top_img"]
        elif angle == "side":
            return device.razer_urls["side_img"]
        elif angle == "perspective":
            return device.razer_urls["perspective_img"]
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


def has_multiple_sources(device_obj):
    """
    Returns True or False to determine whether a device has multiple light sources.
    """
    source_list = get_supported_lighting_sources(device_obj)
    if len(source_list) > 1:
        return True
    else:
        return False


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

    primary_colours =   (Optional) Use this list [R,G,B] these instead of default primary colour.
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

    # Determine colours
    if not primary_colours:
        primary_colours = pref.get_device_state(serial, source, "colour_primary")

    if not secondary_colours:
        secondary_colours = pref.get_device_state(serial, source, "colour_secondary")

    if primary_colours:
        primary_red = primary_colours[0]
        primary_green = primary_colours[1]
        primary_blue = primary_colours[2]
    else:
        primary_red = 0
        primary_green = 255
        primary_blue = 0

    if secondary_colours:
        secondary_red = secondary_colours[0]
        secondary_green = secondary_colours[1]
        secondary_blue = secondary_colours[2]
    else:
        secondary_red = 255
        secondary_green = 0
        secondary_blue = 0

    # Execute function (only if source is known)
    if fx:
        if effect == "none":
            fx.none()

        elif effect == "spectrum":
            fx.spectrum()

        elif effect == "wave":
            # Params:  <direction 1-2>
            if params:
                fx.wave(int(params[0]))
            else:
                fx.wave(1)
                remember_params(1)

        elif effect == "reactive":
            # Params:  <speed 1-4>
            if params:
                fx.reactive(primary_red, primary_green, primary_blue, int(params[0]))
            else:
                fx.reactive(primary_red, primary_green, primary_blue, 2)
                remember_params(2)

        elif effect == "blinking":
            if params:
                fx.blinking(primary_red, primary_green, primary_blue)
            else:
                fx.blinking(primary_red, primary_green, primary_blue)

        elif effect == "breath":
            # Params: <type>
            if params:
                if params[0] == 'random':
                    fx.breath_random()
                    remember_params('random')

                elif params[0] == 'single':
                    fx.breath_single(primary_red, primary_green, primary_blue)

                elif params[0] == 'dual':
                    fx.breath_dual(primary_red, primary_green, primary_blue,
                                   secondary_red, secondary_green, secondary_blue)

                # TODO: Add triple breath support

            else:
                fx.breath_random()
                remember_params('random')

        elif effect == "pulsate":
            fx.pulsate(primary_red, primary_green, primary_blue)

        elif effect == "ripple":
            # Params: <type>
            if params:
                if params[0] == 'single':
                    fx.ripple(primary_red, primary_green, primary_blue, 0.01)

                elif params[0] == 'random':
                    fx.ripple_random(0.01)

            else:
                fx.ripple_random()
                remember_params('random')

        elif effect == "starlight":
            # Params: <type> [speed 1-3]
            # TODO: Add option to set speed. Requires re-structure.
            speed = 2 # Normal

            if params:
                if params[0] == 'single':
                    fx.starlight_single(primary_red, primary_green, primary_blue, speed)

                elif params[0] == 'dual':
                    fx.starlight_dual(primary_red, primary_green, primary_blue,
                                      secondary_red, secondary_green, secondary_blue, speed)

                elif params[0] == 'random':
                    fx.starlight_random(speed)
            else:
                fx.starlight_random(speed)
                remember_params('random')

        elif effect == "static":
            fx.static(primary_red, primary_green, primary_blue)

        pref.set_device_state(device_object.serial, source, "effect", effect)

    else:
        print("Unrecognised source! FX not applied.")


def set_brightness(pref, device_object, source, value):
    """
    Function to set the brightness for a specific area of the device.
    """

    if source == "main":
        device_object.brightness = int(value)

    elif source == "backlight":
        if value == "toggle":
            if device_object.fx.misc.backlight.active == True:
                device_object.fx.misc.backlight.active = False
            else:
                device_object.fx.misc.backlight.active = True
        else:
            device_object.fx.misc.backlight.brightness = int(value)

    elif source == "logo":
        if value == "toggle":
            if device_object.fx.misc.logo.active == True:
                device_object.fx.misc.logo.active = False
            else:
                device_object.fx.misc.logo.active = True
        else:
            device_object.fx.misc.logo.brightness = int(value)

    elif source == "scroll":
        if value == "toggle":
            if device_object.fx.misc.scroll_wheel.active == True:
                device_object.fx.misc.scroll_wheel.active = False
            else:
                device_object.fx.misc.scroll_wheel.active = True
        else:
            device_object.fx.misc.scroll_wheel.brightness = int(value)

    if value != "toggle":
        pref.set_device_state(device_object.serial, source, "brightness", int(value))


def set_brightness_toggle(pref, device_object, source, state):
    """
    Function to turn on or off a specific area of the device (for supported devices)

    state = True/False/"toggle"
    """

    if source == "backlight":
        source_obj = device_object.fx.misc.backlight

    elif source == "logo":
        source_obj = device_object.fx.misc.logo

    elif source == "scroll":
        source_obj = device_object.fx.misc.scroll_wheel

    if str(state) == "toggle":
        if source_obj.active == True:
            source_obj.active = 0
        else:
            source_obj.active = 1
    else:
        source_obj.active = state


def is_brightness_toggled(device_object, source):
    """
    Determines if a device toggles its brightness on/off.

    Returns True if specified source is on/off.
    Returns False if specified source is variable.
    """
    if source == "main":
        if device_obj.has("lighting_active"):
            return True

    if device_obj.has("lighting_backlight"):
        supported_sources.append("backlight")

    if device_obj.has("lighting_logo"):
        supported_sources.append("logo")

    if device_obj.has("lighting_scroll"):
        supported_sources.append("scroll")


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


def save_colours_to_all_sources(pref, device_object, colour_name, colour_set):
    """
    Function to bulk save a colour for all light sources the device supports, e.g.
    logo, scroll, etc.

    The tray applet uses this as it sets colour across the entire device.

    colour_name     String as used in devicestate, e.g. "colour_primary"
    colour_set      List in format [red, green, blue]
    """
    serial = device_object.serial

    def save_colour(source, capability):
        if device_object.has(capability):
            pref.set_device_state(serial, source, colour_name, colour_set)

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
    return {
        "1": {"name": _("Green") + " 1", "col": [0, 255, 0]},
        "2": {"name": _("Green") + " 2", "col": [0, 225, 0]},
        "3": {"name": _("Green") + " 3", "col": [0, 200, 0]},
        "4": {"name": _("Green") + " 4", "col": [0, 175, 0]},
        "5": {"name": _("Green") + " 5", "col": [0, 150, 0]},
        "6": {"name": _("Green") + " 6", "col": [0, 125, 0]},
        "7": {"name": _("Green") + " 7", "col": [0, 100, 0]},
        "8": {"name": _("Green") + " 8", "col": [0, 75, 0]},
        "9": {"name": _("Green") + " 9", "col": [0, 50, 0]},
    }


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


def get_tray_icon_preview_bg_colours():
    """
    Uses GTK to determine the background color of a user's panel where
    the tray applet will be shown.

    Returns a list of possible colours - light and dark.
    """
    colours = []
    win = Gtk.Window()
    style_context = win.get_style_context()
    colours.append(style_context.lookup_color("dark_bg_color").color.to_string())
    colours.append(style_context.lookup_color("bg_color").color.to_string())
    return colours


def get_tray_icon(dbg, pref, path):
        """
        Icon Sources
            "tray_icon": {"type": "?"}
                builtin     = One provided by Polychromatic.    "humanity-light"
                custom      = One specified by user.            "/path/to/file"
                gtk         = Use icon by GTK name.             "keyboard"
        """

        # If it's the first time loading, set default icon to desktop environment.
        if not pref.exists("tray_icon", "type"):
            set_default_tray_icon(pref)

        icon_type = pref.get("tray_icon", "type", "builtin")
        icon_value = pref.get("tray_icon", "value", "0")
        icon_fallback = os.path.join(path.data_source, "tray", "humanity-light.svg")

        try:
            if icon_type == "builtin":
                # icon_value = UUID
                icon_index = pref.load_file(os.path.join(path.data_source, "tray/icons.json"))
                return os.path.join(path.data_source, "tray", icon_index[icon_value]["path"])

            elif icon_type == "custom":
                # icon_value = Path to icon
                if os.path.exists(icon_value):
                    return icon_value
                else:
                    dbg.stdout("Icon missing: " + icon_value, dbg.error)
                    dbg.stdout("Using fallback!", dbg.error)
                    return icon_fallback

            elif icon_type == "gtk":
                # icon_value = Icon name used by GTK
                return icon_value

            else:
                return icon_fallback

        except Exception:
            dbg.stdout("Error whlie loading icon, using fallback.", dbg.error)
            return icon_fallback


def restart_tray_applet(dbg, path):
    """
    Restarts the tray applet if an instance is running in the background.
    """
    dbg.stdout("Restarting tray applet...", dbg.action, 1)

    try:
        pid = int(subprocess.check_output(["pidof", "polychromatic-tray-applet"]))
        os.kill(pid, 9)
    except Exception:
        dbg.stdout("Tray applet not running so won't restart.", dbg.action, 1)
        return

    # Where is the tray applet?
    if os.path.dirname(__file__).endswith("bin"):
        # System-wide installation
        tray_bin_path = os.path.dirname(__file__) + "/polychromatic-tray-applet"
    else:
        # Development
        tray_bin_path = os.path.abspath(os.path.join(path.data_source, "../polychromatic-tray-applet"))

    # Attempt to gracefully stop the process, then launch again.
    try:
        subprocess.Popen(tray_bin_path)
        dbg.stdout("Successfully reloaded tray applet.", dbg.success, 1)

    except OSError as e:
        dbg.stdout("Failed to relaunch tray applet!", dbg.error)
        dbg.stdout("Exception: " + str(e), dbg.error)

    return


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


def colour_to_hex(colour):
    """
    Converts [R,G,B] list to #RRGGBB string.
    """
    return "#{0:02X}{1:02X}{2:02X}".format(*colour)


def hex_to_colour(hex_string):
    """
    Converts "#RRGGBB" string to [R,G,B] list.
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


# Module Initalization
_ = setup_translations(__file__, "polychromatic")
