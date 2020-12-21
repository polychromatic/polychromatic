#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module is a higher level interface for custom effects that transparently
connects to the supported backend, regardless of driver.

This is used internally for rendering software effects as well as "scripted"
effects written by users.
"""

from . import common


class FX(object):
    """
    Backends use this class for the get_device_object() functionality. This
    is for supporting individual LED lighting where supported by the device.

    This object is the 'fx' object used in custom effect scripts as well as
    Polychromatic internally for software effects.

    All classes should be implemented. If they are unused
    """
    def __init__(self, rows, cols, name, backend, form_factor, serial):
        """
        Initalise essential variables - these are user facing variables.

        Params:
            rows        (int)   Number of rows, 0-based.
            cols        (int)   Number of cols, 0-based.
            name        (str)   Hardware's name
            backend     (str)   ID of the backend
            form_factor (str)   ID of the form factor
            serial      (str)   Hardware's serial number
        """
        self.rows = rows
        self.cols = cols
        self.name = name
        self.backend = backend
        self.form_factor = form_factor

    def rgb_to_hex(self, red, green, blue):
        """
        Converts a RGB value to a hex colour string.

        Input:  (0, 255, 0)
        Output: "#00FF00"
        """
        return common.rgb_to_hex([red, green, blue])

    def hex_to_rgb(self, value):
        """
        Converts a HEX colour string to a RGB string.

        Input:  "#FF0000"
        Output: [255, 0, 0]
        """
        return common.hex_to_rgb(value)

    def set(self, x, y, red, green, blue):
        """
        Dummy implementation for the backend to set an LED position to the
        specified red, green and blue values for drawing later.

        The X and Y positions should be 0-based.

        Input:  (x, y, red, green, blue)
        """
        raise NotImplementedError

    def draw(self):
        """
        Dummy implementation for the backend to submit the new matrix to the
        hardware.
        """
        raise NotImplementedError

    def clear(self):
        """
        Dummy implementation for the backend to clear the matrix, essentially
        turning off all the LEDs.
        """
        raise NotImplementedError

    def brightness(self, percent):
        """
        Dummy implementation for the backend to set the brightness of all the
        LEDs. Could be used for fade effects.

        Input: percent (int between 0-100)
        """
        raise NotImplementedError
