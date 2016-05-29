#!/usr/bin/env python3
#
#  Example script to enable the macro keys.
#

import razer.daemon_dbus
daemon = razer.daemon_dbus.DaemonInterface()
daemon.marco_keys(True)
