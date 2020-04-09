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

/*****************************
 * Send data to Python
*****************************/
function send_data(request, data) {
    data["request"] = request;
    document.title = JSON.stringify(data);
}


/*****************************
 * Global Variables
*****************************/
// Strings stored as JSON (passed from Python on app start)
var LOCALE;
var BUTTON_SVGS;
var ICONS_TRAY;
var ICONS_EMBLEMS;
var VERSION;
var COLOURS;
var PREFERENCES;
var CUSTOM_ICONS;

// For CSS transitions that are timed in JavaScript.
var TRANSITION_SPEED = 300 + 50;

// Backend status
var BACKEND_OPENRAZER = false;

// Cached responses from controller
var CACHE_DEVICE_LIST = null;       // -- get_device_list() listing all devices.
var CACHE_CURRENT_DEVICE = null;    // -- get_device() for current device.


/*****************************
 * Common Functions
*****************************/
function get_string(string) {
    return LOCALES[string];
}

function get_svg(name) {
    return BUTTON_SVGS[name];
}

function get_random_element_id() {
    var time = new Date().getTime();
    return "id-" + time;
}


/*****************************
 * Main application
*****************************/
// Run when application first starts.
function build_view(data) {
    //
    // Reset the entire application's interactive elements.
    //
    function _add_header_button(id, fn, image, label) {
        return `<button id="${id}-tab" class="tab" onclick="${fn}" onwheel="_onwheel(event, this)"><img src="${image}"/><span>${label}</span></button>`;
    }

    var header = `
        <h3 id="title"></h3>
        <div id="header-tabs" class="tabs">
            ${_add_header_button("devices", "set_tab_devices()", "img/devices/keyboard.svg", get_string("devices"))}
            <!--
                FIXME: Features not present. Requires further development.
            ${_add_header_button("effects", "set_tab_effects()", "img/general/effects.svg", get_string("effects"))}
            ${_add_header_button("profiles", "set_tab_profiles()", "img/general/profiles.svg", get_string("profiles"))}
            ${_add_header_button("events", "set_tab_events()", "img/general/events.svg", get_string("events"))}
            -->
            <div class="right">
                ${_add_header_button("preferences", "set_tab_preferences()", "img/general/preferences.svg", get_string("preferences"))}
            </div>
        </div>
    `;

    var footer = `
        <button onclick="quit()">${get_string("close-app")}</button>
    `;

    $("header").html(header);
    $("content").html(" ");
    $("footer").html(footer);
}

function quit() {
    send_data("quit", {});
}

function set_title(title) {
    //
    // Sets the title of the current view.
    //
    $("#title").html(title);
}

function set_layout_split(sidebar, content) {
    //
    // Resets the layout to the common left-right sidebar-content presentation.
    //
    // Params:
    //      sidebar         (list)      An array describing the sidebar.
    //                                  [{"label": "Name of Group", items: [{"icon": str, "label": str, "onclick": str, "classes": str, "id": str}]}]
    //      content         (str)       HTML content.
    //
    var sidebar_html = `<div class="sidebar-items">`;
    for (g = 0; g < sidebar.length; g++) {
        var group = sidebar[g];

        sidebar_html += `<div class="sidebar-item-group">
                            <div class="sidebar-heading">${group.label}</div>`;

        for (i = 0; i < group.items.length; i++) {
            var item = group.items[i];

            sidebar_html += `<button id="${item.id}" class="sidebar-item ${item.classes}" onclick="${item.onclick}" onwheel="_onwheel(event, this)">
                    <img src="${item.icon}"/> <span>${item.label}</span>
                </button>`;
        }

        sidebar_html += `</div>`;
    }
    sidebar_html += `</div>`;

    $("content").html(`
        <div class="sidebar-container">
            <div class="left">
                ${sidebar_html}
            </div>
            <div class="right">
                ${content}
            </div>
        </div>`);
}


/*****************************
 * Colour Conversion
*****************************/
// Hex -> RGB
function hex_to_rgb(hex) {
    //
    // Converts from hex to decimal. Outputs [R,G,B].
    //
    return [
        "0x" + hex[1] + hex[2] | 0,
        "0x" + hex[3] + hex[4] | 0,
        "0x" + hex[5] + hex[6] | 0
    ];
}

function rgb_to_hex(r,g,b) {
    //
    // Converts from decimal to hex. Outputs "#RRGGBB".
    //
    function _to_hex(input) {
        input = Number(input);
        if (input.toString().length < 2) {
            input = "0" + input;
        }
        return input.toString(16);
    }
    return "#" + _to_hex(r) + _to_hex(g) + _to_hex(b);
}

/*****************************
 * Behaviours
*****************************/
/* Prevent accidental drops onto the window */
$(document).on({
    dragover: function() {
        return false;
    },
    drop: function() {
        return false;
    }
});


/*****************************
 * Misc
*****************************/
function _warn_save_data_version(data) {
    //
    // Issued by Controller. Shows a warning when the save data is newer then the application.
    //
    // data {} => app_version, pref_version, save_version
    //
    var app_version = data["app_version"];
    var pref_version = data["pref_version"];
    var save_version = data["save_version"];
    var body = `
        <p>${get_string("save_data_warning_text1")}</p>
        <p>${get_string("save_data_warning_text2")}</p>
        <p>
            <code>${get_string("save_data_warning_app_version")} ${app_version}</code>
            <br>
            <code>${get_string("save_data_warning_saved_version")} ${save_version} ${get_string("save_data_warning_pref_version").replace("1", pref_version)}</code>
        </p>
        <p>${get_string("save_data_warning_text3").replace("~/.config/polychromatic", "<code>~/.config/polychromatic</code>")}</p>
    `;

    open_dialog(get_string("save_data_warning_title"), body, "serious", [[get_string("ok"), ""]], "18em", "40em")
}

function open_help() {
    send_data("open_uri", {uri: "https://polychromatic.app/docs"});
}

function open_troubleshooter() {
    send_data("troubleshoot_openrazer", {});
}

function _show_troubleshoot_results(data) {
    //
    // Issued by Controller. Opens a dialog showing the results and suggestions
    // for the user to try.
    //
    // Params:
    //    data          See openrazer.py troubleshoot()
    //
    var full_test = data["success"];
    var tests = Object.keys(data);
    var results_html = "";

    var icons = {
        false: "img/general/warning.svg",
        true: "img/general/success.svg",
        null: "img/general/unknown.svg"
    }

    var colours = {
        false: "yellow",
        true: "lime",
        null: "gray"
    }

    for (t = 0; t < tests.length; t++) {
        var test = tests[t];
        if (test == "success") continue;
        var result = data[test];
        results_html += `<tr>
            <td style="color:${colours[result]}"><img src="${icons[result]}"/> ${get_string("troubleshoot_" + test)}</td>
        </tr>`

        if (result == false) {
            var suggestion = get_string("troubleshoot_" + test + "_suggestion");

            // Place a '$' before a command to apply code formatting (until end of line)
            if (suggestion.search("$") != -1) {
                suggestion = suggestion.replace("$ ", "<code>") + "</code>";
            }
            results_html += `<tr>
                <td style="opacity:0.75; padding:0.25em 2.5em 1em">${suggestion}</td>
            </tr>`;
        }
    }

    var body = `<p style="margin:0.5em 6em 1em 0">
            ${ full_test ? get_string("troubleshoot_test_complete") : get_string("troubleshoot_test_partial")}
        </p>
        <div style="height:50vh; overflow:auto">
            <table class="no-grid">
                <tbody>
                    ${results_html}
                </tbody>
            </table>
        </div>`;

    open_dialog(get_string("troubleshoot"), body, null, [[get_string("open-help"), "open_help()"], [get_string("close"), ""]], "80vh", "40em")
}
