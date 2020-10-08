#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module controls the 'Presets' tab of the Controller GUI.
"""

from .. import common
from .. import effects
from .. import locales
from .. import preferences as pref
from . import shared

from PyQt5.QtWidgets import QWidget, QPushButton, QToolButton, QMessageBox, QListWidget, QTreeWidget, QLabel, QComboBox

class PresetsTab(shared.TabData):
    """
    Allows the user to quickly change the existing state of the device right now.
    """
    def __init__(self, appdata):
        super().__init__(appdata)

    def set_tab(self):
        """
        Presets tab opened.
        """
        print("stub: PresetsTab.set_tab")
