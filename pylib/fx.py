#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2021 Luke Horwell <code@horwell.me>
#
"""
This module is a higher level interface for custom effects that transparently
connects to the supported backend, regardless of driver.

This is used internally for rendering software effects as well as "scripted"
effects written by users.

To achieve effects, colours may be converted between different colour spaces:
    - RGB (Red, Green, Blue)            -> using hex codes for storage
    - HSV (Hue, Saturation, Value)      -> for colour intensity
    - HSL (Hue, Saturation, Lightness)  -> for black/white intensity
"""

import colour
import math

from . import common


class FX(object):
    """
    Backends use this class for the get_device_object() functionality. This
    is for supporting individual LED lighting where supported by the device.

    This object is the 'fx' object used in custom effect scripts as well as
    Polychromatic internally for software effects.

    All classes stubbed as NotImplementedError should be implemented.
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

    #######################################################
    # To be implemented by the backend
    #######################################################
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
        LEDs. Could be used for fade effects globally.

        Input: percent (int between 0-100)
        """
        raise NotImplementedError

    #######################################################
    # Helper functions for scripting effects
    #######################################################
    def rgb_to_hex(self, red, green, blue):
        """
        Converts the specified RGB values into a HEX string.

        Input:  (0, 255, 0)
        Output: "#00FF00"
        """
        return common.rgb_to_hex([red, green, blue])

    def hex_to_rgb(self, value):
        """
        Converts a HEX colour string to a RGB list.

        Input:  "#FF0000"
        Output: [255, 0, 0]
        """
        return common.hex_to_rgb(value)

    def saturate_hex(self, hex_value, amount):
        """
        Change the saturation of a colour by a relative amount (-1 to 1) and
        return the new colour hex value.

        Params:
            hex_value   (str)   Hex value
            amount      (float) Relative amount to saturate (-1 to 1)
        """
        c = colour.Color(hex_value)

        # Value must be between 0 and 1
        new_value = c.get_saturation() + amount
        if new_value < 0:
            new_value = 0
        elif new_value > 1:
            new_value = 1

        c.set_saturation(new_value)
        return c.get_hex_l()

    def saturate_rgb(self, rgb, amount):
        """
        Alias to saturate_hex(), but inputs/outputs RGB values.

        Params:
            rgb         (list)  List of RGB integers [red, green, blue]
            amount      (float) Relative amount to saturate (-1 to 1)
        """
        return self.hex_to_rgb(self.saturate_hex(self.rgb_to_hex(rgb[0], rgb[1], rgb[2]), amount))

    def hue_hex(self, hex_value, amount):
        """
        Change the hue of a colour by a relative amount (-1 to 1) and
        return the new colour hex value.

        Params:
            hex_value   (str)   Hex value
            amount      (float) Relative amount to cycle hue (-1 to 1)
        """
        c = colour.Color(hex_value)
        c.set_hue(c.get_hue() + amount)
        return c.get_hex_l()

    def hue_rgb(self, rgb, amount):
        """
        Alias to hue_hex(), but inputs/outputs RGB values.

        Params:
            rgb         (list)  List of RGB integers [red, green, blue]
            amount      (float) Relative amount to cycle hue (-1 to 1)
        """
        return self.hex_to_rgb(self.hue_hex(self.rgb_to_hex(rgb[0], rgb[1], rgb[2]), amount))

    def lightness_hex(self, hex_value, amount):
        """
        Change the lightness of a colour by a relative amount (-1 to 1) and
        return the new colour hex value.

        Params:
            hex_value   (str)   Hex value
            amount      (float) Relative amount to cycle hue (-1 to 1)
        """
        c = colour.Color(hex_value)

        # Value must be between 0 and 1
        new_value = c.get_luminance() + amount
        if new_value < 0:
            new_value = 0
        elif new_value > 1:
            new_value = 1

        c.set_luminance(new_value)
        return c.get_hex_l()

    def lightness_rgb(self, rgb, amount):
        """
        Alias to lightness_hex(), but inputs/outputs RGB values.

        Params:
            rgb         (list)  List of RGB integers [red, green, blue]
            amount      (float) Relative amount to cycle hue (-1 to 1)
        """
        return self.hex_to_rgb(self.lightness_hex(self.rgb_to_hex(rgb[0], rgb[1], rgb[2]), amount))

    def gradient(self, colours=[], steps=0):
        """
        Return a list of colours that builds a gradient from start to finish
        using the specified colours (equal distance between each step)

        For best results, make sure the steps are divisable by the number
        of colours. Otherwise, you may will get more colours then expected.

        For example, ["#000000", "#FFFFFF"] (black, white) across 10 steps
        makes the 5th colour the midpoint (grey)

        Params:
            colours     (list)  List of colours for the gradient
            steps       (int)   Total colours to return for rendering the gradient
        """
        if len(colours) < 2:
            raise ValueError("Insufficient colours! At least 2 required to generate gradient.")

        output = []
        steps_between_stops = math.ceil(steps / (len(colours) - 1))

        for index, item in enumerate(colours):
            try:
                next_colour = colours[index + 1]
            except IndexError:
                # This is the last colour
                continue

            c = colour.Color(item)
            for c2 in list(c.range_to(next_colour, steps_between_stops)):
                output.append(c2.get_hex_l())

        return output
