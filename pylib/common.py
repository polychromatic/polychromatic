#!/usr/bin/env python3

"""
    Module for common functions used by Polychromatic's
    Controller and Tray Applet.
"""
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017 Luke Horwell <luke@ubuntu-mate.org>

import os
import sys
import gettext
from time import sleep
from threading import Thread
import math

# Devices that do not support RGB at all.
# (excludes Ultimate which supports shades of green)
fixed_coloured_devices = ["Taipan"]

class CpuThreadData:
    def __init__(self):
        self.stop = False
cpu_thread_data = CpuThreadData()

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

    def stdout(self, msg, colour_code='\033[0m', verbosity=0):
        # msg           String containing message for stdout.
        # color         stdout code (e.g. '\033[92m')
        # verbosity     0 = Always shown
        #               1 = -v flag
        #               2 = -vv flag

        if self.verbose_level >= verbosity:
            # Only colourise output if running in a real terminal.
            if sys.stdout.isatty():
                print(colour_code + msg + '\033[0m')
            else:
                print(msg)


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


def get_device_type(device_type):
    """
    Convert the daemon's device type string to what Polychromatic identifies as "form factor".
    This is used for determining icons.
    """
    if device_type == "firefly":
        form_factor = "mousemat"
    elif device_type == "tartarus":
        form_factor = "keypad"
    else:
        form_factor = device_type
    return(form_factor)


def has_multiple_sources(device_obj):
    """
    Returns True or False to determine whether a device has multiple light sources.
    """
    main_light = device_obj.has("lighting")
    backlight_light = device_obj.has("lighting_backlight")
    logo_light = device_obj.has("lighting_logo")
    scroll_light = device_obj.has("lighting_scroll")

    light_sources = 0
    for value in [main_light, backlight_light, logo_light, scroll_light]:
        if value == True:
            light_sources += 1

    if light_sources > 1:
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
    elif string == 'cpu':
        return _("System Monitor")
    else:
        return string


def set_lighting_effect(pref, device_object, source, effect, fx_params=None):
    """
    Function to set a effect for a specific area of the device.

    device_object = Device to apply effect to.
    source =        Lighting source labelled by Polychromatic.
                        e.g. main / scroll / wheel
    effect =        Effect name identified by Polychromatic.
                        e.g. wave / spectrum / static
    params =        (Optional) Any parameters for the effect, seperated by '?'.
                        e.g. 255?255?255?2
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
    primary_colours = pref.get_device_state(serial, source, "colour_primary")
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

    # Stop the CPU effect thread if it exists.
    cpu_thread_data.stop = True

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

        elif effect == "cpu":
            # Stop any other effect (needed to shutdown Ripple)
            fx.static(255, 255, 255)
            
            # Start a thread to monitor CPU
            # usage and change the lighting on the fly.
            cpu_thread_data.stop = False
            thread = Thread(target=cpu_monitor_thread, args=(cpu_thread_data, device_object, pref, source))
            thread.daemon = True
            thread.start()

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
    Function to store the colour for all sources the device supports.

    E.g. the tray applet sets the colour for all the device.

    colour_name = string as used in devicestate, e.g. "colour_primary"
    colour_set = list in format [red, green, blue]
    """
    serial = device_object.serial

    def save_colour(source, capability):
        if device_object.has(capability):
            pref.set_device_state(serial, source, colour_name, colour_set)

    save_colour("main", "lighting")
    save_colour("backlight", "lighting_backlight")
    save_colour("logo", "lighting_logo")
    save_colour("scroll", "lighting_scroll")


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


def devicestate_monitor_start(callback_function, file_path):
    """
    Watches the devicestate.json file for changes, so different instances
    of Polychromatic (e.g. tray applet / controller) can refresh.

    callback_function   =   Function to call when there is a change.
    file_path           =   Full path to devicestate.json
    """
    thread = Thread(target=devicestate_monitor_thread, args=(callback_function, file_path))
    thread.daemon = True
    thread.start()


def devicestate_monitor_thread(callback_function, file_path):
    """
    Seperate thread for monitoring devicestate.json changes.
    See devicestate_monitor_start() for reference.
    """
    def _init_devicestate_file():
        if not os.path.exists(file_path):
            with open(file_path, "a") as f:
                f.write("{}")

    while True:
        try:
            before = os.stat(file_path).st_mtime
            sleep(1)
            after = os.stat(file_path).st_mtime
            if before != after:
                 callback_function()
        except FileNotFoundError:
            _init_devicestate_file()

def cpu_usage(last_idle, last_total):
    with open('/proc/stat') as f:
        fields = [float(column) for column in f.readline().strip().split()[1:]]
    idle, total = fields[3], sum(fields)
    idle_delta, total_delta = idle - last_idle, total - last_total
    last_idle, last_total = idle, total
    utilisation = 100.0 * (1.0 - idle_delta / total_delta)
    return (utilisation, last_idle, last_total)

def cpu_monitor_thread(data, device, pref, source):
    rows, cols = device.fx.advanced.rows, device.fx.advanced.cols

    # Number of CPU rows is half rounded up
    cpu_rows = min(rows, math.ceil(rows//2))
    mem_rows = max(0, rows - cpu_rows)

    cpu_query_time = 0.25 # seconds
    serial = device.serial
    last_idle = 0
    last_total = 0
    
    while True:
        # If we used psutil, we could get CPU and RAM this way.
        #cpu = psutil.cpu_percent(cpu_query_time)
        #mem = psutil.virtual_memory()

        (cpu, last_idle, last_total) = cpu_usage(last_idle, last_total)
        
        # Get RAM usage
        tot_m, used_m, free_m = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
        mem_percent = 1-(free_m/tot_m)

        primary_colours = pref.get_device_state(serial, source, "colour_primary")
        secondary_colours = pref.get_device_state(serial, source, "colour_secondary")

        if primary_colours:
            primary_red = primary_colours[0]
            primary_green = primary_colours[1]
            primary_blue = primary_colours[2]
        else:
            primary_red = 255
            primary_green = 0
            primary_blue = 0

        if secondary_colours:
            secondary_red = secondary_colours[0]
            secondary_green = secondary_colours[1]
            secondary_blue = secondary_colours[2]
        else:
            secondary_red = 0
            secondary_green = 255
            secondary_blue = 0
            

        # Scale cpu and memory usage to the number of cols
        num_light = int(cols*(cpu/100))
        mem_light = int(cols*mem_percent)

        # CPU
        for row in range(0, cpu_rows):
            for col in range(cols):
                if col <= num_light:
                    device.fx.advanced.matrix[row, col] = (primary_red, primary_green, primary_blue)
                else:
                    device.fx.advanced.matrix[row, col] = (128, 128, 128)

        # Memory
        for row in range(cpu_rows, cpu_rows+mem_rows):
            for col in range(cols):
                if col <= mem_light:
                    device.fx.advanced.matrix[row, col] = (secondary_red, secondary_green, secondary_blue)
                else:
                    device.fx.advanced.matrix[row, col] = (128, 128, 128)

        if data.stop:
            #print('CPU thread shutdown')
            return
        device.fx.advanced.draw()
        sleep(cpu_query_time)

def has_fixed_colour(device_obj):
    """
    Returns True if the device does not support RGB (e.g. can only turn LEDs on/off)
    """
    for name in fixed_coloured_devices:
        if device_obj.name.find(name) != -1:
            return True
    return False

"""
Module Initalization
"""
_ = setup_translations(__file__, "polychromatic-common")
