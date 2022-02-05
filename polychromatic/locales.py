# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2022 Luke Horwell <code@horwell.me>
"""
Contains the UI localization for Polychromatic. Powered by GNU's gettext.
"""
import os
import gettext


class Locales(object):
    """
    Supports localisation throughout the application by utilising gettext.
    The "_" object is used for processing strings.
    """
    def __init__(self, force_locale=""):
        self.force_locale = force_locale
        self.locale = force_locale
        self.translation = None
        self._ = None

    def init(self):
        """
        Initialises translations for the application.

        Returns:
            gettext.translation() bound to an i18n variable.
        """
        is_relative = os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "img"))
        relative_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "locale/"))

        # For development or a standalone "opt" build
        if is_relative and self.force_locale:
            self.translation = gettext.translation("polychromatic", localedir=relative_path, fallback=True, languages=[self.locale])
        elif is_relative:
            self.translation = gettext.translation("polychromatic", localedir=relative_path, fallback=True)

        # For packaged/system-wide installs
        elif not is_relative and self.force_locale:
            self.translation = gettext.translation("polychromatic", fallback=True, languages=[self.locale])
        else:
            self.translation = gettext.translation("polychromatic", fallback=True)

        self._ = self.translation.gettext
        return self._

    def get_current_locale(self):
        """
        Returns a string describing the current locale. E.g. "de" or "en_US".
        """
        if self.translation and "language" in self.translation.info():
            return self.translation.info()["language"]

        # Fallback to default
        return "en_GB"
