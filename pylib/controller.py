#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2019 Luke Horwell <code@horwell.me>
#
"""
This module is the 'controller' aspect of Polychromatic Controller.
"""

import os
import json
import gettext
from threading import Thread
from . import common
from . import locales
from . import preferences as pref
from .backends import openrazer


class PolychromaticController():
    """
    Functions for Polychromatic's GUI operations.
    """
    def __init__(self, _app, _window, _webview, _debug):
        # Required for program operation
        global dbg
        dbg = _debug

        self.window = _window
        self.webview = _webview
        self.send_view_data = _app.send_view_data
        self.send_view_variable = _app.send_view_variable

        # Set later in initalise_app()
        self.version = None
        self.versions = None
        self.backends = {
            "openrazer": False
        }

    def run_function(self, function, data):
        """
        Runs a requested Python function passing a Python dictionary consisting
        of its data.
        """
        self.webview.run_js("{0}({1});".format(function, json.dumps(data)))

    def initalise_app(self, version, versions):
        """
        Starts loading the logic for the application.
        """
        self.version = version
        self.versions = versions
        dbg.stdout("Version " + version, dbg.debug, 1)

        self.send_view_variable("LOCALES", locales.LOCALES)
        self.run_function("build_view", {})

        dbg.stdout("OpenRazer: Getting device list...", dbg.debug, 1)
        devices = openrazer.get_device_list()

        if devices == -1:
            dbg.stdout("OpenRazer: Daemon not running", dbg.warning)

        elif type(devices) == str:
            dbg.stdout("OpenRazer: Daemon encountered exception: " + str(devices), dbg.warning)

        else:
            # Daemon OK
            self.backends["openrazer"] = True


        dbg.stdout("Application Ready.", dbg.success, 1)
        self.window.show_window()


# Module Initalization
dbg = common.Debugging()
path = pref.Paths()
_ = common.setup_translations(__file__, "polychromatic")
