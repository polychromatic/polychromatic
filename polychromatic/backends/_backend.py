#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020-2022 Luke Horwell <code@horwell.me>
#
"""
Contains the parent "Backend" class that is inherited by all backend modules.

A "backend" implements a data layer of processing between Polychromatic's interfaces
and the vendor's driver, daemon or other implementation. This application acts like
an orchestrator for presenting and relaying instructions, but is not expected to
actually send binary or payloads to the hardware itself.

Refer to the online documentation for more details:
https://docs.polychromatic.app/
"""

from ..fx import FX
import glob
import os
import grp


class BackendBase(object):
    """
    All backends inherit from this class. Contains useful functions and any
    reimplementations from Polychromatic's base class.
    """
    def __init__(self, base):
        self.backend_id = "Unknown"
        self._base = base

        # Pass a function for translating strings in UI messages. Ignore for debug() messages.
        self._ = base._

    def debug(self, message=""):
        """
        Use this function to output messages to the user when they have verbose enabled.
        This may be useful when users are diagnosing issues.
        """
        self._base.dbg.stdout("[{0}] {1}".format(self.backend_id, str(message)), self._base.dbg.debug, 1)

    def get_backend_storage_path(self):
        """
        Returns a path for storing data for the backend.
        """
        config_path = os.path.join(self._base.paths.config, "backends", self.backend_id)
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        return config_path

    def get_form_factor(self, form_factor="unrecognised"):
        """
        Return a form factor dictionary for Polychromatic.

        See common.get_form_factor() for the dictionary output.
        See common.FORM_FACTORS for a list of valid IDs to pass to this function.
        """
        return self._base.common.get_form_factor(self._, form_factor)

    def get_icon(self, folder="", name=""):
        """
        Return an icon path from: data/img/<folder>/<name>.svg
        The file extension is omitted.
        """
        return self._base.common.get_icon(folder, name)

    def get_exception_as_string(self, e):
        """
        Returns a traceback in string format. Use this to relay error messages to the user.

        try:
            <something that might fail>
        except Exception as e:
            return self.get_exception_as_string(e)
        """
        return self._base.common.get_exception_as_string(e)

    def __repr__(self):
        return self.backend_id


class Backend(BackendBase):
    """
    A backend implementing the communication required between this software
    and a driver/daemon.

    Most functions are stubs and must be reimplemented.
    """
    def __init__(self, *args):
        super().__init__(*args)

        # Set the Backend ID here
        # (Also to be added in ../middleman.py)
        self.backend_id = "unknown"

        # Name of backend
        self.name = "OpenRazer"

        # Filename of the logo stored in data/img/logo/ (SVG preferred)
        self.logo = "example.svg"

        # Set this string to the backend version
        self.version = "0.1.0"

        # URLs and license for the backend
        self.project_url = ""
        self.bug_url = ""
        self.releases_url = ""
        self.license = "GPLv3"

        # This module may contain useful functions. See BackendHelpers() for usage.
        self.helpers = BackendHelpers()

    def init(self):
        """
        Perform the logic for initalizing the backend, such as connecting
        to a daemon using the necessary library.

        Return:
            - True      Success!
            - (str)     Traceback/error message. Cannot use backend.
        """
        raise NotImplementedError

    class UnknownDeviceItem(object):
        """
        An object describing a device that may potentially be compatible, but
        in its current state, cannot be used.

        For example, a installation problem or permission error prevents
        this device from being controlled.
        """
        def __init__(self):
            # Human readable name of the device (if known)
            self.name = "Unknown"

            # Specify the backend ID here
            self.backend_id = "openrazer"

            # Use Backend.get_form_factor(), passing an ID from common.FORM_FACTORS
            # that identifies this device. Pass "unrecognised" to function if unknown.
            self.form_factor = {}

    def get_unsupported_devices(self):
        """
        Returns a list of UnknownDeviceItem(), or empty list.
        """
        return []

    #####################################################################
    class DeviceItem(object):
        """
        An object describing the complete state of the device and its available
        functions. This may include current settings, device options,
        serial number and firmware version.

        This object also contains the code for executing options and parameters,
        as well as defining how Polychromatic should present them.
        """
        def __init__(self):
            # Human readable name of the device (including vendor name)
            self.name = "Unnamed Device"

            # Backend ID
            self.backend_id = ""

            # Use Backend.get_form_factor(), passing an ID from common.FORM_FACTORS
            self.form_factor = {}

            # Local file path to device image (or empty string for no image)
            self.real_image = ""

            # String containing the device's serial number, must be unique.
            self.serial = "X"

            # Does this device only have one colour?
            # Set to True for hardware that have individually addressable LEDs,
            # but physically only displays one colour from the RGB range.
            self.monochromatic = False

            # Device's vendor and product ID
            self.vid = "????"
            self.pid = "????"

            # If applicable, a string describing the firmware version, e.g. "v1.0"
            self.firmware_version = ""

            # If applicable, a string describing the keyboard locale, e.g. "en_GB"
            # This will be used for determining graphics in the effect editor.
            self.keyboard_layout = ""

            # Stores a DPI() object, unless device does not support DPI X/Y.
            self.dpi = None

            # Stores a Matrix() object, if device supports per-LED lighting.
            self.matrix = None

            # List of Zone() objects.
            self.zones = []

        def __str__(self):
            return self.name

        def __repr__(self):
            return "{0}:{1}".format(self.serial, self.name.replace(" ", ""))

        def refresh(self):
            """
            This function is called before showing the current status for a device, such as:
            - Controller: After selecting/refreshing a device in the Device tab
            - Tray: Once when the applet starts
            - CLI: Listing the current device status

            It is expected the device's options and features have their correct values at this
            point, and acts as a cache until the device is refreshed again. It co-exists alongside
            each option's .refresh() function, which is used when the application needs
            to refresh a specific option or feature.

            Each backend may implement this differently depending whether the
            hardware knows what it's up to or if it uses a software persistence implementation.
            """
            return

        def get_summary(self):
            """
            Returns a list describing the current hardware state of the device,
            such as current brightness, effect or settings.

            The list consists of a dictionary like so:
            {
                "icon": "/path/to/icon.svg"     (str) Absolute path to icon
                "label": "1800 DPI"             (str) Label to display
            }

            Icons can be retrieved using Backend.get_icon()
            """
            # TODO: Add ID to fix positions effect/brightness/dpi/battery then the rest
            # TODO: Fixed makes it easier for editing state in memory - one read/write!
            return []

        class DPI(object):
            """
            An object storing the current DPI values and get/set functions.
            """
            def __init__(self):
                self.x = 0
                self.y = 0
                self.min = 0
                self.max = 0
                self.stages = []

            def refresh(self):
                """
                Reload the DPI variables stored in this object.
                """
                raise NotImplementedError

            def set(self, x, y):
                """
                Sets the new DPI value to the specified X/Y value.
                """
                raise NotImplementedError

        class Matrix(FX):
            """
            An object holding data and objects for individual LED software-driven lighting,
            if supported by the device.

            Devices with NAND/flash memory that isn't designed for repeated usage
            should not implement this feature, as it may damage the hardware.

            See also: fx.FX()
            """
            def __init__(self):
                self.name = "Unknown Device"
                self.form_factor_id = "unrecognised"
                self.rows = 0
                self.cols = 0

            def init(self):
                """
                Prepare the device for custom frames. If unnecessary, this can be ignored.
                """
                return

            def set(self, x=0, y=0, red=255, green=255, blue=255):
                """
                Set a colour at the specified co-ordinate.
                """
                raise NotImplementedError

            def draw(self):
                """
                Send the data to the hardware to be displayed.
                """
                raise NotImplementedError

            def clear(self):
                """
                Reset all LEDs to an off state.
                """
                raise NotImplementedError

            def brightness(self, percent):
                """
                Set the global brightness of the LEDs. Could be used for fade effects globally.
                """
                raise NotImplementedError

        class Zone(object):
            """
            An object that describes a specific lighting area of the hardware.
            If the device has no concept of this or is monolithic, call this zone "main".
            """
            def __init__(self):
                # Internal ID
                self.zone_id = ""

                # Human readable text describing this zone, e.g. "Left Side"
                self.label = "Unknown Zone"

                # Full path using self.get_icon() - usually from {data}/img/zones/
                self.icon = ""

                # List of Option() objects - see below.
                self.options = []

                def __str__(self):
                    return self.zone_id

                def __repr__(self):
                    return self.zone_id

    class Option(object):
        """
        Options are settings that the user can change. This is the base class,
        use one of the child classes below. These tell Polychromatic how to
        present them, the parameters (if any) and the function to execute.
        """
        def __init__(self):
            # Internal to identify this option later.
            self.uid = ""

            # Human readable text describing this option, e.g. "Brightness"
            self.label = "Unknown Option"

            # Full path using self.get_icon() - usually from {data}/img/options/
            self.icon = ""

            # ------ The following depend on the option ------
            # Is this option currently selected?
            self.active = False

            # List of Parameter() objects
            self.parameters = []

            # Does selecting this option need a colour?
            self.colours_required = 0

            # Which colours are assigned for this option?
            #   - Initially, this should be populated with previously set colours.
            #   - Values in the list change when the user changes colours via the interface.
            #   - Must be same length as colours_required.
            # Format: ["#RRGGBB"]
            self.colours = []

        def __str__(self):
            return self.uid

        def __repr__(self):
            return self.uid

        def refresh(self):
            """
            Refresh the active variable for the option and that of any parameters.
            If the option doesn't have an active state, ignore this function.

            Nothing is returned from this function. However, if an exception occurs
            or is manually raised, an error will be shown to the user.
            """
            return

        def apply(self, data=None):
            """
            Execute the action on the device. The "data" argument varies by option type.

            Nothing is returned from this function. However, if an exception occurs
            or is manually raised, an error will be shown to the user.
            """
            raise NotImplementedError

        class Parameter(object):
            """
            An object describing a parameter that can be selected. For example, a
            "Wave" option may have a "Fast" and "Slow" mode.

            This Parameter() object is passed to an option's apply() function.
            """
            def __init__(self):
                # Can be any data type, this will be passed as an argument to Option.apply()
                self.data = None

                # Human readable text describing this option, e.g. "Fast"
                self.label = "Unknown Parameter"

                # Full path using get_icon() - usually from {data}/img/params/
                self.icon = ""

                # Is this parameter currently selected?
                self.active = False

                # Select this parameter as a fallback?
                # (Only one should be default. If there's no default, use the first one)
                self.default = False

                # Does selecting this parameter require a colour?
                # (Make sure the option's colour_list is populated)
                self.colours_required = 0

            def __str__(self):
                return str(self.data)

            def __int__(self):
                return int(self.data)

            def __repr__(self):
                return str(self.data)

    class EffectOption(Option):
        """
        For presenting hardware effects. These are grouped together
        under one section/menu. There are no additional variables to set.

        Parameters: Optional
        Colours: Optional
        """
        def __init__(self):
            super().__init__()

    class ToggleOption(Option):
        """
        For options that are either on or off.

        Parameters: Ignored
        Colours: Ignored
        """
        def __init__(self):
            super().__init__()

            # Optionally change the labels depending on interface (menu/checkbox)
            self.label_enable = "" # Enable
            self.label_disable = "" # Disable
            self.label_toggle = "" # Enabled

            # Optionally the tray can show alternate icons representing on/off states
            self.icon_enable = ""
            self.icon_disable = ""

        def apply(self, enabled=True):
            """
            Execute the action on the device. This argument will be a boolean.
            """
            raise NotImplementedError

    class SliderOption(Option):
        """
        For an option that is a variable between two integers.

        Parameters: Ignored
        Colours: Ignored
        """
        def __init__(self):
            super().__init__()

            # Current value, the range, how much to step and the suffix strings
            self.value = 0
            self.min = 1
            self.max = 100
            self.step = 1
            self.suffix = ""
            self.suffix_plural = ""

        def apply(self, value=0):
            """
            Execute the action on the device. This argument will be an integer.
            """
            raise NotImplementedError

    class MultipleChoiceOption(Option):
        """
        For an option that should be presented as a drop down or list.
        There are no variables to set. These are populated from parameters.

        Parameters: Required
        Colours: Ignored
        """
        def __init__(self):
            super().__init__()

    class DialogOption(Option):
        """
        No input necessary, but displays a message to the user when the
        button (or menu item) is clicked.

        Parameters: Ignored
        Colours: Ignored
        """
        def __init__(self):
            super().__init__()

            self.button_label = ""
            self.message = ""

    class ButtonOption(Option):
        """
        No input necessary, run the apply() function straight away.

        Parameters: Ignored
        Colours: Ignored
        """
        def __init__(self):
            super().__init__()

            self.button_label = ""

    def get_devices(self):
        """
        Return:
            - (list)  A list of DeviceItem() objects.
            - (str)   Traceback/error message. Cannot continue.
        """
        return NotImplementedError

    def get_device_by_name(self, name):
        """
        For the application to quickly retrieve a device object based on the
        name of the device.

        Return:
            - DeviceItem()      Found the specified device.
            - (str)             Traceback/error message. Cannot use device.
            - None              Device not found.
        """

    def get_device_by_serial(self, serial):
        """
        For the application to quickly retrieve a device object based on the
        serial number.

        Return:
            - DeviceItem()      Found the specified device.
            - (str)             Traceback/error message. Cannot use device.
            - None              Device not found.
        """

    def troubleshoot(self, fn_progress_set_max, fn_progress_advance):
        """
        Perform troubleshooting steps to identify issues with the installation of
        the backend. These checks could include verifying the device is being
        detected, or a binary is accessible (/usr/bin/xyz), for instance.

        If the backend is simple in nature, implementing a troubleshooter might not be necessary.

        fn_progress_set_max and fn_progress_advance are functions passed to this function.
        To optionally provide feedback using the progress bar, you can call fn_progress_set_max(int)
        with the maximium value. Then, call fn_progress_advance() to add 1 to the progress bar.

        Troubleshooting code should be implemented in polychromatic/troubleshoot/<backend>.py.

        Return:
            - (list)  A list of dictionary results in format below.
            - (str)   Traceback/error message. Cannot continue.
            - None    Troubleshooter not avaliable on this operating system

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
        User requests to restart the backend - which could be a daemon, or
        other command to reinitialise the devices.

        For some backends, this may not even be necessary.

        Return:
            - True      Successfully executed restart.
            - False     Failed to restart.
            - None      Not applicable.
        """
        return None


class BackendHelpers():
    """
    Shared functions that are useful for backends.
    """
    def get_usb_pids_by_vid(self, vid_to_find):
        """
        Returns a integer list of USB PIDs for a VID plugged into the system.
        """
        vendor_files = glob.glob("/sys/bus/usb/devices/*/idVendor")
        found_pids = []
        for vendor in vendor_files:
            with open(vendor, "r") as f:
                vid = str(f.read()).strip().upper()
                if vid == vid_to_find:
                    with open(os.path.dirname(vendor) + "/idProduct") as f:
                        pid = str(f.read()).strip().upper()
                        found_pids.append(pid)
        return found_pids

    def is_user_in_group(self, group):
        """
        Check the user groups for the currently logged in user and returns a
        boolean to indicate whether the specified group was found.
        """
        if group in [grp.getgrgid(g).gr_name for g in os.getgroups()]:
            return True

        return False
