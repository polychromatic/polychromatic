#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017 Luke Horwell <luke@ubuntu-mate.org>
#

"""
Polychromatic Pages Module: Menu

The tabbed UI for the main application.
"""

from ... import common as common
from time import sleep as sleep
import os
import sys

from . import preferences as subpage_preferences
from . import devices as subpage_devices
from . import profiles as subpage_profiles

_ = common.setup_translations(__file__, "polychromatic")
fade_speed = common.fade_speed
fade_interval = common.sleep_interval

subpages = {
#   UUID: [<has sidebar?>, <label>, <module for printing>]
    0: [_("Devices"), subpage_devices],
    1: [_("Profiles"), subpage_profiles],
    2: [_("Preferences"), subpage_preferences]
}

active_tab = -1
active_sidebar = -1

class MainScreen(object):
    def __init__(self, controller, ui, pref, path, dbg):
        """
        Inputs:
        --> controller  Controller() object from main application.
        --> ui          UIControls() object from main application.
        --> pref        Preferences() object from common module.
        --> path        Paths() object from preferences module.
        """
        self.uid = "mainscreen"
        self.webkit = controller.webkit
        self.update_page = controller.update_page
        self.controller = controller
        self.pref = pref
        self.path = path
        self.ui = ui
        self.dbg = dbg

        # Remember the last tab
        self.current_tab_no = -1

    def open_screen(self, params=[]):
        """
        params[0]   int     Tab number
                                0 = Devices
                                1 = Profiles
                                2 = Preferences
        params[1]   int     Sidebar number
                                Defers depending on subpage - see its module.
        """
        global active_tab
        global active_sidebar
        active_tab = params[0]
        active_sidebar = params[1]

        self.dbg.stdout("Opening tab: {0} (sidebar item {1})".format(str(active_tab), str(active_sidebar)), self.dbg.action, 2)

        # Tabs
        html_tab = self.ui.print_tab(0, "states/keyboard.svg", _("Devices"), ("active" if active_tab == 0 else ""))
        html_tab += self.ui.print_tab(1, "ui/profile-default.svg", _("Profiles"), ("active" if active_tab == 1 else ""))
        html_tab += self.ui.print_tab(2, "ui/controller.svg", _("Preferences"), "tab-right " + ("active" if active_tab == 2 else ""))
        self.update_page("#tabs", "html", html_tab)
        self.update_page("#tabs", "fadeIn", fade_speed)

        # Header
        if not self.current_tab_no == active_tab:
            self.update_page("#header", "html", "<h3 id='page-title' hidden>{0}</h3>".format(subpages[active_tab][0]))
            self.update_page("#header h3", "fadeIn", fade_speed)

        # Sidebar
        html_sidebar = "<div id='sidebar'>"
        html_sidebar += subpages[active_tab][1].print_sidebar(self, active_sidebar)
        html_sidebar += "</div>"

        # Contents of page
        html_content = "<div id='sidebar-page'>"
        html_content += subpages[active_tab][1].print_contents(self, active_sidebar)
        html_content += "</div>"

        # Footer - same for all subpages
        html_footer = self.ui.print_button(_("Close Application"), "close-app", "quit")
        if not self.current_tab_no == active_tab:
            self.update_page("#footer-left", "html", "")
            self.update_page("#footer-right", "hide")
            self.update_page("#footer-right", "fadeIn", fade_speed)
            self.update_page("#footer-right", "html", html_footer)

        # Ready to display
        self.update_page("#content", "html", html_sidebar + html_content)
        self.update_page("#content", "addClass", "has-tabs")
        self.update_page("#content", "addClass", "has-sidebar")
        self.update_page("#sidebar-page", "hide")
        self.update_page("#sidebar-page", "fadeIn", fade_speed)
        self.update_page("#content", "fadeIn", fade_speed)
        self.current_tab_no = active_tab

    def close_screen(self, new_uid):
        self.update_page("#content", "removeClass", "has-tabs")
        self.update_page("#content", "removeClass", "has-sidebar")

    def process_command(self, cmd):
        """
        Process a command specific to this page or active subpage.
        """
        if cmd.startswith("switch-tab?"):
            tab_no = int(cmd.split("?")[1])
            self.update_page("#content", "hide")
            self.open_screen([tab_no, 0])
            return True

        elif cmd.startswith("switch-sidebar?"):
            subpage_no = int(cmd.split("?")[1])
            self.open_screen([self.current_tab_no, subpage_no])
            return True

        elif subpages[active_tab][1].process_command(self, cmd):
            return True

        else:
            return False
