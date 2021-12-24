# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2021 Luke Horwell <code@horwell.me>
"""
Contains the UI localization for Polychromatic. Powered by GNU's gettext.
"""
import os
import gettext


class Locales(object):
    """
    Supports localisation through the application by utilising gettext to know
    which locale is in use, and get the "_" object for processing strings.
    """
    def __init__(self, force_locale=""):
        self.locale = force_locale
        self.locale_path = None
        self.translation = None
        self._ = None

        if not self.locale:
            self.locale = "en_GB"

    def init(self):
        """
        Initialises translations for the application.

        Returns:
            gettext.translation() bound to an i18n variable.
        """
        is_relative = os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "img"))

        if is_relative:
            # Use relative path (development or standalone build)
            self.locale_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "locale/"))
        else:
            # Use system path
            self.locale_path = "/usr/share/locale/"

        self.translation = gettext.translation("polychromatic", localedir=self.locale_path, fallback=True, languages=[self.locale])
        self._ = self.translation.gettext

        return self._

    def get_current_locale(self):
        """
        Returns a string describing the current locale. E.g. "de" or "en_US".
        """
        if self.translation and "language" in self.translation.info():
            return self.translation.info()["language"]

        # Fallback in use
        return "en_GB"
