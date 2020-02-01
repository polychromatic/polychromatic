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

// For CSS transitions that are timed in JavaScript.
var TRANSITION_SPEED = 300 + 50;

// Backend status
var OPENRAZER_READY = false;

// Cached responses from controller
var CACHE_DEVICE_LIST = null;       // -- get_device_list() listing all devices.
var CACHE_CURRENT_DEVICE = null;    // -- get_device() for current device.
var COLOURS = null;


/*****************************
 * Common Functions
*****************************/
function get_string(string) {
    return LOCALES[string];
}

function get_svg(name) {
    return svg[name];
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
        return `<button id="${id}-tab" class="tab" onclick="${fn}"><img src="${image}"/><span>${label}</span></button>`;
    }

    var header = `
        <h3 id="title"></h3>
        <div id="header-tabs" class="tabs">
            ${_add_header_button("devices", "set_tab_devices()", "img/devices/keyboard.svg", get_string("devices"))}
            ${_add_header_button("effects", "set_tab_effects()", "img/fa/effects.svg", get_string("effects"))}
            ${_add_header_button("profiles", "set_tab_profiles()", "img/fa/profiles.svg", get_string("profiles"))}
            ${_add_header_button("schedule", "set_tab_schedule()", "img/fa/schedule.svg", get_string("schedule"))}
            <div class="right">
                ${_add_header_button("preferences", "set_tab_preferences()", "img/fa/preferences.svg", get_string("preferences"))}
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

            sidebar_html += `<button id="${item.id}" class="sidebar-item ${item.classes}" onclick="${item.onclick}">
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
