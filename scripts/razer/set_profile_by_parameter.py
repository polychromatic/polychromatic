#!/usr/bin/env python3
#
#  A small utility to load a profile from a script.
#
#  By: (C) 2016, Gian Uberto "saint" Lauri <saint@eng.it>
#

import sys
import razer.daemon_dbus
import polychromatic.profiles

# Initialise Profiles,
daemon = razer.daemon_dbus.DaemonInterface()
profiles = polychromatic.profiles.Profiles(daemon)

# Dirty and minimal command line handling. We need to get just the
# profile name, no options at all. This loop builds up the name trying
# to handle blanks within. We could just take argv[1] and force the
# use of the quotes (single or double) to handle profiles like "saint
# own keyboard"
profilename=""
sep=""
for argo in sys.argv[1:]:
  profilename+=sep+argo
  sep=" "
  
# and this line does all the magic. Free software: sitting on the
# shoulders of a giant...
profiles.activate_profile_from_file(profilename)

