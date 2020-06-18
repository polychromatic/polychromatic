#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module is a higher level interface for custom effects that transparently
connects to the supported backend, regardless of driver.

It is also used to render keyframe effects.

The API is based on OpenRazer's Python library.
"""

# from . import common


class FX(object):
    """
    The class that provides the object 'fx' used in custom effect scripts.
    """
    def __init__(self):
        """
        Initalise variables used by the custom effect.
        """
        # User
        self.rows = 0
        self.cols = 0
        self.name = "Unknown"
        self.backend = "unknown"
        self.form_factor = "unknown"
        self.matrix = {}

        # Internal
        self._device = None

    def rgb_to_hex(self, red, green, blue):
        """
        Converts a RGB value to a hex colour string.

        Input:  (0, 255, 0)
        Output: "#00FF00"
        """
        pass

    def hex_to_rgb(self, red, green, blue):
        """
        Converts a HEX colour string to a RGB string.

        Input:  "#FF0000"
        Output: (255, 0, 0)
        """
        pass

    def set_brightness_by_value(self, value):
        """
        Set the brightness of the entire device using a value between 0 and 255.
        """
        pass

    def set_brightness_by_percent(self, percent):
        """
        Set the brightness of the entire device passing an integer between 0 and 100.
        """
        pass

    def draw(self):
        """
        Send the frames to the hardware.
        """
        pass
