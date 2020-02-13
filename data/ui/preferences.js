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

function set_tab_preferences() {
    //
    // Open the tab for configuring the application's options.
    //
    send_data("reload_preferences", {"callback": "_set_tab_preferences"});
}

function _set_tab_preferences() {
    //
    // CACHE_DEVICES variable updated. Ready to populate data for the tab.
    //
    $(".tab").removeClass("active");
    $("#preferences-tab").addClass("active");
    set_title(get_string("preferences"));

    // ------------------------
    // Sidebar
    // ------------------------
    var sidebar = [
        {
            "label": get_string("application"),
            "items": [
                {
                    "icon": "img/emblems/software.svg",
                    "label": get_string("general"),
                    "onclick": "show_pref('general')",
                    "classes": "",
                    "id": "nav-general"
                },
                {
                    "icon": "img/general/tray-applet.svg",
                    "label": get_string("tray_applet"),
                    "onclick": "show_pref('tray')",
                    "classes": "",
                    "id": "nav-tray"
                },
                {
                    "icon": "img/general/palette.svg",
                    "label": get_string("saved_colours"),
                    "onclick": "show_pref('colours')",
                    "classes": "",
                    "id": "nav-colours"
                },
                {
                    "icon": "img/logo/polychromatic.svg",
                    "label": get_string("about"),
                    "onclick": "show_pref('about')",
                    "classes": "",
                    "id": "nav-about"
                }
            ]
        },
        {
            "label": get_string("backends"),
            "items": [
                {
                    "icon": "img/logo/openrazer.svg",
                    "label": "OpenRazer",
                    "onclick": "show_pref('openrazer')",
                    "classes": "",
                    "id": "nav-openrazer"
                }
            ]
        }
    ]

    // ------------------------
    // Content
    // ------------------------
    // Sections are hidden and revealed via show_pref("<id>")
    function _program_logo(img, name) {
        return `<div class="program-logo">
            <img src="${img}">
            <span>${name}</span>
        </div>`;
    }

    function _program_link(url, name) {
        return `<p><a onclick="open_uri('${url}')" title="${url}">${name}</a></p>`;
    }

    // -- About [Application]
    var about = "";
    about += `${_program_logo("img/logo/polychromatic.svg", "polychromatic")}
    <div class="program-links">
        ${_program_link("https://polychromatic.app", "https://polychromatic.app")}
    </div>`;

    about += group_title(get_string("application"));
    about += group(get_string("version"), `<code class="transparent">${VERSION.polychromatic}</code>`, true);
    about += group(get_string("save_format"), `<code class="transparent">${VERSION.polychromatic_pref}</code>`, true);

    about += group_title(get_string("dependencies"));
    about += group("Python", `<code class="transparent">${VERSION.python}</code>`, true);
    about += group("WebKit2", `<code class="transparent">${VERSION.webkit}</code>`, true);
    about += group("PyGObject", `<code class="transparent">${VERSION.gi}</code>`, true);
    about += group("GTK", `<code class="transparent">${VERSION.gtk}</code>`, true);

    about += group_title(get_string("links"));
    about += `<div style="margin: 0 2em;">
        ${button("view-src-1", "open_uri('https://github.com/polychromatic/polychromatic')", get_string("view_source_code"), "external")}
        ${button("whats-new-1", "open_uri('https://github.com/polychromatic/polychromatic/releases/latest')", get_string("whats_new"), "external")}
    </div>`;

    about += group_title(get_string("license"));
    var license_link = `<a onclick="open_uri('https://polychromatic.app/docs/license/')">https://polychromatic.app/docs/license/</a>`;
    about += `<div style="margin: 0 2em;">
        <p>${get_string("license_line_1")}</p>
        <p>${get_string("license_line_2")}</p>
        <p>${get_string("license_line_3").replace("[url]", license_link)}</p>
        <p><a onclick="open_license_notices()">${get_string("license_notices")}</a></p>
    </div>`;

    // -- General [Application]
    var general = group_title(get_string("effects"));
    general += group(get_string("editor"), checkbox("effect_live_preview", get_string("effect_live_preview"), PREFERENCES["effects"]["live_preview"], "change_pref('effects', 'live_preview', this.checked)"))

    // -- Tray Applet [Application]
    var _icon_path = PREFERENCES["tray"]["icon"];
    if (_icon_path.startsWith("ui/") === true) {
        _icon_path = "../" + _icon_path;
    }

    var tray = group_title(get_string("appearance"));
    tray += group(get_string("icon"), icon_picker("tray_icon", ICONS_TRAY, _icon_path));

    tray += group_title(get_string("advanced"));
    tray += group(get_string("compatibility"), checkbox("force_legacy_gtk_status", get_string("force_legacy_gtk_status"), PREFERENCES["tray"]["force_legacy_gtk_status"], "change_pref('tray', 'force_legacy_gtk_status', this.checked)"));

    // -- Saved Colours [Application]
    var colours = group_title(get_string("default_colours"));
    colours += help_text(get_string("about_saved_colours"))
    colours += group(get_string("primary_colour"), colour_picker("default-primary", "_save_default_colour(0)", PREFERENCES["colours"]["primary"], get_string("primary_colour"), false), true);
    colours += group(get_string("secondary_colour"), colour_picker("default-secondary", "_save_default_colour(1)", PREFERENCES["colours"]["secondary"], get_string("secondary_colour"), false), true);

    colours += group_title(get_string("saved_colours"));

    // -- OpenRazer [Backends]
    var openrazer = "";
    openrazer += `${_program_logo("img/logo/openrazer.svg", "OpenRazer")}
    <div class="program-links">
        ${_program_link("https://openrazer.github.io", "https://openrazer.github.io")}
    </div>`;

    openrazer += group_title(get_string("version"));
    openrazer += group("OpenRazer", `<code class="transparent">${VERSION.openrazer}</code>`, true);

    openrazer += group_title(get_string("configuration"));
    openrazer += group(get_string("options"), `<a onclick="open_uri('/home/$USER/.config/openrazer/razer.conf')">~/.config/openrazer/razer.conf</a>`, true);
    openrazer += group(get_string("logs"), `<a onclick="open_uri('/home/$USER/.local/share/openrazer/logs/razer.log')">~/.local/share/openrazer/logs/razer.log</a>`, true);

    openrazer += group_title(get_string("links"));
    openrazer += `<div style="margin: 0 2em;">
        ${button("view-src-2", "open_uri('https://github.com/openrazer/openrazer')", get_string("view_source_code"), "external")}
        ${button("whats-new-2", "open_uri('https://github.com/openrazer/openrazer/releases/latest')", get_string("whats_new"), "external")}
    </div>`;

    // Put it all together
    var content = `<div id="preferences-content">
        <div id="section-about" class="section" style="display:none">${about}</div>
        <div id="section-general" class="section" style="display:none">${general}</div>
        <div id="section-tray" class="section" style="display:none">${tray}</div>
        <div id="section-colours" class="section" style="display:none">${colours}</div>
        <div id="section-openrazer" class="section" style="display:none">${openrazer}</div>
    </div>`;
    set_layout_split(sidebar, content);

    // Open the first section
    show_pref("general");
}

function show_pref(id) {
    //
    // Opens a preference page from the sidebar.
    //
    //  id      Suffix of section to show, e.g. "about"
    //
    $(".sidebar-item").removeClass("active");
    $("#nav-" + id).addClass("active");

    $(".section").hide();
    $("#section-" + id).show();
}

function change_pref(group, item, value) {
    //
    // An option on the preferences page was changed. This will write the change
    // in cache (PREFERENCES variable) as well as the controller to save to file.
    //
    //  group           Group name in preferences.json, e.g. "effects"
    //  item            Item name nested under the group, e.g. "live_preview"
    //  value           New value to write.
    //
    PREFERENCES[group][item] = value;
    send_data("set_preference", {
        "group": group,
        "item": item,
        "value": value
    });
}

function open_uri(uri) {
    //
    // For buttons or links that open an external resource.
    //
    send_data("open_uri", {"uri": uri});
}

function open_license_notices() {
    //
    // Opens a dialogue for additional copyright notices of the libraries used
    // in the application.
    //
    // This section is intentionally un-translatable.
    //
    var legal = `<pre>This application makes uses of the following libraries:

jQuery v3.3.1 (MIT)
Copyright (c) JS Foundation and other contributors
https://github.com/jquery/jquery

HTML5-Color-Picker 1.20 (GPLv3)
Copyright (c) 2015-2019 Rubchuk Vladimir
https://github.com/NC22/HTML5-Color-Picker

FontAwesome 5.x (CC BY 4.0)
Copyright (c) FortAwesome
https://github.com/FortAwesome/Font-Awesome

Play
Copyright (c) 2011 Jonas Hecksher
This Font Software is licensed under the SIL Open Font License, Version 1.1.

</pre>`;
    open_dialog(get_string("license_notices"), legal, null, [[get_string("close"), ""]], "80vh", "80vw");
}

function _save_default_colour(colour_id) {
    //
    // onchange after selecting a new default colour in the picker. The picker
    // dialogue is still open at this point.
    //
    //  colour_id       Integer of the default colour. This is due to single/double quotes limitations.
    //
    var colours = {
        0: "primary",
        1: "secondary"
    }
    change_pref("colours", colours[colour_id], $("#colour-input").val());
}
