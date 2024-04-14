import unittest

import polychromatic.fx as fx


class TestFX(unittest.TestCase):
    """
    Test the FX 'helper' API calls for effects to use. Excludes device-specific features.
    """
    @classmethod
    def setUpClass(self):
        self.fx = fx.FX()

    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_rgb_to_hex(self):
        self.assertEqual(self.fx.rgb_to_hex(64, 128, 255), "#4080FF", "Cannot convert RGB to HEX")

    def test_hex_to_rgb(self):
        self.assertEqual(self.fx.hex_to_rgb("#ff8040"), [255, 128, 64], "Cannot convert HEX to RGB")

    def test_saturate_hex(self):
        # Saturate dull green to a brighter green
        self.assertEqual(self.fx.saturate_hex("#408040", 1).upper(), "#00C000", "Cannot saturate HEX value")

    def test_saturate_rgb(self):
        # Same as test above
        self.assertEqual(self.fx.saturate_rgb([64, 128, 64], 1), [0, 192, 0], "Cannot saturate RGB value")

    def test_hue_hex(self):
        # Change hue of red to the middle of the HSL colour graph (aqua)
        self.assertEqual(self.fx.hue_hex("#FF0000", 0.5).upper(), "#00FFFF", "Cannot hue HEX value")

    def test_hue_rgb(self):
        # Same as test above
        self.assertEqual(self.fx.hue_rgb([255, 0, 0], 0.5), [0, 255, 255], "Cannot hue RGB value")

    def test_lightness_hex(self):
        # Reduce lightness of black to grey
        self.assertEqual(self.fx.lightness_hex("#FFFFFF", -0.5).upper(), "#7F7F7F", "Cannot set lightness of HEX value")

    def test_lightness_rgb(self):
        # Similar test to above
        self.assertEqual(self.fx.lightness_rgb([0, 0, 0], 0.5), [127, 127, 127], "Cannot set lightness of RGB value")

    def test_gradient_2_colours(self):
        # Gradient from black to white, across 10 steps. Midpoint should be grey.
        gradient = self.fx.gradient(["#000000", "#FFFFFF"], 3)
        self.assertEqual(gradient[1].upper(), "#7F7F7F", "Cannot verify gradient is accurate")

    def test_gradient_3_colours(self):
        # Gradient from black to white to black, across 10 steps. Midpoint should be white.
        gradient = self.fx.gradient(["#000000", "#FFFFFF", "#000000"], 6)
        self.assertEqual(gradient[2].upper(), "#FFFFFF", "Cannot verify gradient is accurate")
