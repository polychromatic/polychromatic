#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2019 Luke Horwell <code@horwell.me>
#
"""
This module abstracts data between Polychromatic and the OpenRazer daemon.
"""

import glob
import os
import subprocess
from .. import common

# External Imports
import openrazer.client as rclient

dbg = common.Debugging()


def get_device_list():
    """
    Gathers a device list of devices bound to the device and possible devices that
    may be supported by OpenRazer at a future date.

    Returns:
        (list)      Success: List of currently plugged in Razer devices with basic metadata.
        -1          Error Code -1: Daemon not running.
        (str)       Error: Daemon threw an exception. Returns string of exception.
    """
    devices = []
    try:
        rdevices = rclient.DeviceManager().devices
    except rclient.DaemonNotFound:
        return -1
    except Exception as e:
        return str(e)

    # Devices that are bound by the daemon
    uid = -1
    for rdevice in rdevices:
        uid += 1
        name = rdevice.name
        serial = str(rdevice.serial)
        form_factor = common.get_form_factor(rdevice.type)

        try:
            real_image = rdevice.device_image
        except AttributeError:
            real_image = rdevice.razer_urls["top_img"]
        except KeyError:
            real_image = ""

        devices.append({
            "uid": uid,
            "backend": "openrazer",
            "name": name,
            "serial": serial,
            "form_factor": form_factor.get("label"),
            "form_factor_id": form_factor.get("id"),
            "icon": form_factor.get("icon"),
            "real_image": real_image,
            "available": True
        })

    # Devices that are Razer but not bound (not supported or driver issue)
    unknown_list = _get_incompatible_device_list(rdevices)
    form_factor = common.get_form_factor("unrecognised")

    for vid, pid in unknown_list:
        devices.append({
            "uid": "{0}{1}".format(vid, pid),
            "backend": "openrazer",
            "name": "{0}:{1}".format(vid, pid),
            "serial": "000000000",
            "form_factor": form_factor.get("label"),
            "form_factor_id": form_factor.get("id"),
            "icon": form_factor.get("icon"),
            "real_image": "",
            "available": False
        })

    return devices


def get_device(uid):
    """
    Returns a dictonary describing the state of a device. This includes its current
    settings, the type of lighting it supports, its serial and firmware version.

    Params:
        uid         Numeric ID of device in daemon's device list.

    Returns:
        {}          Success: Dictonary of metadata
        None        Error: Device no longer available
        (str)       Error: Exception details
    """
    try:
        rdevice = rclient.DeviceManager().devices[uid]
    except KeyError:
        return None
    except Exception as e:
        return str(e)

    name = rdevice.name
    form_factor = common.get_form_factor(rdevice.type)
    vid_pid = _get_device_vid_pid(rdevice)
    vid = vid_pid.get("pid")
    pid = vid_pid.get("vid")
    real_image = _get_device_image(rdevice)

    # Determine zones and effects supported by them
    capabilities = rdevice.capabilities
    zones = []

    if capabilities.get("lighting"):
        zones.append("main")
    if capabilities.get("lighting_logo"):
        zones.append("logo")
    if capabilities.get("lighting_scroll"):
        zones.append("scroll")
    if capabilities.get("lighting_left"):
        zones.append("left")
    if capabilities.get("lighting_right"):
        zones.append("right")
    if capabilities.get("lighting_backlight"):
        zones.append("backlight")

    zone_metadata = common.get_zone_metadata(zones, name)
    zone_names = zone_metadata["names"]
    zone_icons = zone_metadata["icons"]

    # Determine other device data
    name = ""
    serial = ""
    firmware_version = 0
    monochromatic = False
    macros = False
    keyboard_layout = ""
    game_mode = None
    matrix = False
    matrix_rows = 0
    matrix_cols = 0
    dpi_x = 0
    dpi_y = 0
    dpi_ranges = []
    dpi_max = 0
    poll_rate = 0
    poll_rate_ranges = [250, 500, 1000] # Always static

    if capabilities.get("firmware_version"):
        firmware_version = rdevice.firmware_version

    if capabilities.get("name"):
        name = rdevice.name

    if capabilities.get("serial"):
        serial = str(rdevice.serial)

    if capabilities.get("keyboard_layout"):
        keyboard_layout = rdevice.keyboard_layout

    if capabilities.get("game_mode_led"):
        # Prevent dbus.Boolean()
        game_mode = False
        if rdevice.game_mode_led:
            game_mode = True

    if capabilities.get("lighting_led_matrix"):
        matrix = True
        matrix_rows = rdevice.fx.advanced.rows
        matrix_cols = rdevice.fx.advanced.cols

    if capabilities.get("dpi"):
        dpi_x = rdevice.dpi[0]
        dpi_y = rdevice.dpi[1]
        max_dpi = rdevice.max_dpi

        max_ranges = {
            16000: [200, 800, 1800, 4500, 9000, 16000],
            8200: [200, 800, 1800, 4800, 6400, 8200]
        }

        try:
            dpi_ranges = max_ranges[max_dpi]
        except KeyError:
            dpi_ranges = [200,
                int(max_dpi / 10),
                int(max_dpi / 8),
                int(max_dpi / 4),
                int(max_dpi / 2),
                int(max_dpi)
            ]

    if capabilities.get("poll_rate"):
        poll_rate = rdevice.poll_rate

    # Determine which effects are supported (and currently set) for each zone.
    zone_states = {}
    zone_supported = {}

    for zone in zones:
        zone_states[zone] = {}
        zone_supported[zone] = {}

        zone_to_capability = {
            "main": "lighting",
            "logo": "lighting_logo",
            "scroll": "lighting_scroll",
            "backlight": "lighting_backlight",
            "left": "lighting_left",
            "right": "lighting_right"
        }

        zone_to_device = {
            "main": rdevice.fx,
            "logo": rdevice.fx.misc.logo,
            "scroll": rdevice.fx.misc.scroll_wheel,
            "backlight": rdevice.fx.misc.backlight,
            "left": rdevice.fx.misc.left,
            "right": rdevice.fx.misc.right
        }

        def _create_list_for_key_if_empty(key, subkey):
            try:
                key[subkey]
            except KeyError:
                key[subkey] = []

        # Hardware effects
        for effect in ["spectrum", "wave", "reactive", "static", "pulsate", "blinking"]:
            if capabilities.get(zone_to_capability[zone] + "_" + effect):
                zone_supported[zone][effect] = True

        # Hardware breath (and options)
        for effect in ["breath_dual", "breath_random", "breath_single", "breath_triple"]:
            if capabilities.get(zone_to_capability[zone] + "_" + effect):
                zone_supported[zone]["breath"] = True
                _create_list_for_key_if_empty(zone_supported[zone], "breath_options")
                zone_supported[zone]["breath_options"].append(effect.replace("breath_", ""))

        # Hardware starlight (and options)
        for effect in ["starlight_dual", "starlight_random", "starlight_single"]:
            if capabilities.get(zone_to_capability[zone] + "_" + effect):
                zone_supported[zone]["starlight"] = True
                _create_list_for_key_if_empty(zone_supported[zone], "starlight_options")
                zone_supported[zone]["starlight_options"].append(effect.replace("starlight_", ""))

            # Daemon's ripple (and options)
            if capabilities.get(zone_to_capability[zone] + "_ripple") or capabilities.get(zone_to_capability[zone] + "_ripple_random"):
                zone_supported[zone]["ripple"] = True
                _create_list_for_key_if_empty(zone_supported[zone], "ripple_options")

            if capabilities.get(zone_to_capability[zone] + "_ripple"):
                zone_supported[zone]["ripple_options"].append("single")

            if capabilities.get(zone_to_capability[zone] + "_ripple_random"):
                zone_supported[zone]["ripple_options"].append("random")

        # Brightness (slider)
        if capabilities.get(zone_to_capability[zone] + "_brightness"):
            zone_supported[zone]["brightness_slider"] = True

            # 'main' brightness is outside the 'fx' class.
            if zone == "main":
                zone_states[zone]["brightness"] = int(rdevice.brightness)
            else:
                zone_states[zone]["brightness"] = int(zone_to_device[zone].brightness)

        # OR brightness (toggle) on/off - overrides slider in case device reports both capabilities.
        if capabilities.get(zone_to_capability[zone] + "_active"):
            if "brightness_slider" in zone_supported[zone]:
                del zone_supported[zone]["brightness_slider"]
            zone_supported[zone]["brightness_toggle"] = True

            # 'main' does not have an 'active' attribute
            if not zone == "main":
                zone_states[zone]["brightness"] = int(zone_to_device[zone].active)

        # Get current status provided by daemon (OpenRazer 2.7.0+)
        try:
            # Not applicable to non-Chroma devices (Bug? OpenRazer daemon could return an object)
            if matrix:
                zone_states[zone]["effect"] = str(zone_to_device[zone].effect)
                zone_states[zone]["colors"] = _convert_colour_bytes(zone_to_device[zone].colors)
                zone_states[zone]["params_speed"] = int(zone_to_device[zone].speed)
                zone_states[zone]["params_direction"] = int(zone_to_device[zone].wave_dir)
        except Exception as e:
            dbg.stdout("Unable to get device states for " + name, dbg.error)
            dbg.stdout(common.get_exception_as_string(e))
            dbg.stdout("This probably indicates a bug or improperly specified Chroma device:\n{0} ({1}:{2})".format(name, vid, pid), dbg.warning)
            for key in ["effect", "colors", "params_speed", "params_direction"]:
                if key in zone_states[zone]:
                    del zone_states[zone][key]

    # If this is a mouse, get the current battery level.
    battery_level = None
    if form_factor.get("id") == "mouse":
        battery_level = _get_battery_level_dirty()


    return {
        "uid": "{0}{1}".format(vid, pid),
        "backend": "openrazer",
        "vid": vid,
        "pid": pid,
        "name": name,
        "form_factor": form_factor.get("label"),
        "form_factor_id": form_factor.get("id"),
        "icon": form_factor.get("icon"),
        "real_image": real_image,
        "serial": serial,
        "firmware_version": firmware_version,
        "keyboard_layout": keyboard_layout,
        "game_mode": game_mode,
        "monochromatic": _is_device_monochromatic(rdevice),
        "dpi_x": dpi_x,
        "dpi_y": dpi_y,
        "dpi_ranges": dpi_ranges,
        "poll_rate": poll_rate,
        "battery_level": battery_level,
        "matrix": matrix,
        "matrix_rows": matrix_rows,
        "matrix_cols": matrix_cols,
        "zone_names": zone_names,
        "zone_icons": zone_icons,
        "zone_states": zone_states,
        "zone_supported": zone_supported,
        "available": True
    }



def _get_incompatible_device_list(devices):
    """
    Scans 'lsusb' for incompatible Razer devices. As the daemon doesn't recognise them,
    they can be listed, but cannot be interacted with. Excludes already connected devices.

    Returns:
        (list)      In format: [[vid1, pid1], [vid2, pid2]]
        None        An error occurred (e.g. 'lsusb' not installed)
    """
    all_usb_ids = []
    reg_ids = []
    unreg_ids = []

    # Strip lsusb to just get VIDs and PIDs
    try:
        lsusb = subprocess.Popen("lsusb", stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
    except FileNotFoundError:
        dbg.stdout("'lsusb' not available, unable to determine if product is connected.", dbg.error)
        return None

    for usb in lsusb.split("\n"):
        if len(usb) > 0:
            try:
                vidpid = usb.split(" ")[5].split(":")
                all_usb_ids.append([vidpid[0].upper(), vidpid[1].upper()])
            except AttributeError:
                pass

    # Get VIDs and PIDs of current devices to exclude them.
    for device in devices:
        vidpid = _get_device_vid_pid(device)
        reg_ids.append([vidpid.get("vid"), vidpid.get("pid")])

    # Identify Razer VIDs that are not registered in the daemon
    for usb in all_usb_ids:
        if usb[0] != "1532":
            continue

        if usb in reg_ids:
            continue

        unreg_ids.append(usb)

    return unreg_ids


def _get_device_vid_pid(device):
    """
    Extracts VID:PID from the daemon's device object in list format: [VID,PID]

    In the event OpenRazer's _vid and _pid is inaccessible, then 0000 is returned.

    Returns:
        {vid, pid}      Success: A dictionary consisting of the VID and PID.
    """
    try:
        vid = str(hex(device._vid))[2:].upper().rjust(4, '0')
        pid = str(hex(device._pid))[2:].upper().rjust(4, '0')
    except Exception:
        dbg.stdout("VID PID unavailable for " + device.name + ". Using dummy IDs.", dbg.warning)
        vid = "0000"
        pid = "0000"

    return {
        "vid": vid,
        "pid": pid
    }


def _is_user_in_plugdev_group():
    """
    Check the groups of the currently logged in user to identify if it is
    missing 'plugdev' as required by the daemon.
    """
    if "plugdev" in [grp.getgrgid(g).gr_name for g in os.getgroups()]:
        return True
    else:
        return False


def _get_device_image(device):
    """
    OpenRazer doesn't store device images, they are referenced by a URL.

    This function will download a copy of the image for caching purposes.
    """
    try:
        real_image = device.device_image
    except AttributeError:
        real_image = device.razer_urls["top_img"]
    except KeyError:
        real_image = ""

    # TODO: Download image in background

    return real_image


def _is_device_monochromatic(device):
    """
    Returns a boolean to state whether the device is Chroma powered but
    does not show RGB.
    """
    if not device.has("lighting_led_matrix") or device.name.find("Ultimate") != -1:
        return True
    return False


def _convert_colour_bytes(raw):
    """
    Convert the daemon's '.colors' function to a usage hex.
    """
    input_hex = str(raw.hex())
    primary_hex = "#000000"
    secondary_hex = "#000000"
    tertiary_hex = "#000000"

    if len(input_hex) >= 6:
        primary_hex = input_hex[:6]

    if len(input_hex) >= 12:
        secondary_hex = input_hex[6:12]

    if len(input_hex) >= 18:
        tertiary_hex = input_hex[12:18]

    return {
        "primary": "#" + primary_hex,
        "secondary": "#" + secondary_hex,
        "tertiary": "#" + tertiary_hex
    }


def _get_battery_level_dirty():
    """
    Read the driver file for the current battery level. The OpenRazer Python
    library (and/or daemon) does not currently support getting battery information.

    Assumes only one mouse with a battery is present.

    Returns:
        (int)       Value was successfully read.
        None        Value cannot be read, or battery not present.
    """
    # TODO: Should be added to Python library
    battery_value = 0

    # Inherits some GPL code from openrazer/scripts/razer_mouse/driver/get_battery.py
    mouse_dirs = glob.glob(os.path.join("/sys/bus/hid/drivers/razermouse/", "*:*:*.*"))
    mouse_dirs = glob.glob(os.path.join("/tmp/daemon_test/", "*:*:*.*"))

    for directory in mouse_dirs:
        for filename in ["charge_level", "get_battery"]:
            filepath = os.path.join(directory, filename)
            if os.path.exists(filepath):
                with open(filepath, "r") as battery_file:
                    try:
                        battery_percentage_ns = int(battery_file.read().strip())
                        battery_value = (100 / 255) * battery_percentage_ns
                        return int(battery_value)
                    except ValueError:
                        pass
                    except Exception:
                        pass
    return None

