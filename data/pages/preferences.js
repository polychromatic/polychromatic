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

function reset_all_prompt() {
    // Expects string variable pushed: del_all_text
    if ( confirm(del_all_text) == true ) {
      cmd('pref-reset-all');
    }
}

function toggle_startup(element) {
    set_pref_chkstate('startup', 'enabled', element);
    state = $(element).is(':checked');
    if ( state == true ) {
        $('.startup-options').fadeIn('fast');
    } else {
        $('.startup-options').fadeOut('fast');
    }
}

$('#start-effect-dropdown').change(function() {
    selected = $("#start-effect-dropdown option:selected").val();
    set_pref_str('startup', 'start_effect', selected);
    if ( selected == 'profile' ) {
        $('#profiles-list').fadeIn('fast');
    } else {
        $('#profiles-list').fadeOut('fast');
    }
});

$('#profiles-list').change(function() {
    selected = $("#profiles-list option:selected").val();
    set_pref_str('startup', 'start_profile', selected);
});

$(document).ready(function () {
    // Expects string variable pushed: no_change
    $("#start-brightness").change(function () {
        var value = $(this).val();
        $('#start-brightness-text').text(value + "%");
        if (value == 0) {
            $("#start-brightness-text").text(no_change);
        }
        set_pref_str('startup','start_brightness', value);
    });

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
function changelog_dialog_open() {
    $('#dialog-changelog').addClass('in');
    $('#dialog-changelog').show();
    $('#overlay').fadeIn('fast');
    $('.blur-focus').addClass('blur');
}

function changelog_dialog_close() {
    $('#dialog-changelog').addClass('out');
    setTimeout(function(){ $('#dialog-changelog').removeClass('out').removeClass('in').hide() }, 250);
    $('#overlay').fadeOut('fast');
    $('.blur-focus').removeClass('blur');
}

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
