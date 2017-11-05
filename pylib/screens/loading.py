#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017 Luke Horwell <luke@ubuntu-mate.org>
#

"""
Polychromatic Pages Module: Loading

User interface for showing the loading screens.
"""

from .. import common as Common
from time import sleep as sleep
import os
import sys

_ = Common.setup_translations(__file__, "polychromatic")
fade_speed = Common.fade_speed
fade_interval = Common.sleep_interval

class Loading(object):
    def __init__(self, controller, ui, pref, path, dbg):
        """
        Inputs:
        --> controller  Controller() object from main application.
        --> ui          UIControls() object from main application.
        --> pref        Preferences() object from common module.
        --> path        Paths() object from preferences module.
        """
        self.uid = "loading"
        self.webkit = controller.webkit
        self.update_page = controller.update_page
        self.pref = pref
        self.path = path
        self.ui = ui
        self.dbg = dbg

    def open_screen(self, params=[]):
        html = "<img id='loading-1' class='loading' src='../img/ui/loading-1.svg'/>"
        html += "<img id='loading-2' class='loading' src='../img/ui/loading-2.svg'/>"
        html += "<img id='loading-3' class='loading' src='../img/ui/loading-3.svg'/>"
        self.update_page("#content", "append", html)
        self.update_page("#content", "fadeIn", fade_speed)

    def close_screen(self, new_uid):
        self.update_page("#content", "fadeOut", fade_speed)
        sleep(fade_interval)

    def process_command(self, cmd):
        pass
