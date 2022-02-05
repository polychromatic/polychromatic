# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2021-2022 Luke Horwell <code@horwell.me>
"""
Variables and functions for essential operation of the application.
All interfaces and most classes will inherit these.
"""
from .locales import Locales
from .middleman import Middleman

from .paths import Paths as Paths
from . import common as common_class
from . import preferences as preferences_class

import os


class PolychromaticBase(object):
    """
    Essential variables/functions for minimum functionality of the application.
    """
    # Should the process restart later
    exec_path = ""
    exec_args = []

    # Localization
    i18n = Locales()
    _ = i18n.init()

    # Storage
    paths = Paths()

    # TODO: Refactor later
    common = common_class
    common.paths = paths
    dbg = common.Debugging()
    pref = preferences_class
    pref.path = paths
    pref.init(_)
    preferences = pref.load_file(paths.preferences)

    # Devices
    middleman = Middleman()

    # Functions
    @classmethod
    def init_base(self, path, args):
        """
        Finish populating variables. Run this after initializing the class.
        """
        PolychromaticBase.exec_path = path
        PolychromaticBase.exec_args = args
        PolychromaticBase.middleman._base = self

    @classmethod
    def reinit_locales(self, locale):
        PolychromaticBase.i18n = Locales(locale)
        PolychromaticBase._ = self.i18n.init()
