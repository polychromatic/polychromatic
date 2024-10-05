# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2024 Luke Horwell <code@horwell.me>
"""
This module controls the 'Preferences' window of the Controller GUI.
"""

import configparser
import os

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QDoubleSpinBox, QLabel, QMessageBox, QPushButton,
                             QSpinBox, QTabWidget, QWidget)

from .. import preferences as pref
from .. import procpid
from ..base import PolychromaticBase
from . import shared


class PreferencesWindow(shared.TabData):
    """
    A window for adjusting the options of the application, viewing background
    processes and getting more information about backends in use.
    """
    def __init__(self, appdata):
        super().__init__(appdata)
        self.openrazer = OpenRazerPreferences(appdata)
        self.dialog = None
        self.pref_data = None
        self.prompt_restart = False
        self.restart_applet = False

        self.options = [
            # [group, item, <Qt object>, Qt object name, Inverted?]
            # -- General
            ["controller", "download_device_images", QCheckBox, "DownloadDeviceImages", False],
            ["controller", "system_qt_theme", QCheckBox, "UseSystemQtTheme", False],
            ["controller", "show_menu_bar", QCheckBox, "AlwaysHideMenuBar", True],
            ["controller", "landing_tab", QComboBox, "LandingTabCombo", False],
            ["controller", "window_behaviour", QComboBox, "WindowBehaviourCombo", False],
            ["controller", "toolbar_style", QComboBox, "ToolbarStyle", False],

            # -- Tray
            ["tray", "autostart", QCheckBox, "TrayAutoStart", False],
            ["tray", "mode", QComboBox, "TrayModeCombo", False],
            ["tray", "autostart_delay", QSpinBox, "TrayDelaySpinner", 0],

            # -- Editor
            ["editor", "live_preview", QCheckBox, "LivePreview", False],
            ["editor", "hide_key_labels", QCheckBox, "HideKeyLabels", False],
            ["editor", "system_cursors", QCheckBox, "UseSystemCursors", False],
            ["editor", "suppress_confirm_dialog", QCheckBox, "SuppressConfirmDialog", False],
            ["editor", "show_saved_colour_shades", QCheckBox, "ShowSavedColourShades", False],
        ]

    def open_window(self, open_tab=None):
        """
        Opens the Preferences window to change Polychromatic's options.

        Parameters:
            open_tab    (int)   Optionally jump to this specific tab index.
        """
        self.pref_data = pref.load_file(self.paths.preferences)
        self.prompt_restart = False
        self.restart_applet = False

        self.dialog = shared.get_ui_widget(self.appdata, "preferences", QDialog)
        self.dialog.findChild(QDialogButtonBox, "DialogButtons").accepted.connect(self._save_changes)

        # Set icons for tabs
        tabs = self.dialog.findChild(QTabWidget, "PreferencesTabs")
        tabs.setTabIcon(0, self.widgets.get_icon_qt("general", "controller"))
        tabs.setTabIcon(1, self.widgets.get_icon_qt("general", "tray-applet"))
        tabs.setTabIcon(2, self.widgets.get_icon_qt("effects", "paint"))
        tabs.setTabIcon(3, self.widgets.get_icon_qt("general", "matrix"))
        tabs.setTabIcon(4, self.widgets.get_icon_qt("emblems", "software"))

        # Set icons for controls
        if not self.appdata.system_qt_theme:
            self.dialog.findChild(QPushButton, "SavedColoursButton").setIcon(self.widgets.get_icon_qt("general", "edit"))
            self.dialog.findChild(QPushButton, "SavedColoursReset").setIcon(self.widgets.get_icon_qt("general", "reset"))

        # Options
        for option in self.options:
            self._load_option(option[0], option[1], option[2], option[3], option[4])

        self.dialog.findChild(QPushButton, "SavedColoursButton").clicked.connect(self.modify_colours)
        self.dialog.findChild(QPushButton, "SavedColoursReset").clicked.connect(self.reset_colours)

        # Create Icon Picker
        def _set_new_tray_icon(new_icon):
            self.dbg.stdout("New tray icon saved in memory: " + new_icon, self.dbg.debug, 1)
            self.pref_data["tray"]["icon"] = new_icon
            self.restart_applet = True

        tray_icon_picker = self.widgets.create_icon_picker_control(_set_new_tray_icon, self.pref_data["tray"]["icon"], self._("Choose Tray Applet Icon"), shared.IconPicker.PURPOSE_TRAY_ONLY)
        tray_icon_widget = self.dialog.findChild(QLabel, "TrayIconPickerPlaceholder")
        tray_icon_widget.parentWidget().layout().replaceWidget(tray_icon_widget, tray_icon_picker)

        # Drop custom icons when using native themes
        if self.appdata.system_qt_theme:
            combo = self.dialog.findChild(QComboBox, "LandingTabCombo")
            for i in range(0, combo.count()):
                combo.setItemIcon(i, QIcon())

        # Prompt for a restart after changing these options
        def _cb_set_restart_flag():
            self.prompt_restart = True

        self.dialog.findChild(QCheckBox, "UseSystemQtTheme").stateChanged.connect(_cb_set_restart_flag)

        # Restart the tray applet after changing these options
        def _cb_set_applet_flag(i):
            self.restart_applet = True

        self.dialog.findChild(QComboBox, "TrayModeCombo").currentIndexChanged.connect(_cb_set_applet_flag)

        # FIXME: Hide incomplete features
        self.dialog.findChild(QComboBox, "LandingTabCombo").removeItem(3)
        self.dialog.findChild(QComboBox, "LandingTabCombo").removeItem(2)

        # Disable tray applet tab if not installed
        if not procpid.ProcessManager().is_component_installed("tray-applet"):
            tabs.setTabEnabled(1, False)

        tray_hint = self.dialog.findChild(QLabel, "TrayAutoStartTip")
        tray_hint.hide()

        # Show/hide hints depending on current environment
        try:
            current_desktop = os.environ["XDG_CURRENT_DESKTOP"]

            # Hide native Qt theme hint on Qt desktops.
            if current_desktop in ["KDE", "LXQt"]:
                self.dialog.findChild(QLabel, "UseSystemQtThemeTip").hide()

            # Some environments deprecated the tray.
            for desktop in ["GNOME", "Pantheon"]:
                if current_desktop.lower().find(desktop.lower()) >= 0:
                    tray_hint.show()
        except KeyError:
            pass

        # Tray applet not available under Flatpak
        if self.appdata.flatpak_mode:
            self.dialog.findChild(QTabWidget, "PreferencesTabs").setTabEnabled(1, False)
            self.dialog.findChild(QTabWidget, "PreferencesTabs").setTabToolTip(1, self._("Not available under Flatpak"))
            self.dialog.findChild(QWidget, "tray").setEnabled(False)

        # Show time!
        self.dialog.findChild(QTabWidget, "PreferencesTabs").setCurrentIndex(open_tab if open_tab else 0)
        self.dialog.open()

    def _load_option(self, group, item, qcontrol, qid, inverted):
        """
        Applies the setting in memory with the control.

        Params:
            group           Preference group, e.g. "controller"
            item            Preference item, e.g. "landing_tab"
            qcontrol        Qt control object, e.g. QCheckBox
            qid             Name of Qt control, e.g. "UseSystemQtTheme"
            invert          (Optional, boolean) UI inverted to stored config
            must_restart    Changing this option requires application restart.
        """
        data = self.pref_data[group][item]
        widget = self.dialog.findChild(qcontrol, qid)

        if qcontrol == QCheckBox:
            widget.setChecked(not data if inverted else data)
        elif qcontrol == QComboBox:
            widget.setCurrentIndex(data)
        elif qcontrol == QSpinBox:
            widget.setValue(data)

    def _set_option(self, group, item, qcontrol, qid, inverted):
        """
        Updates the preferences in memory to reflect the UI control state.

        Params:
            Same as _get_option().
        """
        widget = self.dialog.findChild(qcontrol, qid)

        if qcontrol == QCheckBox:
            data = widget.isChecked()
            if inverted:
                data = not data
        elif qcontrol == QComboBox:
            data = widget.currentIndex()
        elif qcontrol == QSpinBox:
            data = widget.value()

        self.pref_data[group][item] = data
        self.appdata.preferences[group][item] = data

    def _save_changes(self):
        """
        Writes the preferences to file according to the GUI.
        """
        self.dbg.stdout("Saving preferences...", self.dbg.action, 1)
        for option in self.options:
            self._set_option(option[0], option[1], option[2], option[3], option[4])

        result = pref.save_file(self.paths.preferences, self.pref_data)
        if result:
            self.dbg.stdout("Save complete.", self.dbg.success, 1)
        else:
            self.dbg.stdout("Save failed! Check permissions?", self.dbg.error)
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     self._("Save Error"),
                                     self._("Save failed. Please check the permissions and try again."))
            return False

        # Update memory for the rest of the application
        PolychromaticBase.preferences = self.pref_data

        # Instant reload
        if self.pref_data["controller"]["show_menu_bar"] == True:
            self.menubar.reinstate_menu_bar()
        else:
            self.menubar.hide_menu_bar()

        # Force refresh of current tab
        self.appdata.main_window.findChild(QAction, "actionRefreshTab").trigger()

        # Some options require a restart
        if self.prompt_restart:
            self.dbg.stdout("Program settings changed. Prompting to restart application.", self.dbg.action, 1)
            procmgr = procpid.ProcessManager()

            def _cb_restart_now():
                procmgr.restart_self(self.exec_path, self.exec_args)

            self.widgets.open_dialog(self.widgets.dialog_generic,
                                     self._("Restart Required"),
                                     self._("To apply these changes, the application must be restarted. Any unsaved changes will be lost."),
                                     buttons=[QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ignore],
                                     default_button=QMessageBox.StandardButton.Ok,
                                     actions={QMessageBox.StandardButton.Ok: _cb_restart_now})

        # Reload tray applet
        if self.restart_applet:
            self.dbg.stdout("Tray applet settings changed. Will restart component.", self.dbg.success, 1)
            process = procpid.ProcessManager("tray-applet")
            process.reload()

    def modify_colours(self):
        """
        Opens the colour picker for editing saved colours for later use.
        """
        def _cb_dummy(a, b):
            # List is saved upon closing, nothing to do.
            pass

        virtual_picker = self.widgets.create_colour_control("#FFFFFF", _cb_dummy, None, self._("Saved Colours"))
        virtual_picker.findChild(QPushButton).click()

    def reset_colours(self):
        """
        Reset colours to the defaults.
        """
        def _cb_reset_colours():
            os.remove(self.paths.colours)
            pref.init(self._)

        self.widgets.open_dialog(self.widgets.dialog_generic,
                                 self._("Reset to Default Colours"),
                                 self._("All colours in the list will be reset. Continue?"),
                                 buttons=[QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel],
                                 default_button=QMessageBox.StandardButton.Ok,
                                 actions={QMessageBox.StandardButton.Ok: _cb_reset_colours})


class OpenRazerPreferences(shared.TabData):
    """
    A special window for changing the OpenRazer configuration file when OpenRazer
    is in use.
    """
    def __init__(self, appdata):
        super().__init__(appdata)

        self.conf_path = None
        try:
            self.conf_path = "{0}/openrazer/razer.conf".format(os.environ["XDG_CONFIG_HOME"])
        except KeyError:
            self.conf_path = "{0}/.config/openrazer/razer.conf".format(os.environ.get("HOME", "~"))

        # Client settings
        self.client = [
            # "Filename", <data type>
            ["ripple_refresh_rate", float]
        ]

    def _get_openrazer_version(self):
        """
        Returns the current version of OpenRazer in decimal format: <major.minor>, e.g. 3.1
        """
        for backend in self.middleman.backends:
            if backend.backend_id == "openrazer":
                version = backend.version.split(".")[:2]
                return float("{0}.{1}".format(version[0], version[1]))
        return 0

    def open_log(self):
        self.menubar.openrazer.open_log()

    def restart_daemon(self):
        self.menubar.openrazer.restart_daemon()

    def open_window(self):
        """
        Opens a window for adjusting OpenRazer options.

        If configparser is not present for some reason, open the text editor.
        """
        version = self._get_openrazer_version()

        if version < 3.2:
            os.system("xdg-open file://{0}".format(self.conf_path))
            return

        self.keys = [
            # "Object Name",                "Group",    "Item",                         <data type>
            ["verbose_logging",             "General",  "verbose_logging",              bool],
            ["devices_off_on_screensaver",  "Startup",  "devices_off_on_screensaver",   bool],
            ["restore_persistence",         "Startup",  "restore_persistence",          bool],
            ["persistence_dual_boot_quirk", "Startup",  "persistence_dual_boot_quirk",  bool],
            ["battery_notifier",            "Startup",  "battery_notifier",             bool],
            ["battery_notifier_freq",       "Startup",  "battery_notifier_freq",        int], # seconds
            ["battery_notifier_percent",    "Startup",  "battery_notifier_percent",     int],
        ]

        self.dialog = shared.get_ui_widget(self.appdata, "openrazer-config", QDialog)
        self.dialog.findChild(QDialogButtonBox, "DialogButtons").accepted.connect(self._save_and_restart)

        # razer.conf
        for key in self.keys:
            object_name = key[0]
            group = key[1]
            key_name = key[2]
            data_type = key[3]

            if data_type == bool:
                chkbox = self.dialog.findChild(QCheckBox, object_name)
                chkbox.setChecked(self._read_config(group, key_name, bool))

            elif data_type == int:
                spinner = self.dialog.findChild(QSpinBox, object_name)
                spinner.setValue(self._read_config(group, key_name, int))

                if key_name == "battery_notifier_freq":
                    spinner.setValue(int(int(self._read_config(group, key_name, int) or 0) / 60))

        # Client
        for meta in self.client:
            filename = meta[0]
            data_type = meta[1]
            path = os.path.join(self.paths.config, "backends", "openrazer", filename)

            if not os.path.exists(path):
                continue

            try:
                with open(path, "r") as f:
                    data = str(f.readline()).strip()
                    data = data_type(data)
            except ValueError:
                self.dbg.stdout("Ignoring unexpected data from override file: " + filename, self.dbg.warning, 1)
                continue

            if data_type == int:
                chkbox = self.dialog.findChild(QCheckBox, filename)
                chkbox.setChecked(True if data == 1 else False)

            elif data_type == float:
                spinner = self.dialog.findChild(QDoubleSpinBox, filename)
                spinner.setValue(float(data))

        self.dialog.findChild(QCheckBox, "battery_notifier").clicked.connect(self._update_ui_state)
        self.dialog.findChild(QCheckBox, "restore_persistence").clicked.connect(self._update_ui_state)
        self._update_ui_state()

        # Hide options not available for older versions
        if version < 3.9:
            self.dialog.findChild(QWidget, "restore_persistence_related").hide()

        self.dialog.open()

    def _update_ui_state(self):
        """
        Enable/disable controls as appropriate to the currently selected choices.
        """
        battery_notifications_enabled = self.dialog.findChild(QCheckBox, "battery_notifier").isChecked()
        for object_name in ["battery_notifier_percent", "battery_notifier_freq"]:
            self.dialog.findChild(QSpinBox, object_name).setEnabled(battery_notifications_enabled)
            self.dialog.findChild(QLabel, f"{object_name}_label").setEnabled(battery_notifications_enabled)

        restore_persistence_enabled = self.dialog.findChild(QCheckBox, "restore_persistence").isChecked()
        self.dialog.findChild(QCheckBox, "persistence_dual_boot_quirk").setEnabled(restore_persistence_enabled)

    def _save_and_restart(self):
        """
        Updates the razer.conf file according to the GUI options.
        """
        # razer.conf
        for key in self.keys:
            object_name = key[0]
            group = key[1]
            key_name = key[2]
            data_type = key[3]

            if data_type == bool:
                value = self.dialog.findChild(QCheckBox, object_name).isChecked()
            elif data_type == int:
                value = self.dialog.findChild(QSpinBox, object_name).value()

                if key_name == "battery_notifier_freq":
                    value = int(value * 60)
            else:
                continue

            self._write_config(group, key_name, value)

        # Client
        for meta in self.client:
            filename = meta[0]
            data_type = meta[1]
            path = os.path.join(self.paths.config, "backends", "openrazer", filename)

            if data_type == int:
                data = 1 if self.dialog.findChild(QCheckBox, filename).isChecked() else 0
                with open(path, "w") as f:
                    f.write(str(data))

            elif data_type == float:
                data = self.dialog.findChild(QDoubleSpinBox, filename).value()
                with open(path, "w") as f:
                    f.write(str(data))

        # Restart the daemon to apply changes
        self.menubar.openrazer.restart_daemon()

    def _read_config(self, group, key_name, data_type):
        """
        Reads OpenRazer's razer.conf file, similar format to an INI.
        If value is not found, the default is False or 0.
        """
        config = configparser.ConfigParser()
        config.read(self.conf_path)

        try:
            value = config[group][key_name]
            if value == "True":
                return True
            elif value == "False":
                return False
            else:
                return data_type(value)
        except KeyError:
            # Return default data
            if data_type == int:
                return 0
            elif data_type == bool:
                return False

    def _write_config(self, group, key_name, value):
        """
        Overwrites a new key to OpenRazer's razer.conf file.
        """
        import configparser
        config = configparser.ConfigParser()
        config.read(self.conf_path)

        if group not in config:
            config[group] = {}
        config[group][key_name] = str(value)

        if not os.path.exists(os.path.dirname(self.conf_path)):
            os.makedirs(os.path.dirname(self.conf_path))

        with open(self.conf_path, "w") as f:
            config.write(f)
