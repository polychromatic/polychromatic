#!/usr/bin/env python3

"""
    Module for common functions used by Polychromatic's
    Controller and Tray Applet.
"""
# Polychromatic is licensed under the GPLv2.
# Copyright (C) 2017 Luke Horwell <luke@ubuntu-mate.org>

import os
import gettext

# Use i18n translations for some strings in this module.
whereami = os.path.abspath(os.path.join(os.path.dirname(__file__)))

if os.path.exists(os.path.join(whereami, '../locale/')):
    locale_path = os.path.join(whereami, '../locale/')
else:
    locale_path = '/usr/share/locale/'

global _
t = gettext.translation('polychromatic-common', localedir=locale_path, fallback=True)
_ = t.gettext

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
    logo_light = device_obj.has("lighting_logo")
    scroll_light = device_obj.has("lighting_scroll")

    light_sources = 0
    for value in [main_light, logo_light, scroll_light]:
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
