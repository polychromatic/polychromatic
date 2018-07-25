#!/usr/bin/env python3

"""
    Module for managing, manipulating and submitting
    application profiles to the keyboard.
"""
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2015-2018 Luke Horwell <code@horwell.me>
#               2015-2016 Terry Cain <terry@terrys-home.co.uk>

import os
from shutil import copyfile

version = 1

try:
    # Relative copy
    import pylib.preferences as pref
except ImportError:
    # Installed to system
    import polychromatic.preferences as pref
except:
    print("Unable to import preferences module!")
    exit(1)

path = pref.Paths()

class AppProfiles(object):
    def __init__(self):
        # For tracking which UUID is loaded in memory.
        self.selected_uuid = None

        # For temporarily storing file changes in memory.
        self.memory = {}

    def backup_profile(self, uuid):
        """
        Retain a copy of the profile on file system when making changes.
        """
        file_profile = os.path.join(path.profile_folder, uuid + '.json')
        file_backup  = os.path.join(path.profile_backups, uuid + '.json')

        if os.path.exists(file_backup):
            os.remove(file_backup)
        copyfile(file_profile, file_backup)

    def remove_profile(self, uuid):
        """
        Delete profile from file system.
        """
        file_profile = os.path.join(path.profile_folder, uuid + '.json')
        file_backup  = os.path.join(path.profile_backups, uuid + '.json')

        if os.path.exists(file_profile):
            os.remove(file_profile)
        if os.path.exists(file_backup):
            os.remove(file_backup)

    # Returns a UUID for application to use.
    def new_profile(self):
        """
        Create profile on the file system.
        """
        uuid = pref.generate_uuid()
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

    def load_profile(self, uuid):
        """
        Load profile from file system and return its data and store in module's memory.
        """
        profile_path = os.path.join(path.profile_folder, uuid + ".json")
        self.memory = pref.load_file(profile_path)
        return(self.memory)

    def save_profile_from_memory(self, uuid):
        """
        Commit profile from module memory to file system.
        """
        self.backup_profile(uuid)
        profile_path = os.path.join(path.profile_folder, uuid + '.json')
        data = self.memory
        pref.save_file(profile_path, data)

    # If the value should be written to memory, then do not use this function.
    def set_metadata(self, uuid, key, value):
        """
        Set meta data for a particular profile, then save immediately.
        """
        # uuid  = string of UUID filename
        # key   = group, e.g. "name"
        # value = what to set, e.g. "Test Application"
        self.backup_profile(uuid)
        profile_path = os.path.join(path.profile_folder, uuid + '.json')
        newdata = pref.load_file(profile_path)
        newdata[key] = value
        pref.save_file(profile_path, newdata)

    def list_profiles(self):
        """
        Returns a sorted list of profiles in the folder.
        """
        # Includes the JSON extension.
        dir_listing = os.listdir(path.profile_folder)
        profiles = []

        # Sort the profiles A-Z.
        sorted_names = {}
        for filename in dir_listing:
            uuid = filename[:-5] # Strip .json
            data = self.load_profile(os.path.join(path.profile_folder, uuid))
            try:
                human_name = data["name"]
            except:
                print("Profile UUID corrupt: " + str(uuid))
                continue
            sorted_names[human_name] = int(uuid)

        sorted_list = []
        for human_name in sorted(sorted_names):
            uuid = str(sorted_names[human_name])
            sorted_list.append(uuid)

        return(sorted_list)

    def send_profile_to_keyboard(self, kbd_obj, data):
        """
        Load a profile and keyboard.
        """
        for row in range(0, kbd_obj.fx.advanced.rows):
            for col in range(0, kbd_obj.fx.advanced.cols):
                try:
                    kbd_obj.fx.advanced.matrix[row, col] = data["rows"][str(row)][col]
                except Exception:
                    print("Matrix has no data: x={0} y={1}".format(str(row), str(col)))
                    pass
        kbd_obj.fx.advanced.draw()

    def send_profile_from_file(self, kbd_obj, uuid):
        """
        Load a profile and send it to the keyboard.
        """
        profile_path = os.path.join(path.profile_folder, uuid + ".json")
        data = pref.load_file(profile_path)
        self.send_profile_to_keyboard(kbd_obj, data)

    def get_metadata(self, uuid):
        """
        Returns a dictonary containing the metadata for a profile.
        """
        data = self.load_profile(uuid)
        return {
            "name": data.get("name", "Unknown"),
            "icon": data.get("icon", "../img/ui/generic-application.svg")
        }
