# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2024 Luke Horwell <code@horwell.me>
"""
This module controls the 'Devices' tab of the Controller GUI.
"""

import json
from polychromatic.procpid import DeviceSoftwareState
from .. import bulkapply
from .. import common
from .. import effects
from .. import locales
from .. import preferences as pref
from .. import middleman
from . import shared
from ..backends._backend import Backend as Backend
from ..qt.flowlayout import FlowLayout as QFlowLayout

import os
import subprocess
import time
import shutil
import webbrowser

from PyQt5.QtCore import Qt, QSize, QMargins, QThread
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QWidget, QDialogButtonBox, QGroupBox, QGridLayout, \
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
        self.current_device = None
        self.load_thread = None

        # UI Elements
        self.Contents = self.main_window.findChild(QWidget, "DeviceContents")
        self.SidebarTree = self.main_window.findChild(QTreeWidget, "DeviceSidebarTree")
        self.SidebarTree.itemClicked.connect(self._sidebar_changed)

        # Useful complimentary software
        self.input_remapper = shutil.which("input-remapper-gtk")

        # Avoid garbage collection cleaning up invisible controls
        self.btn_grps = {}

    def set_tab(self):
        """
        Device tab opened. Populate the device and task lists, and open the
        properties for the first device (if applicable)
        """
        self.set_title(self._("Devices"))

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
        device_list = self.middleman.get_devices()
        unknown_device_list = self.middleman.get_unsupported_devices()

        # Clear device entries
        devices_branch.takeChildren()

        for device in device_list:
            item = QTreeWidgetItem()
            item.setText(0, device.name)
            item.setIcon(0, QIcon(device.form_factor["icon"]))
            item.section = "device"
            item.device_item = device
            devices_branch.addChild(item)

        devices_branch.sortChildren(0, Qt.AscendingOrder)

        # For unknown devices, check support status using local index
        device_index = json.loads(open(f"{self.paths.data_dir}/devices/openrazer.json", "r").read())
        supported_pids = device_index.keys()

        for device in unknown_device_list:
            vidpid = f"{device.vid}:{device.pid}"

            if vidpid in supported_pids:
                device.name = device_index[vidpid].get("name", device.name)
                device.supported = True

            item = QTreeWidgetItem()
            item.setText(0, device.name)
            item.setIcon(0, QIcon(device.form_factor["icon"]))
            item.section = "device-unknown"
            item.device_item = device
            devices_branch.addChild(item)

        # Only show tasks when there are multiple devices present
        if len(device_list) > 1:
            tasks_branch.setHidden(False)
        else:
            tasks_branch.setHidden(True)

        # Backends loaded, but no usable devices
        if len(device_list) == 0 and len(unknown_device_list) > 0:
            first_item = devices_branch.child(0)
            first_item.setSelected(True)
            self.open_unknown_device(first_item.device_item)

        # All backends failed to load
        elif len(self.middleman.backends) == 0 and len(self.middleman.import_errors) > 0:
            self._open_no_backend_found(ERROR_BACKEND_IMPORT)

        # No backends are installed
        elif len(self.middleman.backends) == 0 and len(self.middleman.not_installed) > 0:
            self._open_no_backend_found(ERROR_NO_BACKEND)

        # Backends present, but no devices listed
        elif len(device_list) == 0:
            self._open_no_backend_found(ERROR_NO_DEVICE)

        # Open the first device initially
        if len(device_list) > 0:
            first_item = devices_branch.child(0)
            first_item.setSelected(True)
            self.open_device(first_item.device_item)

    def _sidebar_changed(self, item):
        """
        User chooses an item on the sidebar. The "section" variable is appended
        directly into the QTreeWidgetItem.
        """
        if item.section == "apply-to-all":
            self.open_apply_to_all()
        elif item.section == "device-unknown":
            self.open_unknown_device(item.device_item)
        elif item.section == "device":
            self.open_device(item.device_item)

    def _get_device_summary_widget(self, device):
        """
        Generate the heading at the top of the page that shows the name, image
        and current state of the selected device.
        """
        badges = []
        # TODO: Need new state class
        #current_sw_effect = device["state"]["effect"]
        #current_preset = device["state"]["preset"]

        # Go through each zone and find out if things are the same
        effects_used = []
        effect_name = ""
        effect_icon = ""
        brightnesses = []

        for zone in device.zones:
            for option in zone.options:
                if isinstance(option, Backend.SliderOption) and option.uid == "brightness":
                    brightnesses.append(option.value)
                if isinstance(option, Backend.EffectOption) and option.active:
                    effects_used.append(option.uid)
                    effect_name = option.label
                    effect_icon = option.icon

        state = DeviceSoftwareState(device.serial)
        sw_effect = state.get_effect()
        if sw_effect:
            badges.append({
                "label": sw_effect.get("name"),
                "icon": sw_effect.get("icon"),
            })
        elif effects_used and all(i == effects_used[0] for i in effects_used):
            badges.append({
                "label": effect_name,
                "icon": effect_icon,
            })
        elif effects_used:
            badges.append({
                "label": self._("(Varies)"),
                "icon": common.get_icon("general", "effects"),
            })

        if brightnesses and all(i == brightnesses[0] for i in brightnesses):
            value = brightnesses[0]
            if value >= 40:
                icon = common.get_icon("params", "100")
            elif value >= 1:
                icon = common.get_icon("params", "50")
            else:
                icon = common.get_icon("params", "0")

            badges.append({
                "label": str(value) + "%",
                "icon": icon,
            })
        elif brightnesses:
            badges.append({
                "label": self._("(Varies)"),
                "icon": common.get_icon("options", "brightness"),
            })

        if device.dpi:
            if device.dpi.x == device.dpi.y:
                label = f"{device.dpi.x} DPI"
            else:
                label = f"{device.dpi.x}, {device.dpi.y} DPI"

            badges.append({
                "label": label,
                "icon": common.get_icon("general", "dpi"),
            })

        if device.battery:
            label = f"{str(device.battery.percentage)}%"
            if device.battery.percentage >= 90:
                icon = "battery-100"
            elif device.battery.percentage >= 70:
                icon = "battery-75"
            elif device.battery.percentage >= 40:
                icon = "battery-50"
            elif device.battery.percentage >= 15:
                icon = "battery-25"
            else:
                icon = "battery-0"

            if device.battery.is_charging:
                icon = "battery-charging"
                label += " (charging)"

            badges.append({
                "label": label,
                "icon": common.get_icon("general", icon),
            })

        # TODO: Add additional preset state

        if device.real_image:
            real_image = shared.get_real_device_image(device.real_image)
        else:
            real_image = common.get_icon("devices", "noimage")

        # TODO: Move buttons to toolbar
        buttons = [
            {
                "id": "device-info",
                "icon": None,
                "label": self._("Device Info"),
                "disabled": False,
                "action": self.show_device_info
            }
        ]

        return self.widgets.create_summary_widget(real_image, device.name, badges, buttons)

    def open_device(self, device):
        """
        Show details and controls for changing the current hardware state
        of the specified device.
        """
        self.current_device = device

        self.set_cursor_busy()
        layout = self.Contents.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        shared.clear_layout(layout)

        try:
            device.refresh()
        except Exception as e:
            # State may have changed, reload the device tab.
            # TODO: Show "device changes detected" in status bar. Needs global function.
            self.middleman.invalidate_cache()
            return self.set_tab()

        layout.addWidget(self._get_device_summary_widget(device))

        for zone in device.zones:
            widgets = []
            first_zone = True if device.zones[0] == zone else False

            # Effects are all 'collapsed' into one row. When encountering the first
            # effect, remember the index to insert here later.
            has_effects = False
            effects_index = 0

            for index, option in enumerate(zone.options):
                if isinstance(option, Backend.EffectOption):
                    if not has_effects:
                        has_effects = True
                        effects_index = index
                    continue

                widgets.append(self._create_row_control(option))

            # Controls for effects, its parameters and colours
            def _get_effect_options(zone, force_inactive):
                options = []
                for option in zone.options:
                    # Override active flag when software effect is running.
                    if force_inactive:
                        option.active = False

                    if isinstance(option, Backend.EffectOption):
                        options.append(option)

                return options

            state = DeviceSoftwareState(device.serial)
            sw_effect = state.get_effect()
            effect_options = _get_effect_options(zone, True if sw_effect else False)
            active_effect = self.middleman.get_active_effect(zone)
            effect_row = self._create_effect_controls(zone, effect_options)
            if effect_row:
                widgets.insert(effects_index, effect_row)
                effects_index += 1

            # Show parameters and colours for selected effect (if applicable)
            if active_effect:
                param_row = self._create_effect_parameter_controls(device, zone, active_effect)
                if param_row:
                    widgets.insert(effects_index, param_row)
                    effects_index += 1

                colours_required = self.middleman.get_active_colours_required(active_effect)
                if colours_required > 0:
                    for pos in range(0, colours_required):
                        widgets.insert(effects_index, self._create_colour_control(device, zone, pos, active_effect.colours))
                        effects_index += 1

            # General device controls
            if first_zone:
                # -- Mouse DPI
                if device.dpi:
                    widgets.append(self.special_controls.create_dpi_control(device))

                # TODO: Button to set compatible software effects - or as "Custom" effect?

                # -- Mouse Acceleration
                # TODO: Move to middleman for all interfaces?
                if device.form_factor == "mouse":
                    widgets.append(self.special_controls.create_mouse_accel_control())

                # -- Information about OpenRazer daemon's built-in macro feature (deprecated)
                if device.has_macro_keys:
                   widgets.append(self.special_controls.create_openrazer_macro_control())

                # -- Information about programmable keys
                if device.has_programmable_keys and self.input_remapper:
                    widgets.append(self.special_controls.create_programmable_keys_control(self.input_remapper))

            # Before adding to the main layout, use group boxes if there's multiple zones
            if len(device.zones) > 1:
                group = self.widgets.create_group_widget(zone.label)
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
        self.open_device(self.current_device)

    def _create_row_control(self, option):
        """
        Returns a list of widgets for the specified option.
        """
        if isinstance(option, Backend.SliderOption):
            return self.widgets.create_row_widget(option.label, self._create_control_slider(option))

        elif isinstance(option, Backend.ToggleOption):
            return self.widgets.create_row_widget(option.label, self._create_control_toggle(option))

        elif isinstance(option, Backend.MultipleChoiceOption):
            return self.widgets.create_row_widget(option.label, self._create_control_select(option))

    def _create_control_slider(self, option):
        """
        Returns a list of controls that make up a slider for changing a variable option.
        """
        slider = QSlider(Qt.Horizontal)
        slider.setValue(option.value)
        slider.setMinimum(option.min)
        slider.setMaximum(option.max)
        slider.setSingleStep(option.step)
        slider.setPageStep(option.step * 2)
        slider.setMaximumWidth(150)

        # BUG: Qt: Ticks don't appear with stylesheet
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(int(option.max / 10))

        label = QLabel()
        suffix = option.suffix if option.value == 1 else option.suffix_plural
        label.setText(str(option.value) + suffix)

        # Change label while sliding
        def _slider_moved(value):
            suffix = option.suffix if value == 1 else option.suffix_plural
            label.setText(str(value) + suffix)
        slider.sliderMoved.connect(_slider_moved)
        slider.valueChanged.connect(_slider_moved)

        # Send request once dropped
        def _slider_dropped():
            self.dbg.stdout(f"{self.current_device.name}: Applying option {option.uid} with value: {str(slider.value())}", self.dbg.action, 1)
            try:
                option.apply(slider.value())
            except Exception as e:
                self._catch_command_error(self.current_device, e)

        slider.sliderReleased.connect(_slider_dropped)
        slider.valueChanged.connect(_slider_dropped)

        return [slider, label]

    def _create_control_toggle(self, option):
        """
        Returns a list of controls that make up a toggle for a binary choices.
        """
        checkbox = QCheckBox(option.label_toggle)

        if option.active:
            checkbox.setChecked(option.active)

        def _state_changed():
            onoff = "on" if checkbox.isChecked() else "off"
            self.dbg.stdout(f"{self.current_device.name}: Turning {onoff} option {option.uid}", self.dbg.action, 1)
            try:
                option.apply(checkbox.isChecked())
            except Exception as e:
                self._catch_command_error(self.current_device, e)

        checkbox.stateChanged.connect(_state_changed)
        return [checkbox]

    def _create_control_select(self, option):
        """
        Returns a list of controls that make up a multiple choice dropdown.
        """
        params = option.parameters
        selected_index = 0
        combo = QComboBox()
        combo.setIconSize(QSize(16, 16))

        for index, param in enumerate(params):
            combo.addItem(param.label)
            if param.icon:
                combo.setItemIcon(combo.count() - 1, QIcon(param.icon))
            if param.active:
                selected_index = index

        combo.setCurrentIndex(selected_index)

        def _current_index_changed(index):
            param = params[index]
            self.dbg.stdout(f"{self.current_device.name}: Setting option {option.uid} to {param.data}", self.dbg.action, 1)
            try:
                option.apply(param.data)
            except Exception as e:
                self._catch_command_error(self.current_device, e)

        combo.currentIndexChanged.connect(_current_index_changed)
        return [combo]

    def _create_effect_controls(self, zone, options):
        """
        Return a row widget containing the specified options. These are grouped
        together and will be presented as larger buttons.
        """
        widgets = []
        self.btn_grps[zone] = QButtonGroup()

        for option in options:
            button = QToolButton()
            button.setText(option.label)
            button.setCheckable(True)
            button.setIconSize(QSize(40, 40))
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            if option.icon:
                button.setIcon(QIcon(option.icon))
            button.setMinimumHeight(70)
            button.setMinimumWidth(105)
            button.option = option
            self.btn_grps[zone].addButton(button)

            if option.active:
                button.setChecked(True)

            widgets.append(button)

        def _clicked_effect_button(button):
            option = button.option
            param = self.middleman.get_default_parameter(option)
            self.middleman.stop_software_effect(self.current_device.serial)

            try:
                if param:
                    self.dbg.stdout(f"{self.current_device.name}: Setting effect {option.uid} (with parameter {str(param.data)}')", self.dbg.action, 1)
                    option.apply(param.data)
                else:
                    self.dbg.stdout(f"{self.current_device.name}: Setting effect {option.uid} (no parameters)", self.dbg.action, 1)
                    option.apply()
            except Exception as e:
                self._catch_command_error(self.current_device, e)

            self.reload_device()

        self.btn_grps[zone].buttonClicked.connect(_clicked_effect_button)

        if not widgets:
            return None

        return self.widgets.create_row_widget(self._("Effect"), widgets, wrap=True)

    def _create_effect_parameter_controls(self, device, zone, option):
        """
        Returns a list of row widgets that change the active effect's parameters.
        """
        if not option.parameters:
            return None

        def _clicked_param_button():
            for radio in self.btn_grps["radio_param_" + zone.zone_id]:
                if not radio.isChecked():
                    continue
                self.dbg.stdout(f"{device.name}: Setting parameter for '{option.uid}' to '{radio.param.data}'", self.dbg.action, 1)
                try:
                    option.apply(radio.param.data)
                except Exception as e:
                    self._catch_command_error(self.current_device, e)
                self.reload_device()

        def _make_button(param):
            radio = QRadioButton()
            radio.setText(param.label)
            radio.clicked.connect(_clicked_param_button)
            radio.option = option
            radio.param = param

            if param.active:
                radio.setChecked(True)

            if len(option.parameters) == 1 and param.active:
                radio.setDisabled(True)

            if param.icon:
                radio.setIcon(QIcon(param.icon))
                radio.setIconSize(QSize(22, 22))
            return radio

        widgets = []
        for param in option.parameters:
            widgets.append(_make_button(param))

        self.btn_grps["radio_param_" + zone.zone_id] = widgets
        return self.widgets.create_row_widget(self._("Effect Mode"), widgets, vertical=True)

    def _create_colour_control(self, device, zone, pos, colours):
        """
        Returns a row widget to set a colour at a specified position for the active option/parameter.
        Position is 0-based, so 0 = primary, 1 = secondary, etc
        """
        pretty_labels = {
            0: self._("Primary Colour"),
            1: self._("Secondary Colour"),
            2: self._("Tertiary Colour"),
        }

        try:
            label = pretty_labels[pos]
        except KeyError:
            label = self._("Colour 4").replace("4", str(pos))

        def _set_new_colour(new_hex, data):
            self.dbg.stdout(f"{self.current_device.name}: Setting {label.lower()} to {new_hex} for active option in zone {zone.zone_id}", self.dbg.action, 1)
            try:
                self.middleman.set_colour_for_active_effect_zone(zone, new_hex, pos)
            except Exception as e:
                self._catch_command_error(self.current_device, e)

        _set_data = {"zone": zone, "colour_no": pos}

        colour_widget = self.widgets.create_colour_control(colours[pos], _set_new_colour, _set_data, self._("Change []").replace("[]", label), device.monochromatic)
        return self.widgets.create_row_widget(label, [colour_widget])

    def _catch_command_error(self, device=Backend.DeviceItem, err=""):
        """
        Shows a error message when a command sent to a device was unsuccessful.
        """
        backend_name = device.backend.name
        exception = common.get_exception_as_string(err)
        my_fault = common.is_exception_fault_by_app(err)

        self.dbg.stdout(exception, self.dbg.error)

        if my_fault:
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     self._("Request Failed"),
                                     self._("There's a fault with Polychromatic's integration with [OpenRazer] for this device or option.").replace("[OpenRazer]", backend_name),
                                     self._("To help fix this, please check Polychromatic's issue tracker and create a new issue if a similar one does not exist.").replace("[OpenRazer]", backend_name),
                                     details=exception)
        else:
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     self._("Communication Error"),
                                     self._("An error occurred outside of Polychromatic's control when this command was sent to [OpenRazer].").replace("[OpenRazer]", backend_name),
                                     self._("Try restarting [OpenRazer] and Polychromatic and give it another go. If this error appears again, it might need fixing in [OpenRazer].").replace("[OpenRazer]", backend_name),
                                     details=exception)

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
        layout.setContentsMargins(0, 0, 0, 0)
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
                    "action": self._open_openrazer_help_unrecognised
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
            backend_name = "openrazer"
            exception = self.middleman.import_errors[backend_id].strip()
            dbg.stdout("\n{0}\n------------------------------\n{1}\n".format(backend_name, exception), dbg.error)
            self.widgets.open_dialog(self.widgets.dialog_generic,
                                    _("Backend Error: []").replace("[]", backend_name),
                                    _("An error occurred trying to load []. The error below may provide a clue to what happened.").replace("[]", backend_name),
                                    info_text=_("The last line of the exception was:") + "\n" + exception.split("\n")[-1],
                                    details=exception)

    def _open_openrazer_help_unrecognised(self):
        self.appdata.menubar._prompt_on_locale_change(self._("Online Help"))
        webbrowser.open("https://docs.polychromatic.app/openrazer/#my-device-is-showing-up-as-unrecognised")

    def _open_openrazer_help_unsupported(self):
        self.appdata.menubar._prompt_on_locale_change(self._("Online Help"))
        webbrowser.open("https://docs.polychromatic.app/openrazer/#my-device-isnt-listed-as-supported-what-do-i-do")

    def open_unknown_device(self, device):
        """
        Show guidance on a device that could be controlled, but isn't possible right now.
        """
        layout = self.Contents.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        shared.clear_layout(layout)

        backend_name = "OpenRazer"

        def _restart_backend():
            # OpenRazer is the only backend
            return self.appdata.menubar.openrazer.restart_daemon()

        if device.supported:
            image = common.get_icon("empty", "openrazer")
            title = device.name
            desc = self._("This supported device wasn't detected by the OpenRazer daemon (v1.0.0)").replace("1.0.0", self.middleman.get_backend("openrazer").version)
            buttons = [
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
                    "action": self._open_openrazer_help_unrecognised
                },
            ]
        else:
            image = common.get_icon("empty", "nodevice")
            title = self._("Unsupported Device") + f": {device.vid}:{device.pid}"
            desc = self._("This device needs support adding to OpenRazer before it can be used in Polychromatic.")
            buttons = [
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
                    "action": self._open_openrazer_help_unsupported
                }
            ]

        self.widgets.populate_empty_state(layout, image, title, desc, buttons)

    def open_bad_device(self, msg1, msg2, exception):
        """
        Show a page to inform the user the device could not be opened. Possibly
        due to a temporary glitch or unsupported feature.
        """
        layout = self.Contents.layout()
        layout.setContentsMargins(0, 0, 0, 0)
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
        Show options that change the device state for all connected devices.
        """
        self.set_cursor_busy()
        layout = self.Contents.layout()
        layout.setContentsMargins(15, 15, 15, 15)
        shared.clear_layout(layout)

        btngrp = QButtonGroup()
        bulk_options = bulkapply.BulkApplyOptions(self.middleman)
        mix_match_msg = self._("Not available for all connected devices")

        def _create_button(option):
            """Creates a button similar to an effect button"""
            button = QToolButton()
            button.setText(option.label)
            button.setIconSize(QSize(40, 40))
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setIcon(QIcon(option.icon))
            button.setMinimumHeight(70)
            button.setMinimumWidth(105)
            button.option = option
            btngrp.addButton(button)
            if option.label.find("*") > 0:
                button.setToolTip(mix_match_msg)
            return button

        def _create_group_widget(label, widgets):
            """Nests widgets into a group"""
            group = self.widgets.create_group_widget(label)
            container = QWidget()
            container.setLayout(QFlowLayout())
            container.setContentsMargins(QMargins(30, 6, 15, 0))
            for widget in widgets:
                container.layout().addWidget(widget)
            layout.addWidget(group)
            group.layout().addWidget(container)

        def _add_to_page(label, options):
            """Adds this set of bulk options onto the page"""
            if options:
                buttons = []
                for option in options:
                    buttons.append(_create_button(option))
                _create_group_widget(label, buttons)

        _add_to_page(self._("Brightness"), bulk_options.brightness)
        _add_to_page(self._("Effects"), bulk_options.effects)

        if bulk_options.mix_match:
            mixmatch_label = QLabel("* " + mix_match_msg)
            mixmatch_label.setContentsMargins(QMargins(40, 0, 15, 0))
            mixmatch_label.setDisabled(True)
            layout.addWidget(mixmatch_label)

        _add_to_page(self._("Colours"), bulk_options.colours)

        def _bulk_grp_clicked(button):
            try:
                button.option.apply()
            except Exception as e:
                self._catch_command_error(self.current_device, e)

        btngrp.buttonClicked.connect(_bulk_grp_clicked)
        self.btn_grps["bulk"] = btngrp

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
        btn_test_matrix = dialog.findChild(QPushButton, "TestMatrix")

        # Dialog Button Icons
        if not self.appdata.system_qt_theme:
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

            def mkitem(data, value="", icon=None, disabled=False):
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
                if disabled:
                    item.setDisabled(True)
                if icon:
                    item.setIcon(1 if value != "" else 0, QIcon(icon))
                return item

            backend = device.backend

            hw = mkitem(_("Hardware"))
            hw.addChild(mkitem(_("Name"), device.name))
            hw.addChild(mkitem(_("Backend"), backend.name, os.path.join(self.paths.data_dir, "img", "logo", backend.logo)))
            if device.vid:
                hw.addChild(mkitem("VID:PID", "{0}:{1}".format(device.vid, device.pid)))
            else:
                hw.addChild(mkitem("VID:PID", None))
            hw.addChild(mkitem(_("Form Factor"), device.form_factor["label"], device.form_factor["icon"]))
            hw.addChild(mkitem(_("Serial"), device.serial))
            if device.firmware_version:
                hw.addChild(mkitem(_("Firmware Version"), device.firmware_version))
            if device.keyboard_layout:
                hw.addChild(mkitem(_("Keyboard Layout"), device.keyboard_layout))
            tree.addTopLevelItem(hw)

            # Software Effects
            cfx = mkitem(_("Custom Effects"))
            fx_supported = True if device.matrix else False
            cfx.addChild(mkitem(_("Supported"), fx_supported, disabled=not fx_supported))
            if device.matrix:
                btn_test_matrix.setDisabled(False)
                dimensions = common.get_plural(device.matrix.rows, _("1 row"), _("2 rows").replace("2", str(device.matrix.rows)))
                dimensions += ", " + common.get_plural(device.matrix.cols, _("1 column"), _("2 columns").replace("2", str(device.matrix.cols)))
                cfx.addChild(mkitem(_("Matrix Dimensions"), dimensions, common.get_icon("general", "matrix")))

                if device.monochromatic:
                    cfx.addChild(mkitem(_("Colour Range"), _("256 colours"), common.get_icon("params", "triple")))
                else:
                    cfx.addChild(mkitem(_("Colour Range"), _("16 million colours"), common.get_icon("tray", "ring")))
            tree.addTopLevelItem(cfx)

            # Battery
            if device.battery:
                battery = mkitem(_("Battery"))
                # TODO: Determine battery icon from a new icon class (reusual)
                if device.battery.is_charging:
                    battery.addChild(mkitem(_("Status"), _("Charging (0%)").replace("0", str(device.battery.percentage))))
                else:
                    battery.addChild(mkitem(_("Status"), _("Discharging (0%)").replace("0", str(device.battery.percentage))))
                battery.addChild(mkitem(_("Type"), _("Removable") if device.battery.is_removable else _("Rechargable")))
                tree.addTopLevelItem(battery)

            # DPI
            if device.dpi:
                dpi = mkitem(_("DPI"))
                dpi.addChild(mkitem(_("Current DPI"), f"({device.dpi.x}, {device.dpi.y})"))
                default_stages = []
                for stage in device.dpi.default_stages:
                    dpi_x, dpi_y = stage
                    default_stages.append(dpi_x if dpi_x == dpi_y else f"({dpi_x},{dpi_y})")
                dpi.addChild(mkitem(_("Default Stages"), ", ".join(map(str, default_stages))))

                if device.dpi.user_stages:
                    stages = [value[0] if value[0] == value[1] else f"({value[0]},{value[1]})" for value in device.dpi.user_stages]
                    dpi.addChild(mkitem(_("Custom Stages"), ", ".join(stages)))
                else:
                    dpi.addChild(mkitem(_("Custom Stages"), self._("(Not set)"), disabled=True))
                dpi.addChild(mkitem(_("Supports Sync?"), device.dpi.can_sync, disabled=not device.dpi.can_sync))
                dpi.addChild(mkitem(_("Minimum"), device.dpi.min))
                dpi.addChild(mkitem(_("Maximum"), device.dpi.max))
                tree.addTopLevelItem(dpi)

            def _get_colour_item(option, colours_required):
                item = mkitem(_("Colours"), str(colours_required))
                for index in range(0, colours_required):
                    colour_hex = option.colours[index]
                    item.addChild(mkitem(_("Input 0").replace("0", str(index + 1)), colour_hex, common.generate_colour_bitmap(self.dbg, colour_hex)))
                return item

            # Zones
            zones = mkitem(_("Zones"))
            exclude_expand = []
            for zone in device.zones:
                zone_item = mkitem(zone.label, "", zone.icon)

                for option in zone.options:
                    option_item = mkitem(option.label, "", option.icon)
                    exclude_expand.append(option_item)

                    option_type = "Unknown"
                    if isinstance(option, Backend.EffectOption):
                        option_type = _("Effect")
                    elif isinstance(option, Backend.ToggleOption):
                        option_type = _("Toggle")
                    elif isinstance(option, Backend.SliderOption):
                        option_type = _("Slider")
                    elif isinstance(option, Backend.MultipleChoiceOption):
                        option_type = _("Dropdown")

                    option_item.addChild(mkitem(_("Option ID"), option.uid))
                    option_item.addChild(mkitem(_("Type"), option_type))
                    option_item.addChild(mkitem(_("Active"), option.active))

                    if option.parameters:
                        param_parent = mkitem(_("Parameters"))
                        for param in option.parameters:
                            param_item = mkitem(param.label, "", param.icon)
                            param_item.addChild(mkitem(_("Parameter ID"), param.data))
                            param_item.addChild(mkitem(_("Active"), param.active))
                            if param.colours_required:
                                param_item.addChild(_get_colour_item(option, param.colours_required))
                            param_parent.addChild(param_item)
                        option_item.addChild(param_parent)

                    if isinstance(option, Backend.SliderOption):
                        option_item.addChild(mkitem(_("Current Value"), f"{str(option.value)} {option.suffix}"))
                        option_item.addChild(mkitem(_("Minimum"), option.min))
                        option_item.addChild(mkitem(_("Maximum"), option.max))
                        option_item.addChild(mkitem(_("Interval"), option.step))

                    if option.colours_required:
                        option_item.addChild(_get_colour_item(option, option.colours_required))

                    zone_item.addChild(option_item)
                    zone_item.setExpanded(False)
                zones.addChild(zone_item)

            tree.addTopLevelItem(zones)
            tree.expandAll()
            for item in exclude_expand:
                item.setExpanded(False)

            dialog.setWindowTitle("{0} - {1}".format(_("Device Information"), device.name))
            self.set_cursor_normal()

        def _test_matrix():
            dialog.accept()
            self._test_device_matrix(device)

        device = self.current_device
        btn_close.clicked.connect(_close)
        btn_test_matrix.clicked.connect(_test_matrix)
        dialog.open()
        _populate_tree()

    def _test_device_matrix(self, device):
        """
        Opens a dialogue box to allow the user to test the individual key
        lighting for their device.
        """
        _ = self._

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
            self.middleman.replay_active_effect(device)
            self.dialog.accept()

        # Populate table
        for x in range(0, device.matrix.cols):
            table.insertColumn(x)
            header = QTableWidgetItem()
            header.setText(str(x))
            table.setHorizontalHeaderItem(x, header)

        for y in range(0, device.matrix.rows):
            table.insertRow(y)
            header = QTableWidgetItem()
            header.setText(str(y))
            table.setVerticalHeaderItem(y, header)

        def _set_pos():
            indexes = table.selectedIndexes()
            device.matrix.clear()
            for index in indexes:
                device.matrix.set(index.column(), index.row(), 255, 255, 255)
            if len(indexes) == 0:
                cur_pos.setText("")
            elif len(indexes) == 1:
                x = indexes[0].column()
                y = indexes[0].row()
                cur_pos.setText(_("Coordinate: X,Y").replace("X", str(x)).replace("Y", str(y)))
            elif len(indexes) > 1:
                cur_pos.setText(_("Coordinate: (Multiple)"))
            device.matrix.draw()

        # Connect signals and set focus
        btn_close.clicked.connect(_close_test)
        table.itemSelectionChanged.connect(_set_pos)
        table.setFocus()
        table.setCurrentCell(0, 0)
        self.dialog.adjustSize()
        self.dialog.resize(QSize(self.dialog.width() + 5, self.dialog.height()))
        self.dialog.setWindowTitle(self._("Inspect Matrix") + " - " + device.name)
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

        If a device has fixed requirements, Backend.DeviceItem.DPI shouldn't be used
        and instead be implemented as an MultipleChoiceOption or SliderOption.
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
            slider.setMinimum(device.dpi.min)
            slider.setMaximum(device.dpi.max)
            slider.setSingleStep(100)
            slider.setPageStep(200)

        slider_x.setValue(device.dpi.x)
        slider_y.setValue(device.dpi.y)
        value_x.setText(str(device.dpi.x))
        value_y.setText(str(device.dpi.y))

        if int(device.dpi.x) == int(device.dpi.y):
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
            if slider_y.isHidden():
                new_size_y = new_size_x
            else:
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
            self.dbg.stdout(f"{device.name}: Setting DPI to {slider_x.value()}, {slider_y.value()}", self.dbg.action, 1)
            try:
                device.dpi.set(slider_x.value(), slider_y.value())
            except Exception as e:
                DevicesTab._catch_command_error(self, device=device, err=e)

            # Sync state with stages buttons
            for button in self.stage_buttons_group.buttons():
                button.setChecked(slider_x.value() == button.dpi_value[0] and slider_y.value() == button.dpi_value[1])

        # Some mice have a zero Y axis
        if device.name in ["Razer Basilisk Essential"]:
            slider_y.setHidden(True)
            value_y.setHidden(True)
            slider_lock.setHidden(True)

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
        stages = device.dpi.default_stages

        # Use custom stages if the user saved them for this device
        # TODO: Should reuse this code
        dpi_file = os.path.join(self.paths.dpi, device.name + ".list")
        if os.path.exists(dpi_file):
            values = []
            with open(dpi_file, "r") as f:
                for line in f.readlines():
                    try:
                        dpi_x, dpi_y = line.split(",")
                        values.append([int(dpi_x), int(dpi_y)])
                    except ValueError:
                        # TODO: Output to stderr
                        pass
            if values:
                stages = values

        def _set_dpi_by_button(button):
            dpi_x, dpi_y = button.dpi_value
            slider_lock.setChecked(dpi_x == dpi_y)
            slider_x.setValue(dpi_x)
            slider_y.setValue(dpi_y)
            button.setChecked(True)

        def _edit_dpi_stages():
            self.dpi_editor = DPIStageEditor(self.appdata, device)

        for index, value in enumerate(stages):
            dpi_x, dpi_y = value
            button = QPushButton()
            button.setCheckable(True)
            if device.dpi.x == dpi_x and device.dpi.y == dpi_y:
                button.setChecked(True)
            button.setText(str(dpi_x) if dpi_x == dpi_y else f"{dpi_x},{dpi_y}")
            button.dpi_value = value

            stage_widget.layout().addWidget(button)
            self.stage_buttons_group.addButton(button)

        self.stage_buttons_group.buttonClicked.connect(_set_dpi_by_button)

        edit_btn = QPushButton()
        edit_btn.setText(self._("Edit"))
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
        # TODO: Move to middleman to use for all mice
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
        button = QPushButton()
        button.setText(self._("Open Mouse Settings"))
        button.setIconSize(QSize(24, 24))
        button.setIcon(QIcon.fromTheme("input-mouse"))
        button.clicked.connect(_open_mouse_settings)
        layout.addWidget(button)
        layout.addStretch()

        return self.widgets.create_row_widget(self._("Acceleration"), [widget])

    def create_programmable_keys_control(self, path):
        """
        Returns a widget that informs the user that this software does not
        have a key remapping solution right now.
        """
        def _open_input_remapper():
            subprocess.Popen([path])

        button = QPushButton()
        button.setText(self._("Open Input Remapper"))
        button.clicked.connect(_open_input_remapper)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)

        return self.widgets.create_row_widget("", [button, spacer])

    def create_openrazer_macro_control(self):
        """
        For OpenRazer keyboards, returns a widget that informs the user how to
        use the macro recording feature provided by openrazer-daemon.
        """
        def _open_macro_dialog():
            self.widgets.open_dialog(self.widgets.dialog_generic,
                self._("About Macro Recording"),
                self._("OpenRazer provides a simple on-the-fly macro recording feature.\n\n" + \
                "1. Press FN+[M] to enter macro mode.\n" + \
                "2. Press the macro key to assign to. Only M1-M5 are supported.\n" + \
                "3. Press the keys in sequence to record.\n" + \
                "4. Press FN+[M] to exit macro mode.\n\n" + \
                "Macros remain in memory until the openrazer-daemon process is stopped. The replay speed will be instantaneous, which can be problematic with some software/games."))

        button = QPushButton()
        button.setText(self._("Usage Instructions"))
        button.clicked.connect(_open_macro_dialog)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)

        return self.widgets.create_row_widget(self._("Macros"), [button, spacer])


class DPIStageEditor(shared.TabData):
    """
    A dialog to edit the DPI stages and save them for quick access or to sync to the hardware buttons.
    """
    def __init__(self, appdata, device=Backend.DeviceItem):
        super().__init__(appdata)
        self.dialog = shared.get_ui_widget(self.appdata, "custom-dpi", q_toplevel=QDialog)
        self.device = device

        # TODO: Refactor later into new class/object
        self.dpi_file = os.path.join(appdata.paths.dpi, device.name + ".list")
        custom_enabled = os.path.exists(self.dpi_file)

        # Labels
        self.device_name = self.dialog.findChild(QLabel, "DeviceName")
        self.device_range = self.dialog.findChild(QLabel, "DeviceDPIRange")
        self.device_icon = self.dialog.findChild(QLabel, "DeviceIcon")
        self.sync_possible = self.dialog.findChild(QLabel, "SyncPossible")
        self.sync_impossible = self.dialog.findChild(QLabel, "SyncImpossible")

        # Input
        self.stages_enabled = self.dialog.findChild(QCheckBox, "StagesEnabled")
        self.stages_table = self.dialog.findChild(QTableWidget, "StagesTable")

        # Buttons
        self.btn_sync = self.dialog.findChild(QPushButton, "SyncNow")
        self.btn_stage_add = self.dialog.findChild(QPushButton, "StageAdd")
        self.btn_stage_del = self.dialog.findChild(QPushButton, "StageDel")
        self.dialog_buttons = self.dialog.findChild(QDialogButtonBox, "buttonBox")
        self.btn_save = self.dialog_buttons.button(QDialogButtonBox.Save)

        # Set icons for controls
        if not self.appdata.system_qt_theme:
            self.btn_sync.setIcon(self.widgets.get_icon_qt("general", "refresh"))
            self.btn_stage_add.setIcon(self.widgets.get_icon_qt("general", "new"))
            self.btn_stage_del.setIcon(self.widgets.get_icon_qt("general", "minus"))

        # Set up UI
        self.device_name.setText(device.name)
        self.device_range.setText(self.appdata._("Up to 123 DPI").replace("123", str(device.dpi.max)))
        shared.set_pixmap_for_label(self.device_icon, shared.get_real_device_image(device.real_image), 48)
        self.toggle_custom_setting(custom_enabled)
        self.sync_possible.setVisible(device.dpi.can_sync == True)
        self.sync_impossible.setVisible(device.dpi.can_sync == False)
        self.btn_sync.setEnabled(device.dpi.can_sync == True)

        # Set up events
        self.stages_enabled.clicked.connect(self.toggle_custom_setting)
        self.btn_sync.clicked.connect(self.sync_now)
        self.btn_save.clicked.connect(self.save_changes)
        self.btn_stage_add.clicked.connect(self.stage_add)
        self.btn_stage_del.clicked.connect(self.stage_del)

        if os.path.exists(self.dpi_file):
            self.load_from_file()

        self.dialog.open()

    def toggle_custom_setting(self, enabled):
        """
        Update the UI when enabling/disabling custom DPI stages. When disabling, default values will be restored.
        """
        self.stages_enabled.setChecked(enabled)
        for widget in [self.stages_table, self.btn_stage_add, self.btn_stage_del]:
            widget.setEnabled(enabled)

        if not enabled:
            self._update_dpi_table(self.device.dpi.default_stages)

    def _update_dpi_table(self, values=[]):
        """
        Replace the data in the table with the specified values.
        """
        while self.stages_table.columnCount() > 0:
            self.stages_table.removeColumn(0)

        for item in values:
            value_x = item[0]
            value_y = item[1]
            last_column = self.stages_table.columnCount()
            self.stages_table.insertColumn(last_column)

            cell = self.stages_table.item(0, last_column)
            if not cell:
                cell = QTableWidgetItem()
                self.stages_table.setItem(0, last_column, cell)
            if value_x == value_y:
                cell.setText(str(value_x))
            else:
                cell.setText(f"{value_x},{value_y}")

    def load_from_file(self):
        """
        Load saved DPI data from disk.
        """
        # TODO: Should reuse this code
        values = []
        with open(self.dpi_file, "r") as f:
            for line in f.readlines():
                try:
                    dpi_x, dpi_y = line.split(",")
                    values.append([int(dpi_x), int(dpi_y)])
                except ValueError:
                    # TODO: Output to stderr
                    pass
        self._update_dpi_table(values)

    def stage_add(self):
        """
        Add another stage to the end of the list.
        """
        self.stages_table.insertColumn(self.stages_table.columnCount())
        self.stages_table.setCurrentCell(0, self.stages_table.columnCount() - 1)

    def stage_del(self):
        """
        Remove the last stage from the end of the list.
        """
        column = self.stages_table.currentColumn()
        if column == -1:
            self.stages_table.removeColumn(self.stages_table.columnCount() - 1)
        else:
            self.stages_table.removeColumn(self.stages_table.currentColumn())

        self.stages_table.setCurrentCell(0, self.stages_table.currentColumn())

    def parse_dpi(self):
        """
        Return a list of valid DPI values from user input. Unless there is a validation error, which will raise ValueError.

        The list will be in the list format expected by DeviceItem.DPI.sync():
        [ [1800,1800], [6500, 4800], [...] ]
        """
        values = []
        for col in range(0, self.stages_table.columnCount()):
            cell = self.stages_table.item(0, col)
            if not cell:
                continue
            data = cell.text()
            if len(data) == 0:
                continue
            data = data.split(",")
            try:
                if len(data) == 1:
                    values.append([int(data[0]), int(data[0])])
                elif len(data) == 2:
                    values.append([int(data[0]), int(data[1])])
            except ValueError:
                # TODO: Show dialog pop up -or- mark invalid cells before sync clicked?
                # ... setting 'sync_possible' label would be overwritten later after successful sync.
                pass

        return sorted(values, key=lambda item: int(item[0]))

    def sync_now(self):
        """
        Sync the current DPI values displayed to the hardware.
        """
        dpi_stages = self.parse_dpi()

        if not dpi_stages:
            # Restore to defaults
            self.toggle_custom_setting(False)
            dpi_stages = self.parse_dpi()

        self.device.dpi.sync(dpi_stages)
        self.sync_possible.setText(self._("DPI stages were successfully synchronised to the hardware."))

    def save_changes(self):
        """
        Save the custom values, save to disk then close the dialog.
        """
        values = self.parse_dpi()

        if self.stages_enabled.isChecked():
            with open(self.dpi_file, "w") as f:
                for value in self.parse_dpi():
                    dpi_x, dpi_y = value
                    f.write(f"{dpi_x},{dpi_y}\n")

        if not self.stages_enabled.isChecked() and os.path.exists(self.dpi_file) or not values:
            os.remove(self.dpi_file)

        self.appdata.tab_devices.open_device(self.device)
