#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2019-2020 Luke Horwell <code@horwell.me>
#
"""
This module manages, edits and renders custom effects.
"""

import os
import base64
import hashlib
import time
import json

from . import common
from . import preferences as pref

path = pref.Paths()
dbg = common.Debugging()


class EffectData(object):
    """
    Memory storage for managing a custom effect.

    See online documentation at https://polychromatic.app/docs/ for details on this
    specification.
    """
    def __init__(self):
        """
        Initialises the object. Data will be altered in memory before saving
        to disk.
        """
        self.file_path = None               # Absolute path to the file
        self.name = ""                      # "Awesome effect name"
        self.author = ""                    # Author name or alias
        self.author_url = ""                # Optional URL to author's website
        self.emblem = None                  # E.g. "lamp", "software"
        self.icon = None                    # base64 encoded string of an image (PNG/JPG)
        self.effect_type = ""               # static / animated / scripted
        self.formfactor = ""                # As used in common.get_device_type()
        self.mapping = ""                   # BlackWidow Chroma
        self.mapping_dimensions = [0, 0]    # Rows and columns
        self.mapping_locale = ""            # en_GB
        self.layers = {}                    # {layer_no: {"name:" "name", "frames": {frame_no: {x: {y: "#FFF"}}}}}
        self.rendered_frames = None         # {frame: {x: {y: "#FFF"}}}
        self.key_labels = {}                # {x: {y: "label"}}

        # Animated effects only
        self.playback = {
            "fps": 0,                       # Speed between each keyframe
            "loop": False                   # When false, stays on the last frame.
        }

    def load_from_file(self, path):
        """
        Loads the contents from disk to memory.

        Params:
            filename        Full filename, no spaces. E.g. ~/.config/polychromatic/effects/my-effect.json

        Returns boolean if load operation was successful.
        """
        if not os.path.exists(path):
            dbg.stdout("File does not exist: " + path, dbg.error)
            return False

        try:
            with open(path) as stream:
                data = json.load(stream)

            # File -> Memory
            self.file_path = path
            metadata = data.get("metadata")
            self.name = metadata.get("name")
            self.author = metadata.get("author")
            self.author_url = metadata.get("author_url")
            self.emblem = metadata.get("emblem")
            self.icon = metadata.get("icon")
            self.effect_type = metadata.get("effect_type")
            self.formfactor = metadata.get("formfactor")
            self.mapping = metadata.get("mapping")
            self.mapping_dimensions = metadata.get("mapping_dimensions")
            self.mapping_locale = metadata.get("mapping_locale")

            self.layers = data.get("layers")
            self.key_labels = data.get("key_labels")

            self.playback["fps"] = data.get("playback").get("fps")
            self.playback["loop"] = data.get("playback").get("loop")

            return True

        except Exception as e:
            dbg.stdout("Failed to read effect file: " + path, dbg.error)
            dbg.stdout("Exception: " + str(e), dbg.error)
            return False

    def save_to_file(self):
        """
        Saves the contents in memory to disk.

        Returns boolean if save operation was successful.
        """
        structure = {
            "metadata": {
                "name": self.name,
                "author": self.author,
                "author_url": self.author_url,
                "emblem": self.emblem,
                "icon": self.icon,
                "effect_type": self.effect_type,
                "formfactor": self.formfactor,
                "mapping": self.mapping,
                "mapping_dimensions": self.mapping_dimensions,
                "mapping_locale": self.mapping_locale
            },
            "playback": {
                "fps": self.playback["fps"],
                "loop": self.playback["loop"]
            },
            "layers": self.layers,
            "key_labels": self.key_labels
        }

        if len(self.name) == 0:
            return False

        if not self.file_path:
            self.file_path = os.path.join(path.effects, self.generate_filename() + ".json")

            # Prevent overriding if effect with same name exists.
            if os.path.exists(self.file_path):
                self.file_path = os.path.join(path.effects, "{0}-{1}.json".format(self.generate_filename(), str(int(time.time()))))

        try:
            f = open(self.file_path, "w+")
            f.write(json.dumps(structure, sort_keys=True, indent=4))
            f.close()
            dbg.stdout("Successfully written: " + self.file_path, dbg.success, 1)
            return True
        except Exception as e:
            dbg.stdout("Write error: " + self.file_path, dbg.error)
            dbg.stdout("Exception: " + str(e), dbg.error)
            return False

        return False

    def get_icon_path(self, data_source):
        """
        Returns a path to this effect's icon.

        If an emblem (built-in) is specified, then this is used, otherwise the
        base64 encoded "icon" string will be saved to disk cache. Should neither
        be available, a generic icon is returned.
        """
        if self.emblem:
            return data_source + "/ui/img/emblems/" + self.emblem + ".svg"

        if self.icon:
            # Check the 'icon' isn't a path (e.g. human edited JSON file)
            if os.path.exists(self.icon):
                with open(self.icon, "rb") as f:
                    self.icon = base64.b64encode(f.read()).decode("UTF-8")

            # Decode from base64 to file, and cache.
            # First, determine cache filename, which is a SHA1 of the base64 string.
            sha1 = hashlib.sha1()
            sha1.update(self.icon.encode("UTF-8"))
            cache_path = os.path.join(path.cache, sha1.hexdigest())

            if not os.path.exists(cache_path):
                with open(cache_path, "wb") as f:
                    f.write(base64.b64decode(self.icon))

            if os.path.exists(cache_path):
                return cache_path

        # No icon available
        return data_source + "/ui/img/fa/effects.svg"

    def set_icon_path(self, is_emblem, emblem_or_path):
        """
        Saves the effect icon to memory.

        If it's an emblem, this will be just the string.
        If it's a path, this will be base64 encoded so there is no dependency on external files.

        Returns a boolean to indicate success or failure.
        """
        if is_emblem:
            self.emblem = emblem_or_path
            self.icon = None
            return True

        # Encode file as base64 for portability.
        if os.path.exists(emblem_or_path):
            with open(emblem_or_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("UTF-8")
            self.icon = encoded_string
            self.emblem = None
            return True

        return False

    def render(self):
        """
        Returns a "flattened" matrix. All layers in memory are flattened
        into one for playback.
        """
        layers = len(self.layers)

        if layers == 0:
            dbg.stdout("Need at least 1 layer to render this effect.", dbg.error)
            return None

        self.rendered_frames = {}
        for layer in range(layers, 1):
            frames = self.layers[layer]["frames"]
            frame_count = len(frames)

            if frame_count == 0:
                dbg.stdout("Need at least 1 frame to render this effect.", dbg.error)
                return None

            for frame in frames:
                self.rendered_frames[frame] = {}
                matrix = frames[frame]
                rows = matrix.keys()
                for row in rows:
                    self.rendered_frames[frame][row] = {}
                    cols = list(matrix[row].keys())
                    for col in cols:
                        try:
                            data = matrix[row][col]
                            if data == None:
                                continue
                            self.rendered_frames[frame][row][col] = data
                        except KeyError:
                            pass

        return self.rendered_frames

    def set_key_colour(self, layer, x, y, hex_value):
        """
        Sets a hex colour string on a layer at a given position.
        Layers start at 1 and increment upwards.

        A null hex_value indicates the key isn't to be lit up.
        """
        self.layers[layer]["matrix"][row][col] = hex_value

    def set_key_label(self, x, y, value):
        """
        Sets a key label at a given position. Use a null value for no key label.
        """
        self.key_labels[row][col] = value

    def set_fps(self, value):
        """
        Sets the frame rate for playback. Firmware and driver may influence
        the actual speed.
        """
        if value < 1:
            dbg.stdout("Frame rate too low: " + str(value), dbg.warning)
            value = 1
        if value > 60:
            dbg.stdout("Frame rate too high: " + str(value), dbg.warning)
            value = 60

        self.playback["fps"] = value

    def set_loop(self, looped):
        """
        Sets whether the frame should loop after the keyframes finish.

        If false, the last frame will remain displayed.
        """
        self.playback["looped"] = looped

    def generate_filename(self):
        """
        Determines a pretty filename for a new file.
        """
        if len(self.name) > 0:
            filename = ''.join(e for e in self.name if e.isalnum())
            filename = filename.lower().replace(" ", "-")
            return filename

    def rename_self(self):
        """
        Performs a rename of an existing filename. Returns boolean for status.
        """
        old_path = self.file_path
        new_path = os.path.join(path.effects, self.generate_filename() + ".json")

        if len(self.name) == 0 or not os.path.exists(old_path):
            return False

        if old_path == new_path:
            return True

        # Prevent overriding if effect with same name exists.
        if os.path.exists(new_path):
            new_path = os.path.join(path.effects, "{0}-{1}.json".format(self.generate_filename(), str(int(time.time()))))

        try:
            os.rename(old_path, new_path)
            self.file_path = new_path
            return True
        except OSError:
            return False

    def delete_self(self):
        """
        User has requested to delete this effect from the UI. In addition to removing
        the JSON file, anything attached (schedules, profiles) will also be updated
        to remove reference.

        Returns True or False to indicate success.
        """
        dbg.stdout("Deleting: " + self.file_path, dbg.action, 1)
        if not os.path.exists(self.file_path):
            return False
        os.remove(self.file_path)
        return True



def get_effect_list_for_device(effect_dir, formfactor, data_source):
    """
    Returns a list with a sublist in format: [name, icon, filename]

    Parameters:
        - effect_dir        Reads effect JSON from this directory, usually path.effects.
        - formfactor        One of Polychromatic's internal 'form factor' strings. E.g. 'mousemat'
                            If blank, all effects are returned.
    """
    file_list = os.listdir(effect_dir)
    effect_list = []
    for filename in file_list:
        try:
            effect = EffectData()
            effect.load_from_file(os.path.join(effect_dir, filename))
            if effect.formfactor == formfactor or formfactor == None:
                effect_list.append([effect.name, effect.get_icon_path(data_source), filename])
        except Exception as e:
            dbg.stdout("Skipping unreadable JSON: " + filename, dbg.error)
            dbg.stdout("Exception: " + str(e))

    return effect_list
