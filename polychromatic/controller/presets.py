# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
"""
This module controls the 'Presets' tab of the Controller GUI.
"""

from .. import common
from .. import effects
from .. import locales
from .. import preferences as pref
from . import shared

from PyQt5.QtWidgets import QWidget, QPushButton, QToolButton, QMessageBox, \
                            QListWidget, QTreeWidget, QLabel, QComboBox


class PresetsTab(shared.TabData):
    """
    Configure individual "presets" that specify the behaviour/lighting of all
    peripherals at once. Useful for games and applications.
    """
    def __init__(self, appdata):
        super().__init__(appdata)
        self.feature = "presets"
        self.tab_title = self._("Presets")

    def set_tab(self):
        """
        Presets tab opened.
        """
        print("stub: PresetsTab.set_tab")
