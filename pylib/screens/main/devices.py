#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2018 Luke Horwell <luke@ubuntu-mate.org>
#

"""
Polychromatic Pages Module: Devices (subpage of main)

Contains options and views to see the current state of devices
and change their states as-is.
"""

from ... import common as common
from time import sleep as sleep
import os
import sys

_ = common.setup_translations(__file__, "polychromatic")
fade_speed = common.fade_speed
fade_interval = common.sleep_interval

def print_sidebar(self, active_sidebar):
    html_sidebar = ""
    return html_sidebar


def print_contents(self, active_sidebar):
    subpages = {
        0: _print_main_tab
    }

    try:
        return subpages[active_sidebar](self)
    except Exception as e:
        self.dbg.stdout("Failed to populate content!", self.dbg.error)
        self.dbg.stdout("Exception: " + str(e), self.dbg.error)

    return ""


def process_command(self, cmd):
    """
    Process a command specific to this subpage.
    """

    return False


def _print_main_tab(self):
    return ""
