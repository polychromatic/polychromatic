#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module controls the 'Effects' tab of the Controller GUI.
"""

from .. import common
from .. import effects
from .. import locales
from .. import preferences as pref

from PyQt5.QtWidgets import QWidget, QPushButton, QToolButton, QMessageBox, QListWidget, QTreeWidget, QLabel, QComboBox

class EffectsTab(object):
    """
    Allows the user to quickly change the existing state of the device right now.
    """
    def __init__(self, appdata):
        self.appdata = appdata

    def set_tab(self):
        """
        Device tab opened.
        """
        w = self.appdata.main_window

        print("stub: EffectsTab.set_tab")
