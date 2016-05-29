#!/usr/bin/env python3
#
#  Example script to turn on or off game mode.
#

import razer.daemon_dbus
daemon = razer.daemon_dbus.DaemonInterface()
daemon.set_game_mode(True)
