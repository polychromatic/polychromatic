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

 Copyright (C) 2015-2018 Luke Horwell <luke@ubuntu-mate.org>
               2015-2016 Terry Cain <terry@terrys-home.co.uk>
*/

// Sends commands to Python
function cmd(cmd) {
    document.title = cmd;
}

// Dialogue front-end operations
dialog_ani_speed = 250;
function dialog_open(dialogue_id) {
    $('#' + dialogue_id).fadeIn(dialog_ani_speed).addClass('in');
    $('#overlay').fadeIn(dialog_ani_speed);
    $('#header').addClass('modal-blur');
    $('#content').addClass('modal-blur');
    $('#tabs').addClass('modal-blur');
    $('#footer').addClass('modal-blur');
}

function dialog_close(dialogue_id) {
    $('#' + dialogue_id).addClass('out').fadeOut(dialog_ani_speed);
    setTimeout(function() {
        $('#' + dialogue_id).removeClass('out').removeClass('in');
    }, dialog_ani_speed);
    $('#overlay').fadeOut(dialog_ani_speed);
    $('#header').removeClass('modal-blur');
    $('#content').removeClass('modal-blur');
    $('#tabs').removeClass('modal-blur');
    $('#footer').removeClass('modal-blur');
}
