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

version = 3

# For default preferences, please see:
#   https://github.com/lah7/polychromatic/wiki/Preferences-JSON-Structure

################################################################################

class Paths(object):
    """ Directories """
    root = os.path.join(os.path.expanduser('~'), '.config', 'polychromatic')
    profile_folder = os.path.join(root, 'profiles')
    profile_backups = os.path.join(root, 'backups')

    """ Files """
    preferences = os.path.join(root, 'preferences.json')
    profiles = os.path.join(root, 'profiles.json')

    """ Data Source """
    @staticmethod
    def get_data_source(program_path):
        if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(program_path), 'data/'))):
            path = os.path.abspath(os.path.join(os.path.dirname(program_path), 'data/'))
        elif os.path.exists('/usr/share/polychromatic/'):
            path = '/usr/share/polychromatic/'
        else:
            print("Data directory cannot be located. Exiting.")
            exit(1)
        return path

path = Paths()

################################################################################

""" Loads a save file from disk. """
def load_file(filepath, no_version_check=False):
    # Does it exist?
    if os.path.exists(filepath):
        # Load data into memory.
        try:
            with open(filepath) as stream:
                data = json.load(stream)
        except Exception as e:
            print(" ** Failed to load '{0}'.\n **** Exception: {1}".format(filepath, str(e)))
            init_config(filepath)
    else:
        init_config(filepath)
        data = {}
        no_version_check = True

    # Check configuration version if reading the preferences.
    if filepath == path.preferences and no_version_check == False:
        try:
            config_version = int(data['config_version'])
        except KeyError:
            data['config_version'] = version
            config_version = version

        # Is the software newer and the configuration old?
        if version > config_version:
            upgrade_old_pref(config_version)

        # Is the config newer then the software? Wicked time travelling!
        if config_version > version:
            print('\n******** WARNING: Your preferences file is newer then the module! ********')
            print(' ** This could cause undesired glitches in applications. Consider updating the Python modules.')
            print('      Your Config Version:     v.' + str(config_version))
            print('      Software Config Version: v.' + str(version))
            print(' ')

    # Passes data back to the variable
    return(data)

""" Commit the save file to disk. """
def save_file(filepath, newdata):

    # Write configuration version if the preferences.
    if filepath == path.preferences:
        newdata['config_version'] = version

    # Create file if it doesn't exist.
    if not os.path.exists(filepath):
        open(filepath, 'w').close()

    # Write new data to specified file.
    if os.access(filepath, os.W_OK):
        f = open(filepath, "w+")
        f.write(json.dumps(newdata))
        f.close()
    else:
        print(" ** Cannot write to file: " + filepath)

""" Write new data. """
def set(group, setting, value, filepath=None):
    # Example: ("editor", "live_preview", True)
    #          ("24", "name", "Test Program", "/path/to/profiles.json")

    # If haven't explicitly stated which file, assume preferences.
    if filepath == None:
        filepath = path.preferences

    data = load_file(filepath)

    # Create group if non-existent.
    try:
        data[group]
    except:
        data[group] = {}

    # Write new setting and save.
    try:
        data[group][setting] = value
        save_file(filepath, data)
    except:
        print(" ** Failed to write '{0}' for item '{1}' in group '{2}'!".format(value, setting, group))

""" Read data from memory. """
def get(group, setting, default_value="", filepath=None):
    # Example: ("editor", "live_preview", "True")
    #          ("12", "name", "Unknown", "/path/to/profiles.json")

    # If no file explicitly stated, assume preferences.
    if filepath == None:
        filepath = path.preferences

    data = load_file(filepath)

    # Read data from preferences.
    try:
        value = data[group][setting]
        return value
    except:
        # Should it be non-existent, return a fallback option.
        print(" ** Preference '{0}' in '{1}' non-existent. Using default '{2}' instead.".format(setting, group, default_value))
        set(group, setting, default_value)
        return default_value

""" Read a group of data as a list. """
def get_group(group, filepath):
    # Must explictly state the file path, and the group (or "root")

    data = load_file(filepath)

    try:
        if group == 'root':
            listdata = list(data.keys())
        else:
            listdata = list(data[group].keys())
    except:
        print(" ** Failed to retrieve data from group '{0]' from file '{1}'".format(group, os.path.basename(filepath)))
        return []

    return listdata

""" Prepares configuration for first time usage. """
def init_config(filepath):
    try:
        # Backup if the JSON was invalid.
        if os.path.exists(filepath):
            print(' ** JSON File corrupt and will be discarded: ' + filepath)
            os.rename(filepath, filepath + '.bak')
            print(' ** This faulty JSON file has been backed up.')

        # Touch new file
        save_file(filepath, {})
        print(' ** New configuration ready: ' + filepath)

    except Exception as e:
        # Couldn't create the default configuration.
        print(' ** Failed to write default preferences.')
        print(' **** Exception: ', str(e))

""" Erases the configuration stored on disk. """
def clear_config():
    print(' ** Deleting configuration folder "' + path.root + '"...')
    shutil.rmtree(path.root)
    print(' ** Successfully deleted configuration.')

""" Updates the configuration from previous versions. """
def upgrade_old_pref(config_version):
    print(" ** Upgrading configuration from v{0} to v{1}...".format(config_version, version))
    if config_version <= 3:
        # *** "chroma_editor" group now "editor" ***
        data = load_file(path.preferences, True)
        data["editor"] = data["chroma_editor"]
        data.pop("chroma_editor")
        save_file(path.preferences, data)

        # *** Profiles now indexed, not based on file names. ***
        import time
        index = {}
        for profile in os.listdir(path.profile_folder):
            uid = int(time.time() * 1000000)
            old = os.path.join(path.profile_folder, profile)
            new = os.path.join(path.profile_folder, str(uid))
            os.rename(old, new)
            index[str(uid)] = {}
            index[str(uid)]["name"] = profile
        save_file(path.profiles, index)

        # *** Clear backups ***
        shutil.rmtree(path.profile_backups)
        os.mkdir(path.profile_backups)

    print(" ** Configuration successfully upgraded.")

""" Initialisation """
# Create folders if they do not exist.
for folder in [path.root, path.profile_folder, path.profile_backups]:
    if not os.path.exists(folder):
        print(' ** Configuration folder does not exist. Creating: ', folder)
        os.makedirs(folder)

# Create preferences if non-existent.
for json_path in [path.preferences, path.profiles]:
    if not os.path.exists(json_path):
        init_config(json_path)
