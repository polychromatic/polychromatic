#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2020 Luke Horwell <code@horwell.me>
#
"""
This module contains the locale strings for Polychromatic.
"""

import os
import gettext
from . import common


def setup_translations(bin_path, force_locale=None):
    """
    Initalises translations for the application.

    Parameters:
        bin_path        __file__ of the application that is being executed.

    Returns: Result from gettext.translation()
    """
    whereami = os.path.abspath(os.path.join(os.path.dirname(bin_path)))

    if os.path.exists(os.path.join(whereami, "locale/testing")):
        # Using relative path (development build)
        locale_path = os.path.join(whereami, "locale/testing/")
    elif os.path.exists(os.path.join(whereami, "locale/")):
        # Using relative path (/opt build)
        locale_path = os.path.join(whereami, "locale/")
    else:
        # Using system path or en_US if none found
        locale_path = "/usr/share/locale/"

    if force_locale:
        return gettext.translation("polychromatic", localedir=locale_path, fallback=True, languages=[force_locale])

    return gettext.translation("polychromatic", localedir=locale_path, fallback=True)


def _get_gettext(i18n):
    """
    Returns the object for binding to the "_" variable.
    """
    return i18n.gettext


def _get_current_locale(i18n):
    """
    Returns a string describing the current locale. E.g. "de" or "en_US".
    """
    if t.info() == dict:
        return t.info().language

    # Fallback in use
    return "en_GB"


def reload_locales(self, bin_path, force_locale):
    """
    Reloads the locales when passing the --locale parameter.

    Parameters:
        self            This module (locales)
        bin_path        __file__ of the current application
        force_locale    Use a specific locale

    Returns the gettext object which should be re-assigned
    to the application's _ variable.
    """
    self.t = setup_translations(bin_path, force_locale)
    self._ = _get_gettext(t)
    self.CURRENT_LOCALE = _get_current_locale(t)
    self.LOCALES = get_strings()
    self.KEYBOARD_LAYOUTS = get_keyboard_layouts()

    return self._


def get_keyboard_layouts():
    return {
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


def get(string_id):
    """
    Returns a specific string.
    """
    return get_strings()[string_id]


def get_strings():
    """
    Dump all the strings as a dictionary. Used in the view (HTML) environment.
    """
    return {
        # Tabs
        "devices": _("Devices"),
        "effects": _("Effects"),
        "presets": _("Presets"),
        "triggers": _("Triggers"),
        "preferences": _("Preferences"),

        # Form Factors
        "accessory": _("USB Accessory"),
        "keyboard": _("Keyboard"),
        "mouse": _("Mouse"),
        "mousemat": _("Mousemat"),
        "keypad": _("Keypad"),
        "headset": _("Headset"),
        "gpu": _("External Graphics Enclosure"),
        "unrecognised": _("Unrecognised"),

        # Zones
        "main": _("Main"),
        "logo": _("Logo"),
        "scroll": _("Scroll Wheel"),
        "backlight": _("Backlight"),
        "left": _("Left"),
        "right": _("Right"),
        "hex-ring": _("Hex Ring"),
        "laptop-lid": _("Laptop Lid"),

        # Default Colours
        "white": _("White"),
        "red": _("Red"),
        "green": _("Green"),
        "blue": _("Blue"),
        "aqua": _("Aqua"),
        "orange": _("Orange"),
        "pink": _("Pink"),
        "purple": _("Purple"),
        "yellow": _("Yellow"),
        "grey-light": _("Light Grey"),
        "grey-dark": _("Dark Grey"),
        "black": _("Black"),

        # Directions
        "left": _("Left"),
        "right": _("Right"),
        "down": _("Down"),
        "up": _("Up"),
        "clock": _("Clockwise"),
        "anticlock": _("Anti-clockwise"),

        # Devices
        "device-info": _("Device Info"),
        "brightness": _("Brightness"),
        "effect": _("Effect"),
        "effect_options": _("Effect Options"),
        "spectrum": _("Spectrum"),
        "wave": _("Wave"),
        "reactive": _("Reactive"),
        "breath": _("Breath"),
        "ripple": _("Ripple"),
        "pulsate": _("Pulsate"),
        "blinking": _("Blink"),
        "static": _("Static"),
        "starlight": _("Starlight"),
        "game_mode": _("Game Mode"),
        "enabled": _("Enabled"),
        "disabled": _("Disabled"),
        "macros": _("Macros"),
        "dpi": _("DPI"),
        "poll_rate": _("Polling Rate"),
        "apply": _("Apply"),
        "apply-to-all": _("Apply to All"),
        "apply-to-all-unsupported": _("Some of your connected devices do not support all of these effects."),
        "unknown-device": _("Unrecognized: []"),
        "no-config-options": _("Sorry, this application has no configurable options for this device."),

        # Device tab errors for individual devices
        "unknown-device-help": _("This device may work with OpenRazer. Currently, openrazer-daemon hasn't registered this device, which could indicate an installation problem or lack of support right now."),

        # Device tab - there are no devices
        "no-device": _("No devices connected"),
        "no-device-help": _("Please plug in a compatible device to control its lighting effects and features."),

        # Device tab errors for daemon problems
        "daemon-error": _("Daemon Error"),
        "daemon-error-help": _("OpenRazer daemon could not be started."),

        "openrazer-not-running": _("Daemon Not Running"),
        "openrazer-not-running-help": _("The backend was not started automatically. Please run 'openrazer-daemon' and try again."),

        # Device Info
        "device_info_title": _("Device Information: []"),
        "form_factor": _("Form Factor"),
        "serial": _("Serial"),
        "firmware_version": _("Firmware Version"),
        "matrix_support": _("Custom Effects"),
        "matrix_dimensions": _("Matrix Dimensions"),
        "matrix_size": _("X rows, Y columns"),
        "unsupported": _("Unsupported"),
        "supported": _("Supported"),
        "debug_matrix": _("Test Matrix"),
        "debug_matrix_title": _("Test Matrix: []"),
        "debug_matrix_help": _("Hover over the matrix to test individual addressable LEDs on the hardware."),
        "debug_matrix_position": _("Position:"),
        "backend": _("Backend"),

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
        "random": _("Random Colours"),
        "single": _("Single Colour"),
        "dual": _("Dual Colours"),

        # Colours
        "primary_colour": _("Primary Colour"),
        "secondary_colour": _("Secondary Colour"),
        "teritary_colour": _("Teritary Colour"),

        # Buttons
        "ok": _("OK"),
        "cancel": _("Cancel"),
        "save": _("Save"),
        "reset": _("Reset"),
        "colour": _("Colour"),
        "close": _("Close"),
        "close-app": _("Close Application"),
        "troubleshoot": _("Troubleshoot"),
        "open-help": _("Online Help"),
        "retry": _("Retry"),
        "on": _("On"),
        "off": _("Off"),
        "browse": _("Browse"),
        "change": _("Change..."),
        "refresh": _("Refresh"),
        "colours_gtk": _("Use System Picker"),

        # Poll Rates
        "poll_rate_125": _("125 Hz (8 ms)"),
        "poll_rate_500": _("500 Hz (2 ms)"),
        "poll_rate_1000": _("1000 Hz (1 ms)"),

        # Preferences
        "application": _("Application"),
        "backends": _("Backends"),
        "about": _("About"),
        "general": _("General"),
        "tray_applet": _("Tray Applet"),
        "tray_applet_gif_note": _("Heads up! Animated GIFs may not be supported by all desktop environments."),
        "saved_colours": _("Saved Colours"),
        "default_colours": _("Default Colours"),
        "restore_defaults": _("Restore Defaults"),
        "view_source_code": _("View Source Code"),
        "whats_new": _("What's New?"),
        "dependencies": _("Dependencies"),
        "version": _("Version"),
        "save_format": _("Save Data Format"),
        "links": _("Links"),
        "license": _("License"),
        "license_line_1": _("Polychromatic is free software; you can redistribute it and/or modify it under the terms of the GNU General Public Licence v3 as published by the Free Software Foundation."),
        "license_line_2": _("Polychromatic is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public Licence for more details."),
        "license_line_3": _("A copy of the GPLv3 can be viewed at [url]"),
        "license_notices": _("Open Source Notices"),
        "editor": _("Editor"),
        "effect_live_preview": _("While editing, show changes on the actual hardware."),
        "appearance": _("Appearance"),
        "icon": _("Icon"),
        "advanced": _("Advanced"),
        "compatibility": _("Compatibility"),
        "force_legacy_gtk_status": _("Force GTK Status Icon instead of AppIndicator"),
        "apply_changes": _("Apply Changes"),
        "restart_tray_applet": _("Restart Tray Applet"),
        "about_default_colours": _("These colours will be used when setting effects from 'Apply to All' or the tray applet."),
        "about_saved_colours": _("Configure your favourite and frequent colours here."),
        "configuration": _("Configuration"),
        "logs": _("Logs"),
        "options": _("Options"),
        "landing_tab": _("Landing Tab"),
        "unknown": _("Unknown"),

        # Reset Saved Colours Confirmation
        "reset_saved_colours_title": _("Reset Saved Colours?"),
        "reset_saved_colours_body": _("These settings will be reset to their defaults. There is no undo!"),

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
        "error_device_gone_text": _("The request could not be completed due to devices being removed/inserted. Please refresh and try again."),

        # Error: Backend returns False (invalid)
        "error_bad_request_title": _("Controller Problem"),
        "error_bad_request_text": _("The request could not be processed as it is invalid or unsupported at this time."),

        # Error: Backend throws exception (str)
        "error_backend_title": _("Backend Error"),
        "error_backend_text": _("The request could not be completed. An error was thrown by the backend:"),

        # Error: Controller throws uncaught exception
        "error_generic_title": _("Controller Error"),
        "error_generic_text": _("The request could not be completed due to an error."),

        # Error: Backend not ready
        "error_not_ready_title": _("Initialization Error"),
        "error_not_ready_text": _("This device's backend library or daemon could not be initialized."),

        # Error: Could not spawn process
        "error_spawn_process_text": _("Polychromatic was unable to start the helper process. Try re-installing the application and/or checking your PATH variable."),

        # Troubleshooter - General
        "troubleshoot_cannot_run": _("The troubleshooter cannot be started. Here's the error:"),
        "troubleshoot_test_complete": _("All checks completed."),
        "troubleshoot_test_partial": _("Not all of the checks were performed due to errors, here's what was found anyway."),
        "restart_backends": _("Restart Daemon"),
        "restarting_backends": _("Restarting the OpenRazer daemon..."),
        "troubleshooting": _("Troubleshooting..."),

        # Troubleshooter - OpenRazer checks
        "troubleshoot_daemon_found": _("Check if daemon is installed"),
        "troubleshoot_daemon_found_suggestion": _("Install the 'openrazer-meta' package for your distribution."),
        "troubleshoot_daemon_running": _("Check if daemon is running"),
        "troubleshoot_daemon_running_suggestion": _("Start the daemon from the terminal. Look out for any errors: $ openrazer-daemon -Fv"),
        "troubleshoot_pylib_present": _("Check if Python library is installed"),
        "troubleshoot_pylib_present_suggestion": _("Install the 'python3-openrazer' package for your distribution."),
        "troubleshoot_dkms_installed_src": _("Check if DKMS sources are installed"),
        "troubleshoot_dkms_installed_src_suggestion": _("Install the 'openrazer-meta' package for your distribution."),
        "troubleshoot_dkms_installed_built": _("Check if DKMS module is built for this kernel version"),
        "troubleshoot_dkms_installed_built_suggestion": _("Ensure your Linux kernel headers are installed, and try re-installing the DKMS module (replacing 2.x.x with the version of OpenRazer installed) $ sudo dkms install -m openrazer-driver/2.x.x"),
        "troubleshoot_dkms_loaded": _("Check if DKMS module can be loaded"),
        "troubleshoot_dkms_loaded_suggestion": _("For full error details, run $ sudo modprobe razerkbd"),
        "troubleshoot_dkms_active": _("Check if DKMS module is currently loaded"),
        "troubleshoot_dkms_active_suggestion": _("For full error details, run $ sudo modprobe razerkbd"),
        "troubleshoot_secure_boot": _("Check for secure boot on an EFI system"),
        "troubleshoot_secure_boot_suggestion": _("OpenRazer's kernel modules are unsigned, so they will not load at boot. Either disable secure boot, or sign the modules yourself."),
        "troubleshoot_plugdev": _("Check if user account is added to 'plugdev' group"),
        "troubleshoot_plugdev_suggestion": _("If you've recently installed, you may need to restart the computer. Otherwise, run this command, log out, then log back in to the computer: $ sudo gpasswd -a $USER plugdev"),
        "troubleshoot_plugdev_perms": _("Check OpenRazer log for plugdev permission errors"),
        "troubleshoot_plugdev_perms_suggestion": _("Restarting (or replugging) usually fixes the problem. Clear the log to reset this message."),
        "troubleshoot_all_supported": _("Check for unsupported hardware"),
        "troubleshoot_all_supported_suggestion": _("Check the OpenRazer project to confirm your device is listed. To get the device's VID:PID, run $ lsusb | grep Razer"),

        # Icon Picker
        "file_error_title": _("File Error"),
        "file_error_missing": _("The selected file no longer exists."),
        "icon_picker_title": _("Icon Chooser"),
        "add_graphic": _("Add a graphic"),
        "tray": _("Tray"),
        "emblems": _("Emblems"),
        "custom": _("Custom"),
        "choose": _("Choose"),
        "revert": _("Revert"),

        # File Picker
        "filter_jpg": _("JPEG image"),
        "filter_png": _("PNG image"),
        "filter_gif": _("GIF image"),
        "filter_webp": _("WebP image"),
        "filter_svg": _("SVG image"),
        "filter_all_images": _("All supported images"),
        "filter_all_types": _("All files"),

        # Common
        "tasks": _("Tasks"),

        # Effects
        "new_effect": _("New Effect"),
        "import": _("Import..."),
        "keyframed": _("Keyframed"),
        "scripted": _("Script"),
        "play": _("Play"),
        "playing": _("Playing"),
        "edit": _("Edit"),
        "delete": _("Delete"),

        # Effects Overview
        "multiple": _("(Multiple)"),
        "tampered": _("Tampered"),

        # Read Error (Effects/Presets)
        "read_error_title": _("Corrupt Data"),
        "read_error_text": _("The data integrity of this file is invalid. Run the application in the Terminal for more details."),
        "read_error_aftermath_effect": _("This effect cannot be opened as the JSON structure is damaged. For technical details, run this application via the Terminal."),
        # End
        "": ""
    }


# Module Initalization
t = setup_translations(__file__)
_ = _get_gettext(t)
CURRENT_LOCALE = _get_current_locale(t)
LOCALES = get_strings()
KEYBOARD_LAYOUTS = get_keyboard_layouts()
