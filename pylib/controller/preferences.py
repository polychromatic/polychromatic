#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2021 Luke Horwell <code@horwell.me>
#
"""
This module controls the 'Preferences' window of the Controller GUI.
"""

from .. import common
from .. import effects
from .. import locales
from .. import middleman
from .. import procpid
from .. import preferences as pref
from . import shared

import os
#import configparser        # Imported on demand, OpenRazer only

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QPushButton, QTreeWidget, QLabel, \
                            QComboBox, QCheckBox, QDialog, QSpinBox, \
                            QDoubleSpinBox, QDialogButtonBox, QTabWidget, \
                            QMessageBox


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

    def open_window(self):
        """
        Opens the Preferences window to change Polychromatic's options.
        """
        self.pref_data = pref.load_file(self.paths.preferences)

        self.dialog = shared.get_ui_widget(self.appdata, "preferences", QDialog)
        self.dialog.findChild(QDialogButtonBox, "DialogButtons").accepted.connect(self._save_changes)

        # Set Tab Icons
        tabs = self.dialog.findChild(QTabWidget, "PreferencesTabs")
        tabs.setTabIcon(0, self.widgets.get_icon_qt("general", "controller"))
        tabs.setTabIcon(1, self.widgets.get_icon_qt("general", "tray-applet"))
        tabs.setTabIcon(2, self.widgets.get_icon_qt("effects", "paint"))
        tabs.setTabIcon(3, self.widgets.get_icon_qt("general", "matrix"))
        tabs.setTabIcon(4, self.widgets.get_icon_qt("emblems", "software"))

        # Set Dialog Button Icons
        if not self.appdata.system_qt_theme:
            self.dialog.findChild(QPushButton, "SavedColoursButton").setIcon(self.widgets.get_icon_qt("general", "edit"))
            self.dialog.findChild(QPushButton, "SavedColoursReset").setIcon(self.widgets.get_icon_qt("general", "reset"))
            self.dialog.findChild(QDialogButtonBox, "DialogButtons").button(QDialogButtonBox.Save).setIcon(self.widgets.get_icon_qt("general", "save"))
            self.dialog.findChild(QDialogButtonBox, "DialogButtons").button(QDialogButtonBox.Cancel).setIcon(self.widgets.get_icon_qt("general", "cancel"))

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

        tray_icon_picker = self.widgets.create_icon_picker_control(_set_new_tray_icon, self.pref_data["tray"]["icon"], self._("Choose Tray Applet Icon"), shared.IconPicker.purpose_tray_icon_only)
        tray_icon_widget = self.dialog.findChild(QLabel, "TrayIconPickerPlaceholder")
        tray_icon_widget.parentWidget().layout().replaceWidget(tray_icon_widget, tray_icon_picker)

        # Backend Buttons
        self.dialog.findChild(QPushButton, "OpenRazerSettings").clicked.connect(self.menubar.openrazer.configure)
        self.dialog.findChild(QPushButton, "OpenRazerAbout").clicked.connect(self.menubar.openrazer.about)
        self.dialog.findChild(QPushButton, "OpenRazerRestartDaemon").clicked.connect(self.menubar.openrazer.restart_daemon)
        self.dialog.findChild(QPushButton, "OpenRazerTroubleshoot").clicked.connect(self.menubar.openrazer.troubleshoot)

        # Labels disguised as buttons
        view_log = self.dialog.findChild(QLabel, "OpenRazerLog")
        def view_log_clicked(QMouseEvent):
            if QMouseEvent.button() == Qt.LeftButton:
                self.openrazer.open_log()
        view_log.mouseReleaseEvent = view_log_clicked

        if not self.appdata.system_qt_theme:
            self.dialog.findChild(QPushButton, "OpenRazerSettings").setIcon(self.widgets.get_icon_qt("general", "preferences"))
            self.dialog.findChild(QPushButton, "OpenRazerAbout").setIcon(self.widgets.get_icon_qt("general", "info"))
            self.dialog.findChild(QPushButton, "OpenRazerRestartDaemon").setIcon(self.widgets.get_icon_qt("general", "refresh"))
            self.dialog.findChild(QPushButton, "OpenRazerTroubleshoot").setIcon(self.widgets.get_icon_qt("emblems", "utility"))

        # Drop custom icons when using native themes
        if self.appdata.system_qt_theme:
            combo = self.dialog.findChild(QComboBox, "LandingTabCombo")
            for i in range(0, combo.count()):
                combo.setItemIcon(i, QIcon())

        # Prompt for a restart after changing these options
        def _cb_set_restart_flag():
            self.prompt_restart = True

        self.dialog.findChild(QCheckBox, "UseSystemQtTheme").stateChanged.connect(_cb_set_restart_flag)

        # Restart the applet after changing these options
        def _cb_set_applet_flag(i):
            self.restart_applet = True

        self.dialog.findChild(QComboBox, "TrayModeCombo").currentIndexChanged.connect(_cb_set_applet_flag)

        # FIXME: Hide incomplete features
        self.dialog.findChild(QComboBox, "LandingTabCombo").removeItem(3)
        self.dialog.findChild(QComboBox, "LandingTabCombo").removeItem(2)

        # Show time!
        self.dialog.findChild(QTabWidget, "PreferencesTabs").setCurrentIndex(0)
        self.refresh_backend_status()
        self.dialog.open()

    def refresh_backend_status(self):
        """
        Refreshes the current status and enables/disables controls accordingly.
        """
        if not self.dialog:
            return

        # See also: polychromatic_controller.Applicationdata.init_bg_thread.BackgroundThread()
        openrazer_disabled = True if not "openrazer" in self.appdata.middleman.get_backends() else False
        self.dialog.findChild(QPushButton, "OpenRazerSettings").setDisabled(openrazer_disabled)
        self.dialog.findChild(QPushButton, "OpenRazerAbout").setDisabled(openrazer_disabled)
        self.dialog.findChild(QPushButton, "OpenRazerRestartDaemon").setDisabled(openrazer_disabled)
        self.dialog.findChild(QPushButton, "OpenRazerTroubleshoot").setDisabled(openrazer_disabled)
        self.dialog.findChild(QLabel, "OpenRazerLog").setDisabled(openrazer_disabled)

        # Backend Status
        for backend in middleman.BACKEND_ID_NAMES.keys():
            label = self._("Unknown")
            icon = "serious"

            for obj in self.middleman.backends:
                if obj.backend_id == backend:
                    label = self._("Active")
                    icon = "success"
                    break

            if backend in self.middleman.not_installed:
                label = self._("Not Installed")
                icon = "warning"

            elif backend in self.middleman.import_errors.keys():
                label = self._("Error loading the module")
                icon = "serious"

            backend_label = self.dialog.findChild(QLabel, "Status_" + backend + "_label")
            backend_label.setText(label)

            backend_status_icon = self.dialog.findChild(QLabel, "Status_" + backend + "_icon")
            shared.set_pixmap_for_label(backend_status_icon, common.get_icon("general", icon), 24)

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
        self.appdata.preferences = self.pref_data

        # Instant reload
        if self.pref_data["controller"]["show_menu_bar"] == True:
            self.menubar.reinstate_menu_bar()
        else:
            self.menubar.hide_menu_bar()

        # Some options require a restart
        if self.prompt_restart:
            self.dbg.stdout("Program settings changed. Prompting to restart application.", self.dbg.action, 1)
            procmgr = procpid.ProcessManager()

            def _cb_restart_now():
                procmgr.restart_self(self.appdata.exec_path, self.appdata.exec_args)

            self.widgets.open_dialog(self.widgets.dialog_generic,
                                     self._("Restart Required"),
                                     self._("To apply these changes, the application must be restarted. Any unsaved changes will be lost."),
                                     None, None,
                                     [QMessageBox.Ok, QMessageBox.Ignore],
                                     QMessageBox.Ok,
                                     {
                                        QMessageBox.Ok: _cb_restart_now
                                     })

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
                                 None, None,
                                 [QMessageBox.Ok, QMessageBox.Cancel],
                                 QMessageBox.Ok,
                                 {QMessageBox.Ok: _cb_reset_colours})


class OpenRazerPreferences(shared.TabData):
    """
    A special window for changing the OpenRazer configuration file when OpenRazer
    is in use.
    """
    def __init__(self, appdata):
        super().__init__(appdata)

        # OpenRazer uses configparser. If not available, open text editor instead.
        try:
            import configparser
            self.config_possible = True
        except (ImportError, ModuleNotFoundError):
            self.config_possible = False

        self.conf_path = None
        try:
            self.conf_path = "{0}/.config/openrazer/razer.conf".format(os.environ["XDG_CONFIG_HOME"])
        except KeyError:
            pass

        if not self.conf_path:
            try:
                self.conf_path = "/home/{0}/.config/openrazer/razer.conf".format(os.environ["USER"])
            except KeyError:
                self.conf_path = "/home/$USER/.config/openrazer/razer.conf"

        self.keys = [
            # "Group", "Item", <data type>
            ["General", "verbose_logging", bool],
            #["Startup", "sync_effects_enabled", bool],
            ["Startup", "devices_off_on_screensaver", bool],
            ["Startup", "mouse_battery_notifier", bool],
            ["Startup", "mouse_battery_notifier_freq", int],
            ["Startup", "restore_persistence", bool],
        ]

        self.client = [
            # "Filename", <data type>
            ["allow_image_download", int],
            ["ripple_refresh_rate", float]
        ]

    def open_log(self):
        self.menubar.openrazer.open_log()

    def restart_daemon(self):
        self.menubar.openrazer.restart_daemon()

    def open_window(self):
        """
        Opens a window for adjusting OpenRazer options.

        If configparser is not present for some reason, open the text editor.
        """
        if not self.config_possible:
            os.system("xdg-open file://{0}".format(self.conf_path))
            return

        self.dialog = shared.get_ui_widget(self.appdata, "openrazer-config", QDialog)
        self.dialog.findChild(QDialogButtonBox, "DialogButtons").accepted.connect(self._save_and_restart)

        # Set Dialog Button Icons
        if not self.appdata.system_qt_theme:
            self.dialog.findChild(QDialogButtonBox, "DialogButtons").button(QDialogButtonBox.Save).setIcon(self.widgets.get_icon_qt("general", "save"))
            self.dialog.findChild(QDialogButtonBox, "DialogButtons").button(QDialogButtonBox.Cancel).setIcon(self.widgets.get_icon_qt("general", "cancel"))

        # razer.conf
        for key in self.keys:
            group = key[0]
            key_name = key[1]
            data_type = key[2]

            if data_type == bool:
                chkbox = self.dialog.findChild(QCheckBox, key_name)
                chkbox.setChecked(self._read_config(group, key_name, bool))

            elif data_type == int:
                spinner = self.dialog.findChild(QSpinBox, key_name)
                spinner.setValue(self._read_config(group, key_name, int))

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

        self.dialog.open()

    def _save_and_restart(self):
        """
        Updates the razer.conf file according to the GUI options.
        """
        # razer.conf
        for key in self.keys:
            group = key[0]
            key_name = key[1]
            data_type = key[2]

            if data_type == bool:
                value = self.dialog.findChild(QCheckBox, key_name).isChecked()
            elif data_type == int:
                value = self.dialog.findChild(QSpinBox, key_name).value()
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
        import configparser
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
        config[group][key_name] = str(value)
        with open(self.conf_path, "w") as f:
            config.write(f)
