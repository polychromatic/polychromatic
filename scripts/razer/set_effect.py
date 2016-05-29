#!/usr/bin/env python3
#
#  Example script to set effects of the keyboard.
#

import razer.daemon_dbus
daemon = razer.daemon_dbus.DaemonInterface()

# Accepts the following (and additional parameters):
#
#   No Effect       'none'
#   Spectrum        'spectrum'
#   Wave            'wave'  [direction 0-2]
#                            0 = None
#                            1 = Right
#                            2 = Left
#   Reactive        'reactive', [speed, 1-3], [red, 0-255], [green, 0-255], [blue, 0-255]
#                                1 = Slow
#                                2 = Medium
#                                3 = Fast
#   Breath          'breath', [red, 0-255], [green, 0-255], [blue, 0-255], [red, 0-255], [green, 0-255], [blue, 0-255]
#   Static          'static', [red, 0-255], [green, 0-255], [blue, 0-255]

daemon.set_effect('')
