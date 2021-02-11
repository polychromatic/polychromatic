#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2021 Luke Horwell <code@horwell.me>
#
"""
This module controls the 'Effects' tab of the Controller GUI.
"""

from .. import common
from .. import effects
from .. import locales
from .. import procpid
from .. import preferences as pref
from . import shared
from . import editor

import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QPushButton, QToolButton, QMessageBox, \
                            QListWidget, QTreeWidget, QLabel, QComboBox, \
                            QTreeWidgetItem, QMenu, QDialog, QDialogButtonBox, \
                            QButtonGroup, QLineEdit, QTextEdit, QCheckBox, \
                            QGroupBox, QRadioButton, QMainWindow


class EffectsTab(shared.CommonFileTab):
    """
    Allows the user to manage software effects for lighting up their devices.
    """
    def __init__(self, appdata):
        super().__init__(appdata, effects.EffectFileManagement, "EffectContents", "EffectSidebarTree")

        # Set up variables
        self.feature = "effects"

        # Populate tasks
        self.tasks = {
            "new": self.new_file,
            "import": self.import_effect
        }

        self._add_tree_item(self.TasksBranch, self._("New Effect"), common.get_icon("general", "new"), "tasks", "new")
        # FIXME: Not yet implemented: Import Effect
        #self._add_tree_item(self.TasksBranch, self._("Import Effect"), common.get_icon("general", "import"), "tasks", "import")

        # Keep track of editor windows so garbage collection doesn't destroy them
        self.editors = {}

    def show_no_file_screen(self, message_id):
        """
        Effect cannot be opened for viewing - inform the user.

        Params:
            message_id  (int)   0   Empty file list
                                1   File corrupt
        """
        layout = self.Contents.layout()

        titles = {
            0: self._("It's empty here!"),
            1: self._("Error loading effect")
        }

        subtitles = {
            0: self._("Try creating your own effect or import an image or video."),
            1: self._("The application found invalid data in this file. The file might be corrupt.")
        }

        icons = {
            0: None,
            1: None
        }

        buttons = {
            0: [
                {
                    "label": self._("New Effect"),
                    "icon_folder": "general",
                    "icon_name": "new",
                    "action": self.new_file
                }
                # FIXME: Not yet implemented: Import Effect
                #{
                    #"label": self._("Import Effect"),
                    #"icon_folder": "general",
                    #"icon_name": "import",
                    #"action": self.import_effect
                #}
            ],
            1: []
        }

        shared.clear_layout(layout)
        self.widgets.populate_empty_state(layout, icons[message_id], titles[message_id], subtitles[message_id], buttons[message_id])

    def new_file(self):
        """
        Prompts the user which type of effect to create.
        """
        dialog = shared.get_ui_widget(self.appdata, "new-effect", QDialog)

        btn_layered = dialog.findChild(QToolButton, "NewLayered")
        btn_scripted = dialog.findChild(QToolButton, "NewScripted")
        btn_sequence = dialog.findChild(QToolButton, "NewSequence")
        hover_tooltip = dialog.findChild(QLabel, "HoverText")
        dialog_buttons = dialog.findChild(QDialogButtonBox, "DialogButtons")

        # Load icons
        # FIXME: QToolButton() icon not behaving like QPushButton() when button is focused?
        btn_layered.setIcon(self.widgets.get_icon_qt("effects", "layered"))
        btn_scripted.setIcon(self.widgets.get_icon_qt("effects", "scripted"))
        btn_sequence.setIcon(self.widgets.get_icon_qt("effects", "sequence"))

        if not self.appdata.system_qt_theme:
            dialog_buttons.button(QDialogButtonBox.Cancel).setIcon(self.widgets.get_icon_qt("general", "close"))

        # Hovering over a button will show the tooltip as a label too
        def _hover_button(event, button):
            hover_tooltip.setText(button.toolTip())
            button.repaint()

        btn_layered.enterEvent = lambda event: _hover_button(event, btn_layered)
        btn_scripted.enterEvent = lambda event: _hover_button(event, btn_scripted)
        btn_sequence.enterEvent = lambda event: _hover_button(event, btn_sequence)

        # For keyboard navigation
        btn_layered.focusInEvent = lambda event: _hover_button(event, btn_layered)
        btn_scripted.focusInEvent = lambda event: _hover_button(event, btn_scripted)
        btn_sequence.focusInEvent = lambda event: _hover_button(event, btn_sequence)

        # Prepare button events
        def _close_dialog():
            dialog.reject()
        dialog_buttons.rejected.connect(_close_dialog)

        btn_layered.clicked.connect(lambda: self.new_file_stage_2(dialog, effects.TYPE_LAYERED))
        btn_scripted.clicked.connect(lambda: self.new_file_stage_2(dialog, effects.TYPE_SCRIPTED))
        btn_sequence.clicked.connect(lambda: self.new_file_stage_2(dialog, effects.TYPE_SEQUENCE))

        # FIXME: Not yet implemented editors
        btn_layered.setEnabled(False)
        btn_scripted.setEnabled(False)

        dialog.open()

    def new_file_stage_2(self, old_dialog, effect_type):
        """
        Open the metadata window for the user to enter details for their new creation.
        On successful initialization, the effect editor will open.

        Params:
            old_dialog      QDialog() from new_file()
            effect_type     effects.TYPE_* reference
        """
        old_dialog.accept()
        data = self.fileman.init_data("", effect_type)

        # Set default icon to what the effect is
        if effect_type == effects.TYPE_LAYERED:
            data["icon"] = "img/effects/layered.svg"
        elif effect_type == effects.TYPE_SCRIPTED:
            data["icon"] = "img/effects/scripted.svg"
        elif effect_type == effects.TYPE_SEQUENCE:
            data["icon"] = "img/effects/sequence.svg"

        def _save_metadata(newdata):
            """
            After closing the metadata editor, save the data to disk and open
            the editor according to the effect.
            """
            success, path = self.fileman.save_item(newdata)

            if not success:
                self.show_error_message(path, self._show_file_error())
                self.new_file_stage_2(metadata_editor, effect_type)
                return

            # Open the editor
            self.current_file_path = path
            self.current_file_data = newdata
            self.edit_file()

            # Refresh the UI for when the user returns
            self.set_tab()
            self.open_file(path)

        metadata_editor = EffectMetadataEditor(self.appdata, data, _save_metadata)

    def open_file(self, effect_path):
        """
        Opens the specified file in the interface, providing an overview of the
        effect and buttons to modify the file.
        """
        self.current_file_path = effect_path
        self.current_file_data = self.fileman.get_item(effect_path)
        data = self.current_file_data

        if type(data) == int:
            self.show_error_message(effect_path, data)
            self.show_no_file_screen(1)
            return

        layout = self.Contents.layout()
        shared.clear_layout(layout)

        # Summary
        icon_path = data["parsed"]["icon"]
        buttons = [
            {
                "id": "play",
                "icon": self.widgets.get_icon_qt("effects", "play"),
                "label": self._("Play"),
                "disabled": False,
                "action": self.play_effect
            },
            {
                "id": "edit",
                "icon": self.widgets.get_icon_qt("general", "edit"),
                "label": self._("Edit"),
                "disabled": False,
                "action": self.edit_file
            },
            {
                "id": "clone",
                "icon": self.widgets.get_icon_qt("general", "clone"),
                "label": self._("Clone"),
                "disabled": False,
                "action": self.clone_file
            },
            {
                "id": "delete",
                "icon": self.widgets.get_icon_qt("general", "delete"),
                "label": self._("Delete"),
                "disabled": False,
                "action": self.delete_file
            }
        ]

        # Populate indicators
        indicators = []

        # -- Author
        if data["author"]:
            indicators.append({"icon": common.get_icon("effects", "author"), "label": data["author"]})

        # -- Effect Type
        effect_type = data["type"]
        effect_type_name = {
            effects.TYPE_LAYERED: self._("Layered"),
            effects.TYPE_SCRIPTED: self._("Script"),
            effects.TYPE_SEQUENCE: self._("Sequence"),
        }
        effect_type_icon = {
            effects.TYPE_LAYERED: "layered",
            effects.TYPE_SCRIPTED: "scripted-small",
            effects.TYPE_SEQUENCE: "sequence",
        }
        indicators.append({"icon": common.get_icon("effects", effect_type_icon[effect_type]), "label": effect_type_name[effect_type]})

        # -- Device
        if data["map_device"]:
            device_icon = common.get_icon("devices", data["map_device_icon"])
            if not device_icon:
                device_icon = common.get_icon("devices", "accessory")
            indicators.append({"icon": device_icon, "label": data["map_device"]})

        # Create the summary widget
        summary = self.widgets.create_summary_widget(icon_path, data["parsed"]["name"], indicators, buttons)
        summary.setMaximumHeight(170)
        layout.addWidget(summary)
        layout.addStretch()

    def edit_file(self):
        """
        Open the editor for the currently selected effect. Make sure only one
        editor is open per file.
        """
        effect_path = self.current_file_path
        effect_type = self.current_file_data["type"]

        if effect_path in self.editors.keys():
            if self.editors[effect_path].alive:
                self.widgets.open_dialog(self.widgets.dialog_warning,
                                         self._("File In Use"),
                                         self._("This file is being edited in another window. Please close that editor first."))
                return

        if effect_type in [effects.TYPE_LAYERED, effects.TYPE_SEQUENCE]:
            self.editors[effect_path] = editor.VisualEffectEditor(self.appdata, self.fileman, effect_path)

    def import_effect(self):
        """
        Allows the user to create effects from other media, such as videos or images.
        """
        print("stub:effects.import_effect")
        pass

    def play_effect(self, device_name=None):
        """
        Play the currently selected effect.

        Optionally, for scripted effects, they could be compatible to run on one
        or more hardware.
        """
        effect_type = self.current_file_data["type"]
        if not device_name:
            device_name = self.current_file_data["map_device"]

        procmgr = procpid.ProcessManager("helper")
        procmgr.start_component(["--run-fx", self.current_file_path, "--device-name", device_name])


class EffectMetadataEditor(shared.TabData):
    """
    A dialog for modifying the metadata of an effect. This works with data
    that is currently residing in memory.
    """
    def __init__(self, appdata, data, callback_fn):
        """
        Prepare and show the window for editing the metadata of a saved (or
        new) effect.

        Params:
            appdata         ApplicationData() object
            data            Effect data
            callback_fn     Run function after save. The parameter will be the new data.
        """
        super().__init__(appdata)
        self.data = data
        self.effect_type = data["type"]
        self.callback_fn = callback_fn
        self.matrix_devices = {}
        self.device_info = {}
        self.mapping_graphics = effects.DeviceMapGraphics(appdata)
        self.graphic_list = self.mapping_graphics.get_graphic_list()

        # Dialog & Controls
        self.dialog = shared.get_ui_widget(self.appdata, "effect-metadata-editor", QDialog)
        self.buttons = self.dialog.findChild(QDialogButtonBox, "DialogButtons")

        self.name = self.dialog.findChild(QLineEdit, "EffectName")
        self.author = self.dialog.findChild(QLineEdit, "Author")
        self.author_url = self.dialog.findChild(QLineEdit, "AuthorURL")
        self.icon = self.dialog.findChild(QLabel, "EffectIconPlaceholder")
        self.summary = self.dialog.findChild(QTextEdit, "Summary")
        self.map_device = self.dialog.findChild(QComboBox, "MapDevice")
        self.map_graphic_grid = self.dialog.findChild(QRadioButton, "MapGraphicToGrid")
        self.map_graphic_svg = self.dialog.findChild(QRadioButton, "MapGraphicToSVG")
        self.map_graphic_list = self.dialog.findChild(QComboBox, "MapGraphicList")
        self.map_preview = self.dialog.findChild(QLabel, "MappingPreview")
        self.dimensions_device = self.dialog.findChild(QLabel, "DeviceDimensions")

        self._set_mapping_error(False)

        # Prepare icon picker
        def _update_icon(new_icon):
            self.data["icon"] = new_icon

        picker = self.widgets.create_icon_picker_control(_update_icon, self.data["icon"], self._("Choose Effect Icon"))
        self.icon.parentWidget().layout().replaceWidget(self.icon, picker)
        self.icon.deleteLater()
        self.icon = picker

        # Set placeholder based on logged in username
        try:
            self.author.setPlaceholderText(os.getlogin().capitalize())
        except OSError:
            pass

        # Scripted effects do not store mapping information
        if self.effect_type == effects.TYPE_SCRIPTED:
            self.dialog.findChild(QGroupBox, "MappingGroup").setHidden(True)
            self.dialog.adjustSize()

        # Populate metadata fields
        self.name.setText(data["name"])
        self.author.setText(data["author"])
        self.author_url.setText(data["author_url"])
        self.summary.setText(data["summary"])

        # Populate device list (for non-scripted effects)
        if not self.effect_type == effects.TYPE_SCRIPTED:
            found_device_name = False

            for index, device in enumerate(self.appdata.middleman.get_device_all()):
                if not device or not device["matrix"]:
                    continue

                self.matrix_devices[index] = device
                self.map_device.addItem(device["name"])
                self.map_device.setItemIcon(index, QIcon(device["form_factor"]["icon"]))

                # Append data into object
                self.device_info[index] = {}
                self.device_info[index]["icon"] = device["form_factor"]["id"]
                self.device_info[index]["cols"] = device["matrix_cols"]
                self.device_info[index]["rows"] = device["matrix_rows"]

                if data["map_device"] == device["name"]:
                    found_device_name = True
                    self.map_device.setCurrentIndex(index)

            # Select the first device if this is a new creation
            if not data["map_device"]:
                self.map_device.setCurrentIndex(0)

            # Inform the user if the original device for this effect is missing
            elif not found_device_name:
                self._set_mapping_error(True)
                self.map_device.setCurrentIndex(-1)
                self.map_device.setCurrentText(data["map_device"])

            # Populate graphic list
            self._device_updated()

        # Set initial mapping options (when editing an existing effect)
        if not data["type"] == effects.TYPE_SCRIPTED:
            if data["map_graphic"]:
                self.map_graphic_svg.setChecked(True)
            else:
                self.map_graphic_grid.setChecked(True)
            self._update_graphic_preview()

        # Disallow saving if the effect has no name
        name_label = self.dialog.findChild(QLabel,"EffectNameLabel")
        name_label.setText(name_label.text() + "*")

        # Connect signals
        self.dialog.accepted.connect(self._save_changes)
        self.name.textChanged.connect(self._validate_fields)
        self.map_device.currentIndexChanged.connect(self._validate_fields)
        self.map_device.currentIndexChanged.connect(self._device_updated)
        self.map_graphic_grid.toggled.connect(self._select_grid_mode)
        self.map_graphic_svg.toggled.connect(self._select_graphic_mode)
        self.map_graphic_list.currentIndexChanged.connect(self._update_graphic_preview)

        # Set icons
        if not self.appdata.system_qt_theme:
            self.buttons.button(QDialogButtonBox.Cancel).setIcon(self.widgets.get_icon_qt("general", "close"))
            self.buttons.button(QDialogButtonBox.Ok).setIcon(self.widgets.get_icon_qt("general", "ok"))

        # Showtime!
        self._validate_fields()
        self.dialog.open()

    def _validate_fields(self):
        """
        Ensure the fields have sufficient data before saving is allowed.
        """
        conditions = [
            # Must have a name
            len(self.name.text()) > 0
        ]

        # Layered/Sequence effects must have a device to map to
        if not self.effect_type == effects.TYPE_SCRIPTED:
            conditions.append(self.map_device.currentIndex() >= 0)

        self.buttons.button(QDialogButtonBox.Ok).setEnabled(all(x == True for x in conditions))

    def _set_mapping_error(self, visible, alt_reason=""):
        """
        Show/hide the mapping error label, and update the reason.
        """
        label = self.dialog.findChild(QLabel, "MappingErrorLabel")
        label.setHidden(not visible)
        if visible:
            label.setText(self._("This effect was created for \"[]\" but wasn't found. Choose another device to map.").replace("[]", self.data["map_device"]))

            if alt_reason:
                label.setText(alt_reason)

    def _device_updated(self):
        """
        Mapping device changed. Update the graphic list to ensure only compatible
        graphics are displayed.

        If the user is editing an existing effect and chooses a device with less
        columns/rows then previously, let the user know truncating might occur.
        """
        device_name = self.map_device.currentText()
        try:
            device_info = self.device_info[self.map_device.currentIndex()]
        except KeyError:
            return self._set_mapping_error(True)
        device_rows = device_info["rows"]
        device_cols = device_info["cols"]

        dimensions = common.get_plural(device_rows, self._("1 row"), self._("2 rows").replace("2", str(device_rows)))
        dimensions += ", " + common.get_plural(device_cols, self._("1 column"), self._("2 columns").replace("2", str(device_cols)))
        self.dimensions_device.setText(dimensions)

        # Filter graphics so only compatible matrix dimensions are shown
        self.map_graphic_list.clear()
        for name in self.graphic_list.keys():
            graphic = self.graphic_list[name]
            new_index = self.map_graphic_list.count()

            if device_rows != graphic["rows"] or device_cols != graphic["cols"]:
                continue

            self.map_graphic_list.addItem(name)

            if self.data["map_graphic"] == graphic["filename"]:
                self.map_graphic_list.setCurrentIndex(new_index)

            # For new effects, auto select the first localized item (mainly for keyboards)
            if not self.data["map_graphic"] and self.locales._get_current_locale():
                self.map_graphic_list.setCurrentIndex(new_index)

        # For new effects, auto select the first graphic
        # TODO: Be smarter, add hint key to auto select Blade laptops, for example.
        if not self.data["map_graphic"]:
            self.map_graphic_svg.setChecked(True)
            self.map_graphic_list.setCurrentIndex(0)

        # If there are no graphics, only grid can be selected
        self.map_graphic_svg.setEnabled(self.map_graphic_list.count() > 0)
        self.map_graphic_list.setEnabled(self.map_graphic_list.count() > 0)
        self.map_graphic_grid.setChecked(self.map_graphic_list.count() == 0)

    def _select_grid_mode(self):
        """
        User selects the "Grid" radio button.
        """
        self.map_graphic_list.setEnabled(False)
        self.map_graphic_list.setCurrentIndex(-1)
        self._update_graphic_preview()

    def _select_graphic_mode(self):
        """
        User selects the "Graphic" radio button.
        """
        self.map_graphic_list.setEnabled(True)
        if self.map_graphic_list.currentIndex() < 0:
            self.map_graphic_list.setCurrentIndex(0)
            return
        self._update_graphic_preview()

    def _update_graphic_preview(self):
        """
        The graphic options have changed, refresh the preview.
        """
        device_map = effects.DeviceMapGraphics(self.appdata)
        try:
            device_info = self.device_info[self.map_device.currentIndex()]
        except KeyError:
            return self._set_mapping_error(True)
        cols = device_info["cols"]
        rows = device_info["rows"]
        svg_path = None

        # -- Grid
        if self.map_graphic_grid.isChecked():
            svg_path = device_map.get_grid_path(cols, rows)

        # -- Graphic
        elif self.map_graphic_list.currentText() == "":
            return

        elif self.map_graphic_svg.isChecked():
            graphic = self.graphic_list[self.map_graphic_list.currentText()]
            filename = graphic["filename"]
            svg_path = device_map.get_graphic_path(filename)

        # Load SVG into view
        if svg_path:
            shared.set_pixmap_for_label(self.map_preview, svg_path, 256)

    def _save_changes(self):
        """
        Commit the changes and pass them to the callback function.
        """
        # Metadata fields
        self.data["name"] = self.name.text()
        self.data["author"] = self.author.text()
        self.data["author_url"] = self.author_url.text()
        self.data["summary"] = self.summary.toPlainText()

        # Device mapping information
        if not self.data["type"] == effects.TYPE_SCRIPTED:
            device_name = self.map_device.currentText()
            device_info = self.device_info[self.map_device.currentIndex()]
            graphic_name = self.map_graphic_list.currentText()

            self.data["map_device"] = device_name
            self.data["map_device_icon"] = device_info["icon"]
            self.data["map_cols"] = device_info["cols"]
            self.data["map_rows"] = device_info["rows"]
            self.data["map_graphic"] = ""
            if graphic_name:
                self.data["map_graphic"] = self.graphic_list[graphic_name]["filename"]

        self.callback_fn(self.data)
