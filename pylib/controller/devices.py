#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2021 Luke Horwell <code@horwell.me>
#
"""
This module controls the 'Devices' tab of the Controller GUI.
"""

from .. import common
from .. import effects
from .. import locales
from .. import preferences as pref
from .. import middleman
from . import shared

import os
import subprocess
import time

from PyQt5.QtCore import Qt, QSize, QMargins, QThread
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QWidget, QScrollArea, QGroupBox, QGridLayout, \
                            QPushButton, QToolButton, QMessageBox, QListWidget, \
                            QTreeWidget, QTreeWidgetItem, QLabel, QComboBox, \
                            QSpacerItem, QSizePolicy, QSlider, QCheckBox, \
                            QButtonGroup, QRadioButton, QDialog, QTableWidget, \
                            QTableWidgetItem, QAction, QHBoxLayout

# Error codes
ERROR_NO_DEVICE = 0
ERROR_BACKEND_IMPORT = 1
ERROR_NO_BACKEND = 2


class DevicesTab(shared.TabData):
    """
    Allows the user to quickly change the existing state of the device right now.
    """
    def __init__(self, appdata):
        super().__init__(appdata)
        self.special_controls = SpecialControls(appdata)

        # Session
        self.current_backend = None
        self.current_uid = None
        self.current_serial = None
        self.load_thread = None

        # UI Elements
        self.Contents = self.main_window.findChild(QWidget, "DeviceContents")
        self.SidebarTree = self.main_window.findChild(QTreeWidget, "DeviceSidebarTree")
        self.SidebarTree.itemClicked.connect(self._sidebar_changed)

        # Avoid garbage collection cleaning up invisible controls
        self.btn_grps = {}

    def set_tab(self):
        """
        Device tab opened. Populate the device and task lists, and open the
        properties for the first device (if applicable)
        """
        # Open all 'sidebar' tree branches
        self.SidebarTree.expandAll()
        self.SidebarTree.setEnabled(True)

        # Populate sidebar
        tasks_branch = self.SidebarTree.invisibleRootItem().child(0)
        devices_branch = self.SidebarTree.invisibleRootItem().child(1)

        # Give IDs for fixed items
        tasks_branch.section = None
        devices_branch.section = None
        tasks_branch.child(0).section = "apply-to-all"

        # Backends are still initialising
        if not self.appdata.ready:
            self._open_loading()
            return

        # Recache the device list
        self.SidebarTree.parent().show()
        self.appdata.device_list = self.middleman.get_device_list()
        unknown_device_list = self.middleman.get_unsupported_devices()

        # Clear device entries
        devices_branch.takeChildren()
        for device_item in self.appdata.device_list:
            item = QTreeWidgetItem()
            item.setText(0, device_item["name"])
            item.setIcon(0, QIcon(device_item["form_factor"]["icon"]))
            item.section = "device"
            item.backend = device_item["backend"]
            item.uid = device_item["uid"]
            devices_branch.addChild(item)

        devices_branch.sortChildren(0, Qt.AscendingOrder)

        for device_item in unknown_device_list:
            item = QTreeWidgetItem()
            item.setText(0, device_item["name"])
            item.setIcon(0, QIcon(device_item["form_factor"]["icon"]))
            item.section = "device-unknown"
            item.backend = device_item["backend"]
            devices_branch.addChild(item)

        # Only show tasks when there are multiple devices present
        if len(self.appdata.device_list) > 1:
            tasks_branch.setHidden(False)
        else:
            tasks_branch.setHidden(True)

        # Backends loaded, but no usable devices
        if len(self.appdata.device_list) == 0 and len(unknown_device_list) > 0:
            devices_branch.child(0).setSelected(True)
            self.open_unknown_device(devices_branch.child(0).backend)

        # All backends failed to load
        elif len(self.middleman.backends) == 0 and len(self.middleman.import_errors) > 0:
            self._open_no_backend_found(ERROR_BACKEND_IMPORT)

        # No backends are installed
        elif len(self.middleman.backends) == 0 and len(self.middleman.not_installed) > 0:
            self._open_no_backend_found(ERROR_NO_BACKEND)

        # Backends present, but no devices listed
        elif len(self.appdata.device_list) == 0:
            self._open_no_backend_found(ERROR_NO_DEVICE)

        # Open the first device initially
        if len(self.appdata.device_list) > 0:
            first_item = devices_branch.child(0)
            first_item.setSelected(True)
            self.open_device(first_item.backend, first_item.uid)

    def _sidebar_changed(self, item):
        """
        User chooses an item on the sidebar. The "section" variable is appended
        directly into the QTreeWidgetItem.
        """
        if item.section == "apply-to-all":
            self.open_apply_to_all()
        elif item.section == "device-unknown":
            self.open_unknown_device(item.backend)
        elif item.section == "device":
            self.open_device(item.backend, item.uid)

    def open_device(self, backend, uid):
        """
        Show details and controls to instant change the current parameters for
        the specified device.
        """
        self.set_cursor_busy()
        device = self.middleman.get_device(backend, uid)

        if type(device) in [None, str]:
            _ = self._
            backend_name = middleman.BACKEND_ID_NAMES[backend]

            msg1 = _("An error occurred while reading this device. This could be either be a bug in Polychromatic or the [] backend.").replace("[]", backend_name)
            msg2 = _("Try switching to this device again. If this appears once more, try restarting the backend and application. Otherwise, please raise an issue on the relevant project's repository.")

            self.widgets.open_dialog(self.widgets.dialog_error, _("Backend Error"), msg1, msg2, device)
            self.open_bad_device(msg1, msg2, device)
            return

        self.current_backend = backend
        self.current_uid = uid
        self.current_serial = device["serial"]

        layout = self.Contents.layout()
        shared.clear_layout(layout)

        # Show the device's name, image and a summarised status
        real_image = device["real_image"]
        if not device["real_image"]:
            real_image = common.get_icon("devices", "noimage")

        indicators = []
        for item in device["summary"]:
            indicators.append({
                "icon": item["icon"],
                "label": item["label"]
            })

        # The summary indicators only show current effect/preset when set
        state_effect = device["state"]["effect"]
        state_preset = device["state"]["preset"]

        if state_preset:
            indicators = [
                {
                    "icon": None,
                    "label": self._("Preset:")
                },
                {
                    "icon": state_preset["icon"],
                    "label": state_preset["name"]
                }
            ]

        elif state_effect:
            indicators = [
                {
                    "icon": None,
                    "label": self._("Playing:")
                },
                {
                    "icon": state_effect["icon"],
                    "label": state_effect["name"]
                }
            ]

        buttons = [
            {
                "id": "device-info",
                "icon": None,
                "label": self._("Device Info"),
                "disabled": False,
                "action": self.show_device_info
            }
        ]

        summary = self.widgets.create_summary_widget(real_image, device["name"], indicators, buttons)
        layout.addWidget(summary)

        # Create controls for available options
        multiple_zones = len(device["zone_options"].keys()) > 1

        for zone in device["zone_options"].keys():
            current_option_id, current_option_data, current_colours = middleman.Middleman._get_current_device_option(middleman.Middleman, device, zone)
            zone_label = device["zone_labels"][zone]
            widgets = []

            # Effect options will be collected and presented as a group of buttons
            options = device["zone_options"][zone]
            effect_options = []

            # Show brightness first (if present)
            for option in options:
                if option["id"] == "brightness":
                    widgets.append(self._create_row_control(device, zone, option))

            # Effects
            for option in options:
                if option["type"] == "effect":
                    if state_effect:
                        # Ignore active hardware effect when software effect is in use.
                        option["active"] = False
                        current_option_id = None

                    effect_options.append(option)
                    continue

            if len(effect_options) > 0:
                effect_controls = self._create_effect_controls(zone, effect_options)
                param_controls = self._create_effect_parameter_controls(zone, current_option_id, effect_options)
                if effect_controls:
                    widgets.append(effect_controls)
                if param_controls:
                    widgets.append(param_controls)

            # Colours
            if current_colours and len(current_colours) > 0:
                for colour_no, colour_hex in enumerate(current_colours):
                    widgets.append(self._create_colour_control(colour_no, colour_hex, current_option_id, current_option_data, zone, device["monochromatic"]))

            # Other controls (e.g. brightness, poll rate)
            for option in options:
                if not option["type"] == "effect" and not option["id"] == "brightness":
                    widgets.append(self._create_row_control(device, zone, option))

            # Polychromatic-specific interfaces
            # -- DPI
            if zone == "main" and device["dpi_x"]:
                widgets.append(self.special_controls.create_dpi_control(device))

            # -- Mouse Acceleration
            if zone == "main" and device["form_factor"]["id"] == "mouse":
                widgets.append(self.special_controls.create_mouse_accel_control())

            # Group controls if there are multiple zones
            if multiple_zones:
                group = self.widgets.create_group_widget(zone_label)
                for widget in widgets:
                    group.layout().addWidget(widget)
                layout.addWidget(group)
            else:
                for widget in widgets:
                    layout.addWidget(widget)

        layout.addStretch()
        self.set_cursor_normal()

    def reload_device(self):
        """
        Reloads the current device page.
        """
        self.open_device(self.current_backend, self.current_uid)

    def _create_row_control(self, device, zone, option):
        """
        Returns a row widget consisting of the correct controls and bindings.
        """
        option_id = option["id"]
        option_label = option["label"]

        if option["type"] == "slider":
            return self.widgets.create_row_widget(option_label, self._create_control_slider(device, zone, option))

        elif option["type"] == "toggle":
            return self.widgets.create_row_widget(option_label, self._create_control_toggle(device, zone, option))

        elif option["type"] == "multichoice":
            return self.widgets.create_row_widget(option_label, self._create_control_select(device, zone, option))

        elif option["type"] == "label":
            return self.widgets.create_row_widget(option_label, self._create_control_label(device, zone, option))

        elif option["type"] == "dialog":
            return self.widgets.create_row_widget(option_label, self._create_control_dialog(device, zone, option))

    def _create_control_slider(self, device, zone, option):
        """
        Prepares and returns a slider for changing options.
        """
        slider = QSlider(Qt.Horizontal)
        slider.setValue(option["value"])
        slider.setMinimum(option["min"])
        slider.setMaximum(option["max"])
        slider.setSingleStep(option["step"])
        slider.setPageStep(option["step"] * 2)
        slider.setMaximumWidth(150)

        # Qt bug: Ticks won't appear with stylesheet
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(option["max"] / 10)

        label = QLabel()
        label.setText(str(option["value"]) + option["suffix"])

        # Change label while sliding
        def _slider_moved(value):
            label.setText(str(value) + option["suffix"])
        slider.sliderMoved.connect(_slider_moved)
        slider.valueChanged.connect(_slider_moved)

        # Send request once dropped
        def _slider_dropped():
            self._event_set_option(device, zone, option["id"], slider.value())
        slider.sliderReleased.connect(_slider_dropped)
        slider.valueChanged.connect(_slider_dropped)

        return [slider, label]

    def _create_control_toggle(self, device, zone, option):
        """
        Prepares and returns a toggle for changing options.
        """
        checkbox = QCheckBox(self._("Enabled"))

        if option["active"]:
            checkbox.setChecked(option["active"])

        def _state_changed():
            self._event_set_option(device, zone, option["id"], checkbox.isChecked())

        checkbox.stateChanged.connect(_state_changed)
        return [checkbox]

    def _create_control_select(self, device, zone, option):
        """
        Prepares and returns a dropdown for changing options.
        """
        params = option["parameters"]
        current_index = 0

        combo = QComboBox()
        combo.setIconSize(QSize(16, 16))
        for i, param in enumerate(params):
            icon_path = common.get_icon("params", param["id"])
            combo.addItem(param["label"])

            if icon_path:
                combo.setItemIcon(combo.count() - 1, QIcon(icon_path))

            if param["active"] is True:
                current_index = i
            i = i + 1

        combo.setCurrentIndex(current_index)

        def _current_index_changed(index):
            param = params[index]
            self._event_set_option(device, zone, option["id"], param["data"])

        combo.currentIndexChanged.connect(_current_index_changed)
        return [combo]

    def _create_control_label(self, device, zone, option):
        """
        Prepares and returns a control that just shows a string.
        """
        label = QLabel()
        label.setText(option["message"])
        return [label]

    def _create_control_dialog(self, device, zone, option):
        """
        Prepares and returns a control that shows a message when clicking the button.
        """
        def _open_dialog():
            dialog_title = middleman.BACKEND_ID_NAMES[device["backend"]]
            self.widgets.open_dialog(self.widgets.dialog_generic,
                                    dialog_title,
                                    option["message"])

        # Widget and layout keeps the button left-aligned
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        button = QPushButton()
        button.setText(option["button_text"])
        button.clicked.connect(_open_dialog)
        layout.addWidget(button)
        layout.addStretch()
        return [widget]

    def _create_effect_controls(self, zone, effect_options):
        """
        Groups all options with the "effect" type and present them as larger buttons.
        """
        widgets = []
        self.btn_grps[zone] = QButtonGroup()

        for effect in effect_options:
            fx_id = effect["id"]
            fx_params = effect["parameters"]
            fx_string = effect["label"]
            fx_active = effect["active"]
            fx_colours = effect["colours"]

            button = QToolButton()
            button.setText(fx_string)
            button.setCheckable(True)
            button.setIconSize(QSize(40, 40))
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setIcon(QIcon(common.get_icon("options", fx_id)))
            button.setMinimumHeight(70)
            button.setMinimumWidth(70)
            button.effect = effect
            button.zone = zone
            self.btn_grps[zone].addButton(button)

            if fx_active:
                button.setChecked(True)

            widgets.append(button)

        def _clicked_effect_button(button):
            effect = button.effect
            zone = button.zone
            param_count = len(effect["parameters"])
            option_id = effect["id"]
            option_data = None
            colour_hex = []

            # Use saved colour, if available for this effect
            if len(effect["parameters"]) == 0:
                colour_hex = effect["colours"]

            # For effects with parameters, the second one will be used as the first may be 'random' or 'off'.
            if param_count > 0:
                if param_count == 1:
                    param = effect["parameters"][0]
                elif param_count >= 2:
                    param = effect["parameters"][1]

                option_data = param["data"]
                colour_hex = param["colours"]

            self.dbg.stdout("Setting effect {0} (data: {1}) on {2} device {3} (zone: {4}, colours: {5})".format(option_id, str(option_data), self.current_backend, self.current_uid, zone, str(colour_hex)), self.dbg.action, 1)
            response = self.middleman.set_device_state(self.current_backend, self.current_uid, self.current_serial, zone, option_id, option_data, colour_hex)
            self._event_check_response(response)
            self.reload_device()

        self.btn_grps[zone].buttonClicked.connect(_clicked_effect_button)

        if not widgets:
            return None

        return self.widgets.create_row_widget(self._("Effect"), widgets, wrap=True)

    def _create_effect_parameter_controls(self, zone, effect_id, effect_options):
        """
        Creates a set of radio buttons for changing the current effect's parameter.
        """
        widgets = []

        def _clicked_param_button():
            for radio in self.btn_grps["radio_param_" + zone]:
                if not radio.isChecked():
                    continue

                self.dbg.stdout("Setting parameter {} for {} on {} device {} (zone: {}, colours: {})".format(radio.option_data, radio.option_id, self.current_backend, self.current_uid, radio.zone, str(radio.colour_hex)), self.dbg.action, 1)
                self.middleman.set_device_state(self.current_backend, self.current_uid, self.current_serial, radio.zone, radio.option_id, radio.option_data, radio.colour_hex)
                self.reload_device()

        for effect in effect_options:
            if not effect["id"] == effect_id:
                continue

            for param in effect["parameters"]:
                label = param["label"]

                radio = QRadioButton()
                radio.setText(label)
                radio.clicked.connect(_clicked_param_button)

                radio.option_id = effect_id
                radio.option_data = param["data"]
                radio.zone = zone
                radio.colour_hex = param["colours"]

                if param["active"]:
                    radio.setChecked(True)

                icon = common.get_icon("params", param["id"])
                if icon:
                    radio.setIcon(QIcon(icon))
                    radio.setIconSize(QSize(22, 22))

                widgets.append(radio)

        if not widgets:
            return None

        self.btn_grps["radio_param_" + zone] = widgets
        return self.widgets.create_row_widget(self._("Effect Mode"), widgets, vertical=True)

    def _create_colour_control(self, colour_no, colour_hex, option_id, option_data, zone, monochromatic):
        """
        Creates a row control for setting the current colour for the specified
        option (effect)

        colour_no is 0-based. 0 = Primary, 1 = Secondary, etc
        """
        pretty_labels = {
            0: self._("Primary Colour"),
            1: self._("Secondary Colour"),
            2: self._("Tertiary Colour")
        }
        try:
            label = pretty_labels[colour_no]
        except KeyError:
            label = self._("Colour []").replace("[]", str(colour_no))

        _set_data = {"zone": zone, "colour_no": colour_no}

        def _set_new_colour(new_hex, data):
            device = self.middleman.get_device(self.current_backend, self.current_uid)
            self.dbg.stdout("Setting colour of current effect on {0} device {1} (zone: {2}, colour {3}: {4})".format(device["backend"], device["uid"], data["zone"], str(data["colour_no"]), new_hex), self.dbg.action, 1)
            response = self.middleman.set_device_colour(device, data["zone"], new_hex, data["colour_no"])
            self._event_check_response(response)

        return self.widgets.create_row_widget(label, [self.widgets.create_colour_control(colour_hex, _set_new_colour, _set_data, self._("Change []").replace("[]", label), monochromatic)])

    def _event_set_option(self, device, zone, option_id, option_data, colour_hex=[]):
        """
        After clicking or changing an option, send this change to the backend.
        """
        backend = device["backend"]
        uid = device["uid"]
        serial = device["serial"]
        self.dbg.stdout("Setting option '{0}' on {1} ({2} device {3})".format(option_id, device["name"], backend, uid), self.dbg.action, 1)
        self.dbg.stdout("  -> Zone: {0} | Param: {1} | Colours: {2}".format(zone, option_data, colour_hex), self.dbg.action, 1)
        response = self.middleman.set_device_state(backend, uid, serial, zone, option_id, option_data, colour_hex)
        self._event_check_response(response)

    def _event_check_response(self, response):
        """
        Checks the result of the request to the backend. Upon failure, inform the user.
        """
        dbg = self.dbg
        _ = self._
        backend_name = middleman.BACKEND_ID_NAMES[self.current_backend]

        if response == True:
            dbg.stdout("Request successful", dbg.success, 1)
        elif response == False:
            dbg.stdout("Invalid request!", dbg.error, 1)
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     _("Controller Error"),
                                     _("The request is invalid or unsupported at this time. This could be due to a programming error in the application."),
                                    _("If this can be reproduced several times, please create a bug via Help → Report a Bug."))
        elif response == None:
            dbg.stdout("Device no longer available", dbg.error, 1)
            self.widgets.open_dialog(self.widgets.dialog_warning,
                                     _("Device Unavailable"),
                                     _("The request could not be completed due to devices being removed/inserted."),
                                     _("Please refresh and try again."))
            self.reload_device()
        elif type(response) == str:
            dbg.stdout("Backend threw an exception", dbg.error, 1)
            print(response)
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     _("Backend Error"),
                                     _("An error occurred while processing this request with [].").replace("[]", backend_name),
                                     traceback=response)

    def _open_loading(self):
        """
        Show a skeleton loading screen while backends finish loading.

        A thread will spawn to refresh the devices tab (if open) when the
        middleman has fully populated.
        """
        if self.load_thread:
            return

        # Sidebar
        self.SidebarTree.setEnabled(False)
        tasks_branch = self.SidebarTree.invisibleRootItem().child(0)
        devices_branch = self.SidebarTree.invisibleRootItem().child(1)
        tasks_branch.setHidden(True)

        # Skeleton devices
        device_icon = QIcon()
        device_icon.addFile(common.get_icon("general", "placeholder"), mode=QIcon.Disabled)
        skel_strings = [
            "█████████████",
            "████████████",
            "█████████",
            "███████████",
            "███████",
        ]
        for i in range(0, 5):
            skel = QTreeWidgetItem()
            skel.setText(0, skel_strings[i])
            skel.setIcon(0, device_icon)
            skel.setDisabled(True)
            devices_branch.addChild(skel)

        # Skeleton summary
        def dummy():
            pass

        buttons = []
        indicators = [
            {
                "icon": common.get_icon("general", "placeholder"),
                "label": "██████"
            },
            {
                "icon": common.get_icon("general", "placeholder"),
                "label": "███"
            }
        ]
        summary = self.widgets.create_summary_widget(common.get_icon("devices", "noimage"), "████████████", indicators, buttons)

        # Skeleton device controls (brightness & effect)
        skels_text = summary.findChildren(QLabel)
        skels_bg = []

        dummy_slider = QLabel("________________________")
        dummy_slider.setMaximumWidth(180)
        dummy_slider.setAlignment(Qt.AlignLeft)
        skels_bg.append(dummy_slider)

        dummy_buttons = []
        for i in range(0, 5):
            dummy = QLabel()
            dummy.setMinimumHeight(70)
            dummy.setMinimumWidth(70)
            dummy.setMaximumHeight(70)
            dummy.setMaximumWidth(70)
            dummy.setAlignment(Qt.AlignLeft)
            dummy_buttons.append(dummy)
            skels_bg.append(dummy)

        row1 = self.widgets.create_row_widget("███████", [dummy_slider], wrap=True)
        row2 = self.widgets.create_row_widget("████", dummy_buttons, wrap=True)

        label1 = row1.findChild(QLabel)
        label2 = row2.findChild(QLabel)

        skels_text.append(label1)
        skels_text.append(label2)

        # Apply skeleton styling
        for skel in skels_bg:
            skel.setStyleSheet("QLabel { background-color: #202020; color: #202020; margin: 4px 0; }")
        for skel in skels_text:
            skel.setStyleSheet("QLabel { color: #202020; }")

        # Append widgets
        layout = self.Contents.layout()
        for widget in [summary, row1, row2]:
            layout.addWidget(widget)
        layout.addStretch()

        class WaitForBackendThread(QThread):
            @staticmethod
            def run():
                while not self.appdata.ready:
                    time.sleep(0.05)

                refresh = self.main_window.findChild(QAction, "actionRefreshTab")
                refresh.trigger()

        self.load_thread = WaitForBackendThread()
        self.load_thread.start()
        self.set_cursor_busy()

    def _open_no_backend_found(self, message_id):
        """
        No backends are present. Hide the sidebar and show a full screen message.

        Params:
            message_id      (int)   An self.err_* integer.
        """
        self.SidebarTree.parent().hide()

        layout = self.Contents.layout()
        shared.clear_layout(layout)

        graphic = {
            ERROR_NO_DEVICE: common.get_icon("empty", "nodevice"),
            ERROR_BACKEND_IMPORT: common.get_icon("empty", "nobackend"),
            ERROR_NO_BACKEND: common.get_icon("empty", "nobackend")
        }

        title = {
            ERROR_NO_DEVICE: self._("No devices connected"),
            ERROR_BACKEND_IMPORT: self._("No backends loaded"),
            ERROR_NO_BACKEND: self._("No backends installed")
        }

        subtitle = {
            ERROR_NO_DEVICE: self._("Plug in a compatible device to control its lighting effects and features"),
            ERROR_BACKEND_IMPORT: self._("Consult the logs and troubleshooter for hints on fixing this problem"),
            ERROR_NO_BACKEND: self._("Install a compatible backend to configure lighting effects")
        }

        buttons = {
            ERROR_NO_DEVICE: [
                {
                    "label": self._("Troubleshoot"),
                    "icon_folder": "general",
                    "icon_name": "preferences",
                    "action": self._start_troubleshooter
                }
            ],
            ERROR_NO_BACKEND: [
                {
                    "label": self._("Online Help"),
                    "icon_folder": "general",
                    "icon_name": "external",
                    "action": self._open_online_help
                },
                {
                    "label": self._("Troubleshoot"),
                    "icon_folder": "general",
                    "icon_name": "preferences",
                    "action": self._start_troubleshooter
                }
            ]
        }
        buttons[ERROR_BACKEND_IMPORT] = buttons[ERROR_NO_BACKEND].copy()
        buttons[ERROR_BACKEND_IMPORT].append({
            "label": self._("Show Error Details"),
            "icon_folder": "general",
            "icon_name": "warning",
            "action": self._open_backend_exception
        })

        self.widgets.populate_empty_state(layout, graphic[message_id], title[message_id], subtitle[message_id], buttons[message_id])

    def _open_online_help(self):
        """
        Opens the documentation online to learn more about Polychromatic's device
        functionality.
        """
        self.appdata.menubar.online_help()

    def _start_troubleshooter(self):
        """
        Starts the specified troubleshooter; the troubleshooter for the only
        backend available, or shows a prompt for the user to choose the backend
        to troubleshoot.
        """
        # TODO: Prompt not implemented as only one backend (OpenRazer)
        self.appdata.menubar.openrazer.troubleshoot()

    def _open_backend_exception(self):
        """
        Opens a dialog showing the details of an exception for one of the backends.
        """
        dbg = self.dbg
        _ = self._

        for backend_id in self.middleman.import_errors.keys():
            backend_name = middleman.BACKEND_ID_NAMES[backend_id]
            exception = self.middleman.import_errors[backend_id].strip()
            dbg.stdout("\n{0}\n------------------------------\n{1}\n".format(backend_name, exception), dbg.error)
            self.widgets.open_dialog(self.widgets.dialog_generic,
                                    _("Backend Error: []").replace("[]", backend_name),
                                    _("Polychromatic won't be able to interact with devices available under [] until the problem has been resolved.").replace("[]", backend_name),
                                    info_text=_("The last line of the exception was:") + "\n" + exception.split("\n")[-1],
                                    traceback=exception)

    def open_unknown_device(self, backend):
        """
        Show guidance on a device that could be controlled, but isn't possible right now.
        """
        layout = self.Contents.layout()
        shared.clear_layout(layout)

        backend_name = middleman.BACKEND_ID_NAMES[backend]

        def _restart_backend():
            backend_to_restart_fn = {
                "openrazer": self.appdata.menubar.openrazer.restart_daemon
            }
            backend_to_restart_fn[backend]()

        self.widgets.populate_empty_state(layout,
            common.get_icon("empty", "nodevice"),
            self._("Unrecognised Device"),
            self._("The [name] backend hasn't registered this device.").replace("[name]", backend_name) + "\n\n" + \
                self._("This could indicate an error initializing the backend or an installation problem.") + "\n" + \
                self._("Alternately, this may happen if this hardware is not yet supported under this version of [name].").replace("[name]", backend_name),
            [
                {
                    "label": "{0} {1}".format(self._("Restart"), backend_name),
                    "icon_folder": "general",
                    "icon_name": "refresh",
                    "action": _restart_backend
                },
                {
                    "label": self._("Troubleshoot"),
                    "icon_folder": "general",
                    "icon_name": "preferences",
                    "action": self._start_troubleshooter
                },
                {
                    "label": self._("Online Help"),
                    "icon_folder": "general",
                    "icon_name": "external",
                    "action": self._open_online_help
                },
            ])

    def open_bad_device(self, msg1, msg2, exception):
        """
        Show a page to inform the user the device could not be opened. Possibly
        due to a temporary glitch or unsupported feature.
        """
        layout = self.Contents.layout()
        shared.clear_layout(layout)

        def _view_details():
            _ = self._
            self.widgets.open_dialog(self.widgets.dialog_generic, _("Error Details"), msg1, msg2, exception)

        self.widgets.populate_empty_state(layout, common.get_icon("empty", "nobackend"), self._("There was a problem opening this device"), "",
            [
                {
                    "label": self._("View Details"),
                    "icon_folder": "emblems",
                    "icon_name": "software",
                    "action": _view_details
                }
            ])
        self.set_cursor_normal()

    def open_apply_to_all(self):
        """
        Show options for setting options that apply to all connected devices, where
        the option is supported.
        """
        self.set_cursor_busy()
        layout = self.Contents.layout()
        shared.clear_layout(layout)

        bulk = common.get_bulk_apply_options(self._, self.middleman.get_device_all())

        effects = bulk["effects"]
        brightnesses = bulk["brightness"]

        # For creating controls
        self.btn_grps["all"] = QButtonGroup()

        def _create_button(label, icon_path, option_id, option_data, option_colours=0, colour=None):
            # Same button as effects
            button = QToolButton()
            button.setText(label)
            button.setIconSize(QSize(30, 30))
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.setIcon(QIcon(icon_path))
            button.setMinimumHeight(40)
            button.setMinimumWidth(130)
            button.option_id = option_id
            button.option_data = option_data
            button.required_colours = option_colours
            button.colour = colour
            self.btn_grps["all"].addButton(button)
            return button

        def add_to_page(label, widgets):
            group = self.widgets.create_group_widget(label)
            group.layout().setAlignment(Qt.AlignTop)
            group.layout().setContentsMargins(QMargins(30, 5, 30, 5))
            row = 0
            col = 0
            for position, widget in enumerate(widgets):
                group.layout().addWidget(widget, row, col)
                col += 1
                if col >= 5:
                    col = 0
                    row += 1
            layout.addWidget(group)

        def _apply_button_clicked(button):
            self.set_cursor_busy()
            if button.option_id:
                # Setting effect/brightness
                self.middleman.set_bulk_option(button.option_id, button.option_data, button.required_colours)
            else:
                # Setting colour
                self.middleman.set_bulk_colour(button.colour)
            self.set_cursor_normal()

        self.btn_grps["all"].buttonClicked.connect(_apply_button_clicked)

        # Brightness
        if len(brightnesses) > 0:
            widgets = []
            for brightness in brightnesses:
                option_id = brightness["id"]
                option_data = brightness["data"]
                label = brightness["label"]
                icon = common.get_icon("options", str(option_data))
                widgets.append(_create_button(label, icon, option_id, option_data))

            add_to_page(self._("Brightness"), widgets)

        # Options
        if len(effects) > 0:
            widgets = []
            for option in effects:
                option_id = option["id"]
                option_data = option["data"]
                required_colours = option["required_colours"]
                label = option["label"]
                icon = common.get_icon("options", str(option_id))
                widgets.append(_create_button(label, icon, option_id, option_data, option_colours=required_colours))

            add_to_page(self._("Effects"), widgets)

        # Colours
        if len(effects) > 0:
            widgets = []
            for colour in pref.load_file(self.paths.colours):
                label = colour["name"]
                data = colour["hex"]
                icon = common.generate_colour_bitmap(self.dbg, data, 40)
                widgets.append(_create_button(label, icon, None, None, colour=data))

            add_to_page(self._("Colours"), widgets)

        layout.addStretch()
        self.set_cursor_normal()

    def show_device_info(self):
        """
        Opens a dialogue box describing the metadata for the device.
        """
        # Alias
        _ = self._

        # Dialog Controls
        dialog = shared.get_ui_widget(self.appdata, "device-info", QDialog)
        tree = dialog.findChild(QTreeWidget, "DeviceTree")
        btn_close = dialog.findChild(QPushButton, "Close")
        btn_refresh = dialog.findChild(QPushButton, "Refresh")
        btn_test_matrix = dialog.findChild(QPushButton, "TestMatrix")

        # Dialog Button Icons
        if not self.appdata.system_qt_theme:
            btn_refresh.setIcon(self.widgets.get_icon_qt("general", "refresh"))
            btn_test_matrix.setIcon(self.widgets.get_icon_qt("general", "matrix"))
            btn_close.setIcon(self.widgets.get_icon_qt("general", "close"))

        tree.setColumnWidth(0, 250)
        root = tree.invisibleRootItem()

        # Connect signals
        def _close():
            dialog.accept()

        def _populate_tree():
            self.set_cursor_busy()
            root.takeChildren()

            def mkitem(data, value="", icon=None):
                item = QTreeWidgetItem()
                item.setText(0, data)
                if type(value) in [str, int]:
                    item.setText(1, str(value))
                elif type(value) == bool:
                    if value == True:
                        item.setText(1, _("Yes"))
                        item.setIcon(1, QIcon(common.get_icon("general", "success")))
                    else:
                        item.setText(1, _("No"))
                        item.setIcon(1, QIcon(common.get_icon("general", "close")))
                else:
                    item.setText(1, _("(Unavailable or not applicable)"))
                    item.setDisabled(True)
                if icon:
                    item.setIcon(1 if value != "" else 0, QIcon(icon))
                return item

            hw = mkitem(_("Hardware"))
            hw.addChild(mkitem(_("Name"), device["name"]))
            hw.addChild(mkitem(_("Backend"), middleman.BACKEND_ID_NAMES[device["backend"]]))
            hw.addChild(mkitem(_("Internal Device ID"), str(device["uid"])))
            hw.addChild(mkitem(_("Form Factor"), device["form_factor"]["label"], device["form_factor"]["icon"]))
            hw.addChild(mkitem(_("Serial"), device["serial"]))
            hw.addChild(mkitem(_("Image"), device["real_image"], device["real_image"]))
            hw.addChild(mkitem(_("Monochromatic"), device["monochromatic"], common.get_icon("general", "ring-mono") if device["monochromatic"] else common.get_icon("tray", "ring")))
            if device["vid"]:
                hw.addChild(mkitem("VID:PID", "{0}:{1}".format(device["vid"], device["pid"])))
            else:
                hw.addChild(mkitem("VID:PID", None))
            hw.addChild(mkitem(_("Firmware Version"), device["firmware_version"]))
            hw.addChild(mkitem(_("Keyboard Layout"), device["keyboard_layout"]))
            hw.addChild(mkitem(_("Matrix Supported"), device["matrix"]))
            if device["matrix"]:
                dimensions = common.get_plural(device["matrix_rows"], _("1 row"), _("2 rows").replace("2", str(device["matrix_rows"])))
                dimensions += ", " + common.get_plural(device["matrix_cols"], _("1 column"), _("2 columns").replace("2", str(device["matrix_cols"])))
                hw.addChild(mkitem(_("Matrix Dimensions"), dimensions, common.get_icon("general", "matrix")))
                btn_test_matrix.setDisabled(False)
            tree.addTopLevelItem(hw)

            # Summary
            summary = mkitem(_("Current Status"))
            for state in device["summary"]:
                summary.addChild(mkitem(state["label"], "", state["icon"]))
            tree.addTopLevelItem(summary)

            # DPI
            if device["dpi_x"]:
                dpi = mkitem(_("DPI"))
                dpi.addChild(mkitem("DPI X", device["dpi_x"]))
                if device["dpi_y"] > 0:
                    dpi.addChild(mkitem("DPI Y", device["dpi_y"]))
                dpi.addChild(mkitem(_("Default Stages"), ", ".join(map(str, device["dpi_stages"]))))
                dpi.addChild(mkitem(_("Minimum"), device["dpi_min"]))
                dpi.addChild(mkitem(_("Maximum"), device["dpi_max"]))
                tree.addTopLevelItem(dpi)
            else:
                tree.addTopLevelItem(mkitem(_("DPI"), None))

            # Zones
            zones = mkitem(_("Zones"))
            for zone in device["zone_options"].keys():
                label = device["zone_labels"][zone]
                icon = device["zone_icons"][zone]

                zone_item = mkitem(label, "", icon)

                for option in device["zone_options"][zone]:
                    option_icon = common.get_icon("options", option["id"])
                    option_item = mkitem(option["label"], "", option_icon)
                    option_item.addChild(mkitem(_("Internal ID"), option["id"]))
                    option_item.addChild(mkitem(_("Type"), option["type"]))

                    try:
                        if len(option["parameters"]) > 0:
                            param_parent = mkitem(_("Parameters"))
                            for param in option["parameters"]:
                                param_item = mkitem(param["label"], "", common.get_icon("params", param["id"]))
                                param_item.addChild(mkitem(_("Internal ID"), param["id"]))
                                param_item.addChild(mkitem(_("Internal Data"), param["data"]))
                                param_item.addChild(mkitem(_("Active"), param["active"]))
                                if param["colours"]:
                                    for colour_no, colour_hex in enumerate(option["colours"]):
                                        param_item.addChild(mkitem(_("Colour Input []").replace("[]", str(colour_no)), colour_hex, common.generate_colour_bitmap(self.dbg, colour_hex)))
                                param_parent.addChild(param_item)
                            option_item.addChild(param_parent)
                    except KeyError:
                        # N/A: Parameters only for effect/multichoice
                        pass

                    try:
                        option_item.addChild(mkitem(_("Active"), option["active"]))
                    except KeyError:
                        # N/A: Only for effect/toggles
                        pass

                    try:
                        option_item.addChild(mkitem(_("Current Value"), str(option["value"]) + option["suffix"]))
                        option_item.addChild(mkitem(_("Minimum"), option["min"]))
                        option_item.addChild(mkitem(_("Maximum"), option["max"]))
                        option_item.addChild(mkitem(_("Interval"), option["step"]))
                    except KeyError:
                        # N/A: Only for slider
                        pass

                    # Colours (entire option, no parameters)
                    if option["colours"] and not option["parameters"]:
                        for colour_no, colour_hex in enumerate(option["colours"]):
                            option_item.addChild(mkitem(_("Colour Input []").replace("[]", str(colour_no)), colour_hex, common.generate_colour_bitmap(self.dbg, colour_hex)))

                    zone_item.addChild(option_item)
                zones.addChild(zone_item)
            tree.addTopLevelItem(zones)

            tree.expandAll()
            dialog.setWindowTitle("{0} - {1}".format(_("Device Information"), device["name"]))
            self.set_cursor_normal()

        def _test_matrix():
            dialog.accept()
            self._test_device_matrix()

        # Gather data, and exit if an error occurs
        device = self.middleman.get_device(self.current_backend, self.current_uid)
        self._event_check_response(device)

        if device in [str, None, False]:
            return

        btn_close.clicked.connect(_close)
        btn_refresh.clicked.connect(_populate_tree)
        btn_test_matrix.clicked.connect(_test_matrix)
        dialog.open()
        _populate_tree()

    def _test_device_matrix(self):
        """
        Opens a dialogue box to allow the user to test the individual key
        lighting for their device.
        """
        _ = self._
        fx = self.middleman.get_device_object(self.current_backend, self.current_uid)

        # Dialog Controls
        self.dialog = shared.get_ui_widget(self.appdata, "inspect-matrix", QDialog)
        label = self.dialog.findChild(QLabel, "Label")
        table = self.dialog.findChild(QTableWidget, "Matrix")
        btn_close = self.dialog.findChild(QPushButton, "Close")
        cur_pos = self.dialog.findChild(QLabel, "CurrentPosition")

        # Dialog Button Icons
        if not self.appdata.system_qt_theme:
            btn_close.setIcon(self.widgets.get_icon_qt("general", "close"))

        def _close_test():
            # WARNING: Hardcoded 'main' zone for matrix logic
            self.middleman.replay_active_effect(self.current_backend, self.current_uid, "main")
            self.dialog.accept()

        # Populate table
        for x in range(0, fx.cols):
            table.insertColumn(x)
            header = QTableWidgetItem()
            header.setText(str(x))
            table.setHorizontalHeaderItem(x, header)
        for y in range(0, fx.rows):
            table.insertRow(y)
            header = QTableWidgetItem()
            header.setText(str(y))
            table.setVerticalHeaderItem(y, header)

        def _set_pos():
            indexes = table.selectedIndexes()
            fx.clear()
            for index in indexes:
                fx.set(index.column(), index.row(), 255, 255, 255)
            if len(indexes) == 0:
                cur_pos.setText("")
            elif len(indexes) == 1:
                x = indexes[0].column()
                y = indexes[0].row()
                cur_pos.setText(_("Coordinate: X,Y").replace("X", str(x)).replace("Y", str(y)))
            elif len(indexes) > 1:
                cur_pos.setText(_("Coordinate: (Multiple)"))
            fx.draw()

        # Connect signals and set focus
        btn_close.clicked.connect(_close_test)
        table.itemSelectionChanged.connect(_set_pos)
        table.setFocus()
        table.setCurrentCell(0, 0)
        self.dialog.adjustSize()
        self.dialog.setWindowTitle(self._("Inspect Matrix") + " - " + fx.name)
        self.dialog.open()


class SpecialControls(shared.TabData):
    """
    Produces Polychromatic-specific controls for features of this software or
    a fancier interface for hardware settings which would be limited when
    implemented at a backend-level.
    """
    def __init__(self, appdata):
        super().__init__(appdata)

    def create_dpi_control(self, device):
        """
        Creates a sophicated control for setting the DPI X/Y values.

        If a device has unusual requirements or only works on single axis,
        this control shouldn't be used (unspecify "dpi_x") and have the backend
        module define an option to handle the DPI setting.
        """
        dpi_widget = shared.get_ui_widget(self.appdata, "dpi-control", QWidget)

        grid = dpi_widget.findChild(QTableWidget, "Grid")
        slider_x = dpi_widget.findChild(QSlider, "DPI_X_Slider")
        value_x = dpi_widget.findChild(QLabel, "DPI_X_Value")
        slider_y = dpi_widget.findChild(QSlider, "DPI_Y_Slider")
        value_y = dpi_widget.findChild(QLabel, "DPI_Y_Value")
        slider_lock = dpi_widget.findChild(QToolButton, "LockXY")

        # Button group must be attached to class otherwise GC will destroy it
        self.stage_buttons_group = QButtonGroup()
        self.stage_buttons_group.setExclusive(False)

        if not self.appdata.system_qt_theme:
            slider_lock.setIcon(self.widgets.get_icon_qt("general", "lock"))
            # Button padding is too large for this small button
            slider_lock.setStyleSheet("QToolButton { padding: 8px; }")
            value_x.setStyleSheet("QLabel { padding: 4px 0; }")
            value_y.setStyleSheet("QLabel { padding: 4px 0; }")

        # Set up slider parameters and initial values
        for slider in [slider_x, slider_y]:
            slider.setMinimum(device["dpi_min"])
            slider.setMaximum(device["dpi_max"])
            slider.setSingleStep(100)
            slider.setPageStep(200)

        slider_x.setValue(device["dpi_x"])
        slider_y.setValue(device["dpi_y"])
        value_x.setText(str(device["dpi_x"]))
        value_y.setText(str(device["dpi_y"]))

        if int(device["dpi_x"]) == int(device["dpi_y"]):
            slider_lock.setChecked(True)

        # Update grid when moving sliders
        grid.setStyleSheet("QTableView { background-color: #000; gridline-color: #008000; }")
        grid_size = 64
        highest_known_dpi = 20000
        for value in range(0, grid_size):
            grid.insertRow(0)
            grid.insertColumn(0)

        def _refresh_grid_size():
            new_size_x = 53 - int((slider_x.value() / highest_known_dpi) * 50)
            new_size_y = 53 - int((slider_y.value() / highest_known_dpi) * 50)

            if slider_x.value() > highest_known_dpi or slider_y.value() > highest_known_dpi:
                self.dbg.stdout("Your mouse has set a new high DPI record!\nThe DPI grid UI may not display correctly. Please report this as a bug.", self.dbg.warning)

            for pos in range(0, grid_size):
                grid.setRowHeight(pos, new_size_x)
                grid.setColumnWidth(pos, new_size_y)

        # Update controls/label while sliding
        def _update_stage_controls():
            for button in self.stage_buttons_group.buttons():
                button.setChecked(slider_x.value() == slider_y.value() == button.dpi_value)

        def _slider_x_moved(value):
            value_x.setText(str(value))
            if slider_lock.isChecked():
                slider_y.setValue(value)
            _update_stage_controls()

        def _slider_y_moved(value):
            value_y.setText(str(value))
            if slider_lock.isChecked():
                slider_x.setValue(value)
            _update_stage_controls()

        slider_x.sliderMoved.connect(_slider_x_moved)
        slider_x.valueChanged.connect(_slider_x_moved)
        slider_y.sliderMoved.connect(_slider_y_moved)
        slider_y.valueChanged.connect(_slider_y_moved)

        # Send request once dropped
        def _slider_dropped():
            self.dbg.stdout("Setting DPI to {0}, {1}".format(slider_x.value(), slider_y.value()), self.dbg.action, 1)
            tab_devices = self.appdata.tab_devices
            response = self.middleman.set_device_state(tab_devices.current_backend, tab_devices.current_uid, tab_devices.current_serial, "", "dpi", [slider_x.value(), slider_y.value()], [])
            tab_devices._event_check_response(response)

        # TODO: In future, only update after 'mouse drop' or scroll release.
        # Currently it's difficult under stock QSlider. Dragging with mouse only isn't great.
        slider_x.valueChanged.connect(_slider_dropped)
        slider_y.valueChanged.connect(_slider_dropped)
        slider_x.valueChanged.connect(_refresh_grid_size)
        slider_y.valueChanged.connect(_refresh_grid_size)

        # Prepare 'stage' buttons to quickly set default or user-defined stages
        stage_widget = QWidget()
        stage_widget.setLayout(QHBoxLayout())
        stage_widget.layout().setContentsMargins(0, 0, 0, 0)
        stages = device["dpi_stages"]

        if self.appdata.preferences["custom"]["use_dpi_stages"]:
            stages = []
            for i in range(1, 6):
                stages.append(self.appdata.preferences["custom"]["dpi_stage_" + str(i)])
            stages.sort()

        def _set_dpi_by_button(button):
            slider_lock.setChecked(True)
            slider_x.setValue(button.dpi_value)

        def _edit_dpi_stages():
            self.appdata.ui_preferences.open_window(2)

        for index, value in enumerate(stages):
            button = QToolButton()
            button.setCheckable(True)
            if device["dpi_x"] == device["dpi_y"] == value:
                button.setChecked(True)
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.setText(str(value))
            button.dpi_value = value

            if index == 0:
                button.setIcon(self.widgets.get_icon_qt("general", "dpi-slow"))
            elif index == 4:
                button.setIcon(self.widgets.get_icon_qt("general", "dpi-fast"))

            stage_widget.layout().addWidget(button)
            self.stage_buttons_group.addButton(button)

        self.stage_buttons_group.buttonClicked.connect(_set_dpi_by_button)

        edit_btn = QToolButton()
        edit_btn.setText(self._("Edit DPI Stages"))
        edit_btn.setToolTip(self._("Edit DPI Stages"))
        edit_btn.setIcon(self.widgets.get_icon_qt("general", "edit"))
        edit_btn.clicked.connect(_edit_dpi_stages)
        stage_widget.layout().addWidget(edit_btn)

        stage_widget.layout().addStretch()

        _refresh_grid_size()

        return self.widgets.create_row_widget(self._("DPI"), [stage_widget, dpi_widget], vertical=True)

    def create_mouse_accel_control(self):
        """
        Creates a button that'll either:
          - Open mouse acceleration settings for known desktop environments
          - Or inform the user if desktop environment unknown.

        Due to the diverse range of desktop environments, getting mouse
        acceleration values isn't supported right now.
        """
        def _get_current_desktop_env():
            try:
                desktop_env = os.environ["XDG_CURRENT_DESKTOP"]

                # Some distros add a prefix/suffix ("ubuntu", "X-")
                if desktop_env.find("GNOME") != -1:
                    return "GNOME"
                elif desktop_env.find("Cinnamon") != -1:
                    return "Cinnamon"
                elif desktop_env in ["KDE", "MATE", "Pantheon", "LXQt"]:
                    return desktop_env
                return "Unknown"
            except KeyError:
                return "Unknown"

        def _get_command():
            desktop_env = _get_current_desktop_env()
            desktop_to_cmd = {
                "GNOME": "gnome-control-center mouse",
                "Cinnamon": "cinnamon-settings mouse",
                "KDE": "systemsettings5 mouse",
                "MATE": "mate-mouse-properties",
                "Pantheon": "io.elementary.switchboard settings://input/mouse",
                "LXQt": "lxqt-config-input",
            }
            try:
                return desktop_to_cmd[desktop_env]
            except KeyError:
                return None

        def _open_mouse_settings():
            command = _get_command()
            if command:
                self.dbg.stdout("Opening: " + command, self.dbg.action, 1)
                subprocess.Popen(command.split(" "))
                return

            # Desktop environment unknown, inform the user for manual action.
            self.widgets.open_dialog(self.widgets.dialog_generic,
                                     self._("Mouse Acceleration"),
                                     self._("This feature is provided by your operating system. Polychromatic doesn't recognise this desktop environment " + \
                                            "to automatically open the settings window for you.\n\n" + \
                                            "Look for 'mouse', 'input' or 'hardware' in your System Settings."))

        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        button = QToolButton()
        button.setText(self._("Open Mouse Settings"))
        button.setIconSize(QSize(24, 24))
        button.setIcon(QIcon.fromTheme("input-mouse"))
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.clicked.connect(_open_mouse_settings)
        layout.addWidget(button)
        layout.addStretch()

        return self.widgets.create_row_widget(self._("Acceleration"), [widget])

