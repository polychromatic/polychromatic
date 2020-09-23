#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
Contains the parent "Backend" class that is inherited by all backends.

Refer to the online documentation for more details:
https://polychromatic.app/docs/
"""

class Backend(object):
    """
    This parent class is inherited by all backends in their individual modules
    adjacent to this file.
    """
    def __init__(self, dbg, common):
        """
        Identifiable data, variables and session storage for the backend.
        """
        # PRIVATE - See self.debug() for usage.
        self._dbg = dbg

        # The self.common module may contain useful functions for processing.
        self.common = common

        # Backend ID
        self.backend_id = "unknown"

        # Logo should be stored in data/img/logo
        self.logo = "example.svg"

        # Should be the version of the backend itself.
        self.version = "0.1.0"

        # URLs and license
        self.project_url = ""
        self.bug_url = ""
        self.releases_url = ""
        self.license = "GPLv3"

    #####################################################################
    # These are stubs and should be implemented by the backend's module.
    #####################################################################
    def get_device_list(self):
        """
        Returns a list of supported devices that are controllable by this backend.

        Expected data:
        [
            {
                "backend":      (str)   self.backend_id
                "uid":          (int)   ID for this class to recognise this device.
                "name":         (str)   Device name
                "serial":       (str)   Device serial
                "form_factor":  (dict)  self.common.get_form_factor()
                "real_image":   (str)   Path to device image. Can be empty.
                "zones":        (list)  List of zones
            }
        ]
        """
        return []

    def get_unsupported_devices(self):
        """
        Returns a list of devices that are potentially controllable by the backend,
        but due to reasons, the backend cannot control them right now.

        For example, it could be due to a installation problem, permissions error or the
        specific model is unsupported right now.

        Expected data:
        [
            {
                "backend":      (str)   self.backend_id
                "name":         (str)   Device name or identifiable text (e.g. VID/PID)
                "form_factor":  (dict)  self.common.get_form_factor()
            }
        ]
        """
        return []

    def get_device(self, uid):
        """
        Returns a dictionary describing the requested device. This may include current
        settings, the type of lighting it supports, serial number and firmware version.

        If the backend is unable to process this (for example, the device was unplugged)
        then nothing is returned. Should there be an error (e.g. backend bug) then
        self.common.get_exception_as_string(e) should be returned to inform the user.

        A successful request will return data according to the specification below.

        Params:
            uid         (int)   Device ID for that backend.

        Accepted return data types:
            (dict)              Success: Dictionary of metadata.
            None                Failed: Requested device no longer available.
            (str)               Failed: Backend error. Details of exception.

        Expected data:
        {
            # Required

            "backend":          (str)   self.backend_id
            "uid":              (int)   ID for this class to recognise this device.
            "name":             (str)   Name of device
            "form_factor":      (dict)  self.common.get_form_factor()
            "real_image"        (str)   Path to device image. Can be empty.
            "serial":           (str)   Serial of device
            "monochromatic":    (bool)  Does this device only have one colour?

            # If these are not available, specify None:

            "vid":              (str)   VID of device
            "pid":              (str)   PID of device
            "firmware_version": (str)   Firmware revision
            "keyboard_layout":  (str)   Keyboard layout in format "en_GB"
            "summary": [        (list)  List overview current status. Examples:
                {
                    "icon": "/path/to/icon.svg"     (str) Absolute path to icon
                    "string_id": "dpi"              (str) Show string ID next to icon
                    "string": "1800 DPI"            (str) OR show this exact text
                }
            ],
            "dpi_x":            (int)   Device's DPI X value
            "dpi_y":            (int)   Device's DPI Y value
            "dpi_single":       (bool)  Device only accepts one DPI value
            "dpi_ranges":       (list)  List of DPI ranges set by device
            "dpi_min":          (int)   Minimum DPI value supported by device
            "dpi_max":          (int)   Maximum DPI value supported by device
            "matrix":           (bool)  Supports individual LED mapping
            "matrix_rows":      (int)   Total rows in LED matrix
            "matrix_cols":      (int)   Total columns in LED matrix
            "zone_icons": {     (dict)  Graphic to visually represent each zone
                "main":         (str)   Name of icon as seen in {data}/img/zones/
            }
            "zone_options": {   (dict)  Tells Polychromatic how to present the options.
                "main": [       (dict)  Keys for each zone.
                    {
                        # Required

                        "id":                   (str)   ID to identify later. Used for string/icon.
                        "type":                 (str)   "effect", "slider", "toggle" or "multichoice"
                        "parameters": [         (list)  Parameters for "effect" and "multichoice".
                            {
                                "id":           (str)   ID to identify later. Used for string.
                                "data":         (any)   Any data type according to the backend's needs.
                                "active":       (bool)  This parameter is currently in use.
                                "colours":      (int)   This parameter inputs this amount of colours.
                            }
                        ],
                        "colours":              (int)   This option inputs this amount of colours.
                                                        Ignored when parameters are present.
                        "colour_1": "#RRGGBB"   (str)   Currently saved hex value for primary colour.
                        "colour_2": "#RRGGBB"   (str)   Currently saved hex value for secondary colour (etc)

                        # Only for effect and toggle

                        "active":               (bool)  Effect/option in use?

                        # Only for slider

                        "value":                (int)   Current value
                        "min":                  (int)   Start of range, e.g. 0
                        "max":                  (int)   End of range, e.g. 100
                        "step":                 (int)   Range intervals, e.g. 5
                        "suffix":               (str)   String to appear at the end in GUIs
                    }
                ],
            }

            The zone key and any "id" keys are used for strings. These will be passed
            within Polychromatic before being passed back via set_device_state()
            for reference later.
        }
        """
        return None

    def set_device_state(self, uid, zone, option_id, option_data, colours=[]):
        """
        Send a request to the hardware. The data specified by get_device()
        "zone_options" will end up back here.

        Params:
            uid         (int)   Device ID for that backend.
            zone        (str)   Zone ID, e.g. "logo"
            option_id   (str)   ID of the specified control, e.g. "wave"
            option_data (any)   Value depending on type, e.g.
                                (bool)  for toggle
                                (int)   for slider
                                (str)   for "data" (effect/multichoice)
            colours     (list)  List of hex values in format "#RRGGBB"

        Accepted return data types:
            True                Success: Executed request.
            False               Failed: Invalid or malformed request.
            None                Failed: Device no longer available.
            (str)               Failed: Backend error. Details of exception.
        """
        return False

    def get_device_object(self, uid):
        """
        Returns an object class with data and objects for per-key lighting integration.
        This will be used when playing back custom effects - which could be static
        or very dynamic at high frame rates.

        If the device doesn't buffer frames in memory, 'set()' could be used in place of
        'draw()', however this could slow down the effect playback.

        Devices with firmware or NAND/flash memory that isn't designed for software
        programming should not implement this stub, as it may damage the hardware.

        Params:
            uid         (int)   Device ID for that backend.

        Accepted return data types:
            (class object)      Success: See below.
            None                Failed: Device no longer available.
            (str)               Failed: Error details (exception)

        Expected class variables:
            backend             (str)   self.backend_id
            name                (str)   Human-readable device name
            rows                (int)   Number of rows. 1-based index.
            cols                (int)   Number of columns. 1-based index.
            serial              (str)   Device's serial. Must be unique.
            form_factor         (str)   self.common.get_form_factor()

        Expected functions:
            set(x,y,red,green,blue)     Set a colour in the matrix.
            draw()                      Render matrix to device.
            clear()                     Clear all LEDs from matrix.
            brightness(int)             Set the entire device's brightness by percentage.
        }
        """
        return self.backend_id + " does not support get_device_object()!"

    def troubleshoot(self):
        """
        Perform troubleshooting steps to identify issues with the installation of
        the backend. This could check if the device is physically in the system, or the
        binary is accessible (/usr/bin/xyz), for instance.

        If the backend is simple in nature, then this may not be needed.

        This should be implemented in pylib/troubleshoot/<backend>.py.

        Accepted return data types:
            (list)              Completed. Dictionary of results in format below.
            (e)                 Exception details: Failed to run troubleshooting.
            None                Not applicable.

        Expected data:
        [
            {
                "test_name":    (str)   i18n enabled string describing the test
                "suggestion":   (str)   i18n enabled string describing what to do on failure.
                "passed":       (bool)  No problems found. None if undetermined.
            },
            {...}
        ]
        """
        return None

    def restart(self):
        """
        User requests to restart the backend - which could be a daemon, background
        task or some other process that initalises the devices.

        For some backends, this may not even be necessary.

        Accepted return data types:
            True                Successfully executed restart.
            False               Failed to restart.
            None                Not applicable.
        """
        return None

    #####################################################################
    # Useful Functions
    #####################################################################
    def debug(self, message=""):
        """
        Use this function to output messages to the user when they have verbose enabled.
        This may be useful when users are diagnosing issues with the backend.
        """
        self._dbg.stdout("[{0}] {1}".format(self.backend_id, str(message)), self._dbg.debug, 1)
