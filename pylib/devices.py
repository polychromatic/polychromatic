#!/usr/bin/env python3

"""
    Bindings between the UI controls and the actual driver.
"""
# Polychromatic is licensed under the GPLv2.
# Copyright (C) 2015-2016 Luke Horwell <lukehorwell37+code@gmail.com>

class Drivers(object):
    class Razer():
        import razer.daemon_dbus
        import razer.keyboard
        daemon = razer.daemon_dbus.DaemonInterface()

        """
            Set brightness of device

            ui:     razer.set_brightness
            parm:   [value 0-255]
        """
        set_brightness = daemon.set_brightness

        """
            Set current effect

            ui:     razer.set_effect
            parms:  'none'
                    'spectrum'
                    'wave', [direction, int 0-2]
                    'reactive', [reactive_speed, 1-3], [red, 0-255], [green, 0-255], [blue, 0-255]
                    'breath', [red, 0-255], [green, 0-255], [blue, 0-255], [red, 0-255], [green, 0-255], [blue, 0-255]
                    'static', [red, 0-255], [green, 0-255], [blue, 0-255]
        """
        set_effect = daemon.set_effect


        """
            Turn on/off macro keys

            ui:     razer.set_macro_keys
            parm:   [bool]
        """
        set_macro_keys = daemon.marco_keys


        """
            Turn on/off game mode

            ui:     razer.set_game_mode
            parm:   [bool]
        """
        set_game_mode = daemon.game_mode


""" Peripherals that are compatible with the Polychromatic program. """
class Devices(object):
    detected = []
    database = {
        "1532:0203": {
            "manufacturer": "Razer",
            "device_name": "BlackWidow Chroma",
            "ui_controls": ['razer_brightness', 'razer_effects', 'razer_gamemode', 'razer_macro', 'razer_profiles'],
            "bindings": Drivers.Razer
        }
    }

    def detect_devices():
        # FIXME: This is a dummy implementation.
        detected = []
        print('fixme: dummy, not yet implemented: Devices.detect_devices')
        print('Found: [1532:0203] Razer BlackWidow Chroma')
        detected.append(Devices.RazerBlackWidowChromaDummy)
