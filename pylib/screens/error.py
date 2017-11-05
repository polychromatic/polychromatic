#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017 Luke Horwell <luke@ubuntu-mate.org>
#

"""
Polychromatic Pages Module: Error

The screen for when serious errors that stop us dead in our tracks.
"""

from .. import common as Common
from time import sleep as sleep
import os
import sys

_ = Common.setup_translations(__file__, "polychromatic")
fade_speed = Common.fade_speed
fade_interval = Common.sleep_interval

class Error(object):
    def __init__(self, controller, ui, pref, path, dbg):
        """
        Inputs:
        --> controller  Controller() object from main application.
        --> ui          UIControls() object from main application.
        --> pref        Preferences() object from common module.
        --> path        Paths() object from preferences module.
        """
        self.uid = "error"
        self.webkit = controller.webkit
        self.update_page = controller.update_page
        self.pref = pref
        self.path = path
        self.ui = ui
        self.dbg = dbg

    def open_screen(self, params=[]):
        """
        params[0]   int     Error Code
        params[1]   str     State
        params[2]   str     Filename of error image (e.g. generic.png)
        params[3]   str     Title
        params[4]   str     Message
        """
        error_code = params[0]
        state = params[1]
        image_filename = params[2]
        title = params[3]
        message = params[4]
        try:
            traceback = params[5]
        except Exception:
            traceback = None

        self.update_page("#header", "fadeOut", fade_speed)
        self.update_page("#content", "fadeOut", fade_speed)
        self.update_page("#footer", "fadeOut", fade_speed)
        sleep(fade_interval)

        html = "<div id='error-page'>"
        html += "<img id='error-icon' src='../img/error/{0}'/>".format(image_filename)
        html += "<h2 id='error-title' class='{0}'>{1}</h2>".format(state, title)
        html += "<p id='error-details'>{0}</p>".format(message)
        if traceback:
            html += "<div id='error-traceback'>"
            html += "<h5>{0}</h5>".format(_("Exception Details:"))
            html += "<pre id='error-traceback'>{0}</pre>".format(traceback.replace("\n", "<br>"))
            html += "</div>"
        html += "</div>"

        self.update_page("#content", "html", html)
        self.update_page("#content", "fadeIn", fade_speed)
        self.update_page("#footer", "fadeIn", fade_speed)
        self.update_page("#footer-right", "append", self.ui.print_button(_("Close Program"), "quit", "quit"))
        self.update_page("#footer-left", "append", self.ui.print_button(_("Restart Daemon"), "restart-daemon", "restart-daemon"))
        self.update_page("#footer-right", "append", self.ui.print_button(_("Reload"), "reload", "reload"))
        sleep(fade_interval + 0.5)
        self.update_page("#error-page", "append", "<p id='error-code' hidden>{0}</p>".format(_("Support Code:") + " " + str(error_code)))
        self.update_page("#error-code", "fadeIn", fade_speed)

    def close_screen(self, new_uid):
        self.update_page("#content", "fadeOut", fade_speed)
        sleep(fade_interval)

    def process_command(self, cmd):
        pass
