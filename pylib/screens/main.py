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
        self.controller = controller
        self.pref = pref
        self.path = path
        self.ui = ui
        self.dbg = dbg

        self.current_tab_no = -1

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

        self.dbg.stdout("Opening tab: {0} (sidebar item {1})".format(str(active_tab), str(active_sidebar)), self.dbg.action, 2)

        # Tabs
        html_tab = self.ui.print_tab(0, "states/keyboard.svg", _("Devices"), ("active" if active_tab == 0 else ""))
        html_tab += self.ui.print_tab(1, "ui/profile-default.svg", _("Profiles"), ("active" if active_tab == 1 else ""))
        html_tab += self.ui.print_tab(2, "ui/controller.svg", _("Preferences"), "tab-right " + ("active" if active_tab == 2 else ""))
        self.update_page("#tabs", "html", html_tab)
        self.update_page("#tabs", "fadeIn", fade_speed)

        subpages = {
        #   UUID: [<has sidebar?>, <label>, <function for printing>]
            0: [_("Devices"), self._print_tab_content_devices],
            1: [_("Profiles"), self._print_tab_content_profiles],
            2: [_("Preferences"), self._print_tab_content_preferences]
        }

        # Header
        if not self.current_tab_no == active_tab:
            self.update_page("#header", "html", "<h3 id='page-title' hidden>{0}</h3>".format(subpages[active_tab][0]))
            self.update_page("#header h3", "fadeIn", fade_speed)

        # Sidebar (if this page has one)
        html_sidebar = "<div id='sidebar'>"
        if active_sidebar == 0:
            # List of devices
            html_sidebar += self.ui.print_sidebar_item(0, "states/keyboard.svg", _("Devices"), ("active" if active_sidebar == 0 else ""))

        elif active_sidebar == 1:
            # List of profile options
            pass

        elif active_sidebar == 2:
            # Categories for preferences
            pass

        html_sidebar += "</div>"

        # Tabs contents, depending which one is being opened.
        html_content = "<div id='sidebar-page'>"
        html_content += subpages[active_tab][1](active_sidebar)
        html_content += "</div>"

        # Ready to display
        self.update_page("#content", "html", html_sidebar + html_content)
        self.update_page("#content", "addClass", "has-tabs")
        self.update_page("#content", "addClass", "has-sidebar")
        self.update_page("#content", "fadeIn", fade_speed)
        self.current_tab_no = active_tab

    def close_screen(self, new_uid):
        self.update_page("#content", "removeClass", "has-tabs")
        self.update_page("#content", "removeClass", "has-sidebar")

    def process_command(self, cmd):
        if cmd.startswith("switch-tab?"):
            tab_no = int(cmd.split("?")[1])
            self.update_page("#content", "hide")
            self.open_screen([tab_no, 0])
            return True
        elif cmd.startswith("switch-sidebar?"):
            subpage_no = int(cmd.split("?")[1])
            self.open_screen([self.current_tab_no, subpage_no])
            return True
        return False

    def _print_tab_content_devices(self, active_sidebar):
        return "dev"

    def _print_tab_content_profiles(self, active_sidebar):
        return "prof"

    def _print_tab_content_preferences(self, active_sidebar):
        return "pref"
