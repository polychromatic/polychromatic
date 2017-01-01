#!/usr/bin/env python3

"""
    Module for managing, manipulating and submitting
    application profiles to the keyboard.
"""
# Polychromatic is licensed under the GPLv2.
# Copyright (C) 2015-2017 Luke Horwell <luke@ubuntu-mate.org>
#               2015-2016 Terry Cain <terry@terrys-home.co.uk>

import os
import time
from shutil import copyfile

import polychromatic.preferences as pref
path = pref.Paths()

class AppProfiles(object):
    def __init__(self):
        # For tracking which UUID is loaded in memory.
        self.selected_uuid = None

        # For temporarily storing file changes in memory.
        self.memory = {}

    """ Retain a copy of the profile on file system when making changes """
    def backup_profile(self, uuid):
        file_profile = os.path.join(path.profile_folder, uuid + '.json')
        file_backup  = os.path.join(path.profile_backups, uuid + '.json')

        if os.path.exists(file_backup):
            os.remove(file_backup)
        copyfile(file_profile, file_backup)

    """ Delete profile from file system """
    def remove_profile(self, uuid):
        file_profile = os.path.join(path.profile_folder, uuid + '.json')
        file_backup  = os.path.join(path.profile_backups, uuid + '.json')

        if os.path.exists(file_profile):
            os.remove(file_profile)
        if os.path.exists(file_backup):
            os.remove(file_backup)

    """ Create profile on the file system """
    # Returns a UUID for application to use.
    def new_profile(self):
        uuid = str(int(time.time() * 1000000))
        self.selected_uuid = uuid
        filepath = os.path.join(path.profile_folder, uuid + '.json')

        template = {
            "name": "",
            "icon": "",
            "rows": {}
        }

        for row in range(0, 6):
            template["rows"][str(row)] = []
            for col in range(0, 22):
                template["rows"][str(row)].append([0, 0, 0])

        pref.save_file(filepath, template)
        return str(uuid)

    """ Load profile from file system and return its data and store in module's memory """
    def load_profile(self, uuid):
        profile_path = os.path.join(path.profile_folder, uuid + ".json")
        self.memory = pref.load_file(profile_path)
        return(self.memory)

    """ Commit profile from module memory to file system """
    def save_profile_from_memory(self, uuid):
        self.backup_profile(uuid)
        profile_path = os.path.join(path.profile_folder, uuid + '.json')
        data = self.memory
        pref.save_file(profile_path, data)

    """ Set meta data for a particular profile, then save immediately. """
    # If the value should be written to memory, then do not use this function.
    def set_metadata(self, uuid, key, value):
        # uuid  = string of UUID filename
        # key   = group, e.g. "name"
        # value = what to set, e.g. "Test Application"
        self.backup_profile(uuid)
        profile_path = os.path.join(path.profile_folder, uuid + '.json')
        newdata = pref.load_file(profile_path)
        newdata[key] = value
        pref.save_file(profile_path, newdata)

    """ Returns the list of profiles in the folder. """
    def list_profiles(self):
        # Including the JSON extension.
        dir_listing = os.listdir(path.profile_folder)
        profiles = []
        for filename in dir_listing:
            profiles.append(filename.split('.json')[0])
        return(profiles)

    """ Load a profile and keyboard. """
    def send_profile_to_keyboard(self, kbd_obj, data):
        for row in range(0, 6):
            for col in range(0, 22):
                kbd_obj.fx.advanced.matrix[row, col] = data["rows"][str(row)][col]
        kbd_obj.fx.advanced.draw()

    """ Load a profile and send it to the keyboard. """
    def send_profile_from_file(self, kbd_obj, uuid):
        profile_path = os.path.join(path.profile_folder, uuid + '.json')
        data = pref.load_file(profile_path)
        self.send_profile_to_keyboard(kbd_obj, data)
