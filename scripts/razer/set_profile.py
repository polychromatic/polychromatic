#!/usr/bin/env python3
#
#  Example script to load a Polychromatic profile
#

import razer.daemon_dbus
import polychromatic.profiles

# Prepare the Razer daemon
daemon = razer.daemon_dbus.DaemonInterface()

# Load the Polychromatic profile and send to daemon
profiles = polychromatic.profiles.ChromaProfiles(daemon)
profiles.activate_profile_from_file("Name of Profile")
