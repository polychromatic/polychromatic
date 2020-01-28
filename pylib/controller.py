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
import glob
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

    def parse_request(self, request, data):
        """
        Process a request sent from the frontend to the controller.
        """
        try:
            requests = {
                "update_device_list": self._update_device_list,
                "open_device": self._open_device,
                "apply_to_all": self._apply_to_all,
                "set_device_state": self._set_device_state
            }
            requests[request](data)
        except KeyError:
            dbg.stdout("Unknown Request: " + str(request) + " with data: " + str(data), dbg.error)
            self._internal_error("Internal Error", "<code>{0}</code> is not implemented.".format(request), "serious")

    def run_function(self, function, data={}):
        """
        When the Controller is ready to update the frontend, run a function
        and pass data.
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
        self.run_function("build_view")

        # View caches device list via the DEVICES variable.
        dbg.stdout("OpenRazer: Getting device list...", dbg.action, 1)
        devices = openrazer.get_device_list()
        self.send_view_variable("DEVICES", devices)

        if devices == -1:
            dbg.stdout("OpenRazer: Daemon not running", dbg.error)

        elif type(devices) == str:
            dbg.stdout("OpenRazer: Error! Exception: " + str(devices), dbg.error)

        else:
            # Daemon OK
            dbg.stdout("OpenRazer: Ready", dbg.success, 1)
            self.send_view_variable("OPENRAZER_READY", True);
            self.backends["openrazer"] = True

        # Warn if configuration is compatible for this version.
        pref_data = pref.load_file(path.preferences)
        pref_version = pref.version
        save_version = pref_data["config_version"]
        if save_version > pref_version:
            self.run_function("_warn_save_data_version", {
                "app_version": version,
                "pref_version": pref_version,
                "save_version": save_version
            })

        dbg.stdout("Application Ready. Showing window.", dbg.success, 1)
        self.window.show_window()

        self.run_function("_set_tab_devices")
        return True

    def _internal_error(self, title, reason, style):
        """
        Inform the user of event of a serious problem at the Controller layer.
        """
        self.webview.run_js("open_dialog('{0}', '{1}', '{2}', [['OK', '']], '40em', '80em')".format(title, reason.replace("\n", "<br>"), style));

    def _update_device_list(self, data=None):
        """
        Sends an updated device list/integer to the controler.

        Data parameter:
        {
            "callback": <Name of JavaScript function to run>
        }
        """
        self.send_view_variable("DEVICES", openrazer.get_device_list())
        self.run_function(data["callback"])

    def _open_device(self, data):
        """
        Shows the details page for a specific device.

        Data parameter:
        {
            "uid": <id in Razer list>
        }
        """
        data = openrazer.get_device(data["uid"])

        if data == None:
            # Device no longer avaiable (-1)
            self.run_function("open_device_overview")
        elif data == str:
            # Daemon exception (-2)
            self.run_function("_open_device_error", {"code": -2, "exception": data})
        else:
            # OK
            self.run_function("_open_device", data)

    def _apply_to_all(self, data):
        """
        Sets all compatible devices to a specific state.

        Data parameter:
        {
            "type": <str: "string" or "brightness">,
            "value": <str: effect name> OR <int: brightness value>
        }
        """
        request_type = data["type"]
        request_value = data["value"]

        # Default values for effects
        effect_params = {
            "spectrum": None,
            "wave": 1,
            "reactive": 2,
            "breath_random": None,
            "static": None
        }

        for device in openrazer.get_device_list():
            for zone in device["zones"]:
                if request_type == "effect":
                    param = effect_params[request_value]
                    openrazer.set_device_state(device["uid"], request_value, zone, None, [param])
                elif request_type == "brightness":
                    openrazer.set_device_state(device["uid"], "brightness", zone, None, [request_value])

    def _set_device_state(self, data):
        """
        Sets the state of a specific device right now.

        Data parameter:
        {
            "uid": <id in backend>
            "backend": <backend provider>
            "backend_request": <string, e.g. 'wave', 'brightness', 'dpi'>
            "zone": <zone name>
            "colour_hex": [<string of primary hex value>, <second hex>, etc]
            "params": [<if applicable>]
        }
        """
        uid = int(data["uid"])
        backend = data["backend"]
        backend_request = data["backend_request"]
        zone = data["zone"]
        colour_hex = data["colour_hex"]
        params = data["params"]

        dbg.stdout("Processing request '{2}' for device {0} in backend '{1}'...".format(uid, backend, backend_request), dbg.action, 1)
        request = openrazer.set_device_state(uid, backend_request, zone, colour_hex, params)

        if request == None:
            # Device no longer available
            dbg.stdout("Device not found in backend", dbg.warning)
            self._internal_error(locales.LOCALES["error_device_gone_title"], locales.LOCALES["error_device_gone_text"], "warning")

        elif request == False:
            # Invalid request
            dbg.stdout("Invalid request.", dbg.warning)
            self._internal_error(locales.LOCALES["error_bad_request_title"], locales.LOCALES["error_bad_request_text"], "serious")

        elif type(request) == str:
            # Daemon exception
            self._internal_error(locales.LOCALES["error_backend_title"], locales.LOCALES["error_backend_text"] + "<pre>{0}</pre>".format(request), "serious")
            dbg.stdout(request, dbg.error)

        elif request == True:
            # Request OK
            dbg.stdout("Successfully executed request", dbg.success, 1)


# Module Initalization
dbg = common.Debugging()
path = pref.Paths()
_ = common.setup_translations(__file__, "polychromatic")
