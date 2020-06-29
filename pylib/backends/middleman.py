#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2020 Luke Horwell <code@horwell.me>
#
"""
This module abstracts data between Polychromatic and compatible backends
for Polychromatic to provide a user interface for.

Please refer to the documentation for specifications:
https://polychromatic.app/docs/

"""

from .. import common

#
# Avaliable Backends
#
# Data types:
#   bool        Backend is functional
#   str         Exception details
#
BACKEND_OPENRAZER = False

#
# Backend Module Bindings
#
# Data types:
#   <null>      Backend unavailable
#   <fn>        Backend attached to Python module
#
BACKEND_ID = {
    "openrazer": None
}


#
# Import Backends
#
try:
    from . import openrazer as openrazer
    BACKEND_OPENRAZER = True
    BACKEND_ID["openrazer"] = openrazer
except (ImportError, ModuleNotFoundError):
    BACKEND_OPENRAZER = False
except Exception as e:
    BACKEND_OPENRAZER = common.get_exception_as_string(e)


#
# Common Functions
#
def get_versions():
    """
    Returns a dictionary of versions according to the available backends.
    """
    versions = {}

    if BACKEND_OPENRAZER:
        versions["openrazer"] = BACKEND_ID["openrazer"].VERSION

    return versions


def get_device_list():
    """
    Gathers a device list of supported devices, including devices that
    may be supported if the right backend was installed.

    Each backends will return a list for the vendor(s) they support, however
    if one of them fails, the request is interrupted and the user is informed.

    Returns:
        (list)      Success: List of currently plugged in devices with basic metadata.
        (str)       Error: Backend threw an exception. Returns string of exception.
    """
    devices = []

    if BACKEND_OPENRAZER == True:
        try:
            devices = devices + openrazer.get_device_list()
        except Exception:
            return openrazer.get_device_list()

    return devices


def get_device(backend, uid):
    """
    Returns a dictionary describing the state of a device. This may include current
    settings, the type of lighting it supports, serial number and firmware version.

    If the backend is unable to process this (for example, the device was unplugged)
    then nothing is returned. Should there be an error (e.g. backend bug) then an
    exception is returned to inform the user.

    A successful request will return data according to the get_device specification.

    Params:
        backend     (str)   Backend ID
        uid         (int)   Device ID for that backend.

    Returns:
        {}                  Success: Dictionary of metadata
        None                Failed: Requested device no longer available
        (str)               Failed: Backend threw exception
    """
    if not BACKEND_ID[backend]:
        return None

    return BACKEND_ID[backend].get_device(uid)


def get_device_form_factor(backend, uid):
    """
    Returns the output of common.get_form_factor() for the specified device.
    This is to avoid processing the entire get_effect() function.

    Params:
        backend     (str)   Backend ID
        uid         (int)   Device ID for that backend.

    Returns:
        {}                  Success: Dictionary of metadata
        None                Failed: Requested device no longer available
    """
    if not BACKEND_ID[backend]:
        return None

    return BACKEND_ID[backend].get_device_form_factor(uid)


def set_device_state(backend, uid, request, zone, colour_hex, params):
    """
    Sends a request to the the device, like setting the brightness, the hardware
    effect or a hardware property (such as DPI).

    It is expected the parent calling this function has validated the request,
    e.g. command line validated zone for device.

    A successful request will return data according to the set_device_state specification.

    Params:
        backend     (str)   Backend ID
        uid         (int)   Device ID for that backend.
        request     (str)   Polychromatic's request, e.g. "brightness", "effect"
        zone        (str)   If applicable, a valid lighting area, e.g. "logo".
        colour_hex  (lst)   If applicable, a list of strings in format: [#RRGGBB,  #RRGGBB]
        params      (lst)   If required, a list of parameters to parse. E.g. brightness value or wave direction, etc.

    Returns:
        True                Success!
        False               Failed: Malformed request. Backend says it's not possible.
        None                Failed: Requested device no longer available
        (str)               Failed: Backend threw exception
    """
    if not BACKEND_ID[backend]:
        return None

    return BACKEND_ID[backend].set_device_state(uid, request, zone, colour_hex, params)


def set_device_colours(backend, uid, zone, colour_hex):
    """
    Replays the active effect on the device, but changes to a new set of colours.

    A successful request will return data according to the set_device_colours specification.

    Params:
        backend     (str)   Backend ID
        uid         (int)   Device ID for requested backend.
        zone        (str)   A valid lighting area, e.g. "logo".
        colour_hex  (lst)   A list of strings in format: [#RRGGBB,  #RRGGBB]

    Returns:
        True                Success!
        False               Failed: Malformed request. Backend says it's not possible.
        None                Failed: Requested device no longer available
        (str)               Failed: Backend threw exception
    """
    if not BACKEND_ID[backend]:
        return None

    return BACKEND_ID[backend].set_device_colours(uid, zone, colour_hex)


def debug_matrix(backend, uid, row, column):
    """
    Highlights a key for the purposes of testing custom frames.

    Returns:
        None        Success!
        False       Failed: Malformed request. Backend says it's not possible.
        (str)       Failed: Backend threw exception
    """
    if not BACKEND_ID[backend]:
        return None

    return BACKEND_ID[backend].debug_matrix(uid, row, column)


def troubleshoot():
    """
    Performs a series of automatic troubleshooting steps to identify possible
    reasons why the OpenRazer daemon is not detecting a device (Linux only)

    This function is currently exclusive to OpenRazer, but could potentially
    expand to other backends if necessary in future.

    Dictionary consists of:
    {
        "test_name_1"   (bool)      Did the test 1 succeed or fail?
        "test_name_2"   (bool)      Did the test 2 succeed or fail? (etc)
        "success"       (bool)      Did all tests complete?
    }

    The value for "test_name" is used as a key for the locales dictionary.

    Returns:
        (dict)      A dictionary describing the checks and status.
    """
    from . import openrazer_troubleshooter as troubleshooter
    return troubleshooter.troubleshoot()


def restart_backends():
    """
    Restarts the daemon processes for all compatible backends.
    """
    if BACKEND_OPENRAZER:
        openrazer.restart_daemon()

    return True


def get_device_object(backend, uid):
    """
    Returns a 'device' object that can be used for drawing frames to a device
    that supports individual addressable LEDs ("matrix")

    Params:
        backend     (str)       Device backend ID
        uid         (int)       Device ID for backend

    Returns:
        None        Device not found, backend unavailable or other error.
        (dict)      Consisting of:
        {
            "rows": (int)           // Length of Y axis
            "cols": (int)           // Length of X axis
            "name": (str)           // Human readable name
            "serial": (str)         // Device's serial number
            "form_factor": (str)    // Polychromatic processed 'form factor' ID
            "set": (obj)            // Function to set matrix state.
                                    // Should accept: (x,y,r,g,b)
            "draw": (obj)           // Function to 'draw' function for backend
            "clear": (obj)          // Function to 'clear' function for backend
            "brightness": (obj)     // Function to set brightness (0-100%)
        }
    """
    if backend == "openrazer" and BACKEND_OPENRAZER:
        return openrazer.get_device_object(uid)

    return None
