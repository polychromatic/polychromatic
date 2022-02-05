# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
"""
This module contains the events when clicking on interactive menu bar components.
"""

import os
import time
import subprocess
import webbrowser

from ..base import PolychromaticBase
from .. import common
from .. import preferences
from .. import procpid
from . import shared
from . import procviewer
from . import troubleshooter

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QBrush, QPixmap, QFont, QIcon
from PyQt5.QtWidgets import QWidget, QMenuBar, QMenu, QAction, QLabel, QDialog, \
                            QPushButton, QTreeWidget, QTreeWidgetItem, \
                            QTextEdit, QButtonGroup, QProgressBar, QMessageBox, \
                            QApplication


class MenuBar(PolychromaticBase):
    """
    Allows the user to quickly change the existing state of the device right now.
    """
    def __init__(self, appdata):
        self.appdata = appdata
        self._ = appdata._
        self.mainwindow = self.appdata.main_window
        self.menubar = self.mainwindow.findChild(QMenuBar)
        self.widgets = shared.PolychromaticWidgets(appdata)

        # Classes per backend
        self.human_name = None
        self.openrazer = MenuBarOpenRazer(appdata, self.widgets)

        # Bind global menu bar items to their events
        # -- File
        self._bind_item("actionNewEffect", self.new_effect)
        self._bind_item("actionImportEffect", self.import_effect)
        self._bind_item("actionNewPreset", self.new_preset)
        self._bind_item("actionNewPresetNow", self.new_preset_now)

        # -- View
        self._bind_item("actionHideMenuBar", self.hide_menu_bar)
        self._bind_item("actionReinstateMenuBar", self.reinstate_menu_bar)
        self._bind_item("actionForceRefresh", self.force_refresh)
        self._bind_item("actionPreferences", self.open_preferences)

        # -- Tools
        self._bind_item("actionRestartTrayApplet", self.restart_tray_applet)
        self._bind_item("actionProcessViewer", self.open_process_viewer)

        # -- Tools > OpenRazer
        self._bind_item("actionOpenRazerWebsite", self.openrazer.website)
        self._bind_item("actionOpenRazerReportBug", self.openrazer.report_bug)
        self._bind_item("actionOpenRazerReleaseNotes", self.openrazer.release_notes)
        self._bind_item("actionOpenRazerConfigure", self.openrazer.configure)
        self._bind_item("actionOpenRazerOpenLog", self.openrazer.open_log)
        self._bind_item("actionOpenRazerRestartDaemon", self.openrazer.restart_daemon)
        self._bind_item("actionOpenRazerAbout", self.openrazer.about)

        # -- Tools > Troubleshooter
        self._bind_item("actionTroubleshootOpenRazer", self.openrazer.troubleshoot)

        # -- Help
        self._bind_item("actionOnlineHelp", self.online_help)
        self._bind_item("actionWebsite", self.polychromatic_website)
        self._bind_item("actionReleaseNotes", self.polychromatic_release_notes)
        self._bind_item("actionReportBug", self.polychromatic_report_bug)
        self._bind_item("actionDonate", self.polychromatic_donate)
        self._bind_item("actionAbout", self.about_polychromatic)

        self._load_icons()

    def _load_icons(self):
        """
        Load icons for the menu bar if Polychromatic's theme is used.
        """
        if self.appdata.system_qt_theme:
            return

        def _set_icon(object_name, icon_dir, icon_name, object_type=QAction):
            self.mainwindow.findChild(object_type, object_name).setIcon(self.widgets.get_icon_qt(icon_dir, icon_name))

        # -- File
        _set_icon("actionNewEffect", "general", "effects")
        _set_icon("actionImportEffect", "general", "import")
        _set_icon("actionNewPreset", "general", "presets")
        _set_icon("actionNewPresetNow", "devices", "all")
        _set_icon("actionQuitApp", "general", "exit")

        # -- Edit
        _set_icon("actionDuplicate", "general", "clone")
        _set_icon("actionDelete", "general", "delete")
        _set_icon("actionRefreshTab", "general", "refresh")
        _set_icon("actionForceRefresh", "general", "refresh")
        _set_icon("actionPreferences", "general", "preferences")

        # -- View
        _set_icon("actionDevices", "general", "devices")
        _set_icon("actionEffects", "general", "effects")
        _set_icon("actionPresets", "general", "presets")
        _set_icon("actionTriggers", "general", "triggers")
        _set_icon("actionReinstateMenuBar", "general", "pin")
        _set_icon("actionHideMenuBar", "general", "pin")

        # -- Tools
        _set_icon("actionTroubleshootOpenRazer", "emblems", "utility")
        _set_icon("actionRestartTrayApplet", "general", "tray-applet")
        _set_icon("actionProcessViewer", "emblems", "software")

        # -- Tools/OpenRazer
        _set_icon("actionOpenRazerWebsite", "general", "external")
        _set_icon("actionOpenRazerConfigure", "general", "preferences")
        _set_icon("actionOpenRazerOpenLog", "general", "folder")
        _set_icon("actionOpenRazerRestartDaemon", "general", "refresh")

        # -- Help
        _set_icon("actionOnlineHelp", "general", "external")

    def _bind_item(self, object_name="", function=object):
        """
        Set up a menu bar item to run this function when selected.
        """
        action = self.mainwindow.findChild(QAction, object_name)
        action.triggered.connect(function)

    def new_effect(self):
        self.appdata.tab_effects.new_file()

    def import_effect(self):
        self.appdata.tab_effects.import_effect()
        pass

    def new_preset(self):
        print("stub:menubar.new_preset")
        pass

    def new_preset_now(self):
        print("stub:menubar.new_preset_now")
        pass

    def hide_menu_bar(self):
        """
        Hide the menu bar for this session until further notice.
        """
        self.menubar.hide()
        self.mainwindow.findChild(QAction, "actionReinstateMenuBar").setVisible(True)
        self.preferences["controller"]["show_menu_bar"] = False
        preferences.save_file(self.paths.preferences, self.preferences)
        self.widgets.open_dialog(self.widgets.dialog_generic,
                                 self._("Hide Menu Bar"),
                                 self._("The menu bar is now hidden. To temporarily reveal, press Alt."))

    def reinstate_menu_bar(self):
        """
        Keep the menu bar between sessions
        """
        self.mainwindow.findChild(QAction, "actionReinstateMenuBar").setVisible(False)
        self.preferences["controller"]["show_menu_bar"] = True
        preferences.save_file(self.paths.preferences, self.preferences)

    def _is_editor_running(self):
        """
        Returns a boolean to indicate whether an editor is currently running.
        """
        editors = self.appdata.tab_effects.editors
        for editor in editors:
            if editors[editor].alive:
                return True
        return False

    def force_refresh(self):
        """
        Restarts the application execution so backends can be cleanly re-initialised.
        This is useful when devices are inserted/removed.
        """
        if self._is_editor_running():
            self.widgets.open_dialog(self.widgets.dialog_generic,
                                     self._("Force Refresh"),
                                     self._("Please close all editor windows before executing this action."))
            return

        procmgr = procpid.ProcessManager()
        procmgr.restart_self(self.exec_path, self.exec_args)

    def open_preferences(self):
        self.appdata.ui_preferences.open_window()

    def restart_tray_applet(self):
        process = procpid.ProcessManager("tray-applet")
        process.start_component()

    def open_process_viewer(self):
        procviewer.ProcessViewer(self.appdata)

    def _prompt_on_locale_change(self, title):
        """
        Informs the user if the resource they click is only available in English.
        """
        if not self.i18n.get_current_locale().startswith("en"):
            self.widgets.open_dialog(self.widgets.dialog_generic,
                                     title,
                                     self._("Polychromatic is about to open a web page for this resource. Unfortunately, it is only available in English at this time."))

    def online_help(self):
        self._prompt_on_locale_change(self._("Online Help"))

        # For context, open the most relevant documentation
        context = "/"
        tabs = self.mainwindow.findChild(QWidget, "MainTabWidget")
        if tabs:
            current_tab = tabs.currentIndex()
            indexes = {
                0: "/controller/devices/",
                1: "/controller/effects/",
                2: "/controller/presets/",
                3: "/controller/triggers/"
            }
            context = indexes[current_tab]

        webbrowser.open("https://docs.polychromatic.app" + context)

    def polychromatic_website(self):
        self._prompt_on_locale_change(self._("Website"))
        webbrowser.open("https://polychromatic.app/")

    def polychromatic_release_notes(self):
        self._prompt_on_locale_change(self._("What's New?"))
        webbrowser.open("https://polychromatic.app/permalink/latest/")

    def polychromatic_report_bug(self):
        self._prompt_on_locale_change(self._("Report Bug"))
        webbrowser.open("https://polychromatic.app/permalink/bugs/")

    def polychromatic_donate(self):
        self._prompt_on_locale_change(self._("Donate"))
        webbrowser.open("https://polychromatic.app/permalink/donate/")

    def _show_aboutbox(self, title, logo, homepage_url, versions, license_text, links):
        """
        Shows an about dialog box with the specified parameters.

        Params:
            title           (str)   Application title
            logo            (str)   Absolute path to application's logo
            homepage_url    (str)   HTTPS link to the project's homepage
            versions        (list)  Table of strings: [["name": "ver"]]
            license_text    (str)   Show this license text.
            links           (list)  List of links: [["label": "url"]]
        """
        about = shared.get_ui_widget(self.appdata, "about", QDialog)

        # Logo
        about_icon = about.findChild(QLabel, "AppIcon")
        shared.set_pixmap_for_label(about_icon, logo, 96)

        # App Name
        name = about.findChild(QLabel, "AppName")
        name.setText(title)

        # URL under the application title
        url = about.findChild(QLabel, "AppURL")
        def _link(a):
            webbrowser.open(homepage_url)
        url.mousePressEvent = _link
        url.setText(homepage_url)

        # Set text colour if using Polychromatic Qt theme
        if not self.appdata.system_qt_theme:
            name.setStyleSheet("QLabel { color: lime }")
            url.setStyleSheet("QLabel { color: lime }")

        # List versions & dependencies
        tree = about.findChild(QTreeWidget, "VersionTree")
        column = tree.invisibleRootItem()
        for version in versions:
            item = QTreeWidgetItem()
            item.setText(0, version[0])
            item.setText(1, version[1])
            column.addChild(item)

        # Add application links
        links_widget = about.findChild(QWidget, "TabLinks").layout()
        button_grp = QButtonGroup()
        for button in links:
            label = button[0]
            href = button[1]
            btn = QPushButton(QIcon(common.get_icon("general", "external")), label)
            btn.setToolTip(href)
            btn.href = href
            button_grp.addButton(btn)
            links_widget.addWidget(btn)

        def clicked_button_grp(button):
            webbrowser.open(button.href)

        button_grp.buttonClicked.connect(clicked_button_grp)

        # Show license text
        license = about.findChild(QTextEdit, "LicenseText")
        license.setPlainText(license_text)

        # Set up the about window
        close = about.findChild(QPushButton, "Close")
        def _close(a):
            about.accept()
        close.clicked.connect(_close)
        if not self.appdata.system_qt_theme:
            close.setIcon(self.widgets.get_icon_qt("general", "close"))

        window_title = ' '.join(sub[:1].upper() + sub[1:] for sub in title.split(' '))
        about.setWindowTitle(self._("About []").replace("[]", window_title))
        about.setWindowIcon(QIcon(logo))
        about.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        about.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        about.exec()

    def about_polychromatic(self):
        logo = common.get_icon("logo", "polychromatic")

        with open(os.path.join(self.appdata.paths.data_dir, "licenses/app.txt"), "r") as f:
            license = f.read()

        links = [
            [self._("Documentation"), "https://docs.polychromatic.app/"],
            [self._("Source Code"), "https://polychromatic.app/permalink/src/"],
            [self._("Release Notes"), "https://polychromatic.app/permalink/latest/"],
            [self._("Donate"), "https://polychromatic.app/permalink/donate/"]
        ]

        versions = self.appdata.versions
        self._show_aboutbox("polychromatic {0}".format(versions[0][1]), logo, "https://polychromatic.app", versions, license, links)


class MenuBarOpenRazer(MenuBar):
    """
    Options for the OpenRazer backend under the Tools menu. When the backend is
    not present, there may be a limited set of options.
    """
    def __init__(self, appdata, widgets):
        self.human_name = "OpenRazer"
        self.appdata = appdata
        self.widgets = widgets
        self.module = None
        self.running = None
        self.url_website = "https://openrazer.github.io"
        self.url_src = "https://github.com/openrazer/openrazer/"
        self.url_bugs = "https://github.com/openrazer/openrazer/issues"
        self.url_latest = "https://github.com/openrazer/openrazer/releases/latest"

    def _refresh(self):
        """
        Initialises the variables for this class, if not done so already.
        """
        self.module = self.middleman.get_backend("openrazer")
        self.running = True if self.module else False

    def website(self):
        webbrowser.open(self.url_website)

    def report_bug(self):
        webbrowser.open(self.url_bugs)

    def release_notes(self):
        webbrowser.open(self.url_latest)

    def configure(self):
        self.appdata.ui_preferences.openrazer.open_window()

    def open_log(self):
        cmd = None
        try:
            cmd = "xdg-open file://{0}/openrazer/logs/razer.log".format(os.environ["XDG_DATA_HOME"])
        except KeyError:
            pass

        if not cmd:
            try:
                cmd = "xdg-open file:///home/{0}/.local/share/openrazer/logs/razer.log".format(os.environ["USER"])
            except KeyError:
                cmd = "xdg-open file:///home/$USER/.local/share/openrazer/logs/razer.log"

        print("Running: " + cmd)
        os.system(cmd)

    def restart_daemon(self):
        """
        Restart the OpenRazer daemon, which also requires the application and
        any background processes (including the tray applet) to restart.
        """
        def _reload_openrazer():
            self.appdata.main_window.hide()
            self.loading = shared.get_ui_widget(self.appdata, "loading", QDialog)

            label = self.loading.findChild(QLabel, "Label")
            label.setText(self._("Restarting the backend/application..."))
            self.loading.show()
            common.run_thread(_reload_openrazer_thread)

        def _reload_openrazer_thread():
            self.appdata.middleman.get_backend("openrazer").restart()
            procmgr = procpid.ProcessManager()
            procmgr.restart_all()
            procmgr.restart_self(self.exec_path, self.exec_args)

        self.widgets.open_dialog(self.widgets.dialog_generic,
                                 self._("Restart Backend?"),
                                 self._("Restarting this backend will also restart Polychromatic. Any unsaved data will be lost. Continue?"),
                                 buttons=[QMessageBox.Ok, QMessageBox.Cancel],
                                 default_button=QMessageBox.Ok,
                                 actions={QMessageBox.Ok: _reload_openrazer})

    def _get_dbus_version(self):
        """
        For about dialog, get the D-Bus version (used by the OpenRazer driver)
        """
        try:
            output = subprocess.Popen(["dbus-daemon", "--version"], stdout=subprocess.PIPE).communicate()[0]
            return output.decode("UTF-8").split("\n")[0].split(" ")[-1]
        except Exception:
            self.dbg.stdout("Unable to get D-Bus version! Ignoring.", self.dbg.warning)
            return "[Unknown]"

    def _get_dkms_version(self):
        """
        For about dialog, get the DMKS version (used by the OpenRazer driver)
        """
        try:
            output = subprocess.Popen(["dkms", "--version"], stdout=subprocess.PIPE).communicate()[0]
            # Output: "dkms:2.8" or "dkms-2.8.6"
            return output.decode("UTF-8").strip()[5:]
        except Exception:
            self.dbg.stdout("Unable to get DKMS version! Ignoring.", self.dbg.warning)
            return "[Unknown]"

    def troubleshoot(self):
        self.troubleshooter = troubleshooter.TroubleshooterGUI(self.appdata, "openrazer", "OpenRazer")

    def about(self):
        self._refresh()

        # Cannot show details if backend is not running
        if not self.running:
            self.dbg.stdout("Cannot open OpenRazer about dialog as backend is not loaded!", self.dbg.error)
            return

        logo = common.get_icon("logo", "openrazer")
        links = [
            [self._("Website"), self.url_website],
            [self._("Source Code"), self.url_src],
            [self._("Release Notes"), self.url_latest]
        ]

        with open(os.path.join(self.paths.data_dir, "licenses/GPLv2.txt"), "r") as f:
            license = f.read()

        versions = [
            ["Daemon", self.module.devman.daemon_version],
            ["Python Library", self.module.version]
        ]

        # Attempt to add dependencies to the version list
        version_dbus = self._get_dbus_version()
        version_dkms = self._get_dkms_version()

        if version_dbus:
            versions.append(["D-Bus", version_dbus])

        if version_dkms:
            versions.append(["DKMS", version_dkms])

        self._show_aboutbox("OpenRazer {0}".format(self.module.version), logo, "https://openrazer.github.io", versions, license, links)
