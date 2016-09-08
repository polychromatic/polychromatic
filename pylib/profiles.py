#!/usr/bin/env python3

"""
    Module for managing, manipulating and submitting
    application profiles to the keyboard.
"""
# Polychromatic is licensed under the GPLv2.
# Copyright (C) 2015-2016 Luke Horwell <lukehorwell37+code@gmail.com>
#               2015-2016 Terry Cain <terry@terrys-home.co.uk>

import os
import time

import polychromatic.preferences as pref
path = pref.Paths()

class AppProfiles(object):
    """ Profiles require the driver daemon. """
    def __init__(self, rclient):
        self.selected_uuid = None
        self.rclient = rclient

    """ Delete profile from file system """
    def remove_profile(self, uuid):
        file_profile = os.path.join(path.profile_folder, uuid)
        file_backup  = os.path.join(path.profile_backups, uuid)

        if os.path.exists(file_profile):
            os.remove(file_profile)
        if os.path.exists(file_backup):
            os.remove(file_backup)

    """ Create profile on the file system """
    # Returns a UUID for application to use.
    def new_profile(self):
        uuid = str(int(time.time() * 1000000))
        self.selected_uuid = uuid
        filepath = os.path.join(path.profiles, uuid + ".json")

        template = {
            "name": "",
            "icon": "",
            "rows": {}
        }
        for row_no in range(0, 5):
            template["row"] = str(row_no)
            for col_no in range(0, 22):
                template["row"][col_no].append([0,0,0])

        pref.save_file(filepath, template)
        return str(uuid)

    """ Set meta data for a particular profile, then save immediately. """
    # If the value should be written to memory, then do not use this function.
    def set_metadata(self, uuid, key, value):
        # uuid  = string of UUID filename
        # key   = group, e.g. "name"
        # value = what to set, e.g. "Test Application"
        profile_path = os.path.join(path.profile_folder, uuid + '.json')
        newdata = pref.load_file(profile_path)
        newdata[key] = value
        pref.save_file(profile_path, newdata)

    """ Returns the list of profiles in the folder. """
    def list_profiles(self):
        # Including the JSON extension.
        profiles = os.listdir(path.profile_folder)
        return(profiles)

    """ Load a profile and keyboard. """
    def send_profile_to_keyboard(self, kbd_obj, data):
        for row in range(0, 6):
            for col in range(0, 22):
                kbd_obj.fx.advanced.matrix[row, col] = data["rows"][str(row)][col]
        kbd_obj.fx.advanced.draw()

    """ Load a profile and send it to the keyboard. """
    def send_profile_from_file(self, kbd_obj, uuid):
        # kbd_obj = Should be the
        profile_path = os.path.join(path.profile_folder, uuid + '.json')
        data = pref.load_file(profile_path)
        self.send_profile_to_keyboard(kbd_obj, data)
