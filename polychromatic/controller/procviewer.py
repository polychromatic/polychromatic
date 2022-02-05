# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2021-2022 Luke Horwell <code@horwell.me>
"""
This module controls the 'Background Tasks' window accessible from the menu bar.
"""

from ..base import PolychromaticBase
from .. import common
from .. import procpid
from . import shared

import glob
import os
import time
import subprocess

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QDialog, QPushButton, QTreeWidget, \
                            QLabel, QTreeWidgetItem


class ProcessViewer(PolychromaticBase):
    """
    The process viewer provides details into the procpid module implementation.
    Allows the user to view processes spawned by Polychromatic, stop them or
    restart them for diagnosis purposes.
    """
    def __init__(self, appdata):
        self.appdata = appdata
        self.widgets = shared.PolychromaticWidgets(appdata)

        # Session
        self.dialog_is_open = True

        # UI Controls
        self.dialog = shared.get_ui_widget(appdata, "procviewer", q_toplevel=QDialog)
        self.tree = self.dialog.findChild(QTreeWidget, "TasksTree")
        self.close = self.dialog.findChild(QPushButton, "Close")
        self.btn_refresh = self.dialog.findChild(QPushButton, "TasksRefresh")
        self.btn_reload = self.dialog.findChild(QPushButton, "TasksReloadAll")
        self.btn_stop = self.dialog.findChild(QPushButton, "TasksStopTask")

        # Set Dialog Button Icons
        if not self.appdata.system_qt_theme:
            self.close.setIcon(self.widgets.get_icon_qt("general", "close"))
            self.btn_refresh.setIcon(self.widgets.get_icon_qt("general", "refresh"))
            self.btn_reload.setIcon(self.widgets.get_icon_qt("general", "reset"))
            self.btn_stop.setIcon(self.widgets.get_icon_qt("general", "cancel"))

        # Connect signals when interacting with UI controls
        self.close.clicked.connect(self._close)
        self.tree.itemActivated.connect(self._change_item)
        self.tree.itemClicked.connect(self._change_item)
        self.btn_refresh.clicked.connect(self._refresh_list)
        self.btn_reload.clicked.connect(self._reload_all)
        self.btn_stop.clicked.connect(self._stop_task)

        # Showtime!
        self._refresh_list()
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 300)
        self.tree.setColumnWidth(2, 50)
        self.dialog.exec()

    def _close(self):
        self.dialog_is_open = False
        self.dialog.deleteLater()

    def _change_item(self):
        self.btn_stop.setEnabled(True if self.tree.currentItem() else False)

    def _stop_task(self):
        """
        Gracefully interrupt the specified PID validating that it actually
        belongs to a Polychromatic process.
        """
        pid = int(self.tree.currentItem().text(2))
        component = self.tree.currentItem()._component

        self.dbg.stdout("Stopping process PID " + str(pid), self.dbg.action, 1)
        process = procpid.ProcessManager(component)
        process.stop()
        self._refresh_list()

    def _reload_all(self):
        """
        Stops all processes and initiates the autostart procedures.
        """
        set_cursor_busy = shared.TabData(self.appdata).set_cursor_busy
        set_cursor_normal = shared.TabData(self.appdata).set_cursor_normal


        class RebootThread(QThread):
            @staticmethod
            def run():
                self.dbg.stdout("Now reloading background processes...", self.dbg.warning, 1)
                self.btn_stop.setEnabled(False)
                self.btn_reload.setEnabled(False)
                self.btn_reload.setText(self._("Restarting..."))
                set_cursor_busy()

                self.tree.clear()
                item = QTreeWidgetItem()
                item.setText(0, self._("Please wait..."))
                item.setIcon(0, QIcon(common.get_icon("general", "exit")))
                item.setDisabled(True)
                self.tree.addTopLevelItem(item)

                # Gracefully stop using procpid module
                procmgr = procpid.ProcessManager("helper")
                components = procmgr._get_component_pid_list()
                for component in components:
                    process = procpid.ProcessManager(component)
                    self.dbg.stdout("Stopping process PID " + str(process._get_component_pid()), self.dbg.action, 1)
                    process.stop()

                # Before starting new processes, make sure old PIDs have ceased execution
                self.dbg.stdout("Checking all processes have interrupted...", self.dbg.action, 1)
                timeout = 3
                while len(procmgr._get_component_pid_list()) > 0 and timeout > 0:
                    time.sleep(1)
                    timeout = timeout - 1
                    self.dbg.stdout("Still waiting ({0}s timeout)".format(str(timeout)), self.dbg.debug, 1)

                # Reload all by using helper's --autostart
                self.dbg.stdout("Executing autostart...", self.dbg.action, 1)
                procmgr.start_component(["--autostart"])

                # Finished
                set_cursor_normal()
                if self.dialog_is_open:
                    self.btn_reload.setEnabled(True)
                    self.btn_reload.setText(self._("Restart All"))
                    time.sleep(1)
                    self._refresh_list()

                    # Auto refresh view again if tray applet is delayed
                    tray_delay = self.appdata.preferences["tray"]["autostart_delay"]
                    time.sleep(2 if tray_delay < 2 else tray_delay + 2)
                    self._refresh_list()

        self.thread = RebootThread()
        self.thread.start()

    def _refresh_list(self):
        procmgr = procpid.ProcessManager()
        components = procmgr._get_component_pid_list()
        device_list = self.middleman.get_devices()

        tree = self.dialog.findChild(QTreeWidget, "TasksTree")
        tree.clear()
        self.btn_stop.setEnabled(False)

        for component in components:
            procmgr = procpid.ProcessManager(component)
            pid = str(procmgr._get_component_pid())
            running = procmgr.is_another_instance_is_running()

            task = self._("Playing software effect").replace("[]", component)
            task_icon = common.get_icon("effects", "play")
            if component == "tray-applet":
                task = self._("Tray Applet")
                task_icon = common.get_icon("general", "tray-applet")
            elif not running:
                task = self._("No longer running")
                task_icon = common.get_icon("general", "cancel")

            # TODO: Refactor later
            running_device = None
            for device in device_list:
                if device.serial == component:
                    running_device = device

            item = QTreeWidgetItem()
            item.setText(0, task)
            item.setIcon(0, QIcon(task_icon))
            if running_device:
                item.setText(1, running_device.name)
                item.setIcon(1, QIcon(running_device.form_factor["icon"]))
            item.setText(2, pid)
            item._component = component

            if not running:
                item.setText(2, "-")
                item.setDisabled(True)

            tree.addTopLevelItem(item)
