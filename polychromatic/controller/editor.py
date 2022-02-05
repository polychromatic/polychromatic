# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
"""
This module controls the visual editor shared between layered and scripted effects.
"""

from .. import common
from .. import effects
from ..fx import FX
from .. import locales
from .. import preferences as pref
from .. import procpid
from . import shared
from . import effects as controller_effects

from ..qt.flowlayout import FlowLayout as QFlowLayout

import copy
import json
import os
import time

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QRect, QItemSelectionModel, QThread, QSize, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor
from PyQt5.QtWidgets import QWidget, QPushButton, QToolButton, QMessageBox, \
                            QListWidget, QTreeWidget, QLabel, QComboBox, \
                            QTreeWidgetItem, QMenu, QDialog, QDialogButtonBox, \
                            QButtonGroup, QLineEdit, QTextEdit, QCheckBox, \
                            QGroupBox, QRadioButton, QMainWindow, QAction, \
                            QDockWidget, QMenuBar, QToolBar, QStatusBar, \
                            QTableWidget, QWidget, QVBoxLayout, QHBoxLayout, \
                            QScrollArea, QSpinBox, QDesktopWidget, QColorDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Visual mode within the WebView editor
VISUAL_MODE_ADD = 1
VISUAL_MODE_DEL = 2
VISUAL_MODE_PICK = 3


class VisualEffectEditor(shared.TabData):
    """
    Editor for modifying layered or animated effects. The GUI is shared between
    a "Layered" and "Sequence" type of effect.
    """
    def __init__(self, appdata, fileman, save_path):
        """
        Load the effect from file for editing and show the editor window. The
        file is expected to have been initialised (via EffectMetadataEditor) first.

        Params:
            appdata         ApplicationData() object
            fileman         fileman.FlatFileManagement() based object
            effect_path     Path to save data
        """
        super().__init__(appdata)

        self.fileman = fileman
        self.save_path = save_path
        self.data = fileman.get_item(save_path)
        self.modified = False
        self.alive = True
        self.current_colour = "#00FF00"
        self.current_tool = VISUAL_MODE_ADD
        self.layer_labels = self._get_layer_labels()
        self.webview_zoom_level = 1.0
        self.fx = FX()

        # Effect type
        self.effect_type = self.data["type"]
        self.layered_effect = self.effect_type == effects.TYPE_LAYERED
        self.sequence_effect = self.effect_type == effects.TYPE_SEQUENCE

        # Fail if the file moved, or was deleted
        if type(self.data) != dict:
            self._show_file_error()
            return

        # Session variables
        self.suppress_delete_prompt = appdata.preferences["editor"]["suppress_confirm_dialog"]

        # Layered Effects Only
        self.current_layer = 0

        # Sequence Effects Only
        self.current_frame = 0
        self.playback_paused = True
        self.playback_thread = None

        # Load window
        self.window = shared.get_ui_widget(appdata, "editor", QMainWindow)
        self.window.closeEvent = self.closeEvent
        self.menubar = self.window.findChild(QMenuBar, "MenuBar")
        self.statusbar = self.window.findChild(QStatusBar, "StatusBar")
        self.toolbar = self.window.findChild(QToolBar, "MainToolbar")

        # Visual Editor ("webview")
        self.webview = self.window.findChild(QWebEngineView, "MatrixWebView")
        self.action_info_graphic = self.window.findChild(QAction, "MapGraphic")
        self.action_info_grid_x = self.window.findChild(QAction, "MapDimensionX")
        self.action_info_grid_y = self.window.findChild(QAction, "MapDimensionY")

        # -- DeviceRender() is assigned to this variable in init_controls()
        self.device_renderer = None

        # Device (live preview)
        self.live_preview = self.preferences["editor"]["live_preview"]
        self.device = None
        self.matrix = None
        self.init_device_preview()

        # Set up webview paths
        self.webview.page().profile().setCachePath(pref.path.webview_cache)
        self.webview.page().profile().setPersistentStoragePath(pref.path.webview_cache)

        # Assign widgets to variables
        # -- Menu Bar/Toolbar - File
        self.action_save_apply = self.window.findChild(QAction, "actionSaveApply")
        self.action_save = self.window.findChild(QAction, "actionSave")
        self.action_revert = self.window.findChild(QAction, "actionRevert")
        self.action_exit = self.window.findChild(QAction, "actionExit")

        # -- Menu Bar/Toolbar - Edit
        self.menu_edit = self.window.findChild(QMenu, "menuEdit")

        # -- -- Layer only
        self.action_new_layer = self.window.findChild(QAction, "actionNew_Layer")
        self.action_delete_layer = self.window.findChild(QAction, "actionDelete_Layer")
        self.action_duplicate_layer = self.window.findChild(QAction, "actionDuplicate_Layer")
        self.action_layer_up = self.window.findChild(QAction, "actionMove_Layer_Up")
        self.action_layer_down = self.window.findChild(QAction, "actionMove_Layer_Down")

        # -- -- Frame only
        self.action_new_frame = self.window.findChild(QAction, "actionNew_Frame")
        self.action_delete_frame = self.window.findChild(QAction, "actionDelete_Frame")
        self.action_clone_frame = self.window.findChild(QAction, "actionClone_Frame")
        self.action_frame_left = self.window.findChild(QAction, "actionMove_Frame_Left")
        self.action_frame_right = self.window.findChild(QAction, "actionMove_Frame_Right")

        self.menu_shift = self.window.findChild(QMenu, "menuShiftMenu")
        self.action_shift_left = self.window.findChild(QAction, "actionShift_Left")
        self.action_shift_right = self.window.findChild(QAction, "actionShift_Right")
        self.action_shift_up = self.window.findChild(QAction, "actionShift_Up")
        self.action_shift_down = self.window.findChild(QAction, "actionShift_Down")
        self.action_edit_metadata = self.window.findChild(QAction, "actionEditMetadata")
        self.action_edit_triggers = self.window.findChild(QAction, "actionEditTriggers")

        # -- Menu Bar/Toolbar - View
        self.action_view_device_graphic = self.window.findChild(QAction, "actionShow_as_Device_Graphic")
        self.action_view_grid = self.window.findChild(QAction, "actionShow_as_Grid")
        self.action_view_key_labels = self.window.findChild(QAction, "actionShowKeyLabels")
        self.action_zoom_in = self.window.findChild(QAction, "actionZoomIn")
        self.action_zoom_out = self.window.findChild(QAction, "actionZoomOut")
        self.action_zoom_reset = self.window.findChild(QAction, "actionZoomReset")

        # -- Menu Bar/Toolbar - Tools
        self.menu_tools = self.window.findChild(QMenu, "menuTools")
        self.tool_draw = self.window.findChild(QAction, "actionDraw")
        self.tool_eraser = self.window.findChild(QAction, "actionEraser")
        self.tool_picker = self.window.findChild(QAction, "actionColourPicker")

        # -- Menu Bar/Dock - Colours
        self.menu_colours = self.window.findChild(QMenu, "menuColours")

        # -- Menu Bar/Dock - Playback
        self.playback_menu = self.window.findChild(QMenu, "menuPlayback")
        self.playback_jump_start = self.window.findChild(QAction, "actionJumpStart")
        self.playback_jump_end = self.window.findChild(QAction, "actionJumpEnd")
        self.playback_prev = self.window.findChild(QAction, "actionPreviousFrame")
        self.playback_next = self.window.findChild(QAction, "actionNextFrame")
        self.playback_play = self.window.findChild(QAction, "actionPlay")
        self.playback_stop = self.window.findChild(QAction, "actionStop")
        self.playback_loop = self.window.findChild(QAction, "actionLoop")

        # -- Menu Bar - Help
        self.action_help_online = self.window.findChild(QAction, "actionOnlineHelp")
        self.action_help_website = self.window.findChild(QAction, "actionWebsite")
        self.action_help_relnotes = self.window.findChild(QAction, "actionReleaseNotes")
        self.action_help_report_bug = self.window.findChild(QAction, "actionReportBug")
        self.action_help_donate = self.window.findChild(QAction, "actionDonate")
        self.action_help_about = self.window.findChild(QAction, "actionAbout")

        # -- Docks
        self.dock_layers = self.window.findChild(QDockWidget, "LayersDock")
        self.dock_properties = self.window.findChild(QDockWidget, "LayerPropertiesDock")
        self.dock_colours = self.window.findChild(QDockWidget, "ColoursDock")
        self.dock_frames = self.window.findChild(QDockWidget, "FramesDock")

        # -- Layer Dock
        self.layer_tree = self.window.findChild(QTreeWidget, "LayerTree")
        self.btn_layer_delete = self.window.findChild(QPushButton, "LayerDelete")
        self.btn_layer_duplicate = self.window.findChild(QPushButton, "LayerDuplicate")
        self.btn_layer_move_down = self.window.findChild(QPushButton, "LayerMoveDown")
        self.btn_layer_move_up = self.window.findChild(QPushButton, "LayerMoveUp")
        self.btn_layer_new = self.window.findChild(QPushButton, "LayerNew")

        # -- Frame Dock
        self.frame_table = self.window.findChild(QTableWidget, "FramesTable")

        self.btn_frame_new = self.window.findChild(QPushButton, "NewFrame")
        self.btn_frame_delete = self.window.findChild(QPushButton, "DeleteFrame")
        self.btn_frame_clone = self.window.findChild(QPushButton, "CloneFrame")
        self.btn_frame_move_left = self.window.findChild(QPushButton, "MoveFrameLeft")
        self.btn_frame_move_right = self.window.findChild(QPushButton, "MoveFrameRight")

        self.btn_playback_jump_start = self.window.findChild(QToolButton, "PlaybackJumpStart")
        self.btn_playback_jump_end = self.window.findChild(QToolButton, "PlaybackJumpEnd")
        self.btn_playback_play = self.window.findChild(QToolButton, "PlaybackStart")
        self.btn_playback_stop = self.window.findChild(QToolButton, "PlaybackStop")
        self.btn_playback_prev = self.window.findChild(QToolButton, "PlaybackPrev")
        self.btn_playback_next = self.window.findChild(QToolButton, "PlaybackNext")
        self.btn_playback_loop = self.window.findChild(QCheckBox, "PlaybackLoop")
        self.spinner_playback_fps = self.window.findChild(QSpinBox, "PlaybackFPS")
        self.status_frame = QLabel()

        # -- Colours Menu Bar / Dock
        self.saved_colours = self.window.findChild(QWidget, "SavedColoursWidget")

        self.current_colour_block = self.window.findChild(QWidget, "CurrentColourBlock")
        self.current_colour_textbox = self.window.findChild(QLineEdit, "CurrentColourTextBox")
        self.btn_change_colour = self.window.findChild(QPushButton, "ChangeCurrentColour")

        self.label_hue = self.window.findChild(QLabel, "HueLabel")
        self.label_saturation = self.window.findChild(QLabel, "SaturationLabel")
        self.label_lightness = self.window.findChild(QLabel, "LightnessLabel")
        self.btn_hue_increase = self.window.findChild(QPushButton, "HueIncrease")
        self.btn_hue_decrease = self.window.findChild(QPushButton, "HueDecrease")
        self.btn_saturation_increase = self.window.findChild(QPushButton, "SaturationIncrease")
        self.btn_saturation_decrease = self.window.findChild(QPushButton, "SaturationDecrease")
        self.btn_lightness_increase = self.window.findChild(QPushButton, "LightnessIncrease")
        self.btn_lightness_decrease = self.window.findChild(QPushButton, "LightnessDecrease")

        self.action_colours_picker = self.window.findChild(QAction, "actionOpenColourPicker")
        self.action_colours_hue_increase = self.window.findChild(QAction, "actionIncreaseHue")
        self.action_colours_hue_decrease = self.window.findChild(QAction, "actionDecreaseHue")
        self.action_colours_saturation_increase = self.window.findChild(QAction, "actionIncreaseSaturation")
        self.action_colours_saturation_decrease = self.window.findChild(QAction, "actionDecreaseSaturation")
        self.action_colours_lightness_increase = self.window.findChild(QAction, "actionIncreaseLightness")
        self.action_colours_lightness_decrease = self.window.findChild(QAction, "actionDecreaseLightness")
        self.action_colours_manage = self.window.findChild(QAction, "actionManageSavedColours")

        # Font should be applied to dock widgets
        self.docks = [self.dock_layers, self.dock_properties, self.dock_colours, self.dock_frames]
        if not self.appdata.system_qt_theme:
            for dock in self.docks:
                font = QFont("Play", 10, 0)
                dock.setFont(font)

        # Connect buttons/actions
        # -- File
        self.action_save_apply.triggered.connect(self.save_and_close)
        self.action_save.triggered.connect(self.save_now)
        self.action_revert.triggered.connect(self.reload_from_file)
        self.action_exit.triggered.connect(self.closeEvent)

        # -- Edit (Layered)
        self.action_new_layer.triggered.connect(self.new_layer)
        self.action_delete_layer.triggered.connect(self.delete_layer)
        self.action_duplicate_layer.triggered.connect(self.duplicate_layer)
        self.action_layer_up.triggered.connect(self.raise_layer)
        self.action_layer_down.triggered.connect(self.lower_layer)

        self.btn_layer_new.clicked.connect(self.new_layer)
        self.btn_layer_delete.clicked.connect(self.delete_layer)
        self.btn_layer_duplicate.clicked.connect(self.duplicate_layer)
        self.btn_layer_move_up.clicked.connect(self.raise_layer)
        self.btn_layer_move_down.clicked.connect(self.lower_layer)

        # -- Edit (Sequence)
        self.action_new_frame.triggered.connect(self.new_frame)
        self.action_delete_frame.triggered.connect(self.delete_frame)
        self.action_clone_frame.triggered.connect(self.clone_frame)
        self.action_frame_left.triggered.connect(self.shift_frame_left)
        self.action_frame_right.triggered.connect(self.shift_frame_right)

        # -- Edit (Shared)
        self.action_shift_left.triggered.connect(self.shift_all_left)
        self.action_shift_right.triggered.connect(self.shift_all_right)
        self.action_shift_up.triggered.connect(self.shift_all_up)
        self.action_shift_down.triggered.connect(self.shift_all_down)
        self.action_edit_metadata.triggered.connect(self.edit_metadata)
        self.action_edit_triggers.triggered.connect(self.edit_triggers)

        # -- View
        self.action_view_device_graphic.triggered.connect(self.view_device_graphic)
        self.action_view_grid.triggered.connect(self.view_device_grid)
        self.action_view_key_labels.triggered.connect(self.view_key_labels)
        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.action_zoom_reset.triggered.connect(self.zoom_reset)

        # -- Tools
        self.tool_draw.triggered.connect(self.select_mode_draw)
        self.tool_eraser.triggered.connect(self.select_mode_eraser)
        self.tool_picker.triggered.connect(self.select_mode_picker)

        # -- Colours
        self.action_colours_picker.triggered.connect(self.open_colour_picker)
        self.action_colours_hue_increase.triggered.connect(self.set_colour_increase_hue)
        self.action_colours_hue_decrease.triggered.connect(self.set_colour_decrease_hue)
        self.action_colours_saturation_increase.triggered.connect(self.set_colour_increase_saturation)
        self.action_colours_saturation_decrease.triggered.connect(self.set_colour_decrease_saturation)
        self.action_colours_lightness_increase.triggered.connect(self.set_colour_increase_lightness)
        self.action_colours_lightness_decrease.triggered.connect(self.set_colour_decrease_lightness)
        self.action_colours_manage.triggered.connect(self.edit_saved_colours)

        # -- Playback (Sequence only)
        if self.sequence_effect:
            self._init_playback_controls()

        # -- Help
        menubar = self.appdata.menubar
        self.action_help_online.triggered.connect(menubar.online_help)
        self.action_help_website.triggered.connect(menubar.polychromatic_website)
        self.action_help_relnotes.triggered.connect(menubar.polychromatic_release_notes)
        self.action_help_report_bug.triggered.connect(menubar.polychromatic_report_bug)
        self.action_help_donate.triggered.connect(menubar.polychromatic_donate)
        self.action_help_about.triggered.connect(menubar.about_polychromatic)

        # -- Dock: Frames
        self.frame_table.itemSelectionChanged.connect(self.open_frame)
        self.btn_frame_new.clicked.connect(self.new_frame)
        self.btn_frame_delete.clicked.connect(self.delete_frame)
        self.btn_frame_clone.clicked.connect(self.clone_frame)
        self.btn_frame_move_left.clicked.connect(self.shift_frame_left)
        self.btn_frame_move_right.clicked.connect(self.shift_frame_right)

        # -- Dock: Colours (click)
        self.btn_change_colour.clicked.connect(self.open_colour_picker)
        self.current_colour_textbox.textChanged.connect(self.set_colour_by_textbox)
        self.btn_hue_increase.clicked.connect(self.set_colour_increase_hue)
        self.btn_saturation_increase.clicked.connect(self.set_colour_increase_saturation)
        self.btn_lightness_increase.clicked.connect(self.set_colour_increase_lightness)
        self.btn_hue_decrease.clicked.connect(self.set_colour_decrease_hue)
        self.btn_saturation_decrease.clicked.connect(self.set_colour_decrease_saturation)
        self.btn_lightness_decrease.clicked.connect(self.set_colour_decrease_lightness)

        # -- Dock: Colours (scroll)
        for widget in [self.label_hue, self.btn_hue_increase, self.btn_hue_decrease]:
            def _hue_onscroll(evt):
                if evt.angleDelta().y() > 0:
                    self.set_colour_increase_hue()
                else:
                    self.set_colour_decrease_hue()
            widget.wheelEvent = _hue_onscroll

        for widget in [self.label_saturation, self.btn_saturation_increase, self.btn_saturation_decrease]:
            def _saturation_onscroll(evt):
                if evt.angleDelta().y() > 0:
                    self.set_colour_increase_saturation()
                else:
                    self.set_colour_decrease_saturation()
            widget.wheelEvent = _saturation_onscroll

        for widget in [self.label_lightness, self.btn_lightness_decrease, self.btn_lightness_increase]:
            def _lightness_onscroll(evt):
                if evt.angleDelta().y() > 0:
                    self.set_colour_increase_lightness()
                else:
                    self.set_colour_decrease_lightness()
            widget.wheelEvent = _lightness_onscroll

        # Override Behaviours
        # -- Scroll on frames (sequence only)
        def frame_table_wheelEvent(event):
            direction = 1 if int(event.angleDelta().y()) > 0 else -1
            self.frame_table.selectColumn(self.frame_table.currentColumn() + direction)
        self.frame_table.wheelEvent = frame_table_wheelEvent

        # Menu Bar Icons
        if not appdata.system_qt_theme:
            # -- File
            self.action_save_apply.setIcon(self.widgets.get_icon_qt("general", "ok"))
            self.action_save.setIcon(self.widgets.get_icon_qt("general", "save"))
            self.action_revert.setIcon(self.widgets.get_icon_qt("general", "reset"))
            self.action_exit.setIcon(self.widgets.get_icon_qt("general", "exit"))

            # -- Edit
            self.action_new_layer.setIcon(self.widgets.get_icon_qt("general", "new"))
            self.action_delete_layer.setIcon(self.widgets.get_icon_qt("general", "delete"))
            self.action_duplicate_layer.setIcon(self.widgets.get_icon_qt("general", "clone"))
            self.action_layer_up.setIcon(self.widgets.get_icon_qt("general", "move-up"))
            self.action_layer_down.setIcon(self.widgets.get_icon_qt("general", "move-down"))

            self.action_new_frame.setIcon(self.widgets.get_icon_qt("general", "new"))
            self.action_delete_frame.setIcon(self.widgets.get_icon_qt("general", "delete"))
            self.action_clone_frame.setIcon(self.widgets.get_icon_qt("general", "clone"))
            self.action_frame_left.setIcon(self.widgets.get_icon_qt("general", "move-left"))
            self.action_frame_right.setIcon(self.widgets.get_icon_qt("general", "move-right"))

            self.menu_shift.setIcon(self.widgets.get_icon_qt("general", "move-up"))
            self.action_shift_left.setIcon(self.widgets.get_icon_qt("general", "move-left"))
            self.action_shift_right.setIcon(self.widgets.get_icon_qt("general", "move-right"))
            self.action_shift_up.setIcon(self.widgets.get_icon_qt("general", "move-up"))
            self.action_shift_down.setIcon(self.widgets.get_icon_qt("general", "move-down"))
            self.action_edit_metadata.setIcon(self.widgets.get_icon_qt("general", "properties"))
            self.action_edit_triggers.setIcon(self.widgets.get_icon_qt("general", "triggers"))

            # -- View
            self.action_view_device_graphic.setIcon(self.widgets.get_icon_qt("general", "devices"))
            self.action_view_grid.setIcon(self.widgets.get_icon_qt("general", "matrix"))
            self.action_view_key_labels.setIcon(self.widgets.get_icon_qt("devices", "keyboard"))
            self.action_zoom_in.setIcon(self.widgets.get_icon_qt("effects", "zoom-in"))
            self.action_zoom_out.setIcon(self.widgets.get_icon_qt("effects", "zoom-out"))
            self.action_zoom_reset.setIcon(self.widgets.get_icon_qt("effects", "zoom-reset"))

            # -- Tools
            self.tool_draw.setIcon(self.widgets.get_icon_qt("effects", "paint"))
            self.tool_eraser.setIcon(self.widgets.get_icon_qt("effects", "eraser"))
            self.tool_picker.setIcon(self.widgets.get_icon_qt("effects", "picker"))

            # -- Colours
            self.action_colours_picker.setIcon(self.widgets.get_icon_qt("general", "palette"))
            self.action_colours_hue_increase.setIcon(self.widgets.get_icon_qt("effects", "more"))
            self.action_colours_saturation_increase.setIcon(self.widgets.get_icon_qt("effects", "more"))
            self.action_colours_lightness_increase.setIcon(self.widgets.get_icon_qt("effects", "more"))
            self.action_colours_hue_decrease.setIcon(self.widgets.get_icon_qt("effects", "minus"))
            self.action_colours_saturation_decrease.setIcon(self.widgets.get_icon_qt("effects", "minus"))
            self.action_colours_lightness_decrease.setIcon(self.widgets.get_icon_qt("effects", "minus"))
            self.action_colours_manage.setIcon(self.widgets.get_icon_qt("general", "edit"))

            # -- Playback
            self.playback_jump_start.setIcon(self.widgets.get_icon_qt("effects", "rewind"))
            self.playback_jump_end.setIcon(self.widgets.get_icon_qt("effects", "fast-forward"))
            self.playback_prev.setIcon(self.widgets.get_icon_qt("effects", "step-backward"))
            self.playback_next.setIcon(self.widgets.get_icon_qt("effects", "step-forward"))
            self.playback_play.setIcon(self.widgets.get_icon_qt("effects", "play"))
            self.playback_stop.setIcon(self.widgets.get_icon_qt("effects", "stop"))
            self.playback_loop.setIcon(self.widgets.get_icon_qt("effects", "repeat"))

            # -- Help
            self.action_help_online.setIcon(self.widgets.get_icon_qt("general", "external"))

        # Dock Button Icons
        if not appdata.system_qt_theme:
            # -- Layer Dock
            self.btn_layer_delete.setIcon(self.widgets.get_icon_qt("general", "delete"))
            self.btn_layer_duplicate.setIcon(self.widgets.get_icon_qt("general", "clone"))
            self.btn_layer_move_down.setIcon(self.widgets.get_icon_qt("general", "move-down"))
            self.btn_layer_move_up.setIcon(self.widgets.get_icon_qt("general", "move-up"))
            self.btn_layer_new.setIcon(self.widgets.get_icon_qt("general", "new"))

            # -- Frame Dock
            self.btn_frame_new.setIcon(self.widgets.get_icon_qt("general", "new"))
            self.btn_frame_delete.setIcon(self.widgets.get_icon_qt("general", "delete"))
            self.btn_frame_clone.setIcon(self.widgets.get_icon_qt("general", "clone"))
            self.btn_frame_move_left.setIcon(self.widgets.get_icon_qt("general", "move-left"))
            self.btn_frame_move_right.setIcon(self.widgets.get_icon_qt("general", "move-right"))

            self.btn_playback_jump_start.setIcon(self.widgets.get_icon_qt("effects", "rewind"))
            self.btn_playback_jump_end.setIcon(self.widgets.get_icon_qt("effects", "fast-forward"))
            self.btn_playback_play.setIcon(self.widgets.get_icon_qt("effects", "play"))
            self.btn_playback_stop.setIcon(self.widgets.get_icon_qt("effects", "stop"))
            self.btn_playback_prev.setIcon(self.widgets.get_icon_qt("effects", "step-backward"))
            self.btn_playback_next.setIcon(self.widgets.get_icon_qt("effects", "step-forward"))

            # -- Colour Dock
            self.btn_change_colour.setIcon(self.widgets.get_icon_qt("general", "palette"))
            self.btn_hue_increase.setIcon(self.widgets.get_icon_qt("effects", "more"))
            self.btn_saturation_increase.setIcon(self.widgets.get_icon_qt("effects", "more"))
            self.btn_lightness_increase.setIcon(self.widgets.get_icon_qt("effects", "more"))
            self.btn_hue_decrease.setIcon(self.widgets.get_icon_qt("effects", "minus"))
            self.btn_saturation_decrease.setIcon(self.widgets.get_icon_qt("effects", "minus"))
            self.btn_lightness_decrease.setIcon(self.widgets.get_icon_qt("effects", "minus"))

        # Showtime!
        self._init_window()
        self.init_controls()

        # FIXME: Hide incomplete features
        for widget in [self.window.findChild(QAction, "actionEditTriggers")]:
            widget.setDisabled(True)
            widget.setVisible(False)

    def _init_window(self):
        """
        Prepare the window for the type of effect that'll be edited.

        Layered Effects use these docks/interface elements:
            - Layers
            - Properties

        Sequence Effects use:
            - Colours
            - Frames
        """
        if self.layered_effect:
            # Remove frame-specific options
            self.tool_picker.deleteLater()
            self.action_new_frame.deleteLater()
            self.action_delete_frame.deleteLater()
            self.action_clone_frame.deleteLater()
            self.action_frame_left.deleteLater()
            self.action_frame_right.deleteLater()
            self.playback_menu.deleteLater()

        elif self.sequence_effect:
            # Remove layer-specific options
            self.action_new_layer.deleteLater()
            self.action_delete_layer.deleteLater()
            self.action_duplicate_layer.deleteLater()
            self.action_layer_up.deleteLater()
            self.action_layer_down.deleteLater()
            self.dock_layers.deleteLater()
            self.dock_properties.deleteLater()

        # Window properties & geometry
        self.appdata.main_window._set_initial_window_position(self.window, "editor")

        if self.window.windowIcon().isNull():
            self.window.setWindowIcon(QIcon(common.get_icon("general", "effects")))

        # -- If opening in the center, make better use of the screen space
        centered = self.preferences["controller"]["window_behaviour"] == pref.WINDOW_BEHAVIOUR_CENTER
        already_small = self.window.height() > 1024 and self.window.width() > 768
        if centered and not already_small:

            # DEPRECATED: QDesktopWidget(), but some distros ship an older Qt version (5.8, 5.12)
            qt_ver = QtCore.PYQT_VERSION_STR.split(".")
            if qt_ver[0] == "5" and int(qt_ver[1]) <= 14:
                screen = QDesktopWidget().availableGeometry()
            else:
                # For >= Qt 5.15
                screen = self.window.screen().availableGeometry()

            frame = self.window.frameGeometry()
            prefer_height = screen.height() - 175
            prefer_width = screen.width() - 275

            # Position in the center, as usual
            center = screen.center()
            frame.setHeight(prefer_height)
            frame.setWidth(prefer_width)
            frame.moveCenter(center)
            self.window.resize(prefer_width, prefer_height)
            self.window.move(frame.topLeft())

        # Toolbar style
        self.widgets.set_toolbar_style(self.toolbar)

        for button in [self.btn_frame_new, self.btn_frame_delete, self.btn_frame_clone,
                       self.btn_frame_move_left, self.btn_frame_move_right]:
            self.widgets.set_toolbar_style(button)

        # Adjust docks for optimum space
        if self.layered_effect:
            self.dock_layers.adjustSize()
            self.dock_properties.adjustSize()
        elif self.sequence_effect:
            self.dock_colours.adjustSize()
            self.dock_frames.adjustSize()

    def init_controls(self):
        """
        Populate the controls for the effect being loaded.
        """
        # Reset session variables
        self.set_modified(False)
        self.current_layer = 0
        self.current_frame = 0

        # Show Key Labels
        hide_key_labels = self.preferences["editor"]["hide_key_labels"]
        if not hide_key_labels:
            self.action_view_key_labels.setChecked(True)

        if not self.data["map_device_icon"] in ["keyboard", "keypad"]:
            self.action_view_key_labels.setEnabled(False)

        # Prepare visual editor
        rows = self.data["map_rows"]
        cols = self.data["map_cols"]
        graphic_filename = self.data["map_graphic"]
        self.device_renderer = DeviceRenderer(self.appdata, self, self.webview, self.init_editor, graphic_filename, rows, cols, hide_key_labels)
        self.select_mode_draw()
        graphic_name = self.device_renderer.graphic_name

        # Device Graphic / Grid
        self.action_view_device_graphic.setEnabled(True if self.data["map_graphic"] else False)
        self.action_info_graphic.setText(graphic_name)
        self.action_info_grid_x.setText(self._("Columns: []").replace("[]", str(rows)))
        self.action_info_grid_y.setText(self._("Rows: []").replace("[]", str(cols)))

        if not self.data["map_graphic"]:
            self.action_info_graphic.setText(self._("(Not Set)"))

    def init_editor(self):
        """
        Populate the visual editor (grid/graphic) when the webpage is ready.
        """
        self.dbg.stdout("Reading data...", self.dbg.action, 1)

        if self.layered_effect:
            # Populate layer dock
            self.load_layers()

            # Open the first layer and populate properties dock
            self.open_layer()

        elif self.sequence_effect:
            # Populate colours dock
            self.load_colours()

            # Populate frame dock
            self.load_frames()
            self.open_frame()

            # Show the current/total frame position in status bar
            self.statusbar.addPermanentWidget(self.status_frame)

        self.dbg.stdout("Load complete.", self.dbg.success, 1)
        self.window.show()

    def init_device_preview(self):
        """
        Initialise the objects for previewing the device on physical hardware.
        """
        if not self.live_preview:
            return

        # Prepare device object
        device_name = self.data["map_device"]
        self.dbg.stdout("Preparing live preview on '{0}'...".format(device_name), self.dbg.action, 1)
        self.device = self.middleman.get_device_by_name(device_name)

        # Inform the user if the backends are not ready
        if not self.appdata.ready:
            self.dbg.stdout("Backends not ready! Preview not possible yet.", self.dbg.error, 1)
            retry = False

            def do_retry():
                nonlocal retry
                retry = True

            def do_ignore():
                self.dbg.stdout("Loading editor without live preview.", self.dbg.action, 1)

            self.widgets.open_dialog(self.widgets.dialog_warning,
                                        self._("Backend Error"),
                                        self._("Live preview isn't possible yet as the backends haven't finished initialising."),
                                        self._("They might be ready now, try again. Or, choose Ignore to continue without a live preview on physical hardware."),
                                        buttons=[QMessageBox.Retry, QMessageBox.Ignore],
                                        actions={
                                            QMessageBox.Retry: do_retry,
                                            QMessageBox.Ignore: do_ignore
                                        })

            if retry:
                return self.init_device_preview()

        # Inform the user if attempting to load non-existent device
        if not self.device:
            self.dbg.stdout("Device not found! No preview.", self.dbg.error, 1)
            self.widgets.open_dialog(self.widgets.dialog_warning,
                                        self._("Missing Device"),
                                        self._("This effect is designed for a device named '[]', but it wasn't detected.").replace("[]", device_name),
                                        self._("Live preview has been disabled for this session."))
            return

        if self.device and self.device.matrix:
            self.matrix = self.device.matrix

        # Inform the user if attempting to use an unsupported device
        if self.device and not self.matrix:
            self.dbg.stdout("Device not supported! No preview.", self.dbg.error, 1)
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     self._("File Error"),
                                     self._("The device '[]' is assigned to this effect, but does not support individual addressable LEDs.").replace("[]", device_name),
                                     self._("Live preview has been disabled for this session."))
            self.device = None
            return

        # Stop any other effects running on the hardware
        serial = self.device.serial
        state = procpid.DeviceSoftwareState(serial)
        process = procpid.ProcessManager(serial)
        if state.get_effect() or process.is_another_instance_is_running():
            process.stop()

        self.dbg.stdout("Previewing effect '{0}' on device '{1}'.".format(self.data["name"], device_name), self.dbg.success, 1)

    def _init_playback_controls(self):
        """
        Connect the signals for playing back sequence effects within the editor.
        For sequence effects only.
        """
        self.playback_paused = True
        self.playback_stop.setVisible(False)
        self.btn_playback_stop.setVisible(False)

        class PlaybackThread(QThread):
            """
            Playing back sequence effects uses the existing editor signals and
            implementation to automatically go through each frame until the
            user wishes to stop.
            """
            @staticmethod
            def run():
                total_frames = self.frame_table.columnCount() - 1
                while not self.playback_paused and self.alive:
                    self.frame_table.selectColumn(self.frame_table.currentColumn() + 1)
                    self.open_frame(True)

                    if self.current_frame == total_frames:
                        if self.data["loop"] == True:
                            time.sleep(1 / self.data["fps"])
                            self.frame_table.selectColumn(0)
                            self.open_frame(True)
                        else:
                            return

                    time.sleep(1 / self.data["fps"])

        def _jump_start():
            self.frame_table.selectColumn(0)

        def _jump_end():
            self.frame_table.selectColumn(self.frame_table.columnCount() - 1)

        def _jump_prev():
            self.frame_table.selectColumn(self.frame_table.currentColumn() - 1)

        def _jump_next():
            self.frame_table.selectColumn(self.frame_table.currentColumn() + 1)

        def _play_pause_ui(paused):
            self.playback_paused = paused
            self.playback_stop.setVisible(not paused)
            self.btn_playback_stop.setVisible(not paused)
            self.playback_play.setVisible(paused)
            self.btn_playback_play.setVisible(paused)
            self._update_disabled_frame_controls()

        def _play():
            _jump_start()
            self.playback_thread.start()
            self.dbg.stdout("Playback started", self.dbg.action, 1)
            _play_pause_ui(False)

        def _stop():
            self.playback_thread.exit()

            if not self.alive:
                return

            self.dbg.stdout("Playback stopped", self.dbg.action, 1)
            _play_pause_ui(True)

        def _toggle_loop(checked):
            self.set_modified(True)
            self.dbg.stdout("Sequence set to {0}".format("loop" if checked else "play once"), self.dbg.debug, 1)
            self.data["loop"] = checked
            self.playback_loop.setChecked(checked)
            self.btn_playback_loop.setChecked(checked)

        def _set_fps(new_fps):
            self.set_modified(True)
            self.dbg.stdout("Sequence frame rate set to: {0} fps".format(new_fps), self.dbg.debug, 1)
            self.data["fps"] = new_fps

        self.playback_jump_start.triggered.connect(_jump_start)
        self.playback_jump_end.triggered.connect(_jump_end)
        self.playback_prev.triggered.connect(_jump_prev)
        self.playback_next.triggered.connect(_jump_next)
        self.playback_play.triggered.connect(_play)
        self.playback_stop.triggered.connect(_stop)
        self.playback_loop.triggered.connect(_toggle_loop)

        self.btn_playback_jump_start.clicked.connect(_jump_start)
        self.btn_playback_jump_end.clicked.connect(_jump_end)
        self.btn_playback_prev.clicked.connect(_jump_prev)
        self.btn_playback_next.clicked.connect(_jump_next)
        self.btn_playback_play.clicked.connect(_play)
        self.btn_playback_stop.clicked.connect(_stop)
        self.btn_playback_loop.clicked.connect(_toggle_loop)
        self.spinner_playback_fps.valueChanged.connect(_set_fps)

        # Set initial values
        self.playback_loop.setChecked(self.data["loop"] == True)
        self.btn_playback_loop.setChecked(self.data["loop"] == True)
        self.spinner_playback_fps.setValue(int(self.data["fps"]))

        # Prepare thread to playback the effect
        self.playback_thread = PlaybackThread()
        self.playback_thread.finished.connect(_stop)

    def closeEvent(self, event=None):
        """
        Gracefully closes the editor, ensuring any unsaved changes are saved
        if desired, and that any thread(s) are stopped.
        """
        # Prompt for unsaved changes
        if self.modified:
            def _do_not_save():
                self.modified = False
                return self.closeEvent()

            def _do_save():
                return self.save_and_close()

            self.widgets.open_dialog(self.widgets.dialog_warning,
                                     self._("Unsaved Changes"),
                                     self._("This effect was modified. Would you like to save these changes?"),
                                     buttons=[QMessageBox.Save, QMessageBox.Discard, QMessageBox.Cancel],
                                     default_button=QMessageBox.Save,
                                     actions={
                                        QMessageBox.Save: _do_save,
                                        QMessageBox.Discard: _do_not_save
                                     })
            if event:
                event.ignore()
            return

        # Stop any threads
        if self.playback_thread:
            self.dbg.stdout("Stopping playback thread...", self.dbg.action, 1)
            self.playback_thread.exit()

        # If live preview was active, restore original state
        if self.live_preview and self.device:
            self.dbg.stdout("Restoring original device state...", self.dbg.action, 1)
            for zone in self.device.zones:
                self.middleman.replay_active_effect(self.device)

        # Window geometry
        self.appdata.main_window._save_window_position(self.window, "editor")

        # Close window and allow another editor to open again
        self.alive = False
        if event:
            event.accept()
        else:
            self.window.deleteLater()

    def set_modified(self, state):
        """
        Sets the modified flag for this editor. The window title is updated
        accordingly to display the current file and its state.
        """
        self.modified = state
        self.window.setWindowTitle("{0}{2} — {1}".format(self.data["name"], self._("Effect Editor"), "*" if state else ""))

    def _get_layer_labels(self):
        """
        Return a dictionary of human readable labels for layered effects.
        """
        return {
            effects.LAYER_STATIC: self._("Static"),
            effects.LAYER_GRADIENT: self._("Gradient"),
            effects.LAYER_PULSING: self._("Pulsing"),
            effects.LAYER_WAVE: self._("Wave"),
            effects.LAYER_SPECTRUM: self._("Spectrum"),
            effects.LAYER_CYCLE: self._("Cycling"),
            effects.LAYER_SCRIPT: self._("Run Scripted Effect")
        }

    def _show_file_error(self):
        """
        Alias to the _show_file_error() function from the Effects tab.
        """
        self.appdata.tab_effects._show_file_error()
        self.closeEvent()

    def save_and_close(self):
        """
        Saves the data in memory to disk, then closes the editor.
        """
        success = self.save_now()

        if success:
            self.closeEvent()

    def save_now(self):
        """
        Saves the data in memory to disk.
        """
        self.dbg.stdout("Saving Effect: " + self.save_path, self.dbg.action, 1)
        success, save_path = self.fileman.save_item(self.data, self.save_path)

        if not success:
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     self._("Save Error"),
                                     self._("Save failed. Please check the permissions and try again."))
            return False

        self.set_modified(False)
        self.save_path = save_path
        self.statusbar.showMessage(self._("Saved to: []").replace("[]", save_path))
        return True

    def reload_from_file(self):
        """
        Prompts the user if they're happy to dispose of the data in memory in
        favour of the data stored on disk.
        """
        def _do_reload():
            """
            Hot reload the editor from the beginning via the effects class.
            """
            self.dbg.stdout("Reloading effect from disk...", self.dbg.action, 1)
            self.modified = False
            self.alive = False
            self.appdata.tab_effects.open_file(self.save_path)
            self.appdata.tab_effects.edit_file()
            self.closeEvent()

        self.widgets.open_dialog(self.widgets.dialog_warning,
                                 self._("Revert"),
                                 self._("Reload the effect from disk? Any unsaved data will be lost!"),
                                 buttons=[QMessageBox.Yes, QMessageBox.No],
                                 default_button=QMessageBox.Yes,
                                 actions={QMessageBox.Yes: _do_reload})

    # ----------------------------
    # Common
    # ----------------------------
    def _redraw_editor(self):
        """
        Alias to redraw the effect on the editor, based on the effect type.
        """
        aliases = {
            effects.TYPE_LAYERED: self.open_layer,
            effects.TYPE_SEQUENCE: self.open_frame
        }
        aliases[self.effect_type]()

    def _shift_all_positions(self, relative_x, relative_y):
        """
        Offsets the positions of LEDs by the specified relative X or Y value.

        This function only supports the movement of 1 column/row of 1 direction
        at a time.
        """
        self.set_modified(True)

        # Load data into memory
        if self.layered_effect:
            print("fixme:_shift_all_positions TYPE_LAYERED")
            raise NotImplementedError

        elif self.sequence_effect:
            frame = self.data["frames"][self.current_frame]
            new_frame = {}

        # Determine operations
        move_left = relative_x < 0
        move_right = relative_x > 0
        move_down = relative_y > 0
        move_up = relative_y < 0

        # Process changes
        max_x = self.data["map_cols"] - 1
        max_y = self.data["map_rows"] - 1

        if move_left or move_right:
            for x in frame.keys():
                x = int(x)

                # Shift X-axis
                if move_left:
                    new_frame[str(x - 1)] = frame[str(x)]
                elif move_right:
                    new_frame[str(x + 1)] = frame[str(x)]

                # Wrap X-axis
                new_x_keys = new_frame.keys()

                # -- First item goes last
                if str(-1) in new_x_keys:
                    new_frame[str(max_x)] = frame[str(0)]
                    del(new_frame[str(-1)])

                # -- Last item goes first
                if str(max_x + 1) in new_x_keys:
                    new_frame[str(0)] = frame[str(max_x)]
                    del(new_frame[str(max_x + 1)])

        elif move_up or move_down:
            for x in frame.keys():
                x = int(x)
                y_keys = list(frame[str(x)].keys())
                new_frame[str(x)] = {}

                for y in y_keys:
                    y = int(y)

                    # Shift Y-axis
                    if move_up:
                        new_frame[str(x)][str(y - 1)] = frame[str(x)][str(y)]
                    elif move_down:
                        new_frame[str(x)][str(y + 1)] = frame[str(x)][str(y)]

                    # Wrap Y-axis
                    new_y_keys = new_frame[str(x)].keys()

                    # -- First item goes last
                    if str(-1) in new_y_keys:
                        new_frame[str(x)][str(max_y)] = frame[str(x)][str(0)]
                        del(new_frame[str(x)][str(-1)])

                    # -- Last item goes first
                    if str(max_y + 1) in new_y_keys:
                        new_frame[str(x)][str(0)] = frame[str(x)][str(max_y)]
                        del(new_frame[str(x)][str(max_y + 1)])

        # Save new data and refresh UI
        if self.layered_effect:
            print("fixme:_shift_all_positions TYPE_LAYERED")
            raise NotImplementedError

        elif self.sequence_effect:
            self.data["frames"][self.current_frame] = new_frame
            self.open_frame()

    def shift_all_left(self):
        """
        Move all the LEDs by -1 on the X-axis.
        """
        self._shift_all_positions(-1, 0)

    def shift_all_right(self):
        """
        Move all the LEDs by +1 on the X-axis.
        """
        self._shift_all_positions(1, 0)

    def shift_all_up(self):
        """
        Move all the LEDs by -1 on the Y-axis.
        """
        self._shift_all_positions(0, -1)

    def shift_all_down(self):
        """
        Move all the LEDs by +1 on the Y-axis.
        """
        self._shift_all_positions(0, 1)

    def edit_metadata(self):
        """
        Opens a modal metadata window and reloads the effect upon accepting the
        changes.
        """
        def _metadata_changed(newdata):
            if newdata == self.data:
                self.dbg.stdout("Metadata unchanged.", self.dbg.success, 1)
                return

            self.dbg.stdout("Metadata changed, refreshing...", self.dbg.action, 1)
            self.action_view_device_graphic.setDisabled(True if not newdata["map_graphic"] else False)
            self.set_modified(True)
            self.data = newdata
            self.view_device_graphic()
            self.statusbar.clearMessage()

        def _metadata_closed(result):
            self.window.setEnabled(True)

        self.window.setEnabled(False)
        self.metadata_editor = controller_effects.EffectMetadataEditor(self.appdata, self.data, _metadata_changed)
        self.metadata_editor.dialog.finished.connect(_metadata_closed)

    def edit_triggers(self):
        """
        Opens a window to quickly create, modify or delete a trigger that
        uses this effect.
        """
        pass

    def _live_preview_failed(self, e):
        """
        Inform the user the live preview failed.

        Params:
            e       Raw exception
        """
        self.dbg.stdout("Failed to preview on device! Exception: ", self.dbg.error)
        self.dbg.stdout(common.get_exception_as_string(e) + "\n", self.dbg.error)

        # Disable live preview for session
        self.device = None
        self.matrix = None
        self.widgets.open_dialog(self.widgets.dialog_error,
                                 self._("Backend Error"),
                                 self._("An error occurred while sending the frame to the hardware."),
                                 info_text=self._("Live preview has been disabled for this session."),
                                 details=common.get_exception_as_string(e))

    # ----------------------------
    # Tools
    # ----------------------------
    def _select_mode_common(self):
        self.tool_draw.setChecked(False)
        self.tool_eraser.setChecked(False)
        self.tool_picker.setChecked(False)

    def select_mode_draw(self):
        """
        Select tool 1 for the visual editor.

            Layered     Assign LEDs/keys to the current layer
            Sequence    Draw colours on LEDs/keys
        """
        self.current_tool = VISUAL_MODE_ADD
        self.device_renderer.set_mode(VISUAL_MODE_ADD)
        self._select_mode_common()
        self.tool_draw.setChecked(True)

    def select_mode_eraser(self):
        """
        Select tool 2 for the visual editor.

            Layered     Unassign LEDs/keys from the current layer
            Sequence    Clear colour on LEDs/keys
        """
        self.current_tool = VISUAL_MODE_DEL
        self.device_renderer.set_mode(VISUAL_MODE_DEL)
        self._select_mode_common()
        self.tool_eraser.setChecked(True)

    def select_mode_picker(self):
        """
        Select tool 3 for the visual editor.

            Layered     n/a - Unused
            Sequence    Grab the colour on an LED/key
        """
        self.current_tool = VISUAL_MODE_PICK
        self.device_renderer.set_mode(VISUAL_MODE_PICK)
        self._select_mode_common()
        self.tool_picker.setChecked(True)

    # ----------------------------
    # Visual Editor (WebView)
    # ----------------------------
    def _update_zoom_controls(self):
        """
        Enable/disable the zoom controls accordingly, to avoid going under or
        over the min/max zoom levels
        """
        self.webview.setZoomFactor(self.webview_zoom_level)
        min_zoom = 0.25
        max_zoom = 3

        self.action_zoom_in.setEnabled(True)
        self.action_zoom_out.setEnabled(True)

        if self.webview_zoom_level <= min_zoom:
            self.action_zoom_out.setEnabled(False)

        if self.webview_zoom_level >= max_zoom:
            self.action_zoom_in.setEnabled(False)

    def zoom_in(self):
        """
        Increase the zoom of the visual editor viewport.
        """
        self.webview_zoom_level += 0.25
        self._update_zoom_controls()

    def zoom_out(self):
        """
        Decrease the zoom of the visual editor viewport.
        """
        self.webview_zoom_level -= 0.25
        self._update_zoom_controls()

    def zoom_reset(self):
        """
        Reset the zoom of the visual editor viewport.
        """
        self.webview_zoom_level = 1.0
        self._update_zoom_controls()

    def _view_device_reload_ready(self):
        """
        Shared private function for when the user changes the graphic while
        the editor is open. This ensures the state is loaded properly.
        """
        self.init_editor()
        self.device_renderer.set_colour(self.current_colour)
        self.device_renderer.set_mode(self.current_tool)
        self.statusbar.showMessage(self._("Temporarily changed the graphic. To make permanent, edit the metadata."), 5000)

    def view_device_graphic(self):
        """
        Temporarily switch the visual editor graphic to the hardware graphic,
        if available.
        """
        self.statusbar.showMessage(self._("Loading..."), 5000)
        hide_key_labels = not self.action_view_key_labels.isChecked()
        self.device_renderer = DeviceRenderer(self.appdata, self, self.webview, self._view_device_reload_ready, self.data["map_graphic"], self.data["map_rows"], self.data["map_cols"], hide_key_labels)

        if self.data["map_device_icon"] in ["keyboard", "keypad"]:
            self.action_view_key_labels.setEnabled(True)

    def view_device_grid(self):
        """
        Temporarily switch the visual editor graphic to a grid, which allows
        drawing on any device.
        """
        self.statusbar.showMessage(self._("Loading..."), 5000)
        hide_key_labels = not self.action_view_key_labels.isChecked()
        self.device_renderer = DeviceRenderer(self.appdata, self, self.webview, self._view_device_reload_ready, "", self.data["map_rows"], self.data["map_cols"], hide_key_labels)

        self.action_view_key_labels.setEnabled(False)

    def view_key_labels(self):
        """
        Temporarily show/hide the key labels (for keyboards and keypads only)
        """
        if self.action_view_device_graphic.isChecked():
            self.view_device_graphic()
        else:
            self.view_device_grid()
        self.statusbar.showMessage(self._("Temporarily changed the graphic. To make permanent, edit the application's preferences."), 5000)

    # ----------------------------
    # Specific to Layered Effects
    # ----------------------------
    def load_layers(self):
        """
        Clears and populates layers on the dock controls.
        """
        pass

    def open_layer(self):
        """
        Draw the selected layer for editing, and update the properties dock.

        This will redraw the colours in the visual editor and physical device
        (if preview is enabled) based on the currently selected layer.
        """
        pass

    def new_layer(self):
        """
        Create a new layer using default values and loads it.
        """
        pass

    def delete_layer(self):
        """
        Prompts for confirmation before deleting a layer.
        """
        pass

    def duplicate_layer(self):
        """
        Creates a new layer inheriting the data for the currently selected one
        and loads it.
        """
        pass

    def raise_layer(self):
        """
        Moves the layer up by one and refreshes the visual editor.
        """
        pass

    def lower_layer(self):
        """
        Moves the layer down by one and refreshes the visual editor.
        """
        pass

    def assign_key_to_layer(self, x, y):
        """
        User clicks on a key/LED in the visual editor. Add this to the layer
        and update the device preview.
        """
        pass

    def unassign_key_to_layer(self, x, y):
        """
        User clicks on a key/LED in the visual editor. Remove this from the
        layer and update the device preview.
        """
        pass

    # ----------------------------
    # Specific to Sequence Effects
    # ----------------------------
    def load_frames(self):
        """
        Clears and populates frames on the dock controls.
        """
        table = self.frame_table
        frame_count = len(self.data["frames"])

        table.setColumnCount(frame_count)
        for frame in range(0, frame_count):
            table.setColumnWidth(frame, 64)

        # Make sure there is one frame
        if frame_count == 0:
            table.insertColumn(0)
            self.data["frames"] = [{}]

        # Select first frame if deselected
        if len(table.selectedIndexes()) == 0:
            table.setSelection(QRect(0, 0, 1, 1), QItemSelectionModel.Select)

    def open_frame(self, playback_mode=False):
        """
        Open the selected frame for editing.

        This will redraw the colours in the visual editor and physical device
        (if preview is enabled) based on the currently selected frame.

        When 'playback_mode' is on, UI controls will not be updated.
        """
        fx = self.matrix
        self.device_renderer.clear()

        if fx:
            fx.clear()

        if not self.frame_table.selectedIndexes():
            self.frame_table.selectColumn(self.current_frame)
            return

        index = self.frame_table.selectedIndexes()[0].column()
        self.current_frame = index
        total_X = self.data["map_cols"]
        total_Y = self.data["map_rows"]

        # Make sure the frame dictionary keys have parent (x-axis) keys
        for x in range(0, total_X):
            try:
                self.data["frames"][index][str(x)]
            except KeyError:
                # New frame to be written
                self.data["frames"][index][str(x)] = {}
            except IndexError:
                # The last index was just deleted
                self.frame_table.selectColumn(self.current_frame)
                return

        self.status_frame.setText(self._("Frame [1] of [10]").replace("[1]", str(self.current_frame + 1)).replace("[10]", str(self.frame_table.columnCount())))

        # Draw frame on editor (and optionally physical hardware)
        frame = self.data["frames"][index]
        for x in frame.keys():
            for y in frame[x].keys():
                try:
                    hex_value = frame[str(x)][str(y)]
                    self.device_renderer.set_pos(x, y, hex_value)
                except KeyError:
                    # Expected, no data stored for this position
                    continue

                if fx:
                    try:
                        rgb = fx.hex_to_rgb(hex_value)
                        fx.set(int(x), int(y), rgb[0], rgb[1], rgb[2])
                    except Exception as e:
                        self._live_preview_failed(e)

        if fx:
            fx.draw()

        if not playback_mode:
            self._update_disabled_frame_controls()

    def _update_disabled_frame_controls(self):
        """
        Reusable code to update the state of controls.

        For example, disable buttons that are impossible (e.g. move to right
        when already at the end) as well as preventing editing while
        the animation is playing.
        """
        # -- Restricted during playback
        for widget in [
                self.webview, self.dock_colours,
                self.tool_draw, self.tool_eraser, self.tool_picker,
                self.action_edit_metadata, self.action_edit_triggers,

                self.frame_table,
                self.action_new_frame, self.btn_frame_new,
                self.action_clone_frame, self.btn_frame_clone,

                self.menu_shift, self.menu_edit, self.menu_tools, self.menu_colours,
                self.action_shift_left, self.action_shift_right,
                self.action_shift_up, self.action_shift_down
            ]:
            widget.setEnabled(self.playback_paused)

        # -- Prevent deleting the only frame
        total_frames = len(self.data["frames"])
        self.action_delete_frame.setEnabled(total_frames > 1)
        self.btn_frame_delete.setEnabled(total_frames > 1)

        # -- Preventing shift/step frames at start/end
        self.btn_frame_move_left.setEnabled(self.current_frame >= 1)
        self.action_frame_left.setEnabled(self.current_frame >= 1)
        self.playback_prev.setEnabled(self.current_frame >= 1)
        self.btn_playback_prev.setEnabled(self.current_frame >= 1)
        self.playback_jump_start.setEnabled(self.current_frame >= 1)
        self.btn_playback_jump_start.setEnabled(self.current_frame >= 1)

        self.btn_frame_move_right.setEnabled(self.current_frame < total_frames - 1)
        self.action_frame_right.setEnabled(self.current_frame < total_frames - 1)
        self.playback_next.setEnabled(self.current_frame < total_frames - 1)
        self.btn_playback_next.setEnabled(self.current_frame < total_frames - 1)
        self.playback_jump_end.setEnabled(self.current_frame < total_frames - 1)
        self.btn_playback_jump_end.setEnabled(self.current_frame < total_frames - 1)

        # -- Restricted during playback but frame specific
        if not self.playback_paused:
            for widget in [
                self.action_delete_frame, self.btn_frame_delete,
                self.action_frame_left, self.btn_frame_move_left,
                self.action_frame_right, self.btn_frame_move_right,
                self.playback_prev, self.btn_playback_prev,
                self.playback_next, self.btn_playback_next,
                self.playback_jump_start, self.btn_playback_jump_start,
                self.playback_jump_end, self.btn_playback_jump_end
            ]:
                widget.setEnabled(False)

    def load_colours(self):
        """
        Populate the colour dock and functions associated for quickly setting
        the brush (draw) colour.

        Intended for use with sequence effects, the "pixel art" style of editing.
        In addition, saved colours will have lighter/darker colours generated.
        """
        colours = pref.load_file(self.paths.colours)

        # Current colour (picker) and label
        def _set_custom_colour(new_hex, data):
            self._set_current_colour(new_hex)

            # Regenerate the colour list if the list has changed.
            if colours != pref.load_file(self.paths.colours):
                self.dbg.stdout("Colour list changed, reloading dock...", self.dbg.action, 1)
                self.load_colours()

        # Populate saved colours (and variants)
        def _mk_button(parent_widget, name, hex_value):
            button = QPushButton()
            button.setIconSize(QSize(32, 32))
            button.resize(QSize(32, 32))
            button.setFixedSize(32, 32)
            button.setFlat(True)
            button.setToolTip("{0} ({1})".format(name, hex_value))
            button.setStyleSheet("QPushButton { border: none; background: none; padding: 0; margin: 0; }")
            button.setIcon(QIcon(common.generate_colour_bitmap(self.dbg, hex_value, 32)))
            button.clicked.connect(lambda a: self._set_current_colour(hex_value))
            parent_widget.layout().addWidget(button)

        container = QWidget()
        container.setLayout(QFlowLayout())
        container.layout().setSpacing(2)
        container.layout().setContentsMargins(0, 0, 0, 0)

        edit_btn = QPushButton()
        if not self.appdata.system_qt_theme:
            edit_btn.setIcon(self.widgets.get_icon_qt("general", "edit"))
        edit_btn.setText(self._("Edit"))
        edit_btn.setStatusTip(self._("Modify or reorder your saved colours"))
        edit_btn.clicked.connect(self.edit_saved_colours)

        for colour in colours:
            shades = [-45, -30, -15, 0, 15, 30]
            if not self.preferences["editor"]["show_saved_colour_shades"]:
                shades = [0]
            for percent in shades:
                percent = float(percent / 100)
                new_colour = self.fx.lightness_hex(colour["hex"], percent)
                label = "{0} {1}%".format(colour["name"], int(percent * 100))
                if percent == 0:
                    label = colour["name"]
                _mk_button(container, label, new_colour)

        shared.clear_layout(self.saved_colours.layout())
        self.saved_colours.layout().addWidget(container)
        self.saved_colours.layout().addWidget(edit_btn)
        self.dock_colours.setMinimumWidth(240)

    def new_frame(self):
        """
        Creates a blank frame after the current frame, and loads it.
        """
        self.set_modified(True)

        current_index = self.current_frame
        new_index = self.current_frame + 1
        self.dbg.stdout("New frame at position {0}".format(new_index), self.dbg.debug, 1)

        self.data["frames"].insert(new_index, {})

        self.frame_table.insertColumn(new_index)
        self.frame_table.setColumnWidth(new_index, 64)
        self.frame_table.selectColumn(new_index)

    def delete_frame(self):
        """
        Prompts for confirmation before deleting a frame.
        """
        def _do_delete_frame():
            self.set_modified(True)

            old_index = self.current_frame
            new_index = self.current_frame - 1

            if new_index < 0:
                new_index = 0

            del(self.data["frames"][old_index])
            self.frame_table.removeColumn(old_index)
            self.frame_table.selectColumn(new_index)

        if self.suppress_delete_prompt:
            return _do_delete_frame()

        self.widgets.open_dialog(self.widgets.dialog_warning,
                                 self._("Delete Frame"),
                                 self._("Permanently delete this frame? There is no undo."),
                                 info_text=self._("Tip: This confirmation can be suppressed via the Editor tab under Preferences."),
                                 buttons=[QMessageBox.Yes, QMessageBox.No],
                                 default_button=QMessageBox.Yes,
                                 actions={QMessageBox.Yes: _do_delete_frame})

    def clone_frame(self):
        """
        Creates a new frame inheriting the data for the currently selected one
        and loads it.
        """
        self.set_modified(True)

        current_index = self.current_frame
        new_index = self.current_frame + 1
        self.dbg.stdout("Cloned frame at position {0}".format(new_index), self.dbg.debug, 1)

        newdata = copy.deepcopy(self.data["frames"][current_index])
        self.data["frames"].insert(new_index, newdata)

        self.frame_table.insertColumn(new_index)
        self.frame_table.setColumnWidth(new_index, 64)
        self.frame_table.selectColumn(new_index)

    def _swap_frame_data(self, relative_pos):
        """
        Relocate frame data with another data position and reload the frame.
        """
        self.set_modified(True)

        current_index = self.current_frame
        new_index = self.current_frame + relative_pos

        data_src = copy.deepcopy(self.data["frames"][current_index])
        data_dst = copy.deepcopy(self.data["frames"][new_index])

        self.data["frames"][current_index] = data_dst
        self.data["frames"][new_index] = data_src

        self.dbg.stdout("Swapped frame {0} with frame {1}".format(current_index, new_index), self.dbg.debug, 1)
        self.frame_table.selectColumn(new_index)

    def shift_frame_left(self):
        """
        Move the frame to the left by one and refresh the visual editor.
        """
        self._swap_frame_data(-1)

    def shift_frame_right(self):
        """
        Move the frame to the right by one and refresh the visual editor.
        """
        self._swap_frame_data(1)

    def _set_current_colour(self, hex_value, no_textbox_update=False):
        """
        Change the colour to draw with. If the draw tool isn't selected,
        this will automatically change.
        """
        self.dbg.stdout("Brush colour changed: " + hex_value, self.dbg.debug, 1)
        self.current_colour = hex_value
        self.device_renderer.set_colour(hex_value)
        self.select_mode_draw()

        # Allows the user to keep typing when directly typing hex value
        if not no_textbox_update:
            self.current_colour_textbox.setText(hex_value)

        self.current_colour_block.setStyleSheet("QWidget {{ background-color: {0} }}".format(hex_value))
        self._refresh_colour_tweak_controls()

    def open_colour_picker(self):
        """
        Opens the system (Qt) colour picker for choosing a new colour on the fly.
        """
        dialog = QColorDialog()

        # TODO: Nice to have: Use Polychromatic styling for the dialog
        # QColorDialog() is private, so this may be tricky.
        # This does not work!
        shared.load_qt_theme(self.appdata, dialog)

        output = dialog.getColor(title=self._("Choose Brush Colour"), initial=QColor(self.current_colour))

        if not output.isValid():
            return
        self._set_current_colour(output.name())

    def edit_saved_colours(self):
        """
        Opens Polychromatic's colour picker for managing the saved colour list.
        """
        def _update_saved_colours(new_hex, params=[]):
            self._set_current_colour(new_hex)
            self.load_colours()

        picker = self.widgets.create_colour_control(self.current_colour, _update_saved_colours, None, self._("Saved Colours"))
        picker.findChild(QPushButton).click()

    def draw_LED_to_frame(self, x, y):
        """
        User draws a new position on the current frame.
        """
        def _release_click():
            """After an error dialog, the button ends up "stuck" in the webview."""
            self.webview.page().runJavaScript("mouseDown = 0;")

        try:
            self.data["frames"][self.current_frame][str(x)][str(y)] = self.current_colour
        except KeyError:
            _release_click()
            self.dbg.stdout("Can't set LED ({0}, {1}) as out of bounds for device (or save data)".format(str(x), str(y)), self.dbg.error)
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     self._("Out of Bounds"),
                                     self._("There isn't a position for (X,Y) for this device. The graphic contains incorrect metadata or is incompatible for use with this device.").replace("(X,Y)", "({0},{1})".format(str(x), str(y))))
            return

        if self.matrix:
            try:
                rgb = common.hex_to_rgb(self.current_colour)
                self.matrix.set(int(x), int(y), rgb[0], rgb[1], rgb[2])
                self.matrix.draw()
            except Exception as e:
                _release_click()
                self._live_preview_failed(e)

        self.set_modified(True)
        self.dbg.stdout("Set LED ({0},{1}) to {2}".format(x, y, self.current_colour), self.dbg.debug, 1)

    def erase_LED_from_frame(self, x, y):
        """
        User erases a position on the current frame.
        """
        try:
            del(self.data["frames"][self.current_frame][str(x)][str(y)])
        except KeyError:
            self.statusbar.showMessage(self._("This LED is empty - nothing to erase here!"), 5000)
            return

        if self.matrix:
            try:
                self.matrix.set(int(x), int(y), 0, 0, 0)
                self.matrix.draw()
            except Exception as e:
                self._live_preview_failed(e)

        self.set_modified(True)
        self.dbg.stdout("Erase LED ({0},{1})".format(x, y), self.dbg.debug, 1)

    def pick_LED_colour_from_frame(self, x, y):
        """
        User picks a colour from the current frame.
        """
        try:
            hex_value = self.data["frames"][self.current_frame][str(x)][str(y)]
            self._set_current_colour(hex_value)
        except KeyError:
            self.statusbar.showMessage(self._("This LED is empty - no colour to pick here!"), 5000)
            return

        self.dbg.stdout("Pick LED ({0},{1}). Current colour changed to {2}".format(x, y, self.current_colour), self.dbg.debug, 1)

    def set_colour_by_textbox(self, new_hex):
        """
        Emitted when the hex value is changed. The current colour will only be
        updated when the full hex is specified. Qt's input mask already validated this.
        """
        if len(new_hex) < 7:
            return
        self._set_current_colour(new_hex, no_textbox_update=True)

    def _refresh_colour_tweak_controls(self):
        """
        Enables/disables controls for HSL adjustments when the next/previous value
        has been exhausted. For example, pure white (#fff) cannot get any lighter.
        """
        for widget in [self.btn_hue_increase, self.btn_hue_decrease,
                       self.btn_saturation_increase, self.btn_saturation_decrease,
                       self.btn_lightness_decrease, self.btn_lightness_increase,
                       self.action_colours_hue_increase, self.action_colours_hue_decrease,
                       self.action_colours_saturation_increase, self.action_colours_saturation_decrease,
                       self.action_colours_lightness_increase, self.action_colours_lightness_decrease]:
            widget.setEnabled(True)

        if self.fx.hue_hex(self.current_colour, 0.05) == self.current_colour:
            self.btn_hue_increase.setEnabled(False)
            self.action_colours_hue_increase.setEnabled(False)

        if self.fx.hue_hex(self.current_colour, -0.05) == self.current_colour:
            self.btn_hue_decrease.setEnabled(False)
            self.action_colours_hue_decrease.setEnabled(False)

        if self.fx.saturate_hex(self.current_colour, 0.05) == self.current_colour:
            self.btn_saturation_increase.setEnabled(False)
            self.action_colours_saturation_increase.setEnabled(False)

        if self.fx.saturate_hex(self.current_colour, -0.05) == self.current_colour:
            self.btn_saturation_decrease.setEnabled(False)
            self.action_colours_saturation_decrease.setEnabled(False)

        if self.fx.lightness_hex(self.current_colour, 0.05) == self.current_colour:
            self.btn_lightness_increase.setEnabled(False)
            self.action_colours_lightness_increase.setEnabled(False)

        if self.fx.lightness_hex(self.current_colour, -0.05) == self.current_colour:
            self.btn_lightness_decrease.setEnabled(False)
            self.action_colours_lightness_decrease.setEnabled(False)

    def set_colour_increase_hue(self):
        """
        Increases the Hue (HSL) of the current colour.
        """
        self._set_current_colour(self.fx.hue_hex(self.current_colour, 0.05))
        self._refresh_colour_tweak_controls()

    def set_colour_decrease_hue(self):
        """
        Decreases the Hue (HSL) of the current colour.
        """
        self._set_current_colour(self.fx.hue_hex(self.current_colour, -0.05))
        self._refresh_colour_tweak_controls()

    def set_colour_increase_saturation(self):
        """
        Increases the Saturation (HSL) of the current colour.
        """
        self._set_current_colour(self.fx.saturate_hex(self.current_colour, 0.05))
        self._refresh_colour_tweak_controls()

    def set_colour_decrease_saturation(self):
        """
        Decreases the Saturation (HSL) of the current colour.
        """
        self._set_current_colour(self.fx.saturate_hex(self.current_colour, -0.05))
        self._refresh_colour_tweak_controls()

    def set_colour_increase_lightness(self):
        """
        Increases the Value (HSL) of the current colour.
        """
        self._set_current_colour(self.fx.lightness_hex(self.current_colour, 0.05))
        self._refresh_colour_tweak_controls()

    def set_colour_decrease_lightness(self):
        """
        Decreases the Value (HSL) of the current colour.
        """
        self._set_current_colour(self.fx.lightness_hex(self.current_colour, -0.05))
        self._refresh_colour_tweak_controls()


class DeviceRenderer(shared.TabData):
    """
    Responsible for the input/output of the device graphic or grid layout.
    """
    def __init__(self, appdata, editor, webview, ready_fn, map_graphic, map_rows, map_cols, hide_labels=True):
        """
        Params:
            appdata         ApplicationData() object
            editor          VisualEffectEditor() object
            webview         QWebEngineView object
            ready_fn        Run this function as soon as the editor has loaded
            map_graphic     Filename of graphic to use. Blank string indicates to use grid.
            map_rows        Number of rows for device
            map_cols        Number of cols for device
            show_labels     Boolean of whether labels on keyboards/keypads should be visible
        """
        self.appdata = appdata
        super().__init__(appdata)
        self.editor = editor
        self.webview = webview
        self.loaded = False
        self.ready_fn = ready_fn
        self.use_native_cursor = appdata.preferences["editor"]["system_cursors"]
        self.hide_key_labels = hide_labels

        self.device_map = effects.DeviceMapGraphics(appdata)
        self.graphic_filename = map_graphic
        self.graphic_name = self.device_map.get_graphic_name_from_filename(map_graphic)
        self.rows = map_rows
        self.cols = map_cols
        self.mode = 1

        # Wait until the webview has fully loaded, then load the graphic.
        self.webview.loadFinished.connect(self.ready)
        url = QUrl("file://" + os.path.join(self.paths.data_dir, "qt", "editor.html"))

        # Reload if web view previously initialised
        if self.webview.page().url() == url:
            self.webview.reload()
        else:
            # First time opening this editor session
            self.webview.load(url)

        # Connect signals
        self.webview.titleChanged.connect(self._cb_title_changed)

    def ready(self, ok=True):
        """
        As soon as the WebView has fully loaded, load the graphic ready for
        editing, as well as the ready_fn.
        """
        self.loaded = True
        if not ok:
            self.widgets.open_dialog(self.widgets.dialog_error,
                                     self._("Controller Error"),
                                     self._("Failed to load the Qt Web Engine. Unfortunately, editing won't be possible."),
                                     info_text=self._("Make sure the application (and its dependencies) are installed and configured correctly."))
            self.editor.window.close()

        # Load the SVG into the viewport
        svg = self._get_graphic_svg().replace("'", "&quot;")
        self.webview.page().runJavaScript("loadSVG('{0}'); clearLED()".format(svg))

        # Set mode
        self.set_mode(VISUAL_MODE_ADD)

        # Remove scroll bar theming if user prefers native (although it'll look like Chromium instead)
        # Also sets the background colour to match native controls.
        if self.appdata.system_qt_theme:
            self.webview.page().runJavaScript("document.querySelector('#polychromatic-qt-theme').remove()")

            bg_colour = self.main_window.palette().alternateBase().color().name()
            self.webview.page().runJavaScript("document.body.style.background = '{0}'".format(bg_colour))

        # Run ready function
        if self.ready_fn:
            self.ready_fn()

    def _get_graphic_svg(self):
        """
        Returns the SVG of the device's matrix represented as a 'pretty' graphic.
        """
        if not self.graphic_filename:
            return self._generate_grid_svg()

        # Update UI elements
        self.editor.action_view_device_graphic.setChecked(True)
        self.editor.action_view_grid.setChecked(False)

        svg = self.device_map.get_svg_graphic(self.graphic_filename)

        if not svg:
            self.dbg.stdout("Graphic does not exist: '{0}'. Using grid as fallback!".format(self.graphic_filename), self.dbg.error)
            self.widgets.open_dialog(self.widgets.dialog_warning,
                                     self._("Missing File"),
                                     self._("This effect is mapped to a graphic named '[]', but it's not installed.".replace("[]", self.graphic_filename)),
                                     info_text=self._("The grid will be used instead. A different graphic can be chosen by editing the metadata."))
            return self._generate_grid_svg()

        if self.hide_key_labels:
            svg = self._hide_key_labels(svg)

        return svg

    def _generate_grid_svg(self):
        """
        Returns an SVG of the device's matrix grid.
        """
        self.editor.action_view_device_graphic.setChecked(False)
        self.editor.action_view_grid.setChecked(True)

        return self.device_map.get_svg_grid(self.cols, self.rows)

    def _cb_title_changed(self, title):
        """
        JavaScript sends string messages to us (Python) by changing the title.
        This will run when the title changes.
        """
        pieces = title.split(";")
        if pieces[0] == "click":
            x = int(pieces[1])
            y = int(pieces[2])
            callbacks = {
                effects.TYPE_SEQUENCE: {
                    VISUAL_MODE_ADD: self.editor.draw_LED_to_frame,
                    VISUAL_MODE_DEL: self.editor.erase_LED_from_frame,
                    VISUAL_MODE_PICK: self.editor.pick_LED_colour_from_frame
                },
                effects.TYPE_LAYERED: {
                    VISUAL_MODE_ADD: self.editor.assign_key_to_layer,
                    VISUAL_MODE_DEL: self.editor.unassign_key_to_layer
                }
            }
            callbacks[self.editor.effect_type][self.editor.current_tool](x, y)

    def set_mode(self, mode):
        """
        Update the cursor/behaviour inside the visual editor, but only when
        the editor is ready.
        """
        if not self.loaded:
            return

        self.mode = mode
        self.webview.page().runJavaScript("setMode({0}, {1})".format(mode, str(self.use_native_cursor).lower()))

    def set_colour(self, hex_value):
        """
        Update the visual editor's current colour in memory.
        """
        self.webview.page().runJavaScript("currentColour = '{0}';".format(hex_value))

        # Reset 'title' so the same command can be sent again (i.e. draw on same position)
        self.webview.page().runJavaScript("document.title = '';")

    def clear(self):
        """
        Clear all the keys.
        """
        if self.loaded:
            self.webview.page().runJavaScript("clearLED()")

    def set_pos(self, x, y, hex_value):
        """
        Set the colour of a specific key.
        """
        self.webview.page().runJavaScript("mode = 1; setLED({0}, {1}, false, '{2}'); mode = {3};".format(x, y, hex_value, self.mode))

    def _hide_key_labels(self, svg):
        """
        Returns an SVG with the "key labels" hidden or removed.

        This is intended for keyboards/keypads which may not have a localized layout
        for the user, but share the same physical layout as an existing one. Users
        may choose to hide labels as a preference too.
        """
        output = []
        lines = svg.splitlines()

        for line in lines:
            if line.find("class=\"label\"") != -1:
                line = line.replace("class=\"label\"", "opacity=\"0\"")
            output.append(line)
        return "\n".join(output)
