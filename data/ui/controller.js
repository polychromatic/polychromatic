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

 Copyright (C) 2015-2020 Luke Horwell <code@horwell.me>
*/

// Sends commands to Python
function cmd(cmd) {
    document.title = cmd;
}

// Dialogue front-end operations
var transition_speed = 250;

function open_dialog() {
    $("#modal-overlay").show();
    $("header").addClass("blur");
    $("content").addClass("blur");
    $("footer").addClass("blur");
    $("#dialog").addClass("in").fadeIn(transition_speed);
    setTimeout(function() {
        $("#dialog").removeClass("in");
    }, transition_speed + 50);
}

function close_dialog() {
    $("#modal-overlay").hide();
    $("header").removeClass("blur");
    $("content").removeClass("blur");
    $("footer").removeClass("blur");
    $("#dialog").removeClass("in").addClass("out").fadeOut(transition_speed);
    setTimeout(function() {
        $("#dialog").remove();
    }, transition_speed + 50);
}

// UI Helpers
function swap_elements(from, to) {
    $(from).fadeOut(transition_speed);
    setTimeout(function() {
        $(to).fadeIn(transition_speed);
    }, transition_speed);
}

// Colour Picker
var colour_picker;
function colour_picker_init(hex) {
    colour_picker = new KellyColorPicker({
        color: hex,
        place: "colour-picker",
        input: "colour-input",
        size: 160,
        method: "triangle",
        changeCursor: false,
        userEvents: {
            change: function(self) {
                var rgb = self.getCurColorRgb();
                $("#colour-input-red").val(rgb.r);
                $("#colour-input-green").val(rgb.g);
                $("#colour-input-blue").val(rgb.b);
            }
        }
    });

    $(".colour-input-rgb > input").change(function() {
        colour_picker.setColorByHex(rgb_to_hex($("#colour-input-red").val(), $("#colour-input-green").val(), $("#colour-input-blue").val()));
    });
}

function rgb_to_hex(r,g,b) {
    return "#" + ("0" + parseInt(r,10).toString(16)).slice(-2) +
        ("0" + parseInt(g,10).toString(16)).slice(-2) +
        ("0" + parseInt(b,10).toString(16)).slice(-2);
}
