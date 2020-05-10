#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2020 Luke Horwell <code@horwell.me>
#
"""
This module is the 'controller' aspect of Polychromatic Controller.
"""

import os
import json
import glob
import gettext
import webbrowser
import shutil

from threading import Thread
from . import common
from . import locales
from . import preferences as pref
from .backends import middleman

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


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

    def parse_request(self, request, data):
        """
        Process a request sent from the frontend to the controller.
        """
        try:
            requests = {
                # General
                "open_uri": self._open_uri,
                "troubleshoot_openrazer": self._troubleshoot_openrazer,
                "add_custom_icon": self._add_custom_icon,
                "remove_custom_icon": self._remove_custom_icon,

                # Devices tab
                "update_device_list": self._update_device_list,
                "open_device": self._open_device,
                "apply_to_all": self._apply_to_all,
                "set_device_state": self._set_device_state,
                "debug_matrix": self._debug_matrix,
                "restart_backends": self._restart_backends,

                # Preferences tab
                "reload_preferences": self._reload_preferences,
                "set_preference": self._set_preference
            }
        except KeyError:
            dbg.stdout("Unknown Request: " + str(request) + " with data: " + str(data), dbg.error)
            self._internal_error("Internal Error", "<code>{0}</code> is not implemented.".format(request), "serious")
            return False

        try:
            thread = Thread(target=self._execute_request, args=(requests, request, data))
            thread.start()
        except Exception as e:
            dbg.stdout("Failed to execute request: " + str(request) + " with data: " + str(data), dbg.error)
            dbg.stdout(common.get_exception_as_string(e), dbg.error)
            traceback = common.get_exception_as_string(e)
            self._internal_error(locales.LOCALES["error_generic_title"], locales.LOCALES["error_generic_text"] + "<br><br><code>{0}</code>".format(traceback), "serious")

    def _execute_request(self, requests, request, data):
        """
        Actually execute the request (which happens in a different thread to
        prevent the UI from locking up)
        """
        return requests[request](data)

    def run_function(self, function, data={}):
        """
        When the Controller is ready to update the frontend, run a function
        and pass data.
        """
        self.webview.run_js("{0}({1});".format(function, json.dumps(data)))

    def initalise_app(self, version, versions, force_tab=None):
        """
        Starts loading the logic for the application.
        """
        self.version = version
        self.versions = versions
        dbg.stdout("Version " + version, dbg.debug, 1)

        # Append version information
        backend_versions = middleman.get_versions()
        for backend in backend_versions.keys():
            versions[backend] = backend_versions[backend]

        self.send_view_variable("LOCALES", locales.LOCALES)
        self.send_view_variable("COLOURS", pref.load_file(pref.path.colours))
        self.send_view_variable("PREFERENCES", pref.load_file(pref.path.preferences))
        self.send_view_variable("VERSION", versions)
        self.send_view_variable("BUTTON_SVGS", self._get_button_svg_list())
        self.send_view_variable("ICONS_TRAY", pref.load_file(common.get_data_dir_path() + "/ui/img/tray/icons.json"))
        self.send_view_variable("ICONS_EMBLEMS", pref.load_file(common.get_data_dir_path() + "/ui/img/emblems/icons.json"))
        self.send_view_variable("CUSTOM_ICONS", pref.get_custom_icons())
        self.send_view_variable("CUSTOM_ICON_PATH", pref.path.custom_icons)
        self.run_function("build_view")

        # View caches device list via the CACHE_DEVICES variable.
        dbg.stdout("Getting device list...", dbg.action, 1)
        devices = middleman.get_device_list()
        self.send_view_variable("CACHE_DEVICES", devices)

        if type(devices) == str:
            dbg.stdout("Backend Error. Exception: " + str(devices), dbg.error)
            self._internal_error(locales.LOCALES["error_not_ready_title"], locales.LOCALES["error_not_ready_text"] + "<code>{0}</code>".format(devices), "serious")

        else:
            dbg.stdout("Backend Ready", dbg.success, 1)
            self.send_view_variable("BACKEND_OPENRAZER", True);

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

        # Open landing tab
        try:
            landing_tab = pref.get("general", "landing_tab")
            if force_tab:
                landing_tab = force_tab

            fn = {
                "devices": "_set_tab_devices",
                "effects": "_set_tab_effects",
                "presets": "_set_tab_presets",
                "triggers": "_set_tab_triggers",
                "preferences": "_set_tab_preferences",
                "colours": "set_tab_colours",
                "troubleshoot": "open_troubleshooter_from_cli"
            }
            self.run_function(fn[landing_tab])
        except KeyError:
            self.run_function("_set_tab_devices")

        return True

    def _internal_error(self, title, reason, style):
        """
        Inform the user of event of a serious problem at the Controller layer.
        """
        self.webview.run_js("open_dialog(`{0}`, `{1}`, '{2}', [['OK', '']], '40em', '80em')".format(title, reason.replace("\n", "<br>"), style));

    def _get_button_svg_list(self):
        """
        Collects all SVGs and stores them into an array so the view can use them
        when building buttons with icons.

        Instead of an img tag, an svg tag allows manipulation of colours via CSS.
        """
        icons = glob.glob(common.get_data_dir_path() + "/ui/img/button/*.svg")
        output = {}
        for path in icons:
            name = path.split("/").pop().replace(".svg", "")
            with open(path, "r") as f:
                output[name] = "".join(f.readlines())
        return output

    def _update_device_list(self, data=None):
        """
        Sends an updated device list/integer to the controler.

        Data parameter:
        {
            "callback": <Name of JavaScript function to run>
        }
        """
        self.send_view_variable("CACHE_DEVICES", middleman.get_device_list())
        self.run_function(data["callback"])

    def _open_device(self, data):
        """
        Shows the details page for a specific device.

        Data parameter:
        {
            "backend": (str) <backend id>
            "uid": (int) <id in backend list>
        }
        """
        data = middleman.get_device(data["backend"], data["uid"])

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
            "value": <str: effect name>
                     <int: brightness value>
                     <str: colour hex>
        }
        """
        request_type = data["type"]
        request_value = data["value"]

        # Default values for effects
        effect_params = {
            "spectrum": None,
            "wave": 1,
            "reactive": 2,
            "breath_single": None,
            "static": None
        }

        for device in middleman.get_device_list():
            if device["available"] == False:
                continue

            details = middleman.get_device(device["backend"], device["uid"])

            for zone in details["zone_chroma"]:
                if request_type == "effect":
                    param = effect_params[request_value]
                    middleman.set_device_state(device["backend"], device["uid"], request_value, zone, None, [param])

                elif request_type == "brightness":
                    middleman.set_device_state(device["backend"], device["uid"], "brightness", zone, None, [request_value])

                elif request_type == "colour":
                    middleman.set_device_colours(device["backend"], device["uid"], zone, [request_value])

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
            "params": [<if applicable>] or empty: []
        }
        """
        uid = int(data["uid"])
        backend = data["backend"]
        backend_request = data["backend_request"]
        zone = data["zone"]
        colour_hex = data["colour_hex"]
        params = data["params"]

        dbg.stdout("Processing request '{2}' for {1} device {0}...".format(uid, backend, backend_request), dbg.action, 1)
        request = middleman.set_device_state(backend, uid, backend_request, zone, colour_hex, params)

        if request == None:
            # Device no longer available
            dbg.stdout("Device not found in backend", dbg.warning)
            self._internal_error(locales.LOCALES["error_device_gone_title"], locales.LOCALES["error_device_gone_text"], "warning")

        elif request == False:
            # Invalid request
            dbg.stdout("Invalid request.", dbg.warning)
            self._internal_error(locales.LOCALES["error_bad_request_title"], locales.LOCALES["error_bad_request_text"], "warning")

        elif type(request) == str:
            # Daemon exception
            self._internal_error(locales.LOCALES["error_backend_title"], locales.LOCALES["error_backend_text"] + "<pre>{0}</pre>".format(request), "serious")
            dbg.stdout(request, dbg.error)

        elif request == True:
            # Request OK
            dbg.stdout("Successfully executed request", dbg.success, 1)

    def _debug_matrix(self, data):
        """
        Allows the user to test custom effect functionality.

        Data parameter:
        {
            "uid": <id in backend> (string)
            "backend": <backend provider> (string)
            "position": [row, column] (list)
        }
        """
        uid = int(data["uid"])
        backend = data["backend"]
        row = data["position"][0]
        column = data["position"][1]

        request = middleman.debug_matrix(backend, uid, int(row), int(column))

        if request == None:
            # Device no longer available
            self._internal_error(locales.LOCALES["error_device_gone_title"], locales.LOCALES["error_device_gone_text"], "warning")

        elif type(request) == str:
            # Daemon exception
            self._internal_error(locales.LOCALES["error_backend_title"], locales.LOCALES["error_backend_text"] + "<pre>{0}</pre>".format(request), "serious")
            dbg.stdout(request, dbg.error)

        elif request == True:
            # Request OK
            dbg.stdout("OK: [{0},{1}]".format(row, column), dbg.success, 1)

    def _open_uri(self, data):
        """
        Opens a URI, which could be a file or URL.

        Data parameter:
        {
            "uri": <URL or file> (string)
        }
        """
        uri = data["uri"]
        if uri.startswith("http"):
            webbrowser.open(uri);
        elif uri.startswith("/"):
            os.system("xdg-open " + uri)
        else:
            dbg.stdout("Unknown handler for URI: " + uri, dbg.error)

    def _troubleshoot_openrazer(self, data):
        """
        Performs some self checks for common issues with OpenRazer.

        Data parameter is empty: {}
        """
        try:
            dbg.stdout("Running troubleshooter for OpenRazer...", dbg.warning, 1)
            results = middleman.troubleshoot()
            self.run_function("_show_troubleshoot_results", results)
            dbg.stdout("Troubleshooting finished.", dbg.success, 1)
        except Exception as e:
            dbg.stdout("Troubleshooting encountered an exception.", dbg.error, 1)
            exception = common.get_exception_as_string(e)
            dbg.stdout(exception, dbg.error, 1)
            self._internal_error(locales.LOCALES["troubleshoot"],
                locales.LOCALES["troubleshoot_cannot_run"] + "<br><pre>{0}</pre>".format(exception),
                "serious")

    def _reload_preferences(self, data):
        """
        Reloads the preferences from file to memory in case the file was changed
        on the file system.

        Data parameter:
        {
            "callback": <Name of JavaScript function to run>
        }
        """
        self.send_view_variable("PREFERENCES", pref.load_file(path.preferences))
        self.run_function(data["callback"])

    def _set_preference(self, data):
        """
        Writes a new value to preferences.json

        Data parameter:
        {
            "group": (string)
            "item": (string)
            "value": (str, int or bool)
        }
        """
        group = data["group"]
        item = data["item"]
        value = data["value"]

        if type(value) == str and len(value) == 0:
            dbg.stdout("Refusing to write empty preference: '{0}' -> '{1}'!".format(group, item), dbg.error)
            return False

        dbg.stdout("Writing preference: '{0}' -> '{1}' to '{2}".format(group, item, str(value)), dbg.action, 1)
        pref.set(group, item, value)

    def _add_custom_icon(self, data):
        """
        Shows a file selection dialogue to import a new icon.

        Upon successful selection, this will copy the specified image to
        ~/.config/custom_icons, intended to prevent broken links.

        Data parameter is empty: {}
        """
        win = Gtk.Window(title=locales.LOCALES["add_graphic"])
        dialog = Gtk.FileChooserDialog(locales.LOCALES["add_graphic"], \
                    win, \
                    Gtk.FileChooserAction.OPEN, \
                    (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        # Filters
        a = Gtk.FileFilter()
        a.set_name(locales.LOCALES["filter_all_images"])
        a.add_mime_type("image/jpeg")
        a.add_mime_type("image/png")
        a.add_mime_type("image/gif")
        a.add_mime_type("image/webp")
        a.add_mime_type("image/svg+xml")
        dialog.add_filter(a)

        p = Gtk.FileFilter()
        p.set_name(locales.LOCALES["filter_png"])
        p.add_mime_type("image/png")
        dialog.add_filter(p)

        j = Gtk.FileFilter()
        j.set_name(locales.LOCALES["filter_jpg"])
        j.add_mime_type("image/jpeg")
        dialog.add_filter(j)

        g = Gtk.FileFilter()
        g.set_name(locales.LOCALES["filter_gif"])
        g.add_mime_type("image/gif")
        dialog.add_filter(g)

        w = Gtk.FileFilter()
        w.set_name(locales.LOCALES["filter_webp"])
        w.add_mime_type("image/webp")
        dialog.add_filter(g)

        s = Gtk.FileFilter()
        s.set_name(locales.LOCALES["filter_svg"])
        s.add_mime_type("image/svg+xml")
        dialog.add_filter(s)

        a2 = Gtk.FileFilter()
        a2.set_name(locales.LOCALES["filter_all_types"])
        a2.add_pattern("*")
        dialog.add_filter(a2)

        dbg.stdout("Opening GTK file dialog.", dbg.debug, 1)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            dbg.stdout("GTK file response OK: " + filename, dbg.success, 1)
        else:
            dialog.destroy()
            dbg.stdout("GTK file response cancelled.", dbg.warning, 1)
            return None

        path_src = filename
        path_dst = os.path.join(pref.path.custom_icons, os.path.basename(path_src))

        if not os.path.exists(path_src):
            dbg.stdout("Cannot add non-existant custom icon: " + path_src, dbg.error)
            self._internal_error(locales.LOCALES["file_error_title"], locales.LOCALES["file_error_missing"], "warning")
            return False

        shutil.copyfile(path_src, path_dst)
        self.send_view_variable("CUSTOM_ICONS", pref.get_custom_icons())
        dbg.stdout("Added custom icon: " + path_dst, dbg.success, 1)
        self.run_function("_custom_icons_changed", {});
        return True

    def _remove_custom_icon(self, data):
        """
        Deletes a custom image from the config's "custom_icons" folder.

        Data parameter:
        {
            "filename": (string)
        }

        """
        path = os.path.join(pref.path.custom_icons, data["filename"])

        if not os.path.exists(path):
            dbg.stdout("Custom icon non-existant: " + path, dbg.error)
            self._internal_error(locales.LOCALES["file_error_title"], locales.LOCALES["file_error_missing"], "warning")
            return False

        os.remove(path)
        dbg.stdout("Deleted custom icon: " + path, dbg.action, 1)
        self.send_view_variable("CUSTOM_ICONS", pref.get_custom_icons())
        self.run_function("_custom_icons_changed", {});
        return True

    def _restart_backends(self, data):
        """
        Force all compatible backends to restart their daemon processes (if applicable).
        """
        middleman.restart_backends()
        self.run_function("close_dialog", {})
        self.run_function("set_tab_devices", {})


# Module Initalization
dbg = common.Debugging()
path = pref.Paths()
_ = common.setup_translations(__file__, "polychromatic")
