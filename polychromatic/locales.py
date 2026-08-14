# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2024 Luke Horwell <code@horwell.me>
"""
Contains the UI localization for Polychromatic. Powered by GNU's gettext.
"""
import gettext
import os


class Locales(object):
    """
    Supports localisation throughout the application by utilising gettext.
    The "_" object is used for processing strings.
    """
    locale_dirs = [
        "/usr/local/share/locale",
        "/usr/share/locale",
        "/app/share/locale",
    ]

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
        languages = [self.locale] if self.force_locale else None

        self.translation = gettext.translation("polychromatic",
                                               localedir=self.get_locale_path(languages),
                                               languages=languages,
                                               fallback=True)

        self._ = self.translation.gettext
        return self._

    def get_locale_path(self, languages=None):
        """
        Returns the directory holding the message catalogues, or None to leave
        gettext to its own default.

        For packaged installs, gettext derives its default from the Python
        interpreter's prefix, which is only the application's prefix when the
        two are installed together. Inside a Flatpak they are not: the
        application is under /app while the interpreter comes from the runtime's
        /usr, so every translation goes unused unless the directory is named.
        """
        module_path = __file__

        # For development or a standalone "opt" build
        if os.path.exists(os.path.join(os.path.dirname(module_path), "../data/img/")):
            return os.path.abspath(os.path.join(os.path.dirname(module_path), "../locale/"))

        # For packaged/system-wide installs
        for directory in self.locale_dirs:
            if gettext.find("polychromatic", directory, languages):
                return directory

        return None

    def get_current_locale(self):
        """
        Returns a string describing the current locale. E.g. "de" or "en_US".
        """
        if self.translation and "language" in self.translation.info():
            return self.translation.info()["language"]

        # Fallback to default
        return "en_GB"
