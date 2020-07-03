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

 Copyright (C) 2020 Luke Horwell <code@horwell.me>
*/

function set_tab_effects() {
    //
    // Open the tab to show all effects that the user can create, delete or modify.
    //
    $(".tab").removeClass("active");
    $("#effects-tab").addClass("active");
    set_title(get_string("devices"));

    cursor_wait_background();
    send_data("get_effect_list", {"callback": "_set_tab_effects"});
}

function _set_tab_effects() {
    //
    // CACHE_EFFECTS variable updated. Ready to populate data for the tab.
    //
    $(".tab").removeClass("active");
    $("#effects-tab").addClass("active");
    set_title(get_string("effects"));
    cursor_normal();

    var sidebar = [];
    var content = `<div id="effect-content"></div>`;
    var devices = [];

    // ------------------------
    // Sidebar
    // ------------------------
    var empty_library = true;

    // -- Tasks
    sidebar[sidebar.length] = {
        "label": get_string("tasks"),
        "items": [
            {
                "label": get_string("new_effect"),
                "icon": "img/general/new.svg",
                "onclick": "new_effect()",
                "classes": "disabled",
                "id": "new-effect"
            },
            {
                "label": get_string("import"),
                "icon": "img/general/import.svg",
                "onclick": "import_effect()",
                "classes": "disabled",
                "id": "import-effect"
            }
        ]
    };

    // -- Library
    effects = [];

    for (e = 0; e < CACHE_EFFECTS.length; e++) {
        var effect = CACHE_EFFECTS[e];
        effects[effects.length] = {
            "label": effect.name,
            "icon": effect.icon,
            "onclick": `open_effect(this, &quot;${effect.filepath}&quot;, '${effect.type}')`,
            "classes": "",
            "id": `effect-${e}`
        };
    }

    sidebar[sidebar.length] = {
        "label": get_string("effects"),
        "items": effects
    };

    // ------------------------
    // Content
    // ------------------------
    set_layout_split(sidebar, content);

    // Open first effect if present
    if (effects.length > 0) {
        open_effect($("#effect-0"), CACHE_EFFECTS[0].filepath, CACHE_EFFECTS[0].type);
    }
}

function open_effect(element, filepath) {
    //
    // Show the details page for an effect. This sends a request to
    // the controller to retrieve the effect's details.
    //
    //  filepath    Path to the effect
    //
    $(".sidebar-item").removeClass("active");
    $(element).addClass("active");
    send_data("get_effect", {
        "callback": "_open_effect",
        "filepath": filepath
    });
    cursor_wait_background();
}

function _open_effect(effect) {
    //
    // Callback when effect details are returned.
    //
    //  effect      JSON data returned from Controller
    //
    CACHE_CURRENT_EFFECT = effect;
    set_title(effect.ui.name);
    cursor_normal();

    // Determine current status
    function _get_state(image, text) {
        return `<div class="state">
                    <img src="${image}"/>
                    <span>${text}</span>
                </div>`;
    }

    var states_html = "";
    var states_author_html = _get_state("img/effects/author.svg", effect.author);

    if (effect.type == "keyframed") {
        states_html += _get_state("img/effects/layer-middle.svg", get_string("keyframed"));
        states_html += states_author_html;
        states_html += _get_state(`img/devices/${effect.optimised.form_factor}.svg`, get_string(effect.optimised.form_factor));

    } else if (effect.type == "scripted") {
        states_html += _get_state("img/emblems/code.svg", get_string("scripted"));
        states_html += states_author_html;

        var form_factors = effect.depends.form_factor;
        if (form_factors.length == 1) {
            states_html += _get_state(`img/devices/${form_factors[0]}.svg`, get_string(form_factors[0]));
        } else {
            states_html += _get_state("img/devices/all.svg", get_string("multiple"));
        }

        if (effect.ui.tampered === false) {
            states_html += _get_state("img/general/serious.svg", get_string("tampered"));
        }
    }

    // Assemble status (top area) and controls.
    $("#effect-content").html(`
        <div class="common-info">
            <div id="main-image" style="background-image:url('${effect.ui.icon}');"></div>
            <div id="main-text">
                <h3>${effect.ui.name}</h3>
                <div class="states">
                    ${states_html}
                </div>
            </div>
            <div id="main-buttons">
                ${button("effect-play", "play_current_effect()", get_string("play"), "play")}
                ${button("effect-edit", "edit_current_effect()", get_string("edit"), "edit")}
                ${button("effect-del", "delete_current_effect()", get_string("delete"), "bin", true, true)}
            </div>
        </div>
        <div id="effect-preview">
            Not yet implemented
        </div>`);
}

function _open_effect_error() {
    //
    // Empty effect screen when a file cannot be read
    //
    cursor_normal();
    $(".sidebar-item.active").addClass("dim");

    var content = `<div class="common-info error">
            <div id="main-image" style="background-image:url('img/general/warning.svg');"></div>
            <div id="main-text">
                <h3>${get_string("read_error_title")}</h3>
            </div>
        </div>
        <p>${get_string("read_error_aftermath_effect").replace(".", ".<br><br>")}</p>`;
    $("#effect-content").html(content);
}

function play_current_effect() {
    //
    // Requests the Controller to play the currently loaded effect.
    //
    // This will play the current effect on all supported devices.
    //
    var form_factors;
    var filepath = CACHE_CURRENT_EFFECT.ui.filepath;
    var device_list = [];
    cursor_wait_foreground();

    switch(CACHE_CURRENT_EFFECT.type) {
        case "keyframed":
            form_factors = [CACHE_CURRENT_EFFECT.optimised.form_factor];
            break;
        case "scripted":
            form_factors = CACHE_CURRENT_EFFECT.depends.form_factor;
            break;
    }

    for (d = 0; d < CACHE_DEVICES.length; d++) {
        for (f = 0; f < form_factors.length; f++) {
            var device = CACHE_DEVICES[d];
            var form_factor = form_factors[f];
            if (device.form_factor_id === form_factor) {
                device_list[device_list.length] = {"backend": device.backend, "uid": device.uid};
            }
        }
    }

    send_data("render_effect", {
        "render_mode": "hardware",
        "device_list": device_list,
        "filepath": filepath,
        "callback": "_play_current_effect_cb"
    });
}

function _play_current_effect_cb() {
    //
    // Callback when the current effect in now playing.
    //
    cursor_normal();
    $("#effect-play").addClass("disabled").blur();
    $("#effect-play > span").html(get_string("playing"));
}

function edit_current_effect() {
    //
    // Opens the effect editor for the currently loaded effect data.
    //
    var effect_type = CACHE_CURRENT_EFFECT.type;

    switch(effect_type) {
        case "keyframed":
            open_keyframe_editor(CACHE_CURRENT_EFFECT);
            break;
        case "scripted":
            open_script_editor();
            break;
    }
}

function delete_current_effect() {
    //
    // Confirms whether the currently loaded effect should be deleted.
    //
    // FIXME: Stub!
    console.error("not yet implemented");
}

function open_script_editor() {
    //
    // Requests the Controller to open the current scripted effect.
    //
    send_data("get_effect_script", {
        "callback": "_open_script_editor",
        "filepath": CACHE_CURRENT_EFFECT.ui.filepath
    });
}

function _open_script_editor(data) {
    //
    // Callback when the script is loaded, or an error occurred.
    //
    var effect = CACHE_CURRENT_EFFECT;
    disable_tabs();
    set_title(get_string("script_editor_title").replace("[]", effect.ui.name));

    var sidebar = [
        {
            "label": get_string("sections"),
            "items": [
                {
                    "label": get_string("properties"),
                    "icon": "img/editor/properties.svg",
                    "onclick": "_open_fx_properties_pane()",
                    "classes": "",
                    "id": "properties-btn"
                },
                {
                    "label": get_string("editor"),
                    "icon": "img/emblems/code.svg",
                    "onclick": "_open_fx_editor_pane()",
                    "classes": "",
                    "id": "editor-btn"
                }
            ]
        }
    ]

    // Unlike main tabs, the content is always visible, but hidden behind a togglable sidebar.
    var content = "";

    // -----------------------
    // Properties
    // -----------------------

    content += `<div id="fx-properties-pane" style="display:none">`;

    content += group_title(get_string("properties"));
    content += group(get_string("name"), textbox("name", effect.name, null), true);
    // TODO: i18n fields for name
    content += group(get_string("author"), textbox("author", effect.author, null), true);
    content += group(get_string("summary"), textbox("summary", effect.summary, null), true);
    // TODO: i18n fields for summary
    content += group(get_string("icon"), icon_picker("icon", effect.icon, ""), true);

    // Form Factors
    var ff_options = ["accessory", "keyboard", "mouse", "mousemat", "keypad", "headset", "gpu"];
    var ff_checkboxes = "";
    for (f = 0; f < ff_options.length; f++) {
        var option_name = ff_options[f];
        ff_checkboxes += checkbox(option_name, get_string(option_name), effect.depends.form_factor.includes(option_name), "") + "<br>";
    }
    content += group(get_string("designed_form_factors"), checkbox_grid(ff_checkboxes));

    // Parameters
    content += group(get_string("parameters"), textarea("parameters", JSON.stringify(effect.parameters)), true);

    // Read only
    content += group(get_string("save_revision"), effect.revision, true);

    content += "</div>";

    content += `<div id="fx-editor-pane">`;
    content += group_title(get_string("script_editor"));
    content += textarea("script-editor", data.join(""));
    content += "</div>";

    // ------------------------
    // Content
    // ------------------------
    set_layout_split(sidebar, content);

    $("#editor-btn").addClass("active");

    $("footer").html(`

        ${button("open-external", "", get_string("open_external_editor"), "external")}
        ${footer_separator()}
        ${button("revert-btn", "", get_string("revert"), "remove")}
        ${button("save-btn", "", get_string("save"), "save")}
        ${button("save-quit-btn", "", get_string("save-exit"), "exit")}
    `);

    $("#revert-btn").on("click", function() {
        open_dialog(get_string("revert_prompt_title"), get_string("revert_prompt_text"), "warning", [[get_string("cancel"), ""], [get_string("revert"), "_exit_editor_nosave()"]], "10em", "24em");
    });
function _open_fx_properties_pane() {
    //
    // Swap view to the properties list.
    //
    $(".sidebar-item").removeClass("active");
    $("#properties-btn").addClass("active");

    $("#fx-properties-pane").show();
    $("#fx-editor-pane").hide();
}

function _open_fx_editor_pane() {
    //
    // Swap view to the effect editor (keyframed or scripted).
    //
    $(".sidebar-item").removeClass("active");
    $("#editor-btn").addClass("active");

    $("#fx-properties-pane").hide();
    $("#fx-editor-pane").show();
}

function _exit_editor_nosave() {
    //
    // User wants to leave the editor discarding changes.
    //
    console.error("not yet implemented");
}
