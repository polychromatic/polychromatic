#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2020 Luke Horwell <code@horwell.me>
#
"""
This module contains shared locale strings for Polychromatic. Usually used
when referenced by the backend module.
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

    if os.path.exists(os.path.join(whereami, "locale/dist")):
        # Using relative path (development build)
        locale_path = os.path.join(whereami, "locale/dist/")
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


# Module Initalization
t = setup_translations(__file__)
_ = _get_gettext(t)
CURRENT_LOCALE = _get_current_locale(t)
KEYBOARD_LAYOUTS = get_keyboard_layouts()
