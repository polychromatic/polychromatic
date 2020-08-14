#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QWidget, QScrollArea, QGroupBox, QGridLayout, \
                            QPushButton, QToolButton, QMessageBox, QListWidget, \
                            QTreeWidget, QTreeWidgetItem, QLabel, QComboBox, \
                            QSpacerItem, QSizePolicy, QSlider, QCheckBox, \
                            QHBoxLayout

class DevicesTab(object):
    """
    Allows the user to quickly change the existing state of the device right now.
    """
    def __init__(self, appdata):
        self.appdata = appdata
        self.widgets = shared.PolychromaticWidgets(appdata)
        self.locales = appdata.locales
        self._ = appdata._

        # Session
        self.current_backend = None
        self.current_uid = None

        # UI Elements
        self.Contents = self.appdata.main_window.findChild(QWidget, "DeviceContents")
        self.SidebarTree = self.appdata.main_window.findChild(QTreeWidget, "DeviceSidebarTree")
        self.SidebarTree.itemClicked.connect(self._sidebar_changed)

    def set_tab(self):
        """
        Device tab opened. Populate the device and task lists, and open the
        properties for the first device (if applicable)
        """
        # Open all 'sidebar' tree branches
        self.SidebarTree.expandAll()

        # Populate sidebar
        tasks_branch = self.SidebarTree.invisibleRootItem().child(0)
        devices_branch = self.SidebarTree.invisibleRootItem().child(1)

        # Give IDs for fixed items
        tasks_branch.section = None
        devices_branch.section = None
        tasks_branch.child(0).section = "apply-to-all"

        # Recache the device list
        self.SidebarTree.parent().show()
        self.appdata.device_list = self.appdata.middleman.get_device_list()
        unknown_device_list = self.appdata.middleman.get_unsupported_devices()

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

        for device_item in self.appdata.middleman.get_unsupported_devices():
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
        if len(self.appdata.device_list) == 0 and len(unknown_device_list) >= 0:
            devices_branch.child(0).setSelected(True)
            self.open_unknown_device(devices_branch.child(0).backend)

        # All backends failed to load
        elif len(self.appdata.middleman.backends) == 0 and len(self.appdata.middleman.import_errors) > 0:
            self._open_no_backend_found(1)

        # No backends are installed
        elif len(self.appdata.middleman.backends) == 0 and len(self.appdata.middleman.not_installed) > 0:
            self._open_no_backend_found(2)

        # Backends present, but no devices listed
        elif len(self.appdata.middleman.backends) == 0:
            self._open_no_backend_found(0)

        # Open the first device initially
        if len(self.appdata.device_list) > 0:
            device = self.appdata.device_list[0]
            self.open_device(device["backend"], device["uid"])
            devices_branch.child(0).setSelected(True)

    def _sidebar_changed(self, item):
        """
        Navigation on sidebar changed. The variable is appended into the QTreeWidgetItem.
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
        self.current_backend = backend
        self.current_uid = uid
        device = self.appdata.middleman.get_device(backend, uid)

        layout = self.Contents.layout()
        shared.clear_layout(layout)

        # Show the device's name, image and a summarised status
        real_image = device["real_image"]
        if not device["real_image"]:
            real_image = os.path.join(self.appdata.data_path, "ui", "img", "devices", "noimage.svg")

        indicators = []
        for item in device["summary"]:
            try:
                label = self.locales.get(item["string_id"])
            except KeyError:
                label = item["string"]
            indicators.append({
                "icon": item["icon"],
                "label": label
            })

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

        # Create controls for avaliable options
        multiple_zones = len(device["zone_options"].keys()) > 1
        current_id, current_data, current_colours = middleman.Middleman._get_current_device_option(middleman.Middleman, device)

        for zone in device["zone_options"].keys():
            zone_name = locales.get(zone)
            widgets = []

            # Effect options will be collected and presented as a group of buttons
            effect_options = []

            for option in device["zone_options"][zone]:
                if option["type"] == "effect":
                    effect_options.append(option)
                    continue

                widgets.append(self._create_row_control(device, zone, option))

            # Effects
            if len(effect_options) > 0:
                widgets.append(self._create_effect_controls(effect_options))

            # DPI
            if zone == "main" and device["dpi_x"]:
                self._create_dpi_control(device)

            # Colours
            if len(current_colours) > 0:
                for colour_hex in current_colours:
                    widgets.append(self._create_colour_control(colour_hex, current_id, current_data))

            # Group controls if there are multiple zones
            if multiple_zones:
                group = self.widgets.create_group_widget(zone_name)
                for widget in widgets:
                    group.layout().addWidget(widget)
                layout.addWidget(group)
            else:
                for widget in widgets:
                    layout.addWidget(widget)

        layout.addStretch()

    def _create_row_control(self, device, zone, option):
        """
        Returns a row widget consisting of the correct controls and bindings.
        """
        option_id = option["id"]
        option_label = locales.get(option_id)

        if option["type"] == "slider":
            return self.widgets.create_row_widget(option_label, self._create_control_slider(device, zone, option))

        elif option["type"] == "toggle":
            return self.widgets.create_row_widget(option_label, self._create_control_toggle(device, zone, option))

        elif option["type"] == "multichoice":
            return self.widgets.create_row_widget(option_label, self._create_control_select(device, zone, option))

    def _create_control_slider(self, device, zone, option):
        """
        Prepares and returns a slider for changing options.
        """
        slider = QSlider(Qt.Horizontal)
        slider.setValue(option["value"])
        slider.setMinimum(option["min"])
        slider.setMaximum(option["max"])
        #slider.setTracking(False) # ???
        slider.setSingleStep(option["step"])
        slider.setPageStep(option["step"] * 2)

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
        for i, param in enumerate(params):
            combo.addItem(locales.get(param["id"]))
            if param["active"] == True:
                current_index = i
            i = i + 1

        combo.setCurrentIndex(current_index)

        def _current_index_changed(index):
            param = params[index]
            self._event_set_option(device, zone, option["id"], param["data"])

        combo.currentIndexChanged.connect(_current_index_changed)
        return [combo]

    def _create_effect_controls(self, effect_options):
        """
        Groups all options with the "effect" type and present them as larger buttons.
        """
        print("stub:_create_effect_controls")
        return self.widgets.create_row_widget(self._("Effects"), [])

    def _create_colour_control(self, colour_hex, current_id, current_data):
        """
        Creates a row control for setting the current colour.
        """
        print("stub:_create_colour_control")
        return self.widgets.create_row_widget(self._("Colour 1"), [])

    def _create_dpi_control(self, device):
        """
        Creates a more sophicated control for setting the DPI.
        """
        print("stub:_create_dpi_control")
        return self.widgets.create_row_widget(self._("DPI"), [])

    def _event_set_option(self, device, zone, option_id, option_data, colour_hex=[]):
        """
        After clicking or changing an option, send this change to the backend.
        """
        dbg = self.appdata.dbg
        backend = device["backend"]
        uid = device["uid"]
        serial = device["serial"]
        dbg.stdout("Setting option '{0}' on {1} ({2} device {3})".format(option_id, device["name"], backend, uid), dbg.action, 1)
        dbg.stdout("  -> Zone: {0} | Param: {1} | Colours: {2}".format(zone, option_data, colour_hex), dbg.action, 1)
        response = self.appdata.middleman.set_device_state(backend, uid, serial, zone, option_id, option_data, colour_hex)

        _ = self._

        if response == True:
            dbg.stdout("Request successful", dbg.success, 1)
        elif response == False:
            dbg.stdout("Invalid request!", dbg.error, 1)
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     _("Controller Error"),
                                     _("The request is invalid or unsupported at this time. This could be due to a programming error in the application."),
                                    _("If this happens again, please create a bug via Help → Report a Bug."))
        elif response == None:
            dbg.stdout("Device no longer available", dbg.error, 1)
            self.widgets.open_dialog(self.widgets.dialog_warning,
                                     _("Device Unavailable"),
                                     _("The request could not be completed due to devices being removed/inserted."),
                                     _("Please refresh and try again."))
        elif type(response) == str:
            dbg.stdout("Backend threw an exception", dbg.error, 1)
            print(response)
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     _("Backend Error"),
                                     _("The request could not be completed as an error was thrown by the backend."),
                                     traceback=response)

    def _open_no_backend_found(self, message_id):
        """
        No backends are present. Hide the sidebar and show a full screen message.

        Params:
            message_id      (int)   Message to display:
                                    0 = No device found
                                    1 = No backends, import error
                                    2 = No backends, none installed
        """
        self.SidebarTree.parent().hide()

        layout = self.Contents.layout()
        shared.clear_layout(layout)

        graphic = {
            0: common.get_icon("empty", "nodevice"),
            1: common.get_icon("empty", "nobackend"),
            2: common.get_icon("empty", "nobackend")
        }

        title = {
            0: self._("No devices connected"),
            1: self._("No backends loaded"),
            2: self._("No backends installed")
        }

        subtitle = {
            0: self._("Plug in a compatible device to control its lighting effects and features"),
            1: self._("Consult the logs and troubleshooter for hints on fixing this problem"),
            2: self._("Install a compatible backend to configure lighting effects")
        }

        buttons = {
            0: [
                {
                    "label": self._("Troubleshoot"),
                    "icon": os.path.join(self.appdata.data_path, "ui", "img", "tabs", "inactive", "preferences.svg"),
                    "action": self._start_troubleshooter
                }
            ],
            2: [
                {
                    "label": self._("Online Help"),
                    "icon": common.get_icon("general", "external"),
                    "action": self._open_online_help
                },
                {
                    "label": self._("Troubleshoot"),
                    "icon": os.path.join(self.appdata.data_path, "ui", "img", "tabs", "inactive", "preferences.svg"),
                    "action": self._start_troubleshooter
                }
            ]
        }
        buttons[1] = buttons[2].copy()
        buttons[1].append({
            "label": self._("Show Error Details"),
            "icon": common.get_icon("general", "warning"),
            "action": self._open_backend_exception
        })

        self.widgets.populate_empty_state(layout, graphic[message_id], title[message_id], subtitle[message_id], buttons[message_id])

    def _open_online_help(self):
        """
        Opens the documentation online to learn more about Polychromatic's device
        functionality.
        """
        print("stub:_open_online_help")

    def _start_troubleshooter(self):
        """
        Starts the specified troubleshooter; the troubleshooter for the only
        backend available, or shows a prompt for the user to choose the backend
        to troubleshoot.
        """
        print("stub:_start_troubleshooter")

    def _open_backend_exception(self):
        """
        Opens a dialog showing the details of an exception for one of the backends.
        """
        print("stub:_open_backend_exception")

    def open_unknown_device(self, backend):
        """
        Show guidance on a device that could be controlled, but isn't possible right now.
        """
        layout = self.Contents.layout()
        shared.clear_layout(layout)

        backend_name = middleman.BACKEND_ID_NAMES[backend]

        def _restart_backend():
            self.appdata.middleman.restart(backend)

        self.widgets.populate_empty_state(layout,
            common.get_icon("empty", "nodevice"),
            self._("Unrecognised Device"),
            self._("The [name] backend hasn't registered this device.").replace("[name]", backend_name) + "\n\n" + \
                self._("This could indicate an error initializing the backend or an installation problem.") + "\n" + \
                self._("Alternately, this may happen if this hardware is not yet supported under this version of [name].").replace("[name]", backend_name),
            [
                {
                    "label": "{0} {1}".format(self._("Restart"), backend_name),
                    "icon": common.get_icon("general", "refresh"),
                    "action": _restart_backend
                },
                {
                    "label": self._("Troubleshoot"),
                    "icon": os.path.join(self.appdata.data_path, "ui", "img", "tabs", "inactive", "preferences.svg"),
                    "action": self._start_troubleshooter
                },
                {
                    "label": self._("Online Help"),
                    "icon": common.get_icon("general", "external"),
                    "action": self._open_online_help
                },
            ])

    def open_apply_to_all(self):
        """
        Show options for setting options that apply to all connected devices, where
        the option is supported.
        """
        layout = self.Contents.layout()
        shared.clear_layout(layout)
        print("stub:open_apply_to_all")

    def show_device_info(self):
        """
        Opens a dialogue box describing the metadata for the device.
        """
        print("stub:show_device_info")
