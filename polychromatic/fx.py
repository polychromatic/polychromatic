# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
"""
This module is a higher level interface for custom effects for devices that
support it, regardless of vendor.

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
    def __init__(self):
        self.name = "Unknown Device"
        self.form_factor_id = "unrecognised"
        self.rows = 0
        self.cols = 0

    #######################################################
    # To be implemented by the backend
    #   See also: _backend.DeviceItem.Matrix()
    #######################################################
    def init(self):
        """
        Prepare the device for custom frames. If unnecessary, this can be ignored.
        """
        return

    def set(self, x=0, y=0, red=255, green=255, blue=255):
        """
        Set a colour at the specified co-ordinate.
        """
        raise NotImplementedError

    def draw(self):
        """
        Send the data to the hardware to be displayed.
        """
        raise NotImplementedError

    def clear(self):
        """
        Reset all LEDs to an off state.
        """
        raise NotImplementedError

    def brightness(self, percent):
        """
        Set the global brightness of the LEDs. Could be used for fade effects globally.
        """
        raise NotImplementedError

    #######################################################
    # Functions for scripting
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
