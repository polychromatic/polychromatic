# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
"""
This module contains the frontend for the troubleshooter.
"""

import os
import time
import subprocess
import webbrowser

from .. import common
from .. import preferences
from .. import procpid
from . import shared
from . import procviewer

from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QIcon, QBrush
from PyQt5.QtWidgets import QWidget, QLabel, QDialog, QPushButton, \
                            QTreeWidget, QTreeWidgetItem, QProgressBar, \
                            QApplication


class TroubleshooterGUI(QObject):
    """
    Runs the troubleshooter and shows the results in a dialog box.
    """
    signal_progress_bar_advance = pyqtSignal()
    signal_progress_bar_set_max = pyqtSignal(int)

    def __init__(self, appdata, backend, backend_human_name):
        # Required for slot/signals to work
        super().__init__()

        self.appdata = appdata
        self.backend = backend
        self.human_name = backend_human_name
        self._ = appdata._
        self.dbg = self.appdata.dbg
        self.widgets = shared.PolychromaticWidgets(appdata)

        self.result_window = shared.get_ui_widget(self.appdata, "troubleshooter", QDialog)
        self.result_label = self.result_window.findChild(QLabel, "Title")
        self.result_tree = self.result_window.findChild(QTreeWidget, "Results")
        self.result_tree_root = self.result_tree.invisibleRootItem()
        self.result_copy_btn = self.result_window.findChild(QPushButton, "CopyToClipboard")

        if not self.appdata.system_qt_theme:
            self.result_window.findChild(QPushButton, "Close").setIcon(self.widgets.get_icon_qt("general", "close"))

        self.loading = shared.get_ui_widget(self.appdata, "loading", QDialog)
        self.loading_label = self.loading.findChild(QLabel, "Label")
        self.loading_progress_bar = self.loading.findChild(QProgressBar, "ProgressBar")

        self.signal_progress_bar_advance.connect(self.progress_bar_advance)
        self.signal_progress_bar_set_max.connect(self.progress_bar_set_max)

        self.thread = self.TroubleshootThread()
        self.thread.parent = self
        self.thread.result = []
        self.thread.finished.connect(self.finished)

        self.start()

    def progress_bar_advance(self):
        self.loading_progress_bar.setValue(self.loading_progress_bar.value() + 1)

    def progress_bar_set_max(self, max_value):
        self.loading_progress_bar.setRange(0, 0)
        self.loading_progress_bar.setMaximum(max_value)

    class TroubleshootThread(QThread):
        """
        Troubleshooting runs in a separate thread to prevent UI lock up, in case
        the code takes longer to run on some systems.
        """
        def run(self):
            _ = self.parent._

            while not self.parent.appdata.ready:
                self.parent.loading_label.setText(_("Waiting for backends to be ready..."))
                time.sleep(0.1)

            self.parent.loading_label.setText(_("Running troubleshooter..."))
            self.result = self.parent.appdata.middleman.troubleshoot(self.parent.backend, _, self.parent.signal_progress_bar_set_max.emit, self.parent.signal_progress_bar_advance.emit)

    def start(self):
        self.dbg.stdout("Running troubleshooter backend: {0}".format(self.backend), self.dbg.action, 1)
        self.loading_label.setText(self._("Running troubleshooter..."))
        self.loading.setWindowTitle(self._("Troubleshooting..."))
        self.loading.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.loading.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        self.loading.open()

        self.thread.start()

    def finished(self):
        results = self.thread.result
        all_passed = True
        self.loading.close()

        if type(results) == None:
            return self.widgets.open_dialog(self.widgets.dialog_warning,
                                            self._("Troubleshooting Failed"),
                                            self._("The troubleshooter for this backend is not available for this operating system."))

        elif type(results) == str:
            return self.widgets.open_dialog(self.widgets.dialog_error,
                                            self._("Troubleshooting Failed"),
                                            self._("An exception was thrown while running the troubleshooter. This is probably a bug."),
                                            details=results)

        for result in results:
            item = QTreeWidgetItem()

            # "passed" must be either: True (Passed); False (Failed); None (Unknown)
            if result["passed"] is True:
                item.setText(0, self._("Passed"))
                item.setIcon(0, QIcon(common.get_icon("general", "success")))
            elif result["passed"] is False:
                item.setText(0, self._("Failed"))
                item.setIcon(0, QIcon(common.get_icon("general", "serious")))
            else:
                item.setText(0, self._("Unknown"))
                item.setIcon(0, QIcon(common.get_icon("general", "unknown")))

            item.setText(1, result["test_name"])
            item.copyable = False

            # Provide suggestions on failures
            if not result["passed"]:
                all_passed = False

                suggestions = result["suggestions"]
                for line in suggestions:
                    subitem = QTreeWidgetItem()
                    if line.startswith("$"):
                        text = line
                        subitem.setBackground(1, QBrush(Qt.black))
                        subitem.setForeground(1, QBrush(Qt.green))
                        subitem.copyable = True
                    else:
                        text = "• " + line
                        subitem.setDisabled(True)
                    subitem.setText(1, text)
                    subitem.setToolTip(1, line)
                    item.addChild(subitem)
            self.result_tree_root.addChild(item)

        self.result_tree.expandAll()
        self.result_window.findChild(QPushButton, "Close").clicked.connect(self._close_troubleshooter)
        self.result_tree.itemSelectionChanged.connect(self._item_changed)
        self.result_copy_btn.setHidden(True)
        self.result_copy_btn.clicked.connect(self._copy_to_clipboard)
        self.result_window.setWindowTitle(self._("Troubleshooter for []").replace("[]", self.human_name))
        if all_passed:
            self.result_label.setText(self._("Everything appears to be in working order!"))
        self.dbg.stdout("Troubleshooting completed!", self.dbg.success, 1)
        self.result_window.open()

    def _item_changed(self):
        """
        User clicks on one of the results. Shows/hides the "Copy" button.
        """
        selected = self.result_tree.selectedItems()[0]
        self.result_copy_btn.setHidden(selected.copyable == False)

    def _copy_to_clipboard(self):
        """
        Commands can be copied to clipboard for convenience
        """
        selected_text = self.result_tree.selectedItems()[0].text(1).replace("$ ", "")
        QApplication.clipboard().setText(selected_text)

    def _close_troubleshooter(self):
        """
        """
        self.result_window.close()
        self.result_window.deleteLater()
        self.loading.deleteLater()
