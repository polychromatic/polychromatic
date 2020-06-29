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
    def __init__(self, device):
        """
        Initalise variables used by the custom effect.

        Params:
            device      (obj)       middleman.get_device_object()
        """
        self._device = device
        self.rows = device["rows"]
        self.cols = device["cols"]
        self.name = device["name"]
        self.backend = device["backend"]
        self.form_factor = device["form_factor"]

        # Functions
        self.set = device["set"]
        self.draw = device["draw"]
        self.clear = device["clear"]
        self.brightness = device["brightness"]

    def rgb_to_hex(self, red, green, blue):
        """
        Converts a RGB value to a hex colour string.

        Input:  (0, 255, 0)
        Output: "#00FF00"
        """
        pass

    def hex_to_rgb(self, value):
        """
        Converts a HEX colour string to a RGB string.

        Input:  "#FF0000"
        Output: (255, 0, 0)
        """
        pass
