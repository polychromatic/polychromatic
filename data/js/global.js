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


 ** Functions here are persistent on all pages.
 */

/**
 *  Sends commands to Python
 */
function cmd(instruction) {
  document.title = instruction;
}


/**
 * Fade in and out between 2 elements
 *
 * @param from {string} Element
 * @param to {string} Element
 */
function smooth_fade(from, to) {
    if ($(from).is(":visible") == false) {
        $(to).fadeIn('fast');
    } else {
        $(from).fadeOut('fast');
        setTimeout(function () {
            $(to).fadeIn('fast');
        }, 200);
    }
}


/**
 * Change the header of the page.
 *
 * @param text {string} Header text
 */
function change_header(text) {
    var header = $('#page-header');
    header.fadeOut();

    setTimeout(function () {
        header.fadeIn();
        header.html(text);
    }, 400);
}


/**
 * Change the cursor of a specific element.
 *
 * @param type {string} Element, or 'html' for whole page.
 * @param type {string} Cursor type
 */
function set_cursor(element, type) {

    // Removes any existing cursors on this element first.
    $(element).removeClass('cursor-wait');
    $(element).removeClass('cursor-mode-set');
    $(element).removeClass('cursor-mode-picker');
    $(element).removeClass('cursor-mode-clear');

    // Set a new cursor, if applicable.
    if (type == 'wait') {
        $(element).addClass('cursor-wait');
    } else if (type == 'mode-set') {
        $(element).addClass('cursor-mode-set');
    } else if (type == 'mode-picker') {
        $(element).addClass('cursor-mode-picker');
    } else if (type == 'mode-clear') {
        $(element).addClass('cursor-mode-clear');
    }
}

/**
 * Set/update a preference
 *
 */
function set_pref_chkstate(group, setting, element) {
    state = $(element).is(':checked');
    cmd('pref-set?' + group + '?' + setting + '?' + state);
}

function set_pref_str(group, setting, string) {
    cmd('pref-set?' + group + '?' + setting + '?' + string);
}

/**
 * Run once document has loaded
 */
// Always fade in the page.
$('.content').fadeIn('slow');
