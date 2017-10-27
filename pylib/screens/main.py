#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017 Luke Horwell <luke@ubuntu-mate.org>
#

"""
Polychromatic Pages Module: Menu

Contains the base UI for managing the application.
"""

from .. import common as Common
from time import sleep as sleep
import os
import sys

_ = Common.setup_translations(__file__, "polychromatic")
fade_speed = Common.fade_speed
fade_interval = Common.sleep_interval

class MainMenu(object):
    def __init__(self, controller, ui, pref, path, dbg):
        """
        Inputs:
        --> controller  Controller() object from main application.
        --> ui          UIControls() object from main application.
        --> pref        Preferences() object from common module.
        --> path        Paths() object from preferences module.
        """
        self.uid = "mainmenu"
        self.webkit = controller.webkit
        self.update_page = controller.update_page
        self.pref = pref
        self.path = path
        self.ui = ui
        self.dbg = dbg

    def open_screen(self, params=[]):
        """
        params[0]   int     Tab number
                                0 = Devices
                                1 = Profiles
                                2 = Preferences
        params[1]   int     Sidebar number
                                --> Devices
                                    >0  = Based on order of daemon device list
                                --> Profiles
                                    0   = New profile...
                                    1   = Import profile...
                                    >2  = Based on order of profile list
                                --> Preferences
                                    0   = About
                                    1   = General
                                    2   = Tray Applet
                                    3   = Colours
                                    4   = Daemon Status
        """
        active_tab = params[0]
        active_sidebar = params[1]

        # Tabs
        self.dbg.stdout("Opening tab: " + str(active_tab), self.dbg.action, 2)
        html = self.ui.print_tab(0, "states/keyboard.svg", _("Devices"), ("active" if active_tab == 0 else ""))
        html += self.ui.print_tab(1, "ui/profile-default.svg", _("Profiles"), ("active" if active_tab == 1 else ""))
        html += self.ui.print_tab(2, "ui/controller.svg", _("Preferences"), "tab-right " + ("active" if active_tab == 2 else ""))
        self.update_page("#tabs", "html", html)
        self.update_page("#tabs", "fadeIn", fade_speed)

        # Header
        header_titles = {
            0: _("Devices"),
            1: _("Profiles"),
            2: _("Preferences")
        }
        self.update_page("#header", "html", "<h3 id='page-title' hidden>{0}</h3>".format(header_titles[active_tab]))
        self.update_page("#header h3", "fadeIn", fade_speed)

        # Sidebar

        # Tabs contents, depending which one is being opened.
        html = "<div id='sidebar'>"
        html += self.ui.print_sidebar_item(0, "states/keyboard.svg", _("Devices"), ("active" if active_tab == 0 else ""))
        html += "</div>"
        # 0 = Devices
        # 1 = Profiles
        # 2 = Preferences

    def close_screen(self, params=[]):
        pass

    def process_command(self, cmd):
        if cmd.startswith("switch-tab?"):
            tab_no = int(cmd.split("?")[1])
            self.open_screen([tab_no, 0])
            return True
        elif cmd.startswith("switch-sidebar?"):
            tab_no = int(cmd.split("?")[1])
            subpage_no = int(cmd.split("?")[2])
            self.open_screen([tab_no, subpage_no])
            return True
        return False
