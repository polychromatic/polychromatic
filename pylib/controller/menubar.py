#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module contains the events when clicking on interactive menu bar components.
"""

import os
import subprocess
import webbrowser

from .. import common
from .. import preferences
from .. import procpid
from . import shared

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtWidgets import QWidget, QMenuBar, QAction, QLabel, QDialog, \
                            QPushButton, QTreeWidget, QTreeWidgetItem, \
                            QTextEdit, QButtonGroup, QProgressBar


class MenuBar(object):
    """
    Allows the user to quickly change the existing state of the device right now.
    """
    def __init__(self, appdata):
        self.appdata = appdata
        self.mainwindow = self.appdata.main_window
        self.menubar = self.mainwindow.findChild(QMenuBar, "menuBar")
        self.widgets = shared.PolychromaticWidgets(appdata)

        # Classes per backend
        self.human_name = None
        self.openrazer = MenuBarOpenRazer(appdata, self.widgets)

        # Bind global menu bar items to their events
        # -- File
        #self._bind_item("actionNewEffect", pass)
        #self._bind_item("actionNewPreset", pass)
        #self._bind_item("actionNewPresetNow", pass)

        # -- View
        self._bind_item("actionHideMenuBar", self.hide_menu_bar)
        self._bind_item("actionReinstateMenuBar", self.reinstate_menu_bar)
        self._bind_item("actionPreferences", self.open_preferences)

        # -- Tools
        self._bind_item("actionRestartTrayApplet", self.restart_tray_applet)
        self._bind_item("actionRestartHelper", self.restart_helper)

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

    def _bind_item(self, object_name="", function=object):
        """
        Set up a menu bar item to run this function when selected.
        """
        action = self.mainwindow.findChild(QAction, object_name)
        action.triggered.connect(function)

    def hide_menu_bar(self):
        """
        Hide the menu bar for this session until further notice.
        """
        self.menubar.hide()
        self.mainwindow.findChild(QAction, "actionReinstateMenuBar").setVisible(True)
        self.appdata.preferences["controller"]["show_menu_bar"] = False
        preferences.save_file(self.appdata.path.preferences, self.appdata.preferences)

    def reinstate_menu_bar(self):
        """
        Keep the menu bar between sessions
        """
        self.mainwindow.findChild(QAction, "actionReinstateMenuBar").setVisible(False)
        self.appdata.preferences["controller"]["show_menu_bar"] = True
        preferences.save_file(self.appdata.path.preferences, self.appdata.preferences)

    def _run_troubleshooter(self, backend):
        """
        Run the troubleshooter and shows the results in a dialog box.
        """
        _ = self.appdata._
        dbg = self.appdata.dbg

        dbg.stdout("Running Troubleshooter for {0}...".format(backend), dbg.action, 1)
        self.loading = shared.get_ui_widget(self.appdata, "loading", QDialog)

        label = self.loading.findChild(QLabel, "Label")
        label.setText(_("Running troubleshooter..."))
        bar = self.loading.findChild(QProgressBar, "ProgressBar")
        bar.setRange(0,0)

        self.loading.setWindowTitle(_("Troubleshooting..."))
        self.loading.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.loading.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self.loading.open()

        def _troubleshoot_complete():
            _ = self.appdata._
            results = self.thread.result
            self.loading.close()

            if results == None:
                self.widgets.open_dialog(self.widgets.dialog_warning,
                                         _("Troubleshooting Failed"),
                                         _("The troubleshooter for this backend is not avaliable for this operating system."))
                return
            elif results == str:
                self.widgets.open_dialog(self.widgets.dialog_error,
                                         _("Troubleshooting Failed"),
                                         _("The troubleshooter was not expecting that! The process failed as an exception was thrown."),
                                         None,
                                         results)
                return

            self.result_window = shared.get_ui_widget(self.appdata, "troubleshooter", QDialog)
            label = self.result_window.findChild(QLabel, "Title")
            tree = self.result_window.findChild(QTreeWidget, "Results")
            column = tree.invisibleRootItem()

            all_passed = True
            for result in results:
                item = QTreeWidgetItem()
                item.setText(0, _("Passed") if result["passed"] else _("Failed"))
                item.setText(1, result["test_name"])
                item.setIcon(0, QIcon(common.get_icon("general", "success")))

                # Provide suggestions on failures
                if not result["passed"]:
                    item.setIcon(0, QIcon(common.get_icon("general", "serious")))
                    all_passed = False

                    suggestion = result["suggestion"].split(". ")
                    for line in suggestion:
                        subitem = QTreeWidgetItem()
                        subitem.setText(1, "• " + line)
                        subitem.setToolTip(1, line)
                        item.addChild(subitem)
                column.addChild(item)

            def _close_troubleshooter():
                self.result_window.close()
            self.result_window.findChild(QPushButton, "Close").clicked.connect(_close_troubleshooter)

            tree.expandAll()
            self.result_window.setWindowTitle(_("Troubleshooter for []").replace("[]", self.human_name))
            if all_passed:
                label.setText(_("Everything appears to be in working order!"))
            self.result_window.open()

        class TroubleshootThread(QThread):
            def run(self):
                self.result = self.appdata.middleman.troubleshoot(backend, self.appdata._)

        # Run in separate thread just in case this takes longer on some systems
        self.thread = TroubleshootThread()
        self.thread.appdata = self.appdata
        self.thread.result = []
        self.thread.finished.connect(_troubleshoot_complete)
        self.thread.start()

    def open_preferences(self):
        self.appdata.ui_preferences.open_window()

    def restart_tray_applet(self):
        procpid.start_component("tray-applet")

    def restart_helper(self):
        print("stub:restart_helper")

    def online_help(self):
        webbrowser.open("https://polychromatic.app/docs/")

    def polychromatic_website(self):
        webbrowser.open("https://polychromatic.app/")

    def polychromatic_release_notes(self):
        webbrowser.open("https://polychromatic.app/permalink/latest/")

    def polychromatic_report_bug(self):
        webbrowser.open("https://polychromatic.app/permalink/bugs/")

    def polychromatic_donate(self):
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
        _ = self.appdata._

        # Logo
        about_icon = about.findChild(QLabel, "AppIcon")
        pixmap_src = QPixmap(logo)
        pixmap = pixmap_src.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        about_icon.setPixmap(pixmap)

        layout = about.findChild(QWidget, "AppDetails").layout()

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
        license.setMarkdown(license_text)

        # Set up the about window
        close = about.findChild(QPushButton, "Close")
        def _close(a):
            about.accept()
        close.clicked.connect(_close)

        window_title = ' '.join(sub[:1].upper() + sub[1:] for sub in title.split(' '))
        about.setWindowTitle(_("About []").replace("[]", window_title))
        about.setWindowIcon(QIcon(logo))
        about.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        about.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        about.exec()

    def about_polychromatic(self):
        _ = self.appdata._
        logo = common.get_icon("logo", "polychromatic")

        with open(os.path.join(self.appdata.data_path, "license.txt"), "r") as f:
            license = f.read()

        links = [
            [_("Documentation"), "https://polychromatic.app/docs/"],
            [_("Source Code"), "https://polychromatic.app/permalink/src/"],
            [_("Release Notes"), "https://polychromatic.app/permalink/latest/"],
            [_("Donate"), "https://polychromatic.app/permalink/donate/"]
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
        Initalizes the variables for this class, if not done so already.
        """
        self.module = self.appdata.middleman.get_backend("openrazer")
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
        # TODO: Prompt that interuptted background tasks, etc
        print("stub:restart middleman")

    def _get_dbus_version(self):
        """
        For about dialog, get the DBUS version (used by the OpenRazer driver)
        """
        dbg = self.appdata.dbg
        try:
            output = subprocess.Popen(["dbus-daemon", "--version"], stdout=subprocess.PIPE).communicate()[0]
            first_line = str(output).split("\\n")[0]
            return first_line.split(" ")[-1]
        except Exception:
            dbg.stdout("Unable to get DKMS version! Ignoring...", dbg.warning)
            return "[Unknown]"

    def _get_dkms_version(self):
        """
        For about dialog, get the DMKS version (used by the OpenRazer driver)
        """
        dbg = self.appdata.dbg
        try:
            output = subprocess.Popen(["dkms", "--version"], stdout=subprocess.PIPE).communicate()[0]
            first_line = str(output).split("\\n")[0]
            return first_line.split(":")[1].strip()
        except Exception:
            dbg.stdout("Unable to get DKMS version! Ignoring...", dbg.warning)
            return "[Unknown]"

    def troubleshoot(self):
        self._run_troubleshooter("openrazer")

    def about(self):
        self._refresh()
        _ = self.appdata._

        # Cannot show details if backend is not running
        if not self.running:
            dbg = self.appdata.dbg
            dbg.stdout("Cannot open OpenRazer about dialog as backend is not loaded!", dbg.error)
            return

        logo = common.get_icon("logo", "openrazer")
        links = [
            [_("Website"), self.url_website],
            [_("Source Code"), self.url_src],
            [_("Release Notes"), self.url_latest]
        ]

        license = """
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
        """

        versions = [
            ["Daemon", self.module.devman.daemon_version],
            ["Python Library", self.module.version]
        ]

        # Attempt to add dependencies to the version list
        version_dbus = self._get_dbus_version()
        version_dkms = self._get_dkms_version()

        if version_dbus:
            versions.append(["DBUS", version_dbus])

        if version_dkms:
            versions.append(["DKMS", version_dkms])

        self._show_aboutbox("OpenRazer {0}".format(self.module.version), logo, "https://openrazer.github.io", versions, license, links)
