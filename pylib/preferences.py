#!/usr/bin/env python3

"""
    Module for interfacing preferences stored by
    Polychromatic's applications.
"""
# Polychromatic is licensed under the GPLv2.
# Copyright (C) 2015-2016 Luke Horwell <lukehorwell37+code@gmail.com>

import os
import json
import shutil

version = 2

# For default preferences, please see:
#   https://github.com/lah7/polychromatic/wiki/Preferences-JSON-Structure

class Paths(object):
    """ Directories """
    root = os.path.join(os.path.expanduser('~'), '.config', 'polychromatic')
    profile_folder = os.path.join(root, 'profiles')
    profile_backups = os.path.join(root, 'backups')

    """ Files """
    preferences = os.path.join(root, 'preferences.json')
    profiles = os.path.join(root, 'profiles.json')

path = Paths()

class Preferences(object):
    """ Initialise module """
    def __init__(self):
        # Create folders if they do not exist.
        if not os.path.exists(path.root):
            print('Configuration folder does not exist. Creating: ', path.root)
            for folder in [path.root, path.profiles, path.backups]:
                os.makedirs(path)

    """ Loads a save file from disk. """
    def load_file(self, filepath):
        # Does it exist?
        if not os.path.exists(filepath):
            self.init_config(filepath)

        # Load data into memory.
        try:
            with open(filepath) as stream:
                data = json.load(stream)
        except Exception as e:
            print("Failed to load '{0}'.\nException: {1}".format(filepath, str(e)))
            self.init_config(filepath)

        # Check configuration version if reading the preferences.
        if filepath == path.preferences:
            try:
                config_version = int(data['config_version'])
            except KeyError:
                data['config_version'] = version
                config_version = version

            # Is the software newer and the configuration old?
            if version > config_version:
                print('Your Polychromatic configuration will be updated.')
                print("Save format v.{0} => v.{1}".format(config_version, version))
                upgrade_old_pref(config_version)

            # Is the config newer then the software? Wicked time travelling!
            if config_version > version:
                print('\n******** WARNING: Your preferences file is newer then the module! ********')
                print('This could cause undesired glitches in applications. Consider updating the Python modules.')
                print('    Your Config Version:     v.' + str(config_version))
                print('    Software Config Version: v.' + str(version))
                print(' ')

        # Passes data back to the variable
        return(data)

    """ Commit the save file to disk. """
    def save_file(self, filepath, newdata):

        # Write configuration version if the preferences.
        if filepath == path.preferences:
            newdata['config_version'] = version

        # Write new data to specified file.
        if os.access(filepath, os.W_OK):
            f = open(filepath, "w+")
            f.write(json.dumps(newdata))
            f.close()
        else:
            print(" ** Cannot write to file: " + filepath)

    """ Write new data. """
    def set(self, group, setting, value, filepath=None):
        # Example: (self, "editor", "live_preview", True)
        #          (self, "24", "name", "Test Program", "profiles.json")

        # If haven't explicitly stated which file, assume preferences.
        if filepath == None:
            filepath = path.preferences

        data = self.load_file(filepath)

        # Create group if non-existent.
        try:
            data[group]
        except:
            data[group] = {}

        # Write new setting and save.
        try:
            data[group][setting] = value
            self.save_file(filepath, data)
        except:
            print(" ** Failed to write '{0}' for item '{1}' in group '{2}'!".format(value, setting, group))

    """ Read data from memory. """
    def get(self, group, setting, default_value="", filepath=None):
        # Example: (self, "editor", "live_preview")
        # Example: (self, "editor", "live_preview", "True")
        #          (self, "12", "name", "Unknown", "profiles.json")

        # If haven't explicitly stated which file, assume preferences.
        if filepath == None:
            filepath = path.preferences

        data = self.load_file(filepath)

        # Read data from preferences.
        try:
            value = data[group][setting]
            return value
        except:
            # Should it be non-existent, return a fallback option.
            print(" ** Preference '{0}' in '{1}' non-existent. Using default '{2}' instead.".format(group, setting, default_value))
            self.set(group, setting, default_value)
            return default_value

    """ Prepares configuration for first time usage. """
    def init_config(self, filepath):
        try:
            newdata = json.dumps("{}")
            print(' ** Creating new data file...')
            if os.path.exists(filepath):
                print(' ** Existing preferences file is corrupt or being forced overwritten.')
                os.rename(filepath, filepath+'.bak')
                print(' ** Successfully backed up previous preferences JSON file.')

            self.save_file(filepath, newdata)
            print(' ** New configuration ready: ' + filepath)

        except Exception as e:
            # Couldn't create the default configuration.
            print(' ** Failed to write default preferences.')
            print(' ** Exception: ', str(e))

    """ Erases the configuration stored on disk. """
    def clear_config(self):
        print(' ** Deleting configuration folder "' + path.root + '"...')
        shutil.rmtree(path.root)
        print(' ** Successfully deleted configuration.')

    """ Updates the configuration from previous versions. """
    def upgrade_old_pref(self, config_version):
        return


