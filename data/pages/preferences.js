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

 Copyright (C) 2015-2017 Luke Horwell <luke@ubuntu-mate.org>


 ** Functions specific to the Preferences menu.
 */

$(document).ready(function () {
    // Update the icon preview / save when text box changes.
    $('#tray-icon-path').bind('input', function() {
        dialog_icon_preview('tray-icon-path');
        set_pref_str('tray_applet','icon_path', $("#tray-icon-path").val());
    });
});

function switchTab(id) {
    $(".tab").removeClass("active");
    $(".tab-content").fadeOut("fast");
    $(id).addClass("active");
    setTimeout(function(){
        $(id+"-page").fadeIn("fast");
    }, 210);
}

/**
 * Dialogue box for viewing change logs.
 */
function open_release_note(version) {
    cmd("open?https://github.com/lah7/polychromatic/releases/tag/v" + version);
}

/* Set a value in the daemon's razer.conf file */
function set_daemon_conf(group, item, element) {
    command = 'daemon-set-config?' + group + '?' + item;
    state = $(element).is(':checked');
    if ( state == true ) {
        cmd(command + '?True')
    } else {
        cmd(command + '?False')
    }
    $("#daemon-options-restart").fadeIn();
    $("#str-daemon-restart").addClass('btn-serious');
}

/* Edit a colour */
function save_colour(uuid) {
    var new_name = $("#colour-edit-name").val();
    var raw_rgba = $("#colour-edit-preview").css("background-color").split(",");
    var red = $.trim(raw_rgba[0].split("(")[1]);
    var green = $.trim(raw_rgba[1]);
    var blue = $.trim(raw_rgba[2].split(")")[0]);
    cmd("pref-colour-save?" + uuid + "?" + new_name + "?" + red + "?" + green + "?" + blue)
}

/* For only showing relevant options for a page */
function show_only_relevant(element_class, target_element) {
    $(element_class).slideUp('fast');
    $(target_element).slideDown('fast');
}
