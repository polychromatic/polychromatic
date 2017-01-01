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
               2015-2016 Terry Cain <terry@terrys-home.co.uk>


 ** Functions for the Chroma Main Menu.
 */


/**
 * Enable buttons when a profile is clicked
 */
var selected_profile = "null";
function profile_list_change(css_id, uuid, human_name) {
    selected_profile = uuid;
    selected_name = human_name;
    $('#profiles-activate, #profiles-edit, #profiles-delete').removeClass('disabled');
    $('.app-profile-item').removeClass("active");
    $('.effect-item').removeClass("active");
    $('#'+css_id).addClass("active");
    $('#fx-none').addClass("active");

    // Instant profile activation (if 'live_switch' is enabled in preferences)
    if ( live_switch == true ) {
        profile_activate()
    }
}


/**
 * Dialogue box for creating profiles
 */
function new_profile_dialog_open() {
    $('#dialog-new-name').val('');
    $('#dialog-new-icon').val('');
    $("#dialog-new-icon-preview").attr("src", "img/profile-default.svg");
    $("#dialog-new-name-preview").html(" ");
    $('#dialog-new').addClass('in');
    $('#dialog-new').show();
    $('#dialog-new-ok').addClass('disabled');
    $('#overlay').fadeIn('fast');
    $('.blur-focus').addClass('blur');
}

function new_profile_dialog_close() {
    $('#dialog-new').addClass('out')
    setTimeout(function(){ $('#dialog-new').removeClass('out').removeClass('in').hide() }, 250);
    $('#overlay').fadeOut('fast')
    $('.blur-focus').removeClass('blur')
}

// Enable / disable "Create" button if valid data is entered.
$(document).ready(function() {
    $('#dialog-new-name').keyup(function() {
    length = $("#dialog-new-name").val().length;
    if ( length > 0 ) {
        $('#dialog-new-ok').removeClass('disabled');
    } else {
        $('#dialog-new-ok').addClass('disabled');
    }
    });
});

function new_profile_dialog_cancel() {
    new_profile_dialog_close();
}

function new_profile_dialog_ok() {
    new_profile_dialog_close();
    newname = $("#dialog-new-name").val();
    newicon = $("#dialog-new-icon").val();
    // Uses colons instead of "?" in case user uses a name containing a "?".
    cmd('profile-new;' + newname + ';' + newicon);
}


/**
 * Dialogue box for deleting a profile
 */
function del_profile_dialog_open() {
    $('#dialog-del').addClass('in');
    $('#dialog-del').show();
    $('#overlay').fadeIn('fast');
    $('.blur-focus').addClass('blur');
    $("#dialog-del-item").html(selected_name);
}

function del_profile_dialog_close() {
    $('#dialog-del').addClass('out');
    setTimeout(function(){ $('#dialog-del').removeClass('out').removeClass('in').hide() }, 250);
    $('#overlay').fadeOut('fast');
    $('.blur-focus').removeClass('blur');
}

function del_profile_dialog_confirm() {
    del_profile_dialog_close();
    $('#app-'+selected_profile).slideUp('slow');
    setTimeout(function(){
        cmd('profile-del?' + selected_profile);
    }, 500);
}


/**
 * Dialogue box for choosing an application launcher.
 */
function prefill_launcher(selected_div, name, icon) {
    $("#dialog-new-name").val(name);
    $("#dialog-new-icon").val(icon);
    $(".app-launcher-item").removeClass("active");
    $('#'+selected_div).addClass("active");
    $('#dialog-applauncher-ok').show();
    $('#dialog-applauncher-revert').hide();
    $('#dialog-new-ok').removeClass('disabled');
}

function choose_app_launcher_open() {
    $('#dialog-applauncher').addClass('in');
    $('#dialog-applauncher').show();
    $('#dialog-new').addClass('blur');
    $('#dialog-applauncher-ok').hide();
    $('#dialog-applauncher-revert').show();
}

function choose_app_launcher_close() {
    $('#dialog-applauncher').addClass('out');
    $('#dialog-new').removeClass('blur');
    setTimeout(function(){ $('#dialog-applauncher').removeClass('out').removeClass('in').hide() }, 250);
}


/**
 * Dialogue box for quick help documentation.
 */
function help_dialog_open() {
    $('#dialog-help').addClass('in');
    $('#dialog-help').show();
    $('#overlay').fadeIn('fast');
    $('.blur-focus').addClass('blur');
}

function help_dialog_close() {
    $('#dialog-help').addClass('out');
    setTimeout(function(){ $('#dialog-help').removeClass('out').removeClass('in').hide() }, 250);
    $('#overlay').fadeOut('fast');
    $('.blur-focus').removeClass('blur');
}


/**
 * Edit profile.
 */
function profile_edit() {
    cmd('profile-edit?' + selected_profile);
}


/**
 * Activate profile.
 */
function profile_activate() {
    cmd('profile-activate?'+selected_profile);
}


/**
 * Run once document has loaded
 */
$(document).ready(function() {

    // Change brightness control
    $("[type=range]").change(function () {
        var value = $(this).val();
        $('#brightnessValue').text(value + "%");
        if (value == 0) {
            $(this).next().text("Off");
        }
        cmd('brightness?' + value);
    });

    // In dialogues, keep preview boxes updated with text box contents.
    $('#dialog-new-name').bind('input', function() {
        dialog_text_preview('dialog-new-name')
        dialog_icon_preview('dialog-new-icon')
    });
    $('#dialog-new-icon').bind('input', function() {
        dialog_text_preview('dialog-new-name')
        dialog_icon_preview('dialog-new-icon')
    });
});

/**
 * Activate an effect
 *    obj:   Pass 'self' (this)
 *    type:  Name of effect, e.g. "reactive"
 *    parms: Parameters to pass to Python, separated by '?'
 */
function setfx(type, parms) {
    command = "effect?" + type + "?" + parms;
    $(".app-profile-item").removeClass("active");
    $("#effect-list *").removeClass("active");
    $("#fx-" + type).addClass("active");
    cmd(command);
}

/* Fade the background of the header when switching devices */
function changeHeaderImg(image, color) {
    $("#dynamic").css("background-color", "black");
    $(".header").removeClass("wave");
    $("#dynamic").removeClass("spectrum");
    setTimeout(function(){
        $("#dynamic").removeClass();
        $("#dynamic").addClass(image);
    }, 250);
    setTimeout(function(){
        if  ( color == "spectrum" ) {
            $("#dynamic").addClass("spectrum");
        } else if ( color == "wave" ) {
            $(".header").addClass("wave");
            $("#dynamic").css("background-color", "transparent");
        } else {
            $("#dynamic").css("background-color", color);
        }
    }, 500);
}

/* Switch to Device Overview mode */
$("#device-overview").hide();
function switchPaneOverview() {
    $(".device").removeClass("active");
    $("#device-overview-tab").addClass("active");
    $("#device-individual").fadeOut('fast');
    cmd("refresh-active-device");
    setTimeout(function() {
        $("#device-overview").fadeIn('fast');
    }, 210);
}
