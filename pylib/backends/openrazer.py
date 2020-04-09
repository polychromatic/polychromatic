#!/usr/bin/python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017-2020 Luke Horwell <code@horwell.me>
#
"""
This module abstracts data from the OpenRazer Python library (and daemon)
and parses this for Polychromatic to use.

Project URL: https://github.com/openrazer/openrazer
"""

import glob
import os
import subprocess
# 'requests' imported on-demand if device images are to be downloaded.
# 'shutil' imported on-demand for troubleshooter.

# Polychromatic
from .. import common

# OpenRazer
import openrazer.client as rclient
VERSION = rclient.__version__

dbg = common.Debugging()


def get_device_list():
    """
    See: middleman.get_device_list()
    """
    devices = []
    try:
        # TODO: Speed up by initalising DeviceManager() once - param maybe?
        devman = rclient.DeviceManager()
        devman.sync_effects = False
        rdevices = devman.devices
    except rclient.DaemonNotFound:
        return -1
    except Exception as e:
        return common.get_exception_as_string(e)

    # Devices that are bound by the daemon
    uid = -1
    for rdevice in rdevices:
        uid += 1
        name = rdevice.name
        serial = str(rdevice.serial)
        form_factor = common.get_form_factor(rdevice.type)
        zones = _get_supported_zones(rdevice)

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
            "zones": zones,
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
            "zones": "",
            "available": False
        })

    return devices


def get_device(uid):
    """
    See: middleman.get_device(...)
    """
    try:
        # TODO: Speed up by initalising DeviceManager() once - param maybe?
        devman = rclient.DeviceManager()
        devman.sync_effects = False
        rdevice = devman.devices[uid]
    except IndexError:
        return None
    except Exception as e:
        return common.get_exception_as_string(e)

    name = rdevice.name
    form_factor = common.get_form_factor(rdevice.type)
    vid_pid = _get_device_vid_pid(rdevice)
    vid = vid_pid.get("pid")
    pid = vid_pid.get("vid")
    real_image = _get_device_image(rdevice)

    # Determine zones and effects supported by them
    zones = _get_supported_zones(rdevice)
    zone_metadata = common.get_zone_metadata(zones, name)
    zone_names = zone_metadata["names"]
    zone_icons = zone_metadata["icons"]

    # Determine other device data
    # -> Strings
    name = ""
    serial = ""
    firmware_version = None
    keyboard_layout = None

    # -> Booleans
    monochromatic = False
    macros = False
    game_mode = None
    matrix = False          # Also used to determine if 'chroma' hardware.
    battery_charging = False

    # -> Integers
    matrix_rows = None
    matrix_cols = None
    dpi_x = None
    dpi_y = None
    dpi_max = None
    dpi_single = False
    poll_rate = None
    battery_level = None

    # -> Lists
    dpi_ranges = []
    poll_rate_ranges = [250, 500, 1000] # Always static

    # -> Dict
    zone_states = {}
    zone_supported = {}

    if rdevice.has("firmware_version"):
        firmware_version = rdevice.firmware_version

    if rdevice.has("name"):
        name = rdevice.name

    if rdevice.has("serial"):
        serial = str(rdevice.serial)

    if rdevice.has("keyboard_layout"):
        keyboard_layout = rdevice.keyboard_layout

    if rdevice.has("game_mode_led"):
        # Prevent dbus.Boolean()
        game_mode = False
        if rdevice.game_mode_led:
            game_mode = True

    if rdevice.has("lighting_led_matrix"):
        matrix = True
        matrix_rows = rdevice.fx.advanced.rows
        matrix_cols = rdevice.fx.advanced.cols

    if rdevice.has("dpi"):
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

        # DeathAdder 3.5G only supports DPI X (#209)
        if rdevice.has("available_dpi"):
            dpi_single = True

    if rdevice.has("poll_rate"):
        poll_rate = rdevice.poll_rate

    # Determine which effects are supported (and currently set) for each zone.
    for zone in zones:
        zone_states[zone] = {}
        zone_supported[zone] = {}

        zone_to_device = _get_device_zones(rdevice)
        zone_to_capability = _get_zone_capability_prefix()

        def _create_list_for_key_if_empty(key, subkey):
            try:
                key[subkey]
            except KeyError:
                key[subkey] = []

        # Hardware effects
        for effect in ["spectrum", "wave", "reactive", "static", "pulsate", "blinking"]:
            if rdevice.has(zone_to_capability[zone] + "_" + effect):
                zone_supported[zone][effect] = True

        # Hardware breath (and options)
        for effect in ["breath_random", "breath_single", "breath_dual", "breath_triple"]:
            if rdevice.has(zone_to_capability[zone] + "_" + effect):
                zone_supported[zone]["breath"] = True
                _create_list_for_key_if_empty(zone_supported[zone], "breath_options")
                zone_supported[zone]["breath_options"].append(effect.replace("breath_", ""))

        # Hardware starlight (and options)
        for effect in ["starlight_random", "starlight_single", "starlight_dual"]:
            if rdevice.has(zone_to_capability[zone] + "_" + effect):
                zone_supported[zone]["starlight"] = True
                _create_list_for_key_if_empty(zone_supported[zone], "starlight_options")
                zone_supported[zone]["starlight_options"].append(effect.replace("starlight_", ""))

        # Software ripple (provided by daemon)
        if rdevice.has(zone_to_capability[zone] + "_ripple"):
            zone_supported[zone]["ripple"] = True
            _create_list_for_key_if_empty(zone_supported[zone], "ripple_options")
            zone_supported[zone]["ripple_options"].append("single")

        if rdevice.has(zone_to_capability[zone] + "_ripple_random"):
            zone_supported[zone]["ripple"] = True
            _create_list_for_key_if_empty(zone_supported[zone], "ripple_options")
            zone_supported[zone]["ripple_options"].append("random")

        # Brightness (slider)
        if rdevice.has(zone_to_capability[zone] + "_brightness"):
            zone_supported[zone]["brightness_slider"] = True
            zone_states[zone]["brightness"] = int(zone_to_device[zone].brightness)

        # 'main' brightness is outside the 'fx' class.
        elif zone == "main" and rdevice.has("brightness"):
            zone_supported[zone]["brightness_slider"] = True
            zone_states[zone]["brightness"] = int(rdevice.brightness)

        # OR brightness (toggle) on/off - overrides slider in case device reports both capabilities.
        if rdevice.has(zone_to_capability[zone] + "_active"):
            if "brightness_slider" in zone_supported[zone]:
                del zone_supported[zone]["brightness_slider"]
            zone_supported[zone]["brightness_toggle"] = True

            # 'main' does not have an 'active' attribute
            if not zone == "main":
                zone_states[zone]["brightness"] = int(zone_to_device[zone].active)

        # Get current status provided by daemon (OpenRazer 2.8.0+)
        try:
            # Not applicable to non-Chroma devices (Bug? OpenRazer daemon could return an object)
            if matrix:
                effect = str(zone_to_device[zone].effect)
                params = []
                colours = _convert_colour_bytes(zone_to_device[zone].colors)

                # Extract and convert strings that is understood by Polychromatic.
                #
                # For example:
                # Daemon        Effect          Param
                # ------------  --------------  --------------
                # breathSingle  breath          single
                # wave          wave            1 (wave_dir)
                # reactive      reactive        2 (direction)
                # E.g. 'breathSingle' -> breath (effect) and single (param)
                #      'wave'         -> wave (effect) and 1 (param/direction)

                if effect in ["wave"]:
                    params = [int(zone_to_device[zone].wave_dir)]

                elif effect in ["reactive"]:
                    params = [int(zone_to_device[zone].speed)]

                elif effect in ["breathSingle", "breathDual", "breathTriple", "breathRandom"]:
                    effect = "breath_" + effect.split("breath")[1].lower()
                    param = [""]

                elif effect in ["starlightSingle", "starlightDual", "starlightRandom"]:
                    effect = "starlight_" + effect.split("starlight")[1].lower()

                elif effect == "ripple":
                    effect = "ripple_single"

                elif effect == "rippleRandomColour":
                    effect = "ripple_random"

                # Save values
                zone_states[zone]["effect"] = effect
                zone_states[zone]["params"] = params
                zone_states[zone]["colour1"] = colours["primary"]
                zone_states[zone]["colour2"] = colours["secondary"]
                zone_states[zone]["colour3"] = colours["tertiary"]


        except Exception as e:
            dbg.stdout("Unable to get device states for " + name, dbg.error)
            dbg.stdout(common.get_exception_as_string(e))
            dbg.stdout("This probably indicates a bug, wrong OpenRazer version or improperly specified Chroma device:\n{0} ({1}:{2})".format(name, vid, pid), dbg.warning)


    # Get battery data if device has a battery.
    if rdevice.has("battery"):
        battery_level = rdevice.battery_level
        battery_charging = rdevice.is_charging

    # TODO: Get Polychromatic custom effect data

    return {
        "name": name,
        "uid": uid,
        "backend": "openrazer",
        "vid": vid,
        "pid": pid,
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
        "dpi_single": dpi_single,
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


def set_device_state(uid, request, zone, colour_hex, params):
    """
    See: middleman.set_device_state(...)
    """
    try:
        # TODO: Speed up by initalising DeviceManager() once - param maybe?
        devman = rclient.DeviceManager()
        devman.sync_effects = False
        rdevice = devman.devices[uid]
    except KeyError:
        return None
    except Exception as e:
        return common.get_exception_as_string(e)

    zone_to_capability = _get_zone_capability_prefix()
    zone_to_device = _get_device_zones(rdevice)

    # Prepare colours (to RGB values)
    try:
        last_colours = _convert_colour_bytes(rdevice.fx.colors)
        colour_primary = common.hex_to_rgb(last_colours["primary"])
        colour_secondary = common.hex_to_rgb(last_colours["secondary"])
        colour_tertiary = common.hex_to_rgb(last_colours["tertiary"])
    except Exception:
        # Device does not support RGB colours.
        colour_primary = [0, 255, 0]        # Green
        colour_secondary = [255, 0, 0]      # Red
        colour_tertiary = [0, 0, 255]       # Blue

    if colour_hex:
        try:
            if colour_hex[0]:
                colour_primary = common.hex_to_rgb(colour_hex[0])
            if colour_hex[1]:
                colour_secondary = common.hex_to_rgb(colour_hex[1])
            if colour_hex[2]:
                colour_tertiary = common.hex_to_rgb(colour_hex[2])
        except IndexError:
            # Expected, as not all colours may be needed. Use default.
            pass

    try:
        ################################
        # Brightness
        ################################
        if request == "brightness":
            if zone == "main":
                is_brightness = rdevice.has("brightness")
            else:
                is_brightness = rdevice.has(zone_to_capability[zone] + "_brightness")
            is_active = rdevice.has(zone_to_capability[zone] + "_active")
            value = int(params[0])

            # Polychromatic merges "brightness" into either a scale (0-100%) or an on/off toggle.
            if is_brightness and not is_active:
                # 'main' brightness is outside the 'fx' class.
                if zone == "main":
                    rdevice.brightness = value
                else:
                    zone_to_device[zone].brightness = value

            elif is_active:
                # 'main' does not have an 'active' attribute
                if not zone == "main":
                    # 'active' accepts either True/False, or 0/1.
                    zone_to_device[zone].active = value

        ################################
        # Effects
        ################################
        elif request == "spectrum":
            # No params.
            return zone_to_device[zone].spectrum()

        elif request == "wave":
            # Params: <direction 1-2>
            return zone_to_device[zone].wave(int(params[0]))

        elif request == "reactive":
            # Params: <red> <green> <blue> <speed 1-4>
            return zone_to_device[zone].reactive(colour_primary[0], colour_primary[1], colour_primary[2], int(params[0]))

        elif request == "blinking":
            # Params: <red> <green> <blue>
            return zone_to_device[zone].blinking(colour_primary[0], colour_primary[1], colour_primary[2])

        elif request == "breath_random":
            # No params.
            return zone_to_device[zone].breath_random()

        elif request == "breath_single":
            # Params: <red> <green> <blue>
            return zone_to_device[zone].breath_single(colour_primary[0], colour_primary[1], colour_primary[2])

        elif request == "breath_dual":
            # Params: <red1> <green1> <blue1> <red2> <green2> <blue2>
            return zone_to_device[zone].breath_dual(colour_primary[0], colour_primary[1], colour_primary[2],
                colour_secondary[0], colour_secondary[1], colour_secondary[2])

        elif request == "breath_triple":
            # Params: <red1> <green1> <blue1> <red2> <green2> <blue2> <red3> <green3> <blue3>
            return zone_to_device[zone].breath_triple(colour_primary[0], colour_primary[1], colour_primary[2],
                colour_secondary[0], colour_secondary[1], colour_secondary[2],
                colour_tertiary[0], colour_tertiary[1], colour_tertiary[2])

        elif request == "pulsate":
            # Params: <red> <green> <blue>
            return zone_to_device[zone].pulsate(colour_primary[0], colour_primary[1], colour_primary[2])

        elif request == "ripple_single":
            # Params: <red> <green> <blue> <speed>
            return zone_to_device[zone].ripple(colour_primary[0], colour_primary[1], colour_primary[2], float(params[0]))

        elif request == "ripple_random":
            # Params: <red> <green> <blue> <speed>
            return zone_to_device[zone].ripple_random(float(params[0]))

        elif request == "starlight_single":
            # Params: <red> <green> <blue> <speed>
            return zone_to_device[zone].starlight_single(colour_primary[0], colour_primary[1], colour_primary[2], int(params[0]))

        elif request == "starlight_dual":
            # Params: <red1> <green1> <blue1> <red2> <green2> <blue2> <speed>
            return zone_to_device[zone].starlight_dual(colour_primary[0], colour_primary[1], colour_primary[2],
                colour_secondary[0], colour_secondary[1], colour_secondary[2], int(params[0]))

        elif request == "starlight_random":
            # Params: <speed>
            return zone_to_device[zone].starlight_random(int(params[0]))

        elif request == "static":
            # Params: <red> <green> <blue>
            return zone_to_device[zone].static(colour_primary[0], colour_primary[1], colour_primary[2])

        ################################
        # Other
        ################################
        elif request == "game_mode":
            # Params: <true/false>
            if params[0] in [True, "true"]:
                rdevice.game_mode_led = True
            else:
                rdevice.game_mode_led = False

        elif request == "dpi":
            # Params: <dpi X> <dpi Y>
            # DeathAdder 3.5G only supports DPI X (#209)
            if rdevice.has("available_dpi"):
                rdevice.dpi = (int(params[0]), -1)
            else:
                rdevice.dpi = (int(params[0]), int(params[1]))

        elif request == "poll_rate":
            # Params: <poll>
            rdevice.poll_rate = int(params[0])

        else:
            return False

    except Exception as e:
        return common.get_exception_as_string(e)

    return True


def set_device_colours(uid, zone, colour_hex):
    """
    See: middleman.set_device_colours()
    """
    try:
        # TODO: Speed up by initalising DeviceManager() once - param maybe?
        devman = rclient.DeviceManager()
        devman.sync_effects = False
        rdevice = devman.devices[uid]
    except KeyError:
        return None
    except Exception as e:
        return common.get_exception_as_string(e)

    device_zone = _get_device_zones(rdevice)[zone]

    daemon_to_poly_effect = {
        "blinking": "blinking",
        "pulsate": "pulsate",
        "breathSingle": "breath_single",
        "breathDual": "breath_dual",
        "breathTriple": "breath_triple",
        "starlightSingle": "starlight_single",
        "starlightDual": "starlight_dual",
        "ripple": "ripple_single",
        "reactive": "reactive",
        "static": "static"
    }

    # Skip non-Chroma devices.
    if not rdevice.has("lighting_led_matrix"):
        return True

    try:
        request = daemon_to_poly_effect[str(device_zone.effect)]
    except KeyError:
        return False

    try:
        # Effects that don't require parameters.
        if request in ["blinking", "breath_single", "breath_dual", "breath_triple", "pulsate", "static"]:
            set_device_state(uid, request, zone, colour_hex, None)

        # Effects that use the 'speed'
        elif request in ["starlight_single", "starlight_dual", "reactive"]:
            set_device_state(uid, request, zone, colour_hex, [int(device_zone.speed)])

        # Ripple data isn't stored as will reset to a default speed
        elif request in ["ripple_single"]:
            set_device_state(uid, request, zone, colour_hex, [0.01])

    except Exception as e:
        return common.get_exception_as_string(e)

    return True


def _get_device_zones(rdevice):
    """
    Returns a dictionary referencing the classes used for various zones for a device.
    """
    zone_to_device = {
        "main": rdevice.fx,
        "logo": rdevice.fx.misc.logo,
        "scroll": rdevice.fx.misc.scroll_wheel,
        "backlight": rdevice.fx.misc.backlight
    }

    # Ignore missing left/right classes, most devices do not support these.
    try:
        zone_to_device["left"] = rdevice.fx.misc.left
        zone_to_device["right"] = rdevice.fx.misc.right
    except Exception:
        pass

    return zone_to_device


def _get_supported_zones(rdevice):
    """
    Returns a list of zones that are supported by the device.
    """
    zones = []

    if rdevice.has("lighting"):
        zones.append("main")
    if rdevice.has("lighting_logo") or rdevice.has("lighting_logo_active"):
        zones.append("logo")
    if rdevice.has("lighting_scroll") or rdevice.has("lighting_scroll_active"):
        zones.append("scroll")
    if rdevice.has("lighting_left"):
        zones.append("left")
    if rdevice.has("lighting_right"):
        zones.append("right")
    if rdevice.has("lighting_backlight"):
        zones.append("backlight")

    return zones


def _get_zone_capability_prefix():
    """
    Returns a dictionary of the prefixes when reading a device's capabilities
    by zone.
    """
    return {
        "main": "lighting",
        "logo": "lighting_logo",
        "scroll": "lighting_scroll",
        "backlight": "lighting_backlight",
        "left": "lighting_left",
        "right": "lighting_right"
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

    import requests
    from .. import preferences as pref
    device_images_dir = pref.Paths().device_images
    image_path = os.path.join(device_images_dir, device.name)
    fallback_path = os.path.join(common.get_data_dir_path(), "ui/img/devices/noimage.svg")

    if os.path.exists(image_path) and os.stat(image_path).st_size > 8:
        return image_path

    if not real_image:
        dbg.stdout("No device image specified for " + device.name, dbg.warning, 1)
        return fallback_path

    dbg.stdout("Retrieving device image for " + device.name, dbg.warning, 1)
    try:
        r = requests.get(real_image)
        if r.status_code == 200:
            open(image_path, "wb").write(r.content)
            return image_path
        else:
            dbg.stdout("Unable to retrieve device image for " + device.name, dbg.error)
            dbg.stdout("    Status Code: " + str(r.status_code), dbg.error)
            dbg.stdout("    URL: " + real_image, dbg.error)
            return fallback_path
    except Exception as e:
        dbg.stdout("Failed to retrieve device image for " + device.name, dbg.warning)
        dbg.stdout("Exception: " + str(e), dbg.warning)
        return fallback_path


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
    Convert the daemon's '.colors' function to a string hex.
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


def debug_matrix(uid, row, column):
    """
    See: middleman.debug_matrix()
    """
    try:
        # TODO: Speed up by initalising DeviceManager() once - param maybe?
        devman = rclient.DeviceManager()
        devman.sync_effects = False
        rdevice = devman.devices[uid]
    except IndexError:
        return None
    except Exception as e:
        return common.get_exception_as_string(e)

    try:
        rdevice.fx.advanced.matrix[row, column] = (255,255,255)
        rdevice.fx.advanced.draw()
        return True
    except Exception as e:
        return common.get_exception_as_string(e)


def troubleshoot():
    """
    See: middleman.troubleshoot()
    """
    import shutil
    import os
    results = {"success": False}

    # In a future version of OpenRazer (3.0?), most of the troubleshooting is irrelevant as it should be all userspace.

    try:
        # Troubleshooting only supported on Linux.
        uname = os.uname()
        if uname.sysname != "Linux":
            return {"success": False}

        # Gather info about OpenRazer Daemon
        try:
            daemon_pid_file = os.path.join(os.environ["XDG_RUNTIME_DIR"], "openrazer-daemon.pid")
        except KeyError:
            daemon_pid_file = os.path.join("/run/user/", str(os.getuid()), "openrazer-daemon.pid")

        # Can openrazer-daemon be found?
        results["daemon_found"] = True if shutil.which("openrazer-daemon") != None else False

        # Is openrazer-daemon running?
        results["daemon_running"] = False
        if os.path.exists(daemon_pid_file):
            with open(daemon_pid_file) as f:
                daemon_pid = int(f.readline())
            if os.path.exists("/proc/" + str(daemon_pid)):
                results["daemon_running"] = True

        # Gather info about DKMS
        dkms_version = rclient.__version__
        kernel_version = uname.release
        expected_dkms_src = "/var/lib/dkms/openrazer-driver/{0}".format(dkms_version)
        expected_dkms_build = "/var/lib/dkms/openrazer-driver/kernel-{0}-{1}".format(uname.release, uname.machine)

        # Is the OpenRazer DKMS module installed?
        results["dkms_installed_src"] = True if os.path.exists(expected_dkms_src) else False
        results["dkms_installed_built"] = True if os.path.exists(expected_dkms_build) else False

        # Can the DKMS module be loaded?
        modprobe = subprocess.Popen(["modprobe", "-n", "razerkbd"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output = modprobe.communicate()[0].decode("utf-8")
        code = modprobe.returncode
        results["dkms_loaded"] = False
        if code == 0:
            results["dkms_loaded"] = True

        # Is a Razer DKMS module loaded right now?
        lsmod = subprocess.Popen(["lsmod"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        output = lsmod.communicate()[0].decode("utf-8")
        if output.find("razer") != -1:
            results["dkms_active"] = True
        else:
            results["dkms_active"] = False

        # Is secure boot the problem?
        if os.path.exists("/sys/firmware/efi"):
            if output.find("Required key") != -1:
                results["secure_boot"] = False
            else:
                results["secure_boot"] = True

        # Is user in plugdev group?
        groups = subprocess.Popen(["groups"], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
        results["plugdev"] = False
        if groups.find("plugdev") != -1:
            results["plugdev"] = True

        # Does plugdev have permission to read the files in /sys/?
        log_path = os.path.join(os.path.expanduser("~"), ".local/share/openrazer/logs/razer.log")
        if os.path.exists(log_path):
            with open(log_path) as f:
                log = f.readlines()
            if "".join(log).find("Could not access /sys/") == -1:
                results["plugdev_perms"] = True
            else:
                results["plugdev_perms"] = False

        # Supported device in lsusb?
        try:
            devman = rclient.DeviceManager()
            rdevices = devman.devices
            devices = _get_incompatible_device_list(rdevices)
            if devices != None:
                results["all_supported"] = True
                if len(devices) > 0:
                    results["all_supported"] = False
        except Exception:
            pass

    except Exception:
        return results

    results["success"] = True
    return results
