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
    "overview": _("All Devices"),
    "devices": _("Devices"),
    "effects": _("Effects"),
    "profiles": _("Profiles"),
    "schedule": _("Schedule"),
    "preferences": _("Preferences"),
    "device-info": _("Device Info"),
    "brightness": _("Brightness"),
    "effect": _("Effect"),
    "spectrum": _("Spectrum"),
    "wave": _("Wave"),
    "reactive": _("Reactive"),
    "breath": _("Breath"),
    "ripple": _("Ripple"),
    "static": _("Static"),
    "starlight": _("Starlight"),
    "game_mode": _("Game Mode"),
    "enabled": _("Enabled"),
    "learn_more": _("Learn more"),
    "macros": _("Macros"),
    "dpi": _("DPI"),
    "polling_rate": _("Polling Rate"),
    "wave-settings": _("Wave Direction"),
    "left": _("Left"),
    "right": _("Right"),
    "clockwise": _("Clockwise"),
    "anticlockwise": _("Anticlockwise"),
    "up": _("Up"),
    "down": _("Down"),
    "reactive-settings": _("Reactive Speed"),
    "fast": _("Fast"),
    "medium": _("Medium"),
    "slow": _("Slow"),
    "vslow": _("Very Slow"),
    "breath-settings": _("Breath Type"),
    "random": _("Random"),
    "single": _("Single"),
    "dual": _("Dual"),
    "ripple-settings": _("Ripple Type"),
    "color": _("Color"),
    "unknown-device": _("Unrecognized"),
    "close-app": _("Close Application"),
    "troubleshoot": _("Troubleshoot"),
    "retry": _("Retry"),
    "on": _("On"),
    "off": _("Off"),
    "formfactor": _("Form Factor"),
    "serial": _("Serial"),
    "firmware_version": _("Firmware Version"),
    "macro_support": _("Macro Support"),
    "matrix_size": _("Matrix Dimensions"),
    "capability_name": _("Daemon Capability"),
    "capability_supported": _("Supported?"),
    "capability_description": _("Description"),
    "connected-devices": _("Connected Devices"),
    "apply-to-all": _("Apply to All"),
    "unsupported-all-effects": _("Some devices could not be applied as they do not support this effect."),
    "saved-colours": _("Saved Colors"),
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
    "browse": _("Browse"),
    "custom-path-info": _("Choose an image or .desktop file from your computer."),
}
