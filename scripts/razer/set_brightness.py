#!/usr/bin/env python3
#
#  Example script to set brightness of the keyboard.
#

import razer.daemon_dbus
daemon = razer.daemon_dbus.DaemonInterface()

# Accepts a value between 0 and 255.
#
#   0     0%    Off
#   128   50%   Half Lit
#   255   100%  Fully Lit

daemon.set_brightness(255)
