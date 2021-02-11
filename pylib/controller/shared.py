#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2021 Luke Horwell <code@horwell.me>
#
"""
This module contains widgets shared across the Controller GUI.
"""

from .. import common
from .. import locales
from .. import preferences as pref
from .. import procpid
from .. import fileman

from ..qt.flowlayout import FlowLayout as QFlowLayout

import os
import glob
import shutil

from PyQt5 import uic, QtSvg
from PyQt5.QtCore import Qt, QSize, QMargins
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QPixmap, QMovie
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenuBar, \
                            QWidget, QMessageBox, QGridLayout, \
                            QLabel, QPushButton, QToolButton, QGroupBox, \
                            QListWidget, QHBoxLayout, QVBoxLayout, QFormLayout, \
                            QSizePolicy, QSpacerItem, QDialog, QColorDialog, \
                            QDialogButtonBox, QTreeWidget, QTreeWidgetItem, \
                            QLineEdit, QTextEdit, QTabWidget, QScrollArea, \
                            QButtonGroup, QFileDialog, QMenu, QAction, \
                            QDockWidget, QCheckBox, QSpinBox, QComboBox, \
                            QTreeWidget, QDoubleSpinBox, QRadioButton


def load_qt_theme(appdata, window):
    """
    Apply the Polychromatic Qt theme for the main window if enabled by the user.

    Params:
        appdata         ApplicationData() object
        window          QMainWindow() or QDialog() object
    """
    if appdata.system_qt_theme:
        return

    # Load "Play" font
    font = QFont("Play", 10, 0)
    window.setFont(font)

    menu_bar = window.findChild(QMenuBar)
    if menu_bar:
        menu_bar.setFont(font)

    custom_tabs = window.findChild(QWidget, "MainTabCustom")
    if custom_tabs:
        custom_tabs.setFont(font)

    # Load basic colour palettes
    window.setPalette(get_palette(appdata))

    # Load QSS (essentially CSS) with Polychromatic's design
    with open(os.path.join(common.paths.data_dir, "qt", "style.qss"), "r") as f:
        window.setStyleSheet(f.read().replace("[data]", common.paths.data_dir))


def get_palette(app):
    """
    Returns a QPalette with Polychromatic's colours.
    """
    palette = QPalette()
    black = QColor(0, 0, 0)
    white = QColor(255, 255, 255)
    primary = QColor(0, 255, 0)
    secondary = QColor(0, 128, 0)
    palette.setColor(QPalette.Window, QColor(0, 0, 0))
    palette.setColor(QPalette.WindowText, white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, white)
    palette.setColor(QPalette.ToolTipText, white)
    palette.setColor(QPalette.Text, white)
    palette.setColor(QPalette.Button, QColor(50, 50, 50))
    palette.setColor(QPalette.ButtonText, white)
    palette.setColor(QPalette.Link, primary)
    palette.setColor(QPalette.Highlight, secondary)
    palette.setColor(QPalette.HighlightedText, white)
    return palette


def get_ui_widget(appdata, name, q_toplevel=QWidget):
    """
    Returns a QWidget object for the specified .ui file.

    Params:
        appdata         ApplicationData() object
        name            Name of UI file (in ui/ folder) without .ui extension
        q_toplevel      Top-level object class, e.g. QWidget() or QDialog()
    """
    ui_file = os.path.join(appdata.paths.data_dir, "qt", name + ".ui")
    if not os.path.exists(ui_file):
        print("Missing UI file: " + ui_file)
        return None

    widget = uic.loadUi(ui_file, q_toplevel())

    # Apply the styles for dialogs/windows
    if q_toplevel in [QDialog, QMainWindow]:
        load_qt_theme(appdata, widget)

    # Process i18n strings for existing widgets
    translate_ui(appdata, widget)

    return widget


def translate_ui(appdata, widget):
    """
    Iterates over all the translatable widgets from the newly loaded .ui file
    and use gettext to apply the localized strings.
    """
    if appdata.locales._get_current_locale() == "en_GB":
        return

    for widget_type in [QLabel, QMenu, QAction, QPushButton, QToolButton, \
                        QTabWidget, QTreeWidgetItem, QDockWidget, QTreeWidget, \
                        QCheckBox, QRadioButton, QSpinBox, QDoubleSpinBox, \
                        QComboBox]:
        children = widget.findChildren(widget_type)
        for subwidget in children:
            _translate_widget(appdata, subwidget)

    _ = appdata._

    if type(widget) == QDialog:
        widget.setWindowTitle(_(widget.windowTitle()))


def _translate_widget(appdata, widget):
    """
    Translates the strings of a widget that was loaded on-the-fly via uic.loadUi
    """
    _ = appdata._

    if type(widget) == QMenu:
        widget.setTitle(_(widget.title()))
        return

    if type(widget) == QDockWidget:
        widget.setWindowTitle(_(widget.windowTitle()))
        return

    if type(widget) == QSpinBox or type(widget) == QDoubleSpinBox:
        widget.setPrefix(_(widget.prefix()))
        widget.setSuffix(_(widget.suffix()))
        return

    if type(widget) == QTabWidget:
        for index in range(0, widget.count()):
            widget.setTabText(index, _(widget.tabText(0)))
            widget.setTabToolTip(index, _(widget.tabToolTip(0)))
        return

    if type(widget) == QComboBox:
        for index in range(0, widget.count()):
            widget.setItemText(index, _(widget.itemText(0)))
        return

    if type(widget) == QTreeWidget:
        tree_root = widget.invisibleRootItem()
        for index in range(0, tree_root.childCount()):
            item = tree_root.child(index)
            item.setText(0, _(item.text(0)))

            if index in range(0, item.childCount()):
                child = item.child(index)
                child.setText(0, _(child.text(0)))
        return

    if type(widget) == QAction:
        widget.setStatusTip(_(widget.statusTip()))

    if type(widget) == QWidget:
        return

    widget.setText(_(widget.text()))
    widget.setToolTip(_(widget.toolTip()))


def clear_layout(layout):
    """
    Removes all Qt elements inside a layout.
    """
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


def set_pixmap_for_label(qlabel, icon_path, icon_size=24):
    """
    Creates a pixmap for a label maintaining its aspect ratio and size.

    This only applies to QLabel() objects. Buttons and other UI elements use QIcon().

    Params:
        qlabel      (obj)   QLabel() object
        icon_path   (str)   Absolute path to icon
        icon_size   (int)   Dimensions to scale
    """
    pixmap_src = QPixmap(icon_path)
    pixmap = pixmap_src.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    qlabel.setPixmap(pixmap)
    qlabel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)


class TabData(object):
    """
    This parent class is inherited by all tab objects storing common variables.
    """
    def __init__(self, appdata):
        self.appdata = appdata
        self.widgets = PolychromaticWidgets(appdata)
        self.locales = appdata.locales
        self.dbg = appdata.dbg
        self.paths = appdata.paths
        self._ = appdata._
        self.middleman = appdata.middleman
        self.main_window = appdata.main_window
        self.menubar = appdata.menubar

    def set_tab(self):
        """
        Called when the tab is opened via the user interface. Each deriving class
        must implement this.
        """
        raise NotImplementedError

    def set_cursor_normal(self):
        self.main_window.unsetCursor()

    def set_cursor_busy(self):
        self.main_window.setCursor(Qt.BusyCursor)


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

    def get_icon_qt(self, folder, name):
        """
        Returns a QIcon() object with the specified button image.

        Params:
            folder          For common.get_icon()
            name            For common.get_icon()
        """
        icons = common.get_icon_styles(self.appdata.dbg, folder, name, self.appdata.normal_colour, self.appdata.disabled_colour, self.appdata.active_colour, self.appdata.selected_colour, self.appdata.secondary_colour_active, self.appdata.secondary_colour_inactive)
        if not icons:
            return QIcon()

        qicon = QIcon(icons[0])
        qicon.addFile(icons[1], mode=QIcon.Disabled)
        qicon.addFile(icons[2], mode=QIcon.Active)
        qicon.addFile(icons[2], mode=QIcon.Active, state=QIcon.On)
        qicon.addFile(icons[3], mode=QIcon.Selected)
        qicon.addFile(icons[3], mode=QIcon.Selected, state=QIcon.On)
        return qicon

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
                "icon": (QIcon)
                "label": (str)
                "disabled": (bool)
                "action": (obj)     (Function to run when clicked)
            },
            {..}
        ]

        Returns: QWidget()
        """
        summary = get_ui_widget(self.appdata, "widget-summary")
        container_widget = summary.findChild(QWidget, "SummaryContainer")
        image_widget = summary.findChild(QLabel, "SummaryImage")
        title_widget = summary.findChild(QLabel, "SummaryTitle")
        indicators_widget = summary.findChild(QWidget, "SummaryIcons")
        buttons_widget = summary.findChild(QWidget, "SummaryButtons")

        title_widget.setText(title)
        title_widget.setStyleSheet("QLabel { color: lime; font-size: 17px; }")

        # Populate Image
        if os.path.exists(icon_path):
            if icon_path.endswith(".svg"):
                # Replace summary icon with SVG renderer for better quality/scaling
                if icon_path.endswith(".svg"):
                    summary.findChild(QLabel, "SummaryImage").deleteLater()
                    viewer = QSvgWidget()
                    viewer.load(icon_path)
                    viewer.setMinimumHeight(90)
                    viewer.setMinimumWidth(90)
                    viewer.setMaximumHeight(90)
                    viewer.setMaximumWidth(90)
                    summary.setContentsMargins(8 + 6, 8, 8, 8)

                    # Appends to the end - restructure
                    summary.layout().addWidget(viewer)
                    summary.layout().addWidget(container_widget)
                    summary.layout().addWidget(buttons_widget)
                    viewer.show()
            else:
                set_pixmap_for_label(image_widget, icon_path, 115)
        else:
            image_widget.deleteLater()

        # Populate Indicators
        for indicator in indicators:
            widget = QWidget()
            widget.setLayout(QHBoxLayout())
            layout = widget.layout()
            layout.setContentsMargins(0, 0, 10, 0)

            # Create image
            if indicator["icon"]:
                label = QLabel()
                set_pixmap_for_label(label, indicator["icon"], 22)
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
            if btn["icon"]:
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
        group.setLayout(QGridLayout())
        group.layout().setAlignment(Qt.AlignTop)
        return group

    def create_row_widget(self, label_text, widgets=[], vertical=False, wrap=False):
        """
        Returns a widget for use when presenting controls for a particular option.

        Params:
            label_text      (str)   Human readable control label
            widgets         (list)  List of widgets to display
            vertical        (bool)  Use a vertical layout instead of horizontal
            wrap            (bool)  Wrap widgets when they get too long (horizontal only)

        Returns: QWidget()
        """
        widget = QWidget()
        widget.setLayout(QHBoxLayout() if wrap else QFormLayout())
        layout = widget.layout()
        layout.setContentsMargins(QMargins(30, 5, 30, 5))

        # Left - Add label
        label = QLabel()
        label.setText(label_text)
        label.setAlignment(Qt.AlignTop)
        label.setMinimumWidth(150)
        label.setMaximumWidth(150)

        # Right - Add controls
        inner_widget = QWidget()
        if wrap:
            inner_widget.setLayout(QFlowLayout())
        else:
            inner_widget.setLayout(QVBoxLayout() if vertical else QHBoxLayout())

        inner_widget.layout().setContentsMargins(0, 0, 0, 0)
        for w in widgets:
            inner_widget.layout().addWidget(w)

        if wrap:
            layout.addWidget(label)
            layout.addWidget(inner_widget)
        else:
            layout.addRow(label, inner_widget)

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
            buttons         (list)      (Optional) In format: [{icon_folder, icon_name, label, action}, {..}]

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
                button.setIcon(self.get_icon_qt(spec["icon_folder"], spec["icon_name"]))
                button.clicked.connect(spec["action"])
                button_container.layout().addWidget(button)
            button_container.layout().addStretch()

        # Putting it together
        layout.addStretch()
        for widget in [image, text1, text2, button_container]:
            if widget:
                layout.addWidget(widget)
        layout.addStretch()

    def create_colour_control(self, current_hex, callback_fn, callback_data, title, monoscale=False):
        """
        Create a colour picker control for the user to set a colour. Setting
        the colour will open a dialog.

        When a colour is saved, the callback_fn will be executed passing the new
        hex colour as a parameter as well as callback_data (as one variable)

        Params:
            current_hex     String of the current hex value in use.
            callback_fn     Function to run after saving changes.
            callback_data   Additional data to pass to callback_fn.
            title           Title to show when colour is being picked.
            monoscale       Picker should only show green only colours.
        """
        container = QWidget()
        container.setLayout(QHBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)
        preview = QWidget(objectName="PickerPreview")
        preview.setMinimumHeight(28)
        preview.setMaximumHeight(28)
        preview.setMinimumWidth(80)
        preview.setMaximumWidth(80)
        preview.setStyleSheet("QWidget {{ background-color: {0} }}".format(current_hex))

        btn = QPushButton(objectName="PickerCustom")
        btn.setText(self.appdata._("Change..."))
        btn.current_hex = current_hex

        # Dynamic function allows changing the initial colour upon opening the picker later.
        def _change_colour(new_hex):
            btn.current_hex = new_hex
            preview.setStyleSheet("QWidget {{ background-color: {0} }}".format(new_hex))
        btn.change_colour = _change_colour

        # Connect the signal
        def _clicked_change_colour():
            picker = ColourPicker(self.appdata, callback_fn, callback_data, btn.current_hex, title, monoscale, preview)
        btn.clicked.connect(_clicked_change_colour)

        # Put it all together
        container.layout().addWidget(preview)
        container.layout().addWidget(btn)
        container.layout().addStretch()
        return container

    def create_icon_picker_control(self, callback_fn, current_icon, title, purpose=0):
        """
        Create an icon picker control for the user to choose an icon from a list
        of built-in icons, user-imported icons ("custom icons") or an application
        installed on the file system.

        When an icon is saved, the callback_fn will be executed returning the
        relative path (for a built-in icon) or an absolute path (for custom images)
        as a parameter for the function that will process the new selection.

        Params:
            callback_fn     Function to run after saving changes
            current_icon    Initial icon
            title           Window title
            purpose         IconPicker.purpose_* integer.
        """
        container = QWidget()
        container.setLayout(QHBoxLayout())
        container.layout().setContentsMargins(0, 0, 0, 0)

        preview = QLabel()
        preview.setMaximumHeight(24)
        preview.setMaximumWidth(24)
        preview.current_icon = current_icon
        set_pixmap_for_label(preview, common.get_full_path_for_save_data_icon(preview.current_icon), 24)

        # TODO: Improve icon quality on HiDPI displays

        def _changed_icon_callback(new_icon):
            set_pixmap_for_label(preview, common.get_full_path_for_save_data_icon(new_icon), 24)
            callback_fn(new_icon)
            preview.current_icon = new_icon

        def _clicked_change_icon():
            picker = IconPicker(self.appdata, _changed_icon_callback, preview.current_icon, title, purpose)

        btn = QPushButton()
        btn.setText(self.appdata._("Change..."))
        btn.clicked.connect(_clicked_change_icon)

        container.layout().addWidget(preview)
        container.layout().addWidget(btn)
        container.layout().addStretch()
        return container

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

        if not self.appdata.system_qt_theme:
            msgbox.setPalette(get_palette(self.appdata))
            load_qt_theme(self.appdata, msgbox)

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
            msgbox.findChild(QTextEdit).setMinimumWidth(600)

        def _dialog_closed(result):
            for action in actions.keys():
                if result == action:
                    actions[action]()

        # TODO: Use own icons for dialog (when Polychromatic Qt theme is used)

        msgbox.finished.connect(_dialog_closed)
        msgbox.exec()


class ColourPicker(object):
    """
    The colour picker dialog allows the user to quickly choose a colour or
    hand over to the system's colour picker (which on Linux, would be Qt's native picker)
    """
    def __init__(self, appdata, callback_fn, callback_data, current_hex, title, monoscale, preview):
        """
        Params:
            appdata         (obj)   ApplicationData() object
            callback_fn     (obj)   Run this function after saving new colour. The parameters are (new_hex, callback_data)
            callback_data   (any)   Additional data to pass to callback_fn
            current_hex     (str)   Starting colour value (#RRGGBB)
            title           (str)   Window title
            monoscale       (bool)  Only show green shades (for monochromatic devices)
            preview         (obj)   QWidget() of the preview box
        """
        self.appdata = appdata
        self.widgets = PolychromaticWidgets(appdata)
        self.current_hex = current_hex
        self.current_name = ""
        self.callback_fn = callback_fn
        self.callback_data = callback_data
        self.title = title
        self.saved_colours = pref.load_file(appdata.paths.colours)
        self.monoscale = monoscale
        self.preview = preview

        # UI Controls
        self.dialog = get_ui_widget(appdata, "colour-picker", q_toplevel=QDialog)
        self.dialog_btns = self.dialog.findChild(QDialogButtonBox, "buttonBox")
        self.change_btn = self.dialog.findChild(QPushButton, "OpenPicker")
        self.list_save_btn = self.dialog.findChild(QPushButton, "SaveToList")
        self.list_del_btn = self.dialog.findChild(QPushButton, "DeleteFromList")
        self.list_text_input = self.dialog.findChild(QLineEdit, "ColourName")
        self.save_widget = self.dialog.findChild(QWidget, "SaveWidget")
        self.save_widget.setHidden(True)
        self.open_save_widget = self.dialog.findChild(QPushButton, "OpenSaveWidget")
        self.close_save_widget = self.dialog.findChild(QPushButton, "CloseSaveWidget")
        self.saved_tree = self.dialog.findChild(QTreeWidget, "SavedColours")
        self.current_preview = self.dialog.findChild(QWidget, "CurrentPreview")
        self.current_label = self.dialog.findChild(QLabel, "CurrentLabel")

        # Set Dialog Button Icons
        if not self.appdata.system_qt_theme:
            self.change_btn.setIcon(self.widgets.get_icon_qt("general", "edit"))
            self.open_save_widget.setIcon(self.widgets.get_icon_qt("general", "new"))
            self.close_save_widget.setIcon(self.widgets.get_icon_qt("general", "close"))
            self.list_save_btn.setIcon(self.widgets.get_icon_qt("general", "save"))
            self.list_del_btn.setIcon(self.widgets.get_icon_qt("general", "delete"))
            self.dialog_btns.button(QDialogButtonBox.Save).setIcon(self.widgets.get_icon_qt("general", "save"))
            self.dialog_btns.button(QDialogButtonBox.Cancel).setIcon(self.widgets.get_icon_qt("general", "cancel"))

        # If the device only supports a monoscale of "RGB", use a fixed list.
        if monoscale:
            self.list_del_btn.setDisabled(True)
            self.open_save_widget.setDisabled(True)
            self.open_save_widget.setHidden(True)
            self.dialog.findChild(QWidget, "SavedColoursVList").setHidden(True)
            self.saved_colours = common.get_green_shades(self.appdata._)

        # Connect signals when interacting with UI controls
        self.dialog_btns.accepted.connect(self._apply_colour)
        self.change_btn.clicked.connect(self._open_system_picker)
        self.open_save_widget.clicked.connect(self._open_save_widget)
        self.close_save_widget.clicked.connect(self._close_save_widget)
        self.list_text_input.textEdited.connect(self._on_save_input_change)
        self.list_text_input.returnPressed.connect(self._save_to_list)
        self.list_save_btn.clicked.connect(self._save_to_list)
        self.list_del_btn.clicked.connect(self._delete_from_list)
        self.saved_tree.itemSelectionChanged.connect(self._switch_colour)

        # Refresh UI data and open dialog
        self._build_saved_colour_list()
        self._refresh_selected_colour(current_hex)
        self.saved_tree.setColumnWidth(0, 140)
        self.dialog.setWindowTitle(title)
        self.dialog.exec()

    def _switch_colour(self):
        """
        User selects a colour from their selected colour list.
        """
        items = self.saved_tree.selectedItems()
        if items:
            self._refresh_selected_colour(items[0].colour_hex)

    def _add_to_tree(self, name, value):
        """
        Appends an item to the tree.
        """
        item = QTreeWidgetItem()
        item.setText(0, name)
        item.setText(1, value.upper())
        item.setIcon(0, QIcon(common.generate_colour_bitmap(self.appdata.dbg, value, "16x16")))
        item.colour_name = name
        item.colour_hex = value.upper()
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
        self.saved_tree.addTopLevelItem(item)
        return item

    def _get_tree_objects(self):
        root = self.saved_tree.invisibleRootItem()
        items = []
        for i in range(root.childCount()):
            items.append(root.child(i))
        return items

    def _refresh_selected_colour(self, new_hex):
        """
        Refresh the UI to show the newly chosen colour.
        """
        self.current_hex = new_hex
        self.current_preview.setStyleSheet("QWidget {{ background-color: {0} }}".format(new_hex))
        self.current_label.setText("{0}\n({1})".format(new_hex.upper(), ", ".join(map(str, common.hex_to_rgb(new_hex)))))

        self.list_text_input.setText("")
        self.open_save_widget.setDisabled(False)
        self.list_del_btn.setDisabled(True)

        for widget in self._get_tree_objects():
            if widget.colour_hex == new_hex:
                widget.setSelected(True)
                self.current_name = widget.colour_name
                self.save_widget.setHidden(True)
                self.open_save_widget.setDisabled(True)
                self.list_del_btn.setDisabled(False)
                return

        self.saved_tree.clearSelection()

    def _apply_colour(self):
        """
        User applies their newly chosen colour. Saves the colour list to file if
        there are new colours or the order was modified.
        """
        dbg = self.appdata.dbg
        self._save_colour_list_to_file()
        self.preview.setStyleSheet("QWidget {{ background-color: {0} }}".format(self.current_hex))
        dbg.stdout("Colour set to: " + self.current_hex, dbg.success, 1)
        self.callback_fn(self.current_hex, self.callback_data)

    def _save_colour_list_to_file(self):
        """
        Saves the colour list to file.
        """
        # When pre-defined monochromatic colours are used, never save!
        if self.monoscale:
            return

        # TODO: Optimisation: Only save if there are changes (add/remove/reorder)
        dbg = self.appdata.dbg
        dbg.stdout("Saving colour list...", dbg.action, 1)
        colour_list = []
        for item in self._get_tree_objects():
            colour_list.append({
                "name": item.colour_name,
                "hex": item.colour_hex
            })
        pref.save_file(self.appdata.paths.colours, colour_list)

        # Reload the tray applet to use new colour list
        process = procpid.ProcessManager("tray-applet")
        if process.is_another_instance_is_running():
            dbg.stdout("Colour list saved. Reloading tray applet...", dbg.action, 1)
            process.reload()

    def _open_system_picker(self):
        """
        User uses the system's colour picker to pick any colour, which could
        include the ability to choose a pixel on the screen (dependent on OS)
        """
        dialog = QColorDialog()

        # TODO: Nice to have: Use Polychromatic styling for the dialog
        # QColorDialog() is private, so this may be tricky.
        # This does not work!
        load_qt_theme(self.appdata, dialog)

        output = dialog.getColor(title=self.title, initial=QColor(self.current_hex))

        if not output.isValid():
            return
        new_hex = output.name()

        # Strip R/B out of RGB if device is monochromatic
        if self.monoscale:
            as_rgb = common.hex_to_rgb(new_hex)
            new_hex = common.rgb_to_hex([0, as_rgb[1], 0])

        self._refresh_selected_colour(new_hex)

    def _open_save_widget(self):
        self.save_widget.setHidden(False)
        self.open_save_widget.setDisabled(True)

    def _close_save_widget(self):
        self.save_widget.setHidden(True)
        self.open_save_widget.setDisabled(False)

    def _on_save_input_change(self, text):
        self.list_save_btn.setEnabled(True if len(text) > 0 else False)

    def _save_to_list(self):
        """
        Save the colour to their Saved Colour list.
        """
        new_name = self.list_text_input.text()
        new_hex = self.current_hex
        item = self._add_to_tree(new_name, new_hex)
        item.setSelected(True)
        self._close_save_widget()

    def _delete_from_list(self):
        """
        Delete the selected item from the Saved Colour list.
        """
        try:
            item = self.saved_tree.selectedItems()[0]
            self.saved_tree.invisibleRootItem().removeChild(item)
        except IndexError:
            # UI Hiccup - clicked too fast, last item in list, etc
            self.list_del_btn.setDisabled(True)

    def _build_saved_colour_list(self):
        """
        Builds the initial saved colour list.
        """
        self.saved_tree.invisibleRootItem().takeChildren()

        for index, colour in enumerate(self.saved_colours):
            item = self._add_to_tree(colour["name"], colour["hex"])
            if self.current_hex == item.colour_hex:
                item.setSelected(True)
                if index > 5:
                    self.saved_tree.scrollToItem(item)


class IconPicker(object):
    """
    The icon picker dialog allows the user to choose an icon for an effect,
    preset or tray applet.

    For convenience, installed applications and Steam games will be listed as
    icon sources (except for the tray applet)
    """
    purpose_generic = 0
    purpose_tray_icon_only = 1

    def __init__(self, appdata, callback_fn, current_icon, title, purpose=0):
        """
        Params:
            appdata         (obj)   ApplicationData() object
            callback_fn     (obj)   Run this function after saving new colour. The result will be passed as a parameter.
            current_icon    (str)   Initial icon path (usually relative)
            title           (str)   Window title
            purpose         (bool)  One of the IconPicker.* integers to specify intended behaviour.
        """
        self.appdata = appdata
        self._ = appdata._
        self.dbg = appdata.dbg
        self.widgets = PolychromaticWidgets(appdata)
        self.current_icon = current_icon
        self.callback_fn = callback_fn
        self.title = title
        self.purpose = purpose
        self.custom_icon_exts = ["svg", "png", "jpg", "jpeg", "gif"]
        self.custom_icon_filters = [
            self._("Image Files") + "(*.png *.jpg *.jpeg *.gif *.svg)",
            self._("PNG Image") + " (*.png)",
            self._("JPEG Image") + " (*.jpg *.jpeg)",
            self._("GIF Image") + " (*.gif)",
            self._("SVG Image") + " (*.svg)",
            self._("All Files") + " (*)"
        ]

        # UI Controls
        self.dialog = get_ui_widget(appdata, "icon-picker", q_toplevel=QDialog)
        self.dialog_btns = self.dialog.findChild(QDialogButtonBox, "buttonBox")
        self.tabs = self.dialog.findChild(QTabWidget, "IconTabs")
        self.custom_icon_toolbar = self.dialog.findChild(QWidget, "CustomIconToolbar")
        self.custom_icon_add = self.dialog.findChild(QPushButton, "ImportCustomIcon")
        self.custom_icon_del = self.dialog.findChild(QPushButton, "DeleteCustomIcon")
        self.gif_warning = self.dialog.findChild(QWidget, "AnimatedGIFWarningLabel")
        self.button_group = QButtonGroup()
        self.gif_previews = []

        # Tab contents for housing the icons
        self.icons_tray = self.dialog.findChild(QWidget, "TraySet")
        self.icons_emblems = self.dialog.findChild(QWidget, "EmblemSet")
        self.icons_apps = self.dialog.findChild(QWidget, "ApplicationSet")
        self.icons_steam = self.dialog.findChild(QWidget, "SteamSet")
        self.icons_custom = self.dialog.findChild(QWidget, "CustomSet")
        self.tab_index_widgets = {
            0: self.icons_tray,
            1: self.icons_emblems,
            2: self.icons_apps,
            3: self.icons_steam,
            4: self.icons_custom
        }

        # Set Dialog Button Icons
        if not self.appdata.system_qt_theme:
            self.custom_icon_add.setIcon(self.widgets.get_icon_qt("general", "import"))
            self.custom_icon_del.setIcon(self.widgets.get_icon_qt("general", "delete"))
            self.dialog_btns.button(QDialogButtonBox.Ok).setIcon(self.widgets.get_icon_qt("general", "ok"))
            self.dialog_btns.button(QDialogButtonBox.Cancel).setIcon(self.widgets.get_icon_qt("general", "cancel"))
            self.tabs.setTabIcon(0, self.widgets.get_icon_qt("general", "tray-applet"))
            self.tabs.setTabIcon(1, self.widgets.get_icon_qt("emblems", "misc"))
            self.tabs.setTabIcon(2, self.widgets.get_icon_qt("emblems", "software"))
            self.tabs.setTabIcon(3, self.widgets.get_icon_qt("emblems", "steam"))
            self.tabs.setTabIcon(4, self.widgets.get_icon_qt("general", "folder"))

        # Prepare tabs for icon sets
        for widget in [self.icons_tray, self.icons_emblems, self.icons_apps, self.icons_steam, self.icons_custom]:
            widget.setLayout(QFlowLayout())

        # Gather icon data
        list_tray = pref.load_file(os.path.join(common.paths.data_dir, "img", "tray", "icons.json"))
        list_emblems = pref.load_file(os.path.join(common.paths.data_dir, "img", "emblems", "icons.json"))
        if not self.purpose == self.purpose_tray_icon_only:
            list_apps = self._get_application_icons()
            list_steam = self._get_steam_icons()
        list_custom = glob.glob(common.paths.custom_icons + "/*")

        # Populate icon tabs
        all_icon_buttons = []
        self._load_icon_set(1, list_emblems)
        self._load_icon_set(4, list_custom)
        if self.purpose == self.purpose_tray_icon_only:
            self._load_icon_set(0, list_tray)
        else:
            self._load_icon_set(2, list_apps)
            self._load_icon_set(3, list_steam)

        # When changing tray applet icon, limit the selection
        if self.purpose == self.purpose_tray_icon_only:
            self.tabs.removeTab(2)
            self.tabs.removeTab(2)
        else:
            self.tabs.removeTab(0)

        # TODO: Scroll to selected item

        # Prepare and open dialog
        self._setup_drag_drop_custom_icon()
        self.custom_icon_toolbar.setHidden(True)
        self.gif_warning.setHidden(True)
        self.button_group.buttonClicked.connect(self.select_icon)
        self.tabs.currentChanged.connect(self.change_tab)
        self.custom_icon_add.clicked.connect(self.import_custom_icon)
        self.custom_icon_del.clicked.connect(self.delete_custom_icon)

        self.dialog.accepted.connect(self.accept_changes)
        self.dialog.finished.connect(self.close_dialog)
        self.dialog.setWindowTitle(title)
        self.dialog.exec()

    def close_dialog(self):
        """
        Ensure the dialog (and its children) are destroyed. This is because the
        tray applet has some animated icons that have QMovie children.
        """
        for movie in self.gif_previews:
            movie.stop()
            movie.deleteLater()
        self.dialog.deleteLater()

    def _load_icon_set(self, tab_index, icon_list):
        """
        Populates the icons for the specified tab.

        Each button will be injected a variable for save data purposes:
            .icon_path      Relative/absolute path
            .tab_index      Tab index (for setting active state)
        """
        widget = self.tab_index_widgets[tab_index]

        if len(icon_list) == 0:
            label = QLabel()
            if tab_index == 3:
                label.setText(self._("When Steam is installed, icons from your games will appear here."))
            elif tab_index == 4:
                label.setText(self._("Drag and drop icons here, or add them by pressing the Import button."))
            else:
                label.setText(self._("No icons found!"))
            label.setAlignment(Qt.AlignCenter)
            label.setMargin(4)
            widget.layout().addWidget(label)
            return

        # Tray applet supports animated GIFs.
        def _load_animated_gif(button):
            movie = QMovie(common.get_full_path_for_save_data_icon(icon_path))
            movie.button = button

            def _draw_gif(frame):
                movie.button.setIcon(QIcon(movie.currentPixmap()))

            def _loop_gif(movie):
                movie.start()

            self.gif_previews.append(movie)
            movie.frameChanged.connect(_draw_gif)
            movie.finished.connect(_loop_gif)
            movie.start()

        # Populate the list
        for icon_path in icon_list:
            button = self._make_icon_button(icon_path, tab_index)
            widget.layout().addWidget(button)

            if icon_path.endswith(".gif"):
                _load_animated_gif(button)

        # Set initial selection
        for button in self.button_group.buttons():
            if button.icon_path == self.current_icon:
                button.setChecked(True)
                self.tabs.setCurrentIndex(button.tab_index)

                if button.tab_index == 4:
                    self.custom_icon_toolbar.setHidden(False)
                break

    def _make_icon_button(self, icon_path, tab_index):
        """
        Creates an icon button for selection.
        """
        button = QToolButton()
        button.setToolTip(icon_path.split("/")[-1])
        button.setCheckable(True)
        button.setIconSize(QSize(32, 32))
        button.setIcon(QIcon(common.get_full_path_for_save_data_icon(icon_path)))
        button.icon_path = icon_path
        button.tab_index = tab_index
        self.button_group.addButton(button)

        return button

    def change_tab(self, button):
        """
        Tab index changed. Update visibility of import/delete controls depending
        if the page is Custom (the last tab)
        """
        self.custom_icon_toolbar.setHidden(self.tabs.currentIndex() != self.tabs.count() - 1)

    def select_icon(self, button):
        """
        Updates the current icon choice in memory. When a GIF (tray applet) is selected,
        inform the user of the possibility it might not work on their desktop environment.
        """
        self.current_icon = button.icon_path
        gif_selected = button.tab_index == 0 and button.icon_path.endswith(".gif")
        self.gif_warning.setHidden(not gif_selected)

        # Only custom icons can be deleted
        self.custom_icon_del.setEnabled(button.tab_index == 4)

    def accept_changes(self):
        """
        Accepts the new icon choice and closes the icon picker. Runs the callback
        function to process the result.
        """
        self.callback_fn(self.current_icon)
        self.close_dialog()

    def _setup_drag_drop_custom_icon(self):
        """
        Prepare the file drag and drop facility as an alternate way to import
        custom icons.
        """
        def dragEnterEvent(event):
            if event.mimeData().hasUrls():
                event.accept()
            else:
                event.ignore()

        def dropEvent(event):
            uris = event.mimeData().urls()
            for uri in uris:
                if uri.isLocalFile() and uri.path().split(".")[-1].lower() in self.custom_icon_exts:
                    self.process_new_custom_icon(uri.path())

        self.tabs.setAcceptDrops(True)
        self.tabs.dragEnterEvent = dragEnterEvent
        self.tabs.dropEvent = dropEvent

    def process_new_custom_icon(self, source_path):
        """
        Adds the specified icon to the user's custom icons set. This may also
        be triggered by dropping graphics.
        """
        target_path = os.path.join(common.paths.custom_icons, os.path.basename(source_path))

        # Prevent duplicates
        while os.path.exists(target_path):
            self.dbg.stdout("Custom icon filename already exists: " + target_path, self.dbg.warning, 1)
            extension = os.path.basename(target_path).split(".")[-1]
            target_path = target_path.replace("." + extension, "_." + extension)

        if os.path.exists(source_path):
            self.dbg.stdout("Adding custom icon: " + source_path, self.dbg.action, 1)
            shutil.copy(source_path, target_path)
            button = self._make_icon_button(source_path, 4)
            self.tab_index_widgets[4].layout().addWidget(button)

        # Set as selected
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
        button.click()

    def import_custom_icon(self):
        """
        Opens the file browser to import new files to the custom icons set.
        """
        browser = QFileDialog()
        browser.setAcceptMode(QFileDialog.AcceptOpen)
        browser.setFileMode(QFileDialog.ExistingFiles)

        # TODO: Use Polychromatic styles, if possible.
        load_qt_theme(self.appdata, browser)

        files = browser.getOpenFileNames(caption=self._("Import Custom Icon"), filter=";;".join(self.custom_icon_filters))[0]

        for f in files:
            if f.startswith("/"):
                self.process_new_custom_icon(f)

    def delete_custom_icon(self, b):
        """
        Removes the specified icon from the user's custom icon set.
        Any save data referencing this icon will show a generic icon instead.
        """
        button = self.button_group.checkedButton()
        if not button:
            return

        icon_path = button.icon_path
        self.dbg.stdout("Deleting custom icon: " + icon_path, self.dbg.action, 1)
        os.remove(icon_path)
        button.deleteLater()

        self.custom_icon_del.setEnabled(False)

    def _get_application_icons(self):
        """
        Parses the desktop launchers for applications both local and system-wide
        so the user can pick them.
        """
        self.dbg.stdout("Populating application icons...", self.dbg.action, 1)
        local_apps = glob.glob(os.path.expanduser("~") + "/.local/share/applications/*.desktop")
        system_apps = glob.glob("/usr/share/applications/*.desktop")
        file_list = local_apps + system_apps
        icon_list = []

        # Determine where to find application icons (from theme)
        theme_name = QIcon.themeName()
        theme_paths = QIcon.themeSearchPaths()
        search_paths = []
        already_found = []

        search_paths.append(os.path.join(os.path.expanduser("~"), ".local", "share", "icons", "**"))
        for theme_path in theme_paths:
            search_paths.append(os.path.join(theme_path, theme_name, "apps", "48"))
        search_paths.append("/usr/share/icons/hicolor/48x48/apps")
        search_paths.append("/usr/share/icons/hicolor/64x64/apps")
        search_paths.append("/usr/share/icons/hicolor/128x128/apps")
        search_paths.append("/usr/share/icons/hicolor/scalable/apps")
        search_paths.append("/usr/share/pixmaps/")

        def _find_theme_icon(icon_name):
            # Prevent duplicates
            if icon_name in already_found:
                return None

            for search_path in search_paths:
                for path in glob.glob(os.path.join(search_path, "*"), recursive=True):
                    filename = os.path.splitext(os.path.basename(path))[0]
                    if filename == icon_name and os.path.isfile(path):
                        already_found.append(icon_name)
                        return path
            return None

        def parse_launcher_for_icon(lines):
            for line in lines:
                if line.startswith("Icon="):
                    icon = line.split("Icon=")[1].strip()

                    # Absolute path
                    if os.path.exists(icon):
                        icon_list.append(icon)
                        return

                    # Search theme directories
                    theme_icon = _find_theme_icon(icon)
                    if theme_icon:
                        icon_list.append(theme_icon)

        for launcher_path in file_list:
            with open(launcher_path, "r") as f:
                parse_launcher_for_icon(f.readlines())

        self.dbg.stdout("Loaded {0} application icons from {1} launchers.".format(len(icon_list), len(file_list)), self.dbg.success, 1)

        # Sort applications A-Z
        return sorted(icon_list, key=lambda i: os.path.basename(i).lower())

    def _get_steam_icons(self):
        """
        If Steam is installed (usually ~/.steam), the application will try to
        locate "librarycache" which contains many *_icon.jpg files of the games
        the user has installed/cached.
        """
        icon_list = []
        steam_dir = os.path.expanduser("~") + "/.steam"
        if not os.path.exists(steam_dir):
            return []

        for folder in ["steam", "root", "."]:
            librarycache = os.path.join(steam_dir, folder, "appcache", "librarycache")
            if os.path.exists(librarycache):
                icon_list = glob.glob(librarycache + "/*_icon.jpg", recursive=True)

        self.dbg.stdout("Found {0} Steam icons.".format(len(icon_list)), self.dbg.success, 1)
        return icon_list


class CommonFileTab(TabData):
    """
    Shared class that implements an interactive file management interface for
    features that use a FlatFileManagement() system.

    Each feature (e.g. effects, presets) should re-implement the functions
    where appropriate and specific to different tab interfaces.
    """
    def __init__(self, appdata, filemgr_class, content_widget_name, tree_widget_name):
        """
        Initialize the tab.

        Params:
            appdata                 ApplicationData() object
            filemgr_class           Class to initalize (e.g. effects.EffectFileManagement)
            content_widget_name     Name of QWidget containing the tab data
            tree_widget_name        Name of QTreeWidget containing tasks/file list.
        """
        super().__init__(appdata)

        # Class variables
        self.fileman = filemgr_class(appdata.locales, appdata._, appdata.dbg)
        self.current_file_data = {}
        self.current_file_path = ""

        # Specific to feature
        self.feature = "unknown"
        self.tasks = {
            "example": self._clear_tree
        }

        # Internal codes for UI messages
        self.INFO_NO_ITEMS = 1
        self.INFO_BAD_DATA = 2

        self.Contents = self.main_window.findChild(QWidget, content_widget_name)
        self.Sidebar = self.main_window.findChild(QTreeWidget, tree_widget_name)
        self.TasksBranch = self.Sidebar.invisibleRootItem().child(0)
        self.FilesBranch = self.Sidebar.invisibleRootItem().child(1)

        for branch in [self.TasksBranch, self.FilesBranch]:
            branch.action_id = None
            branch.action_data = None

        self.Sidebar.itemClicked.connect(self._sidebar_changed)

    def _add_tree_item(self, branch, label, icon, action_id, action_data):
        """
        Appends a new QTreeWidgetItem() with the specified parameters.

        action_id and action_data are appended into the object so the
        _sidebar_changed() function knows what to do with the data.
        """
        item = QTreeWidgetItem()
        item.setText(0, label)
        item.setIcon(0, QIcon(icon))
        item.action_id = action_id
        item.action_data = action_data
        branch.addChild(item)

    def _clear_tree(self, branch):
        """
        Clears the contents of a tree branch.
        """
        branch.takeChildren()

    def set_tab(self):
        """
        The feature tab is opened.
        """
        # Open all tree branches
        self.Sidebar.expandAll()

        # Populate files in sidebar
        self._clear_tree(self.FilesBranch)
        file_list = self.fileman.get_item_list()
        for item in file_list:
            self._add_tree_item(self.FilesBranch, item["name"], item["icon"], "open", item["path"])
        self.FilesBranch.sortChildren(0, Qt.AscendingOrder)

        # Show the first item
        if len(file_list) == 0:
            self.show_no_file_screen(0)
        else:
            first_item = self.FilesBranch.child(0)
            first_item.setSelected(True)
            self.open_file(first_item.action_data)

    def _sidebar_changed(self, item):
        """
        A task or file on the sidebar is clicked.

        For ID "tasks", the data is a key that triggers a function. No parameters.
        For ID "open", the data will be opened for the user to work with.
        """
        if item.action_id == "tasks":
            self.Sidebar.selectedItems()[0].setSelected(False)
            self.tasks[item.action_data]()
        elif item.action_id == "open":
            self.open_file(item.action_data)

    def show_no_file_screen(self, message_id):
        """
        The file cannot be opened for viewing - inform the user.
        This needs to be implemented by the feature.

        Params:
            message_id  (int)   One of the self.INFO_* variables
        """
        raise NotImplementedError

    def show_error_message(self, path, error_code):
        """
        The file failed to load. Parse the error code and inform the user.

        Params:
            path        (str)   Path to failed file
            error_code  (int)   Integer from fileman.ERROR_*
        """
        reasons = {
            fileman.ERROR_BAD_DATA: self._("The file contains invalid data."),
            fileman.ERROR_MISSING_FILE: self._("The file no longer exists. Please refresh the page."),
            fileman.ERROR_NEWER_FORMAT: self._("This file was saved in a newer version of this program.")
        }

        try:
            reason = reasons[error_code]
        except KeyError:
            reason = self._("Unspecified error: []").replace("[]", str(error_code))

        self.widgets.open_dialog(self.widgets.dialog_error,
                                 self._("File Error"),
                                 self._("This file cannot be opened:") + "\n" + path,
                                 reason)

    def _show_file_error(self, traceback=None):
        """
        Show a dialog for the rare scenario where the file could not be written to.
        """
        self.widgets.open_dialog(self.widgets.dialog_error,
                                 self._("File Error"),
                                 self._("The operation could not be completed due to an error processing this file."),
                                 self._("Please make sure the file permissions are recursively correct:") + '\n' + common.paths.config, traceback)

    def new_file(self):
        """
        Create a new file for this feature.
        The inheriting class should implement this accordingly.
        """
        raise NotImplementedError

    def open_file(self, file_path):
        """
        Opens the specified file in the interface. This should provide an overview
        of the file, a preview and provide options to work with the data.

        The inheriting class should implement this accordingly.
        """
        raise NotImplementedError

    def edit_file(self):
        """
        Open the editor to modify the currently selected file.
        The inheriting class should implement this accordingly.
        """
        raise NotImplementedError

    def delete_file(self):
        """
        Confirm the user is sure the selected file should be deleted.
        """
        name = self.current_file_data["name"]

        def _file_delete_confirmed():
            success = self.fileman.delete_item(self.current_file_path)

            if success != True:
                self._show_file_error(success)
                return

            old_item = self.Sidebar.selectedItems()[0]
            item_index = self.FilesBranch.indexOfChild(old_item)
            self.FilesBranch.removeChild(old_item)
            if self.FilesBranch.childCount() == 0:
                self.show_no_file_screen(0)
                return

            if item_index > self.FilesBranch.childCount() - 1:
                item_index = self.FilesBranch.childCount() - 1

            new_item = self.FilesBranch.child(item_index)
            new_item.setSelected(True)
            self.open_file(new_item.action_data)

        titles = {
            "effects": self._("Delete Effect?"),
            "presets": self._("Delete Preset?")
        }

        msgs = {
            "effects": self._("Delete '[]' effect? This cannot be undone.\n\nPresets that use this effect will be unlinked.").replace("[]", name),
            "presets": self._("Delete '[]' preset? This cannot be undone.\n\nTriggers that automatically activate this preset will no longer function.").replace("[]", name),
        }

        self.widgets.open_dialog(self.widgets.dialog_warning,
                                 titles[self.feature],
                                 msgs[self.feature],
                                 None, None,
                                 [QMessageBox.Yes, QMessageBox.No],
                                 QMessageBox.Yes,
                                 {QMessageBox.Yes: _file_delete_confirmed})

    def clone_file(self):
        """
        Create a new copy of the currently selected effect.
        """
        new_file_path = self.fileman.clone_item(self.current_file_path)

        if not new_file_path:
            self._show_file_error()
            return

        # Get the index for the current item
        current_item = self.Sidebar.selectedItems()[0]
        item_index = self.FilesBranch.indexOfChild(current_item) + 1

        # Add the new item to the list (dynamic, no reloading)
        item = QTreeWidgetItem()
        item.setText(0, self._("[] (Copy)").replace("[]", current_item.text(0)))
        item.setIcon(0, current_item.icon(0))
        item.action_id = "open"
        item.action_data = new_file_path
        self.FilesBranch.insertChild(item_index, item)
        current_item.setSelected(False)
        item.setSelected(True)
        self.open_file(new_file_path)
