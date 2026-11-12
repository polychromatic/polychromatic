import polychromatic.base as base
import polychromatic.bulkapply as bulkapply
from polychromatic.backends._backend import Backend

import unittest


class _FakeMiddleman(object):
    """
    Just enough of a middleman to hand BulkApplyOptions a list of devices.
    """
    def __init__(self, devices):
        self._devices = devices

    def get_devices(self):
        return self._devices


def _make_device(serial, zones):
    """
    Build a device whose zones offer the given effects.

    zones: dict of {zone_id: [effect uids]}
    """
    device = Backend.DeviceItem()
    device.serial = serial
    device.name = serial
    device.zones = []
    for zone_id, uids in zones.items():
        zone = Backend.DeviceItem.Zone()
        zone.zone_id = zone_id
        for uid in uids:
            option = Backend.EffectOption()
            option.uid = uid
            option.label = uid.capitalize()
            zone.options.append(option)
        device.zones.append(zone)
    return device


class TestBulkApplyEffects(unittest.TestCase):
    """
    Test which "Apply to All" effects are flagged as not available on every device.
    """
    @classmethod
    def setUpClass(self):
        self.base = base.PolychromaticBase()
        self.base.init_base("", [])

    def _labels(self, devices):
        options = bulkapply.BulkApplyOptions(_FakeMiddleman(devices))
        return {effect.value: effect.label for effect in options.effects}, options.mix_match

    def test_effect_on_all_devices_is_not_flagged(self):
        labels, mix_match = self._labels([
            _make_device("KBD", {"main": ["spectrum", "wave"]}),
            _make_device("MAT", {"main": ["spectrum", "wave"]}),
        ])
        self.assertEqual(labels["wave"], "Wave")
        self.assertFalse(mix_match)

    def test_effect_missing_on_one_device_is_flagged(self):
        labels, mix_match = self._labels([
            _make_device("KBD", {"main": ["spectrum", "wave"]}),
            _make_device("MAT", {"main": ["spectrum"]}),
        ])
        self.assertEqual(labels["wave"], "Wave*")
        self.assertEqual(labels["spectrum"], "Spectrum")
        self.assertTrue(mix_match)

    def test_multi_zone_device_counts_once(self):
        """
        A mouse with wave on four zones must not make up for a mousemat
        that has no wave at all (4 zones + 1 keyboard >= 3 devices).
        """
        labels, mix_match = self._labels([
            _make_device("MAT", {"main": ["spectrum"]}),
            _make_device("MOUSE", {
                "logo": ["spectrum", "wave"],
                "scroll": ["spectrum", "wave"],
                "left": ["spectrum", "wave"],
                "right": ["spectrum", "wave"],
            }),
            _make_device("KBD", {"main": ["spectrum", "wave"]}),
        ])
        self.assertEqual(labels["wave"], "Wave*")
        self.assertEqual(labels["spectrum"], "Spectrum")
        self.assertTrue(mix_match)
