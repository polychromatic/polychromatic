# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
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
        self.feature = "effects"
        self.tab_title = self._("Effects")

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
            0: self._("Your own software effects appear here. Try creating one!"),
            1: self._("There's invalid data in this file. The file might be corrupt.")
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

    def _check_for_device_new_file(self):
        """
        Makes sure there is a device connected required to create an effect.

        The current codebase doesn't provide a mechanism to list all compatible
        hardware yet, since effects need to store their rows/cols values.
        """
        if len(self.middleman.get_devices()) == 0:
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     self._("New Effect"),
                                     self._("No devices found. New effects require a compatible device to be present."),
                                     info_text=self._("Make sure the device is connected and the backend is working."))
            return False
        return True

    def new_file(self):
        """
        Prompts the user which type of effect to create.
        """
        if not self._check_for_device_new_file():
            return

        dialog = shared.get_ui_widget(self.appdata, "new-effect", QDialog)

        # TODO: Not all effect types are implemented, create sequence one
        self.new_file_stage_2(dialog, effects.TYPE_SEQUENCE)
        return

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
        On successful initialisation, the effect editor will open.

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

        # Backends not ready - cannot show device list
        if not self.appdata.ready:
            self.dbg.stdout("Backends not ready! Device list will not be available for new effect.", self.dbg.warning, 1)
            action = ""

            def do_ignore():
                # Let the metadata editor handle no devices
                pass

            def do_retry():
                nonlocal action
                action = "retry"

            def do_cancel():
                nonlocal action
                action = "cancel"

            self.widgets.open_dialog(self.widgets.dialog_warning,
                                     self._("Backend Not Ready"),
                                     self._("The application is still waiting for the backends to finish initialising so you can pick a device to map your new effect."),
                                     info_text=self._("This might be ready in a few moments."),
                                     buttons=[QMessageBox.Ignore, QMessageBox.Retry],
                                     actions={
                                         QMessageBox.Ignore: do_ignore,
                                         QMessageBox.Retry: do_retry
                                     })

            if action == "cancel":
                return
            elif action == "retry":
                return self.new_file_stage_2(old_dialog, effect_type)

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

        # Show the file's summary text (if any)
        summary_text = data["summary"]
        if len(summary_text) > 0:
            summary_label = QLabel()
            summary_label.setText(summary_text)
            summary_label.setWordWrap(True)
            layout.addWidget(self.widgets.create_row_widget(self._("Summary"), [summary_label]))

        # Show other actions for this effect
        def _edit_metadata():
            # To prevent data loss, don't edit metadata here if the editor is open
            if effect_path in self.editors.keys():
                if self.editors[effect_path].alive:
                    self.widgets.open_dialog(self.widgets.dialog_warning,
                                             self._("File In Use"),
                                             self._("This file is being edited in another window. Please switch to that window to make changes."))
                    return

            def _metadata_changed(newdata):
                result, new_path = self.fileman.save_item(newdata, effect_path)
                self.open_file(new_path)
                if len(self.Sidebar.selectedItems()) > 0:
                    self.Sidebar.selectedItems()[0].setText(0, newdata["name"])
                    self.Sidebar.selectedItems()[0].setIcon(0, QIcon(common.get_full_path_for_save_data_icon(newdata["icon"])))

            self.metadata_editor = EffectMetadataEditor(self.appdata, self.current_file_data, _metadata_changed)

        btn_edit_meta = QPushButton()
        btn_edit_meta.setText(self._("Edit Metadata"))
        btn_edit_meta.setIcon(self.widgets.get_icon_qt("general", "properties"))
        btn_edit_meta.clicked.connect(_edit_metadata)
        widget_edit_meta = self.create_widget_wrapper_for_control([btn_edit_meta])

        other_actions = self.widgets.create_row_widget(self._("Other Actions"), [widget_edit_meta], vertical=True)
        other_actions.findChild(QLabel).setContentsMargins(0, 4, 0, 4)
        layout.addWidget(other_actions)
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
        self.mapping_graphics = effects.DeviceMapGraphics(appdata)
        self.graphic_list = self.mapping_graphics.get_graphic_list()

        # Session: Remember device attributes: icon, cols, rows
        self.device_info = {}

        # Dialog & Controls
        self.dialog = shared.get_ui_widget(self.appdata, "effect-metadata-editor", QDialog)
        self.buttons = self.dialog.findChild(QDialogButtonBox, "DialogButtons")

        # -- Left: Details
        self.name = self.dialog.findChild(QLineEdit, "EffectName")
        self.author = self.dialog.findChild(QLineEdit, "Author")
        self.author_url = self.dialog.findChild(QLineEdit, "AuthorURL")
        self.icon = self.dialog.findChild(QLabel, "EffectIconPlaceholder")
        self.summary = self.dialog.findChild(QTextEdit, "Summary")

        # -- Right: Hardware
        self.map_device_combo = self.dialog.findChild(QComboBox, "MapDeviceCombo")
        self.map_graphic_grid = self.dialog.findChild(QRadioButton, "MapGraphicToGrid")
        self.map_graphic_svg = self.dialog.findChild(QRadioButton, "MapGraphicToSVG")
        self.map_graphic_list = self.dialog.findChild(QComboBox, "MapGraphicList")
        self.map_preview = self.dialog.findChild(QLabel, "MappingPreview")
        self.dimensions_device = self.dialog.findChild(QLabel, "DeviceDimensions")

        self._init_controls()

    def _init_controls(self):
        """
        Populates and set up the UI for this window.
        """
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
            # Some OSes do not support this. Never mind.
            pass

        # Scripted effects do not configure mapping
        if self.effect_type == effects.TYPE_SCRIPTED:
            self.dialog.findChild(QGroupBox, "MappingGroup").setHidden(True)
            self.dialog.adjustSize()

        # Populate metadata fields
        self.name.setText(self.data["name"])
        self.author.setText(self.data["author"])
        self.author_url.setText(self.data["author_url"])
        self.summary.setText(self.data["summary"])

        # Mapping Configuration (non-scripted effects only)
        if not self.effect_type == effects.TYPE_SCRIPTED:
            # Populate device list
            if not self._populate_devices():
                return

            # Select appropriate mapping mode
            if self.data["map_graphic"]:
                self.map_graphic_svg.setChecked(True)
            else:
                self.map_graphic_grid.setChecked(True)
            self._update_graphic_preview()

        # Name is a required field
        name_label = self.dialog.findChild(QLabel, "EffectNameLabel")
        name_label.setText(name_label.text() + "*")

        # Connect signals
        self.dialog.accepted.connect(self._save_changes)
        self.name.textChanged.connect(self._validate_fields)
        self.map_device_combo.currentIndexChanged.connect(self._validate_fields)
        self.map_device_combo.currentIndexChanged.connect(self._device_updated)
        self.map_graphic_grid.toggled.connect(self._set_map_grid)
        self.map_graphic_svg.toggled.connect(self._set_mode_graphic)
        self.map_graphic_list.currentIndexChanged.connect(self._update_graphic_preview)

        # Showtime!
        self._validate_fields()
        self.dialog.open()

    def _populate_devices(self):
        """
        Populate the list of compatible devices to create a software effect for.

        For effects already created, only identical devices (cols/rows) may be
        interchanged (although there is no guarantee that the matrixes map 1:1)
        """
        is_new_file = len(self.data["name"]) == 0
        found_device_name = False

        for device in self.middleman.get_devices():
            if not device or not device.matrix:
                continue

            self.map_device_combo.addItem(QIcon(device.form_factor["icon"]), device.name)
            index = self.map_device_combo.count() - 1

            # Store device data for later
            self.device_info[index] = {}
            self.device_info[index]["icon"] = device.form_factor["id"]
            self.device_info[index]["cols"] = device.matrix.cols
            self.device_info[index]["rows"] = device.matrix.rows

            if self.data["map_device"] == device.name:
                found_device_name = True
                self.map_device_combo.setCurrentIndex(index)

            # Disable option for existing effects and does not match another device
            if not is_new_file:
                if not self.data["map_cols"] == device.matrix.cols or \
                    not self.data["map_rows"] == device.matrix.rows:
                        self.map_device_combo.model().item(index).setEnabled(False)

        # New effect? Select the first device.
        if not self.data["map_device"]:
            self.dialog.setWindowTitle(self._("New Effect"))
            self.map_device_combo.setCurrentIndex(0)

        # Add a placeholder for device if it is not present
        elif not found_device_name and not is_new_file:
            self.map_device_combo.addItem(QIcon(common.get_icon("devices", "unrecognised")), self.data["map_device"])
            index = self.map_device_combo.count() - 1
            self.map_device_combo.setCurrentIndex(index)
            self.device_info[index] = {}
            self.device_info[index]["icon"] = self.data["map_device_icon"]
            self.device_info[index]["cols"] = self.data["map_cols"]
            self.device_info[index]["rows"] = self.data["map_rows"]

        # No devices to map
        if self.map_device_combo.count() == 0:
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     self._("New Effect"),
                                     self._("No compatible devices found. Only individually addressable LED capable hardware can be used for effects."))
            return False

        # Populate graphic list
        self._device_updated()
        return True

    def _validate_fields(self):
        """
        Ensure the fields have sufficient data before saving is allowed.
        """
        conditions = [
            # Must have a name
            len(self.name.text()) > 0
        ]

        self.buttons.button(QDialogButtonBox.Ok).setEnabled(all(x is True for x in conditions))

    def _device_updated(self):
        """
        Mapping device changed. Update the graphic list to ensure only compatible
        graphics are displayed.

        If the user is editing an existing effect and chooses a device with less
        columns/rows then previously, let the user know truncating might occur.
        """
        is_new_file = len(self.data["name"]) == 0
        device_name = self.map_device_combo.currentText()
        device_info = self.device_info[self.map_device_combo.currentIndex()]
        device_rows = device_info["rows"]
        device_cols = device_info["cols"]

        dimensions = common.get_plural(device_rows, self._("1 row"), self._("2 rows").replace("2", str(device_rows)))
        dimensions += ", " + common.get_plural(device_cols, self._("1 column"), self._("2 columns").replace("2", str(device_cols)))
        self.dimensions_device.setText(dimensions)

        # Filter graphics so only compatible matrix dimensions are shown
        self.map_graphic_list.clear()
        found_graphic_index = None
        for name in self.graphic_list.keys():
            graphic = self.graphic_list[name]

            if device_rows != graphic["rows"] or device_cols != graphic["cols"]:
                continue

            new_index = self.map_graphic_list.count()
            self.map_graphic_list.addItem(name)

            if self.data["map_graphic"] == graphic["filename"]:
                self.map_graphic_list.setCurrentIndex(new_index)
                found_graphic_index = new_index

        # If there are no graphics, only grid can be selected
        if self.map_graphic_list.count() > 0:
            self.map_graphic_svg.setEnabled(True)
            self.map_graphic_list.setEnabled(True)
            self._auto_detect_suitable_graphic()
        else:
            self.map_graphic_svg.setEnabled(False)
            self.map_graphic_list.setEnabled(False)
            self.map_graphic_grid.setChecked(True)

        # For new effects, auto select the first graphic
        if is_new_file:
            self.map_graphic_svg.setChecked(True if self.map_graphic_list.count() > 0 else False)
            self._auto_detect_suitable_graphic()

        # For existing effects, (re)select the correct graphic in list
        if self.data["map_graphic"] and found_graphic_index:
            self.map_graphic_list.setCurrentIndex(found_graphic_index)

    def _auto_detect_suitable_graphic(self):
        """
        When loading a new device and the 'graphic' option is set, determine
        the best graphic (as there could be multiple with the same cols/rows)
        """
        self.map_graphic_list.setCurrentIndex(0)
        current_locale = self.i18n.get_current_locale()

        # Pick graphic closely matching device name and locale (if applicable)
        device_name = self.map_device_combo.currentText()
        for name in self.graphic_list.keys():
            graphic = self.graphic_list[name]
            locale = graphic["locale"]
            if name.find(device_name) != -1 and locale == current_locale:
                self.map_graphic_list.setCurrentText(name)

            if name.find(device_name) != -1 and not locale:
                self.map_graphic_list.setCurrentText(name)

    def _set_map_grid(self):
        """
        User selects the "Grid" radio button.
        """
        self.map_graphic_list.setEnabled(False)
        self.map_graphic_list.setCurrentIndex(-1)
        self._update_graphic_preview()

    def _set_mode_graphic(self):
        """
        User selects the "Graphic" radio button.
        """
        self.map_graphic_list.setEnabled(True)
        self._auto_detect_suitable_graphic()
        self._update_graphic_preview()

    def _update_graphic_preview(self):
        """
        The graphic options have changed, refresh the preview.
        """
        device_map = effects.DeviceMapGraphics(self.appdata)
        device_info = self.device_info[self.map_device_combo.currentIndex()]
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
        newdata = self.data.copy()

        # Metadata fields
        newdata["name"] = self.name.text()
        newdata["author"] = self.author.text()
        newdata["author_url"] = self.author_url.text()
        newdata["summary"] = self.summary.toPlainText()

        # Device mapping information
        if not newdata["type"] == effects.TYPE_SCRIPTED:
            device_name = self.map_device_combo.currentText()
            device_info = self.device_info[self.map_device_combo.currentIndex()]
            graphic_name = self.map_graphic_list.currentText()

            newdata["map_device"] = device_name
            newdata["map_device_icon"] = device_info["icon"]
            newdata["map_cols"] = device_info["cols"]
            newdata["map_rows"] = device_info["rows"]
            newdata["map_graphic"] = ""
            if graphic_name:
                newdata["map_graphic"] = self.graphic_list[graphic_name]["filename"]

        self.callback_fn(newdata)
