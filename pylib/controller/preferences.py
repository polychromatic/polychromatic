#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
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
                            QDialogButtonBox, QTabWidget, QMessageBox


class PreferencesWindow(shared.TabData):
    """
    A window for adjusting the options of the application, viewing background
    processes and getting more information about backends in use.
    """
    def __init__(self, appdata):
        super().__init__(appdata)
        self.openrazer = OpenRazerPreferences(appdata)
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

            # -- Tray
            ["tray", "enabled", QCheckBox, "TrayAutoStart", False],
            ["tray", "mode", QComboBox, "TrayModeCombo", False],

            # -- Editor
            ["editor", "live_preview", QCheckBox, "LivePreview", False],
        ]

    def open_window(self):
        """
        Opens the Preferences window to change Polychromatic's options.
        """
        self.pref_data = pref.load_file(pref.path.preferences)

        self.dialog = shared.get_ui_widget(self.appdata, "preferences", QDialog)
        self.dialog.findChild(QDialogButtonBox, "DialogButtons").accepted.connect(self._save_changes)

        # Options
        for option in self.options:
            self._load_option(option[0], option[1], option[2], option[3], option[4])

        # Create pickers
        print("fixme:TrayIconPLACEHOLDER")
        tray_icon_widget = self.dialog.findChild(QLabel, "TrayIconPLACEHOLDER")

        # Background Tasks
        self._refresh_background_tasks_status()

        # Backend Buttons
        self.dialog.findChild(QPushButton, "OpenRazerSettings").clicked.connect(self.menubar.openrazer.configure)
        self.dialog.findChild(QPushButton, "OpenRazerAbout").clicked.connect(self.menubar.openrazer.about)
        self.dialog.findChild(QPushButton, "OpenRazerOpenLog").clicked.connect(self.menubar.openrazer.open_log)
        self.dialog.findChild(QPushButton, "OpenRazerRestartDaemon").clicked.connect(self.menubar.openrazer.restart_daemon)
        self.dialog.findChild(QPushButton, "OpenRazerTroubleshoot").clicked.connect(self.menubar.openrazer.troubleshoot)

        # Backend Status
        for backend in middleman.BACKEND_ID_NAMES.keys():
            label = self._("Not in use")
            icon = "serious"

            for obj in self.middleman.backends:
                if obj.backend_id == backend:
                    label = self._("Currently in use.")
                    icon = "success"
                    break

            if backend in self.middleman.not_installed:
                label = self._("Not installed.")
                icon = "warning"

            elif backend in self.middleman.import_errors.keys():
                label = self._("Error loading the module.")
                icon = "serious"

            pixmap_src = QPixmap(common.get_icon("general", icon))
            pixmap = pixmap_src.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            self.dialog.findChild(QLabel, "Status_" + backend + "_label").setText(label)
            self.dialog.findChild(QLabel, "Status_" + backend + "_icon").setPixmap(pixmap)

        # Prompt for a restart after changing these options
        def _cb_set_restart_flag():
            self.prompt_restart = True

        self.dialog.findChild(QCheckBox, "UseSystemQtTheme").stateChanged.connect(_cb_set_restart_flag)

        # Restart the applet after changing these options
        def _cb_set_applet_flag(i):
            self.restart_applet = True

        self.dialog.findChild(QComboBox, "TrayModeCombo").currentIndexChanged.connect(_cb_set_applet_flag)

        self.dialog.findChild(QTabWidget, "PreferencesTabs").setCurrentIndex(0)
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

        self.pref_data[group][item] = data

    def _refresh_background_tasks_status(self):
        """
        Refreshes the background tasks
        """
        print("stub:PreferencesWindow._refresh_background_tasks_status")

        tree = self.dialog.findChild(QTreeWidget, "TasksTree")

        # TODO: Not fully implemented yet!
        self.dialog.findChild(QTabWidget, "PreferencesTabs").setTabEnabled(3, False)

    def _save_changes(self):
        """
        Writes the preferences to file according to the GUI.
        """
        self.dbg.stdout("Saving preferences...", self.dbg.action, 1)
        for option in self.options:
            self._set_option(option[0], option[1], option[2], option[3], option[4])

        result = pref.save_file(pref.path.preferences, self.pref_data)
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

            def _cb_restart_now():
                procpid.restart_self(self.appdata.exec_path, self.appdata.exec_args)

            self.widgets.open_dialog(self.widgets.dialog_generic,
                                     self._("Restart Required"),
                                     self._("To apply these changes, the application must be restarted. Any unsaved changes will be lost."),
                                     None, None,
                                     [QMessageBox.Apply, QMessageBox.Ignore],
                                     QMessageBox.Apply,
                                     {
                                        QMessageBox.Apply: _cb_restart_now
                                     })

        # Reload tray applet
        if self.restart_applet:
            self.dbg.stdout("Tray applet settings changed. Will restart component.", self.dbg.action, 1)
            procpid.restart_component("tray-applet")

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
            ["General", "verbose_logging", bool],
            ["Startup", "sync_effects_enabled", bool],
            ["Startup", "devices_off_on_screensaver", bool],
            ["Startup", "mouse_battery_notifier", bool],
            ["Startup", "mouse_battery_notifier_freq", int],
            ["Statistics", "key_statistics", bool],
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

        self.dialog.open()

    def _save_and_restart(self):
        """
        Updates the razer.conf file according to the GUI options.
        """
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
