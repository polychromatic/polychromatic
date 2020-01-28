#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2019 Luke Horwell <code@horwell.me>
#
"""
This module contains the locale strings for Polychromatic.
"""

import gettext
from . import common

_ = common.setup_translations(__file__, "polychromatic")

KEYBOARD_LAYOUTS = {
    "en_US": _("English (US)"),
    "en_GB": _("English (British)"),
    "el_GR": _("Greek"),
    "de_DE": _("German"),
    "fr_FR": _("French"),
    "ru_RU": _("Russian"),
    "ja_JP": _("Japanese"),
    "es_ES": _("Spanish"),
    "it_IT": _("Italian"),
    "pt_PT": _("Portuguese (Portugal)"),
    "pt_BR": _("Portuguese (Brazil)"),
    "en_US_mac": _("English (US, Macintosh)")
}

LOCALES = {

    # Tabs
    "devices": _("Devices"),
    "effects": _("Effects"),
    "profiles": _("Profiles"),
    "schedule": _("Schedule"),
    "preferences": _("Preferences"),

    # Devices
    "tasks": _("Tasks"),
    "no-device": _("No devices connected"),
    "device-info": _("Device Info"),
    "brightness": _("Brightness"),
    "effect": _("Effect"),
    "effect_options": _("Effect Options"),
    "spectrum": _("Spectrum"),
    "wave": _("Wave"),
    "reactive": _("Reactive"),
    "breath": _("Breath"),
    "ripple": _("Ripple"),
    "static": _("Static"),
    "starlight": _("Starlight"),
    "game_mode": _("Game Mode"),
    "enabled": _("Enabled"),
    "disabled": _("Disabled"),
    "learn_more": _("Learn more"),
    "macros": _("Macros"),
    "dpi": _("DPI"),
    "poll_rate": _("Polling Rate"),
    "apply-to-all": _("Apply to All"),
    "apply-to-all-unsupported": _("Some of your connected devices do not support all of these effects."),
    "unknown-device": _("Unrecognized: []"),

    # Device Info
    "formfactor": _("Form Factor"),
    "serial": _("Serial"),
    "firmware_version": _("Firmware Version"),
    "macro_support": _("Macro Support"),
    "matrix_size": _("Matrix Dimensions"),
    "capability_name": _("Daemon Capability"),
    "capability_supported": _("Supported?"),
    "capability_description": _("Description"),

    # Wave
    "wave_options": _("Wave Direction"),
    "left": _("Left"),
    "right": _("Right"),
    "clockwise": _("Clockwise"),
    "anticlockwise": _("Anticlockwise"),
    "up": _("Up"),
    "down": _("Down"),

    # Reactive
    "reactive_options": _("Reactive Speed"),
    "fast": _("Fast"),
    "medium": _("Medium"),
    "slow": _("Slow"),
    "vslow": _("Very Slow"),

    # Breath/Ripple
    "breath_options": _("Breath Type"),
    "ripple_options": _("Ripple Type"),
    "random": _("Random Colors"),
    "single": _("Single Color"),
    "dual": _("Dual Colors"),

    # Colours
    "primary_colour": _("Primary Color"),
    "secondary_colour": _("Secondary Color"),
    "teritary_colour": _("Teritary Color"),

    # Buttons
    "ok": _("OK"),
    "colour": _("Color"),
    "close-app": _("Close Application"),
    "troubleshoot": _("Troubleshoot"),
    "retry": _("Retry"),
    "on": _("On"),
    "off": _("Off"),
    "browse": _("Browse"),
    "change": _("Change..."),

    # Poll Rates
    "poll_rate_125": _("125 Hz (8 ms)"),
    "poll_rate_500": _("500 Hz (2 ms)"),
    "poll_rate_1000": _("1000 Hz (1 ms)"),

    # Preferences
    "saved_colours": _("Saved Colors"),
    "about": _("About"),
    "general": _("General"),
    "tray-applet": _("Tray Applet"),
    "daemon": _("Daemon"),
    "effects-welcome-title": _("Select an effect to begin."),
    "new-effect": _("New Effect"),
    "import-effect": _("Import..."),
    "author": _("Author"),
    "type": _("Type"),
    "mapping": _("Mapped Hardware"),
    "key_mapping": _("Key Mapping"),
    "emblem": _("Emblem"),
    "file-system": _("File System"),
    "custom-path-info": _("Choose an image or .desktop file from your computer."),

    # Invalid Save Data Pop-up
    "save_data_warning_title": _("Incompatible Save Data"),
    "save_data_warning_text1": _("Polychromatic's configuration (including effects and profiles) has previously been saved in a newer version of this software."),
    "save_data_warning_text2": _("Running older versions of the software could corrupt your save data or cause glitches."),
    "save_data_warning_app_version": _("Application Version:"),
    "save_data_warning_saved_version": _("Save Data Version:"),
    "save_data_warning_pref_version": _("(Expected: 1 or older)"),
    "save_data_warning_text3": _("Consider updating Polychromatic, or reset the application by deleting: ~/.config/polychromatic"),

    # Error: Backend returns None (can't set device)
    "error_device_gone_title": _("Device Unavailable"),
    "error_device_gone_text": _("The request could not be completed as a device was recently added/removed. Please refresh and try again."),

    # Error: Backend returns False (invalid)
    "error_bad_request_title": _("Backend Error"),
    "error_bad_request_text": _("The request could not be processed as it is not supported at this time."),

    # Error: Backend throws exception (str)
    "error_backend_title": _("Backend Error"),
    "error_backend_text": _("The request could not be completed as an exception was thrown by the backend:"),

    "error_not_ready_title": _("Initialization Error"),
    "error_not_ready_text": _("This device's daemon or Python library could not be initialized. See the exception for details:")
}
