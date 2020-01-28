/*
 Polychromatic is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Polychromatic is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Polychromatic. If not, see <http://www.gnu.org/licenses/>.

 Copyright (C) 2019-2020 Luke Horwell <code@horwell.me>
*/

var DEVICES = null;
var DEVICES_TAB_CURRENT_DEVICE = null;

function update_device_list(callback) {
    //
    // Send request to controller to update the DEVICES variable for the frontend
    // to work with.
    //
    //  Params:
    //      callback        Optional name of function to run after completion.
    //
    send_data("update_device_list", {"callback": callback});
}

function set_tab_devices() {
    //
    // Open the tab for displaying all connected devices and current device state options.
    //
    $(".tab").removeClass("active");
    $("#devices-tab").addClass("active");
    set_title(get_string("devices"));

    send_data("update_device_list", {"callback": "_set_tab_devices"});
}

function _set_tab_devices() {
    //
    // DEVICES variable updated. Ready to populate data for the tab.
    //
    $(".tab").removeClass("active");
    $("#devices-tab").addClass("active");
    set_title(get_string("devices"));

    var sidebar = [];
    var content = `<div id="device-content"></div>`;
    var devices = [];

    // Controller returns:
    //
    // DEVICES == -1        Daemon not present
    // DEVICES == String    Daemon error (not initalised)
    // DEVICES == Array     Daemon OK. Contains device list.

    // ------------------------
    // Sidebar
    // ------------------------
    if (typeof(DEVICES) == "object") {
        for (d = 0; d < DEVICES.length; d++) {
            var device = DEVICES[d];
            var onclick;
            var classes;

            if (device.available === true) {
                onclick = `open_device(this, ${device.uid})`;
                classes = "";
                label = device.name;
            } else {
                onclick = `open_device_not_avaliable(this)`;
                classes = "dim";
                label = get_string("unknown-device").replace("[]", device.name);
            }

            devices[devices.length] = {
                "label": label,
                "icon": device.icon,
                "onclick": onclick,
                "classes": classes,
                "id": "device-" + device.uid
            }
        }

        // "Apply to All" only appears when there are multiple devices.
        if (DEVICES.length == 0) {
            sidebar[0] = {"label": get_string("no-device"), "items": []}

        } else if (DEVICES.length > 1) {
            sidebar[0] = {
                "label": get_string("tasks"),
                "items": [
                    {
                        "label": get_string("apply-to-all"),
                        "icon": "img/devices/all.svg",
                        "onclick": "open_device_to_all()",
                        "classes": "",
                        "id": "apply-to-all"
                    }
                ]
            }
            sidebar[1] = {"label": get_string("devices"), "items": devices}
        } else {
            sidebar[0] = {"label": get_string("devices"), "items": devices}
        }
    }

    // ------------------------
    // Content
    // ------------------------
    if (typeof(DEVICES) == "string") {
        // Show the error exception in a dialogue box.
        var body = `<p>${get_string("error_not_ready_text")}</p>
                       <p><pre>${DEVICES}</pre></p>`;
        open_dialog(get_string("error_not_ready_title"), body, "serious", "18em", "30em");
        content = _device_error("daemon-error");

    } else if (typeof(DEVICES) == "number") {
        content = _device_error("daemon-missing");

    } else if (typeof(DEVICES) == "object") {
        if (DEVICES.length == 0) {
            // Show no devices screen
            content = _device_error("no-device");
        }
    }

    set_layout_split(sidebar, content);

    // Open the first device
    if (typeof(DEVICES) == "object" && DEVICES.length >= 1) {
        if (DEVICES[0].available == true) {
            open_device($("#device-0"), 0);
        } else {
            open_device_not_avaliable();
        }
    }
}

function open_device_to_all() {
    //
    // Opens a section allowing the user to set an effect or brightness to all
    // compatible devices at the same time.
    //
    $(".sidebar-item").removeClass("active");
    $("#apply-to-all").addClass("active");
    set_title(get_string("apply-to-all"));

    var brightness = "";
    var effects = "";
    var output = "";

    // Brightness
    var intervals = [0, 25, 50, 75, 100];
    for (b = 0; b < 5; b++) {
        val = intervals[b];
        brightness += button_large("brightness-" + val, `apply_to_all('brightness', ${val})`, val + "%", `img/brightness/${val}.svg`);
    }

    // Effects
    effects += button_large("all-spectrum", "apply_to_all('effect', 'spectrum')", get_string("spectrum"), "img/effects/spectrum.svg");
    effects += button_large("all-wave", "apply_to_all('effect', 'wave')", get_string("wave"), "img/effects/wave.svg");
    effects += button_large("all-breath", "apply_to_all('effect', 'breath_random')", get_string("breath"), "img/effects/breath.svg");
    effects += button_large("all-reactive", "apply_to_all('effect', 'reactive')", get_string("reactive"), "img/effects/reactive.svg");
    effects += button_large("all-static", "apply_to_all('effect', 'static')", get_string("static"), "img/effects/static.svg");

    output += group_title(get_string("apply-to-all"));
    output += group(get_string("brightness"), brightness);
    output += group(get_string("effects"), effects);
    $("#device-content").html(output);
}

function apply_to_all(type, value) {
    //
    // Sends a request to the controller to set all devices to a specific state.
    //
    //  type        String: 'effects' or 'brightness'
    //  value       Data value to pass to controller, e.g. brightness value or effect name.
    //
    send_data("apply_to_all", {"type": type, "value": value});
}

function open_device(element, uid) {
    //
    // Show the details page for a registered device. This sends a request to
    // the controller to retrieve the device's details.
    //
    //  uid         ID from OpenRazer backend.
    //
    $(".sidebar-item").removeClass("active");
    $(element).addClass("active");
    send_data("open_device", {"uid": uid});
}

function _open_device(device) {
    //
    // Callback when device details are returned.
    //
    //  data        JSON data returned from Controller describing the device.
    //
    set_title(device.name);

    DEVICES_TAB_CURRENT_DEVICE = device;

    // Assemble status (top area) and controls.
    $("#device-content").html(`
        <div class="common-info">
            <div id="main-image" style="background-image:url(${device.real_image});"></div>
            <div id="main-text">
                <h3>${device.name}</h3>
                <div class="states">
                    ${_get_state_html(device)}
                </div>
            </div>
            <button id="more-details-btn" onclick="_show_device_info(${device})">${get_string("device-info")}</button>
        </div>
        <div id="device-controls">
            ${_get_device_controls(device, "set_device_state(this)")}
        </div>`);
}

function _get_state_html(device) {
    //
    // Returns HTML summarising key features of a device.
    //
    //  device      JSON data describing the device.
    //
    var output = "";
    var zones = Object.keys(device.zone_states);
    var multizoned = zones.length > 1 ? true : false;

    function _get_state(image, text) {
        return `<div class="state">
                    <img src="${image}"/>
                    <span>${text}</span>
                </div>`;
    }

    for (s = 0; s < zones.length; s++) {
        var zone = zones[s];
        var name = device.zone_names[zone];
        var state = device.zone_states[zone];

        // -- Current effect
        var effect = state["effect"]

        if (effect != undefined) {
            effect = effect.split("_")[0];
            output += _get_state(`img/effects/${effect}.svg`, get_string(effect));
        }

        // -- Current brightness
        var brightness = state["brightness"];
        if (brightness != undefined) {
            // Is this device have just an on/off switch?
            if (device.zone_supported[zone].brightness_toggle == true) {
                brightness = brightness == 1 ? get_string("on") : get_string("off");
            } else {
                brightness = brightness + "%";
            }

            var icon = "img/brightness/100.svg";
            if (multizoned === true)
                icon = device.zone_icons[zone];

            output += _get_state(icon, brightness);
        }
    }

    // TODO: In future, only show current profile (with link)

    // -- Current battery
    var battery = device["battery_level"];
    if (battery != undefined) {
        output += _get_state("img/fa/battery.svg", battery + "%");
    }

    // -- DPI
    var dpi_x = device["dpi_x"];
    var dpi_y = device["dpi_y"];
    var dpi_only_x = device["dpi_single"];
    if (dpi_x != null) {
        if (dpi_only_x === true || dpi_x === dpi_y) {
            output += _get_state("img/general/dpi.svg", dpi_x);
        } else if (dpi_x !== dpi_y) {
            output += _get_state("img/general/dpi.svg", `${dpi_x}, ${dpi_y}`);
        }
    }

    // -- Poll Rate
    var poll_rate = device["poll_rate"];
    if (poll_rate != null) {
        output += _get_state("img/fa/poll-rate.svg", `${poll_rate} Hz`);
    }

    return output;
}

function _get_device_controls(device, onclick) {
    //
    // Returns HTML of all the possible controls for a device. This code is common
    // across the devices tab (instant changes) as well as profiles (defining controls)
    //
    //  device          JSON data describing the device.
    //  onclick         Function to call when setting a box. This is expected to parse the controls.
    //
    var output = "";

    var zones = Object.keys(device.zone_states);
    var multizoned = zones.length > 1 ? true : false;
    for (s = 0; s < zones.length; s++) {
        var zone = zones[s];
        var name = device.zone_names[zone];
        var state = device.zone_states[zone];
        var supported = device.zone_supported[zone];

        // Only show group names when there are multiple zones.
        if (multizoned === true) {
            output += group_title(name);
        }

        // IDs for checkboxes are in format: [name]-[zone], which will be used in the specified 'onclick' function.

        // Brightness
        if (supported.brightness_slider == true) {
            output += group(get_string("brightness"), slider(`${zone}-brightness`, onclick, 0, 100, 5, state.brightness, "%"));
        }

        if (supported.brightness_toggle == true) {
            output += group(get_string("brightness"), checkbox(`${zone}-brightness`, get_string("on"), state.brightness == 1 ? true : false, onclick));
        }

        // Effects
        var current_effect = state["effect"];
        var effect;
        var subeffect;

        if (current_effect != undefined) {
            [effect, subeffect] = current_effect.split("_");

            var fx_output = "";
            known_fx = ["spectrum", "wave", "reactive", "breath", "ripple", "pulsate", "blinking", "static"];
            for (f = 0; f < known_fx.length; f++) {
                if (supported[known_fx[f]] == true) {
                    var fx_name = known_fx[f];
                    var fx_request = fx_name;
                    fx_output += button_large(`${zone}-${fx_name}`, onclick, get_string(fx_name), `img/effects/${fx_name}.svg`, false, fx_name == effect ? true : false);
                }
            }

            output += group(get_string("effect"), fx_output);

            // Effect Options (if applicable, like "random", "single", etc)
            var fx_options = "";

            var fx_id = `${zone}-${effect}`;
            var fx_grp = `${zone}-${effect}-group`;
            var params = state["params"];
            var param0 = "";
            if (params != undefined) {
                param0 = params[0];
            }

            switch(effect) {
                case "wave":
                    var labels = _get_wave_direction(device["form_factor_id"]);
                    fx_options += radio(`${fx_id}-left`, labels[0], param0 == 2, fx_grp, onclick);
                    fx_options += radio(`${fx_id}-right`, labels[1], param0 == 1, fx_grp, onclick);
                    break;
                case "reactive":
                    fx_options += radio(`${fx_id}-fast`, get_string("fast"), param0 == 1,  fx_grp, onclick);
                    fx_options += radio(`${fx_id}-medium`, get_string("medium"), param0 == 2, fx_grp, onclick);
                    fx_options += radio(`${fx_id}-slow`, get_string("slow"), param0 == 3, fx_grp, onclick);
                    fx_options += radio(`${fx_id}-vslow`, get_string("vslow"), param0 == 4, fx_grp, onclick);
                    break;
                case "ripple":
                case "breath":
                case "starlight":
                    var options = supported[`${effect}_options`];
                    for (i = 0; i < Object.keys(options).length; i++) {
                        var option = options[i];
                        fx_options += radio(`${fx_id}-${option}`, get_string(option), subeffect == option, fx_grp, onclick);
                    }
                    break;
            }

            if (fx_options.length > 0) {
                var label = get_string("effect_options");
                switch(effect) {
                    case "wave":
                    case "reactive":
                    case "breath":
                    case "ripple":
                        label = get_string(`${effect}_options`);
                        break;
                }
                output += group(label, fx_options);
            }
        }

        // Colours
        // -- Primary
        switch(current_effect) {
            case "static":
            case "reactive":
            case "blinking":
            case "pulsate":
            case "breath_single":
            case "breath_dual":
            case "breath_triple":
            case "ripple_single":
            case "starlight_single":
            case "starlight_dual":
                output += group(get_string("primary_colour"), colour_picker(`${zone}-primary`, onclick, state["colour1"]));
        }

        switch(current_effect) {
            case "breath_dual":
            case "breath_triple":
            case "starlight_dual":
                output += group(get_string("secondary_colour"), colour_picker(`${zone}-secondary`, onclick, state["colour2"]));
        }

        switch(current_effect) {
            case "breath_triple":
                output += group(get_string("teritary_colour"), colour_picker(`${zone}-teritary`, onclick, state["colour3"]));
        }

        if (zone == "main") {
            // Game Mode
            if (device["game_mode"] != null) {
                output += group(get_string("game_mode"), checkbox("game-mode", get_string("enabled"), device["game_mode"], onclick));
            }

            // DPI
            // TODO: Fancier DPI selector
            if (device["dpi_x"] != null) {
                var dpiRange = device["dpi_ranges"];
                output += group(get_string("dpi"), dropdown("dpi", onclick, device["dpi_x"], [
                    [dpiRange[0], dpiRange[0]],
                    [dpiRange[1], dpiRange[1]],
                    [dpiRange[2], dpiRange[2]],
                    [dpiRange[3], dpiRange[3]],
                    [dpiRange[4], dpiRange[4]],
                    [dpiRange[5], dpiRange[5]]
                ], false));
            }

            // Poll Rate
            if (device["poll_rate"] != null) { // WHY NOT WORKING?!!!
                output += group(get_string("poll_rate"), dropdown("poll-rate", onclick, device["poll_rate"], [
                    [get_string("poll_rate_125"), 125],
                    [get_string("poll_rate_500"), 500],
                    [get_string("poll_rate_1000"), 1000]
                ], false));
            }
        }
    }

    return output;
}

function set_device_state(element, backend, uid, request, zone) {
    //
    // Change the state of a specific device right now. Used on the 'Devices' tab.
    //
}

}

function _device_error(id) {
    //
    // Returns HTML for a 'pretty' error screen when something is wrong.
    //

    // daemon-error         fa/serious
    // daemon-missing       fa/warning
    // no-device            devices/accessory
    // unrecog-device       devices/accessory? (unrecognised)
    return id;
}

function open_device_not_avaliable(element) {
    //
    // Device is not registered in the daemon, inform the user.
    //
    $(".sidebar-item").removeClass("active");
    $(element).addClass("active");

}

function _get_wave_direction(form_factor_id) {
    //
    // Returns a list of localised direction strings according to the device's form factor.
    //
    switch(form_factor_id) {
        case "mouse":
            return [get_string("down"), get_string("up")];
        case "mousemat":
            return [get_string("clockwise"), get_string("anticlockwise")];
    }

    return [get_string("left"), get_string("right")];
}
