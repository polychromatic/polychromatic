# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2016-2022 Luke Horwell <code@horwell.me>
"""
Module for determining where files are located.
"""
import os


class Paths():
    """
    Reference file/folder paths for data files, configuration and cache directories.
    """
    def __init__(self):
        # System-wide data
        self.data_dir = self.get_data_path()

        # Local data
        self.config = self.get_config_path()
        self.cache = self.get_cache_path()
        self.dev = self.set_dev_mode()
        self.pid_dir = self.get_pid_path()

        # Caches
        self.assets_cache = os.path.join(self.cache, "assets")
        self.effects_cache = os.path.join(self.cache, "effects")
        self.webview_cache = os.path.join(self.cache, "editor")

        # Save Data
        self.effects = os.path.join(self.config, "effects")
        self.presets = os.path.join(self.config, "presets")
        self.custom_icons = os.path.join(self.config, "custom_icons")
        self.states = os.path.join(self.config, "states")

        # Files
        self.preferences = os.path.join(self.config, "preferences.json")
        self.colours = os.path.join(self.config, "colours.json")

        # Legacy (<= v0.3.12)
        self.old_profile_folder = os.path.join(self.config, "profiles")
        self.old_profile_backups = os.path.join(self.config, "backups")
        self.old_devicestate = os.path.join(self.config, "devicestate.json")

        self.create_dirs_if_not_exist()

    def create_dirs_if_not_exist(self):
        """
        Ensure all the directories exist for the application.
        """
        for folder in [self.config, self.presets, self.custom_icons, self.states, self.effects,
                       self.cache, self.assets_cache,  self.effects_cache, self.webview_cache]:
            if not os.path.exists(folder):
                os.makedirs(folder)

    def set_dev_mode(self):
        """
        When developing within the repository, change the paths accordingly.
        """
        try:
            if os.environ["POLYCHROMATIC_DEV_CFG"] == "true":
                # __file__ = polychromatic/base.py
                self.cache = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "savedatadev", "cache"))
                self.config = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "savedatadev", "config"))
        except KeyError:
            return False
        return True

    @staticmethod
    def get_data_path():
        """
        For development/opt, this is normally adjacent to the application executable.
        For system-wide installs, this is generally /usr/share/polychromatic.
        """
        module_path = __file__

        if os.path.exists(os.path.join(os.path.dirname(module_path), "../data/img/")):
            return os.path.abspath(os.path.join(os.path.dirname(module_path), "../data/"))

        for directory in ["/usr/local/share/polychromatic", "/usr/share/polychromatic"]:
            if os.path.exists(directory):
                return directory

        print("Cannot locate data directory! Please reinstall the application.")
        exit(1)

    @staticmethod
    def get_config_path():
        """
        Path for persistent save data for the application.
        """
        try:
            return os.path.join(os.environ["XDG_CONFIG_HOME"], "polychromatic")
        except KeyError:
            return os.path.join(os.path.expanduser("~"), ".config", "polychromatic")

    @staticmethod
    def get_cache_path():
        """
        Path for temporary data to speed up processing later.
        """
        try:
            return os.path.join(os.environ["XDG_CACHE_HOME"], "polychromatic")
        except KeyError:
            return os.path.join(os.path.expanduser("~"), ".cache", "polychromatic")

    @staticmethod
    def get_pid_path():
        """
        Runtime directory for PID text files that reference other Polychromatic processes.
        """
        try:
            return os.path.join(os.environ["XDG_RUNTIME_DIR"], "polychromatic")
        except KeyError:
            return "/tmp/polychromatic"
