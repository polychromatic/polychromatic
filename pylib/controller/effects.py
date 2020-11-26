#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module controls the 'Effects' tab of the Controller GUI.
"""

from .. import common
from .. import effects
from .. import locales
from .. import preferences as pref
from . import shared

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QPushButton, QToolButton, QMessageBox, \
                            QListWidget, QTreeWidget, QLabel, QComboBox, \
                            QTreeWidgetItem


class EffectsTab(shared.CommonFileTab):
    """
    Allows the user to manage software effects for lighting up their devices.
    """
    def __init__(self, appdata):
        super().__init__(appdata, effects.EffectFileManagement, "EffectContents", "EffectSidebarTree")

        # Set up variables
        self.feature = "effects"

        # Populate tasks
        self.tasks = {
            "new": self.new_file,
            "import": self.import_effect
        }

        self._add_tree_item(self.TasksBranch, self._("New Effect"), common.get_icon("general", "new"), "tasks", "new")
        self._add_tree_item(self.TasksBranch, self._("Import Effect"), common.get_icon("general", "import"), "tasks", "import")

    def show_no_file_screen(self, message_id):
        """
        Effect cannot be opened for viewing - inform the user.

        Params:
            message_id  (int)   One of the CommonFileTab.INFO_* variables
        """
        layout = self.Contents.layout()

        titles = {
            0: self._("It's empty here!"),
            1: self._("This one doesn't work!")
        }

        subtitles = {
            0: self._("Try creating your own effect or import an image or video."),
            1: self._("This effect couldn't be loaded due to an error. The file might be corrupt.")
        }

        icons = {
            0: None,
            1: None
        }

        buttons = {
            0: [
                {
                    "label": self._("New Effect"),
                    "icon_folder": "general",
                    "icon_name": "new",
                    "action": self.new_file
                },
                {
                    "label": self._("Import Effect"),
                    "icon_folder": "general",
                    "icon_name": "import",
                    "action": self.import_effect
                }
            ],
            1: []
        }

        shared.clear_layout(layout)
        self.widgets.populate_empty_state(layout, icons[message_id], titles[message_id], subtitles[message_id], buttons[message_id])

    def new_file(self):
        """
        Opens the metadata window for the user to enter some initial details about
        the effeect. On successful initialization, the effect editor will open.
        """
        print("stub:effects.new_file")
        pass

    def open_file(self, effect_path):
        """
        Opens the specified file in the interface, providing an overview of the
        effect and buttons to modify the file.
        """
        self.current_file_path = effect_path
        self.current_file_data = self.filemgr.get_item(effect_path)
        data = self.current_file_data

        if type(data) == int:
            self.show_error_message(effect_path, data)
            self.show_no_file_screen(1)
            return

        layout = self.Contents.layout()
        shared.clear_layout(layout)

        # Summary
        icon_path = data["parsed"]["icon"]
        buttons = [
            {
                "id": "play",
                "icon": self.widgets.get_icon_qt("effects", "play"),
                "label": self._("Play"),
                "disabled": False,
                "action": self.play_effect
            },
            {
                "id": "edit",
                "icon": self.widgets.get_icon_qt("general", "edit"),
                "label": self._("Edit"),
                "disabled": False,
                "action": self.edit_file
            },
            {
                "id": "clone",
                "icon": self.widgets.get_icon_qt("general", "clone"),
                "label": self._("Clone"),
                "disabled": False,
                "action": self.clone_file
            },
            {
                "id": "delete",
                "icon": self.widgets.get_icon_qt("general", "delete"),
                "label": self._("Delete"),
                "disabled": False,
                "action": self.delete_file
            }
        ]
        summary = self.widgets.create_summary_widget(icon_path, data["parsed"]["name"], [], buttons)
        summary.setMaximumHeight(170)
        layout.addWidget(summary)
        layout.addStretch()

    def edit_file(self):
        """
        Open the editor for the currently selected effect.
        """
        print("stub:edit_effect")
        pass

    def import_effect(self):
        """
        Allows the user to create effects from other media, such as videos or images.
        """
        print("stub:effects.import_effect")
        pass

    def play_effect(self):
        """
        Play the currently selected effect.
        """
        print("stub:play_effect")
        pass

