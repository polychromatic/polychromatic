# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
"""
This module controls the 'Triggers' tab of the Controller GUI.
"""

from .. import common
from .. import effects
from .. import locales
from .. import preferences as pref
from . import shared

from PyQt5.QtWidgets import QWidget, QPushButton, QToolButton, QMessageBox, QListWidget, QTreeWidget, QLabel, QComboBox

class TriggersTab(shared.TabData):
    """
    Allows the user to quickly change the existing state of the device right now.
    """
    def __init__(self, appdata):
        super().__init__(appdata)

    def set_tab(self):
        """
        Triggers tab opened.
        """
        print("stub: TriggersTab.set_tab")
