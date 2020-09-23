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
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QFontDatabase, QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenuBar, \
                            QWidget, QMessageBox, QGridLayout, \
                            QLabel, QPushButton, QToolButton, QGroupBox, \
                            QListWidget, QHBoxLayout, QSizePolicy, QSpacerItem, \
                            QDialog

def load_qt_theme(app, qapp, window):
    """
    Apply the Polychromatic Qt theme for the main window if enabled by the user.

    Params:
        app             ApplicationData() object
        qapp            QApplication() object
        window          QMainWindow() or QDialog() object
    """
    if app.system_qt_theme:
        return

    # Load "Play" font
    QFontDatabase.addApplicationFont(os.path.join(app.data_path, "qt", "fonts", "Play_regular.ttf"))
    font = QFont("Play", 10, 1)
    qapp.setFont(font)

    menu_bar = window.findChild(QMenuBar, "menuBar")
    if menu_bar:
        menu_bar.setFont(font)

    custom_tabs = window.findChild(QWidget, "MainTabCustom")
    if custom_tabs:
        custom_tabs.setFont(font)

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
    window.setPalette(ui_palette)

    # Load QSS (essentially CSS) with Polychromatic's design
    with open(os.path.join(app.data_path, "qt", "style.qss"), "r") as f:
        window.setStyleSheet(f.read().replace("[data]", app.data_path))


def get_ui_widget(appdata, name, q_toplevel=QWidget):
    """
    Returns a QWidget object for the specified .ui file.

    Params:
        appdata         ApplicationData() object
        name            Name of UI file (in ui/ folder) without .ui extension
        q_toplevel      Top-level object class, e.g. QWidget() or QDialog()
    """
    ui_file = os.path.join(appdata.data_path, "qt", name + ".ui")
    if not os.path.exists(ui_file):
        print("Missing UI file: " + ui_file)
        return None

    widget = uic.loadUi(ui_file, q_toplevel())

    # TODO: Process i18n strings

    # If a dialog, apply the styles
    if q_toplevel == QDialog:
        load_qt_theme(appdata, appdata.main_app, widget)

    return widget


def clear_layout(layout):
    """
    Removes all Qt elements inside a layout.
    """
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


class PolychromaticWidgets(object):
    """
    Code for building some of the common UI elements of the Controller application.
    """
    def __init__(self, appdata):
        """
        Stores the ApplicationData() object for reference later.
        """
        self.appdata = appdata

        # Dialogues types
        self.dialog_generic = QMessageBox.Information
        self.dialog_error = QMessageBox.Critical
        self.dialog_warning = QMessageBox.Warning

    def create_summary_widget(self, icon_path, title, indicators=[], buttons=[]):
        """
        Returns a summary widget presenting an overview of the selected device,
        effect or preset.

        Params:
            icon_path           (str)   Absolute path to the icon to use.
            icon_path_fallback  (str)   Absolute path when icon cannot be found.
            title               (str)   Summary title, e.g. device or effect name
            indicators          (list)  See indicators below.
            buttons             (list)  See buttons below.

        Indicators list:
        [
            {
                "icon": (str)       (Absolute path)
                "label": (str)
            },
            {..}
        ]

        Buttons list:
        [
            {
                "id": (str)
                "icon": (str)
                "label": (str)
                "disabled": (bool)
                "action": (obj)     (Function to run when clicked)
            },
            {..}
        ]

        Returns: QWidget()
        """
        summary = get_ui_widget(self.appdata, "widget-summary")
        image_widget = summary.findChild(QLabel, "SummaryImage")
        title_widget = summary.findChild(QLabel, "SummaryTitle")
        indicators_widget = summary.findChild(QWidget, "SummaryIcons")
        buttons_widget = summary.findChild(QWidget, "SummaryButtons")

        title_widget.setText(title)
        title_widget.setStyleSheet("QLabel { color: lime }")

        # Populate Image
        if os.path.exists(icon_path):
            # Make sure it fits dimensions
            pixmap_src = QPixmap(icon_path)
            pixmap = pixmap_src.scaled(115, 115, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_widget.setPixmap(pixmap)
            #image_widget.resize(pixmap.width(), pixmap.height())
        else:
            image_widget.deleteLater()

        # Populate Indicators
        for indicator in indicators:
            widget = QWidget()
            widget.setLayout(QHBoxLayout())
            layout = widget.layout()
            layout.setContentsMargins(0,0,10,0)

            # Create image
            if indicator["icon"]:
                label = QLabel()
                pixmap_src = QPixmap(indicator["icon"])
                pixmap = pixmap_src.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
                label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                layout.addWidget(label)

            # Create text
            label = QLabel()
            label.setText(indicator["label"])
            layout.addWidget(label)

            indicators_widget.layout().addWidget(widget)
        indicators_widget.layout().addStretch()

        # Populate Buttons
        for btn in buttons:
            button = QPushButton()
            button.setObjectName(btn["id"])
            if btn["icon"] and os.path.exists(btn["icon"]):
                button.setIcon(btn["icon"])
            button.setText(btn["label"])

            if btn["disabled"]:
                button.setDisabled(True)

            button.clicked.connect(btn["action"])
            buttons_widget.layout().addWidget(button)
        buttons_widget.layout().addStretch()

        return summary

    def create_group_widget(self, title):
        """
        Returns a group widget containing controls for a specific device zone.

        Params:
            title           (str)   Group title

        Returns: QGroupBox()
        """
        group = QGroupBox()
        group.setTitle(title)
        #group.setFont(QFont("Play", 11))
        group.setLayout(QGridLayout())
        group.layout().setAlignment(Qt.AlignTop)
        return group

    def create_row_widget(self, label_text, widgets=[]):
        """
        Returns a widget for use when presenting controls for a particular option.

        Params:
            label_text      (str)   Human readable control label
            widgets         (list)  List of widgets to display

        Returns: QWidget()
        """
        widget = QWidget()
        widget.setLayout(QHBoxLayout())
        layout = widget.layout()

        # Add the label (left)
        label = QLabel()
        label.setText(label_text)
        layout.addWidget(label)
        layout.addStretch()

        # Add the elements on the right
        for w in widgets:
            layout.addWidget(w)
        layout.addStretch()
        return widget

    def populate_empty_state(self, layout, icon_path, title, subtitle, buttons=[]):
        """
        Creates a 'watermark' like background when a page or section is empty.
        For example, this may be used when the device list is empty.

        Params:
            layout          QWidget     QWidget() to apply the layout on. Should be empty.
            icon_path       (str)       Path to the background graphic. Should be 750x500.
            title           (str)       Larger text to display.
            subtitle        (str)       Smaller text to display.
            buttons         (list)      (Optional) In format: [{icon, label, action}, {..}]

        Returns nothing - the layout is directly applied.
        """
        # Center graphic
        image = QLabel()
        pixmap_src = QPixmap(icon_path)
        pixmap = pixmap_src.scaled(750 / 2, 500 / 2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image.setPixmap(pixmap)
        image.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        image.setAlignment(Qt.AlignCenter)

        # Text & buttons
        text1 = QLabel()
        text1.setFont(QFont("Play", 14))
        text1.setAlignment(Qt.AlignCenter)
        text1.setText(title)
        text1.setMargin(10)

        text2 = QLabel()
        text2.setFont(QFont("Play", 11))
        text2.setAlignment(Qt.AlignCenter)
        text2.setText(subtitle)
        text2.setMargin(10)
        text2.setWordWrap(True)

        button_container = None
        if buttons:
            button_container = QWidget()
            button_container.setLayout(QHBoxLayout())
            button_container.layout().addStretch()
            for spec in buttons:
                button = QPushButton()
                button.setText(spec["label"])
                button.setIcon(QIcon(spec["icon"]))
                button.clicked.connect(spec["action"])
                button_container.layout().addWidget(button)
            button_container.layout().addStretch()

        # Putting it together
        layout.addStretch()
        for widget in [image, text1, text2, button_container]:
            if widget:
                layout.addWidget(widget)
        layout.addStretch()

    def open_colour_picker(self, callback_fn):
        """
        Spawns a colour picker dialog for the user to choose a saved colour.

        When a colour is saved, the callback_fn will be executed passing the new
        hex colour as a parameter.

        Params:
            appdata         ApplicationData() object
            callback_fn     Function to run after saving changes
        """
        print("stub:open_colour_picker")
        pass

    def open_icon_picker(self, callback_fn):
        """
        Spawns a icon picker dialog for the user to choose or manage their saved
        icon list.

        When an icon is saved, the callback_fn will be executed passing the relative
        (or built-in) or absolute (for custom images) path as a parameter for the
        function to save.

        Params:
            appdata         ApplicationData() object
            callback_fn     Function to run after saving changes
        """
        print("stub:open_icon_picker")
        pass

    def open_dialog(self, dialog_type, title, text, info_text="", traceback="", buttons=[], default_button=None, actions={}):
        """
        Opens a modal dialogue box to inform of a situation.

        If no functions are passed to the 'ok', 'cancel', etc functions, then the
        dialog will just show a message and then close with no further action.

        Params:
            dialog_type     (str)   One of self.dialog_* variable above.
            title           (str)   Window title
            text            (str)   Description of what happened.
            info_text       (str)   (Optional) Informative text of next steps.
            traceback       (str)   (Optional) More details of the problem
            buttons         (list)  (Optional) QMessageBox.* buttons to display
            default_button  (obj)   (Optional) QMessageBox.* button to default to.
            actions         (dict)  (Optional) Functions to run after dismissing.
                                    E.g. {QMessageBox.Ok = name_of_function, ...}
        """
        msgbox = QMessageBox()
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        msgbox.setIcon(dialog_type)
        load_qt_theme(self.appdata, self.appdata.main_app, msgbox)

        if info_text:
            msgbox.setInformativeText(info_text);

        for button in buttons:
            msgbox.addButton(button)

        if default_button:
            msgbox.setDefaultButton(default_button)

        if not buttons:
            msgbox.addButton(QMessageBox.Ok)
            msgbox.setDefaultButton(QMessageBox.Ok)

        if traceback:
            msgbox.setDetailedText(traceback)
            msgbox.setStyleSheet("QTextEdit { font-family: monospace; }");

        def _dialog_closed(result):
            for action in actions.keys():
                if result == action:
                    actions[action]()

        msgbox.finished.connect(_dialog_closed)
        msgbox.exec()

