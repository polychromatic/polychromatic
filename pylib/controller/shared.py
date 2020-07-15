#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module contains widgets shared across the Controller GUI.
"""

from .. import common
from .. import locales
from .. import preferences as pref

import os
from PyQt5.QtCore import QThread, QRunnable, QThreadPool, pyqtSlot
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QFontDatabase
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QToolButton, QMessageBox, QListWidget

def load_qt_theme(app, qapp, main_window):
    """
    Apply the Polychromatic Qt theme for the main window if enabled by the user.

    Params:
        app             ApplicationData() object
        qapp            QApplication() object
        main_window     QMainWindow() object
    """
    if app.system_qt_theme:
        return

    # Load "Play" font
    QFontDatabase.addApplicationFont(os.path.join(app.data_path, "qt", "fonts", "Play_regular.ttf"))
    font = QFont("Play", 10, 1)
    qapp.setFont(font)
    main_window.menuBar.setFont(font)
    main_window.findChild(QWidget, "MainTabCustom").setFont(font)

    # Load basic colour palettes
    ui_palette = QPalette()
    black = QColor(0, 0, 0)
    white = QColor(255, 255, 255)
    primary = QColor(0, 255, 0)
    secondary = QColor(0, 128, 0)
    ui_palette.setColor(QPalette.Window, QColor(0, 0, 0))
    ui_palette.setColor(QPalette.WindowText, white)
    ui_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    ui_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    ui_palette.setColor(QPalette.ToolTipBase, white)
    ui_palette.setColor(QPalette.ToolTipText, white)
    ui_palette.setColor(QPalette.Text, white)
    ui_palette.setColor(QPalette.Button, QColor(50, 50, 50)) #323232
    ui_palette.setColor(QPalette.ButtonText, white)
    ui_palette.setColor(QPalette.Link, primary)
    ui_palette.setColor(QPalette.Highlight, secondary)
    ui_palette.setColor(QPalette.HighlightedText, white)
    main_window.setPalette(ui_palette)

    # Load QSS (essentially CSS) with Polychromatic's design
    with open(os.path.join(app.data_path, "qt", "style.qss"), "r") as f:
        main_window.setStyleSheet(f.read().replace("[data]", app.data_path))
