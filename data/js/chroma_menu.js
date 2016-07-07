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

 Copyright (C) 2015-2016 Luke Horwell <lukehorwell37+code@gmail.com>
               2015-2016 Terry Cain <terry@terrys-home.co.uk>


 ** Functions for the Chroma Main Menu.
 */


/**
 * Enable buttons when a profile is clicked
 */
function profile_list_change() {
    $('#profiles-activate, #profiles-edit, #profiles-delete').removeClass('btn-disabled');
}


/**
 * Dialogue box for creating profiles
 */
function new_profile_dialog_open() {
    $('#dialog-new-input').val('')
    $('#dialog-new').addClass('in')
    $('#dialog-new').show()
    $('#dialog-new-ok').addClass('btn-disabled');
    $('#overlay').fadeIn('fast')
    $('#content').addClass('blur')
}

function new_profile_dialog_close() {
    $('#dialog-new').addClass('out')
    setTimeout(function(){ $('#dialog-new').removeClass('out').removeClass('in').hide() }, 250);
    $('#overlay').fadeOut('fast')
    $('#content').removeClass('blur')
}

// Enable / disable "Create" button if valid data is entered.
$(document).ready(function() {
    $('#dialog-new-input').keyup(function() {
    length = $("#dialog-new-input").val().length;
    if ( length > 0 ) {
        $('#dialog-new-ok').removeClass('btn-disabled');
    } else {
        $('#dialog-new-ok').addClass('btn-disabled');
    }
    });
});

function new_profile_dialog_cancel() {
    new_profile_dialog_close();
}

function new_profile_dialog_ok() {
    new_profile_dialog_close();
    input = $("#dialog-new-input").val();
    cmd('profile-new?' + input);
}


/**
 * Dialogue box for deleting a profile
 */
function del_profile_dialog_open() {
    $('#dialog-del').addClass('in')
    $('#dialog-del').show()
    $('#overlay').fadeIn('fast')
    $('#content').addClass('blur')

    var selected_profile = $("#profiles-list option:selected").text();
    $("#dialog-del-item").html(selected_profile);
}

function del_profile_dialog_close() {
    $('#dialog-del').addClass('out')
    setTimeout(function(){ $('#dialog-del').removeClass('out').removeClass('in').hide() }, 250);
    $('#overlay').fadeOut('fast')
    $('#content').removeClass('blur')
}

function del_profile_dialog_confirm() {
    del_profile_dialog_close();
    var selected_profile = $("#profiles-list option:selected").text();
    cmd('profile-del?' + selected_profile);
}


/**
 * Edit profile.
 */
function profile_edit() {
    var selected_profile = $("#profiles-list option:selected").text();
    cmd('profile-edit?' + selected_profile);
}


/**
 * Activate profile.
 */
function profile_activate() {
    var selected_profile = $("#profiles-list option:selected").text();
    cmd('profile-activate?'+selected_profile);
}


/**
 * Run once document has loaded
 */
$(document).ready(function () {

    // Change brightness control
    $("[type=range]").change(function () {
        var brightnessRaw = ($(this).val() / 255.0) * 100;
        $('#brightnessValue').text(Math.round(brightnessRaw) + "%");
        if (brightnessRaw == 0) {
            $(this).next().text("Off")
        }
        cmd('brightness?' + Math.round($(this).val()));
    });

    // Instant profile activation (if 'live_switch' is enabled in preferences)
    $('#profiles-list').change(function() {
        if ( live_switch == true ) {
            profile_activate()
        }
    });

});
