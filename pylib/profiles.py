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

import razer.daemon_dbus
import razer.keyboard
import polychromatic.preferences as pref
path = pref.Paths()


class Profiles(object):
    """ Profiles require the driver daemon. """
    def __init__(self, dbus_object):
        self.profiles = {}
        self.active_profile = None
        self.daemon = dbus_object
        self.load_profiles()

    """ Delete profile from file system """
    def remove_profile(self, uuid):
        # Determine where the files are.
        file_profile = os.path.join(path.profile_folder, uuid)
        file_backup  = os.path.join(path.profile_backups, uuid)

        # Delete them, if they exist.
        if os.path.exists(file_profile):
            os.remove(file_profile)
        if os.path.exists(file_backup):
            os.remove(file_backup)

        # Update profile index
        index = pref.load_file(path.profiles)
        index.pop(uuid)
        pref.save_file(path.profiles, index)

    """ Create profile on the file system """
    # Returns a UUID for application to use.
    def new_profile(self):
        uuid = str(int(time.time() * 1000000))
        self.active_uuid = uuid
        self.profiles[uuid] = razer.keyboard.KeyboardColour()

        index = pref.load_file(path.profiles)
        index[str(uuid)] = {}
        pref.save_file(path.profiles, index)
        return str(uuid)

    """ Set metadata for a profile in the index """
    def set_metadata(self, uuid, key, value):
        # uuid  = string of UUID filename
        # key   = group, e.g. "name"
        # value = what to set, e.g. "Test Application"
        index = pref.load_file(path.profiles)
        try:
            index[uuid]
        except KeyError:
            # Create group if it doesn't exist.
            index[uuid] = {}
        index[uuid][key] = value
        pref.save_file(path.profiles, index)

    def load_profiles(self):
        """
        Load profiles
        """
        profiles = os.listdir(path.profile_folder)

        for profile in profiles:
            keyboard = self.get_profile_from_file(profile)
            self.profiles[profile] = keyboard

    def set_active_profile(self, profile_name):
        """
        Set the active profile name

        :param profile_name: Profile name
        :type profile_name: str
        """
        if profile_name in self.profiles:
            self.active_profile = profile_name

    def get_active_profile(self):
        """
        Gets active profile, if one isnt active then the first profile is returned. If no
        profiles are loaded then an empty profile is returned

        :return: Keyboard object
        :rtype: razer.keyboard.KeyboardColour
        """

        profile = razer.keyboard.KeyboardColour()
        try:
            profile = self.profiles[self.active_profile]
        except KeyError:
            if len(list(self.profiles.keys())) > 0:
                profile = self.profiles[list(self.profiles.keys())[0]]
        return profile

    def get_active_profile_name(self):
        """
        Gets active profile

        :return: Profile name
        :rtype: str
        """
        return self.active_profile

    def get_profiles(self):
        """
        Get a list of profiles

        :return: List of profiles
        :rtype: list
        """
        return self.profiles.keys()

    def get_profile(self, profile_name):
        """
        Get a profile

        :param profile_name: Profile
        :type profile_name: str

        :return: Keyboard object
        :rtype: razer.keyboard.KeyboardColour
        """
        return self.profiles[profile_name]

    def save_profile(self, profile_name):

        profile_path = os.path.join(path.profile_folder, profile_name)

        # Backup if it's an existing copy, then erase original copy.
        if os.path.exists(profile_path):
            os.rename(profile_path, os.path.join(path.profile_backups, profile_name))

        with open(os.path.join(path.profile_folder, profile_name), 'wb') as profile_file:
            payload = self.profiles[profile_name].get_total_binary()
            profile_file.write(payload)

    def activate_profile_from_file(self, profile_name):
        print("Applying profile '{0}' ... ".format(profile_name))
        with open(os.path.join(path.profile_folder, profile_name), 'rb') as profile_file:
            payload = profile_file.read()
            keyboard = razer.keyboard.KeyboardColour()
            keyboard.get_from_total_binary(payload)
            self.daemon.set_custom_colour(keyboard)

    def activate_profile_from_memory(self):
        profile_name = self.get_active_profile_name()
        keyboard = self.get_active_profile()
        self.daemon.set_custom_colour(keyboard)
        print("Applying profile '{0}' from memory...".format(profile_name))

    def get_profile_from_file(self, profile_name):
        keyboard = razer.keyboard.KeyboardColour()
        with open(os.path.join(path.profile_folder, profile_name), 'rb') as profile_file:
            payload = profile_file.read()
            keyboard.get_from_total_binary(payload)

        return keyboard
