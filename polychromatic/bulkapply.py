# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2022 Luke Horwell <code@horwell.me>
"""
Handles the bulk "Apply to All" options to apply settings to all devices at once.
"""
from .backends._backend import Backend
from . import common
from . import middleman as mn
from . import preferences


class BulkOption(object):
    """
    An object representing a selectable 'apply to all' button.
    """
    def __init__(self, options=[], middleman=mn.Middleman, label="", icon="", value=None):
        self.options = options
        self.middleman = middleman
        self.label = label
        self.icon = icon
        self.value = value

    def apply(self):
        raise NotImplementedError


class _BulkBrightness(BulkOption):
    def apply(self, a=None):
        # 'a' is an object passed from Tray Applet. Unnecessary.
        for option in self.options:
            if isinstance(option, Backend.SliderOption):
                option.apply(self.value)
            elif isinstance(option, Backend.ToggleOption):
                option.apply(True if self.value > 0 else False)


class _BulkEffect(BulkOption):
    def apply(self, a=None):
        # 'a' is an object passed from Tray Applet. Unnecessary.
        for option in self.options:
            if not option.uid == self.value:
                continue
            if option.parameters:
                default_param = self.middleman.get_default_parameter(option)
                option.apply(default_param.data)
            else:
                option.apply()


class _BulkColour(BulkOption):
    def apply(self, a=None):
        # 'a' is an object passed from Tray Applet. Unnecessary.
        for device in self.options:
            device.refresh()
            try:
                self.middleman.set_colour_for_active_effect_device(device, self.value)
            except IndexError:
                # Not supported for this effect
                pass


class BulkApplyOptions(object):
    """
    Assembles and processes "Apply to All" options for applying a brightness,
    effect or colour to all devices at once. The Controller and tray applet
    interfaces will interpret this data.
    """
    def __init__(self, middleman=mn.Middleman):
        self.middleman = middleman
        self.devices = middleman.get_devices()

        # Stores BulkOption() objects
        self.brightness = []
        self.effects = []
        self.colours = []

        # Some effects not available for every device?
        self.mix_match = False

        self.refresh()

    def refresh(self):
        """
        Analyze devices and populate the bulk objects.
        """
        brightness = []
        effects = []
        has_colours = False

        for device in self.devices:
            for zone in device.zones:
                for option in zone.options:
                    if option.uid == "brightness":
                        brightness.append(option)
                    elif isinstance(option, Backend.EffectOption):
                        effects.append(option)
                    if option.colours_required > 0:
                        has_colours = True

        self._populate_bulk_brightness(brightness)
        self._populate_bulk_effects(effects)
        self._populate_bulk_colours(has_colours)

    def _populate_bulk_brightness(self, options):
        """
        Builds new BulkOption() objects that apply a brightness across all devices and zones.

        NOTE: The values in this function are hardcoded for OpenRazer (0-100). More work
        is required if another backend handles 'brightness' differently (e.g. 0-255)
        """
        self.brightness = []

        for value in [0, 25, 50, 75, 100]:
            label = str(value) + "%"
            icon = common.get_icon("params", str(value))
            self.brightness.append(_BulkBrightness(options, self.middleman, label, icon, value))

    def _populate_bulk_effects(self, options):
        """
        Builds new BulkOption() objects that apply an effect across all devices and zones.
        """
        self.effects = []
        uids = []
        occurrences = {}
        effects = {}

        for option in options:
            try:
                occurrences[option.uid] += 1
            except KeyError:
                occurrences[option.uid] = 1

            # Already added item?
            if option.uid in uids:
                continue

            label = option.label
            icon = option.icon
            effects[option.uid] = _BulkEffect(options, self.middleman, label, icon, option.uid)
            uids.append(option.uid)

        # If the effect can't apply to all devices, add an asterisk
        total_devices = len(self.devices)
        for uid in occurrences.keys():
            if occurrences[uid] < total_devices:
                effects.get(uid).label += "*"
                self.mix_match = True

        for option in effects.keys():
            self.effects.append(effects[option])

    def _populate_bulk_colours(self, has_colours):
        """
        Builds new BulkOption() objects that apply a colour across all devices and zones.
        """
        self.colours = []

        if not has_colours:
            return

        # FIXME: Refactoring required: Not passing _
        colours = preferences.get_colour_list(None)
        for colour in colours:
            colour_hex = colour["hex"]
            label = colour["name"]

            # FIXME: Finish refactoring for function
            icon = common.generate_colour_bitmap(None, colour_hex)
            self.colours.append(_BulkColour(self.devices, self.middleman, label, icon, colour_hex))

