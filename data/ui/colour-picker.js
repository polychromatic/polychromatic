/*****************************
 * Colour Picker
*****************************/
function open_colour_picker(id, title, current_hex, onsaveclick, monochromatic) {
    //
    // Opens a colour picker dialogue. This lists the users' saved colours as
    // well as an interface to choose a colour.
    //
    // Params:
    //  id              Element ID of the hidden input field holding the value.
    //  title           Appears on the title, e.g. "Edit Primary Colour"
    //  current_hex     Current #RRGGBB value.
    //  onsaveclick     Function to run when new colour is chosen. Runs before close_dialog().
    //  monochromatic   true for devices that only support RGB green.
    //
    var rgb = hex_to_rgb(current_hex);
    var colours_html = "";

    for (c = 0; c < COLOURS.length; c++) {
        var name = COLOURS[c].name;
        var value = COLOURS[c].hex;
        colours_html += `<button class="colour-btn" data-value="${value}" class="${value == current_hex ? "active" : ""}">
            <div class="colour-box" style="background-color:${value}"></div>
            <div class="colour-name">${name}</div>
        </button>`;
    }

    var body = `<div id="colour-picker-container" class="${monochromatic == true ? 'greenscale' : ''}">
            <div class="left">
                <canvas id="colour-picker"></canvas>
                <input id="colour-input" type='text' value="${current_hex}" maxlength="7" pattern="#[A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9]">
                <div class="colour-input-rgb">
                    <input id="colour-input-red" type="text" min="0" max="255" step="1" value="${rgb[0]}" maxlength="3" pattern="([0-9]|[1-8][0-9]|9[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"/>
                    <input id="colour-input-green" type="text" min="0" max="255" step="1" value="${rgb[1]}" maxlength="3" pattern="([0-9]|[1-8][0-9]|9[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"/>
                    <input id="colour-input-blue" type="text" min="0" max="255" step="1" value="${rgb[2]}" maxlength="3" pattern="([0-9]|[1-8][0-9]|9[0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])"/>
                </div>
            </div>
            <div class="right">
                <div class="saved-colours-list">
                    ${colours_html}
                </div>
            </div>
        </div>`;

    open_dialog(title, body, "colour-picker", [[get_string("cancel"), ""], [get_string("save"), onsaveclick]], "24em", "40em");

    var picker = new KellyColorPicker({
        color: current_hex,
        place: "colour-picker",
        input: "colour-input",
        size: 165,
        method: "triangle",
        changeCursor: false,
        userEvents: {
            change: function(self) {
                var rgb = self.getCurColorRgb();
                var hex = self.getCurColorHex()
                $("#colour-input-red").val(rgb.r);
                $("#colour-input-green").val(rgb.g);
                $("#colour-input-blue").val(rgb.b);
                $("#colour-input-system").val(hex);
                $(".colour-btn").each(function() {
                    $(this).removeClass("active");
                    if (hex.toLowerCase() === $(this).attr("data-value").toLowerCase()) {
                        $(this).addClass("active");
                    }
                });
            }
        }
    });

    // Inputting values into the HEX or RGB boxes.
    $(".colour-input-rgb > input").change(function() {
        picker.setColorByHex(rgb_to_hex($("#colour-input-red").val(), $("#colour-input-green").val(), $("#colour-input-blue").val()));
        $("#colour-input-system").val(picker.getCurColorHex());
    });

    $(".colour-input-rgb > input").on("wheel", function(e) {
        var direction_down = e.originalEvent.deltaY < 0;
        var current_value = Number($(this).val());

        if (direction_down) {
            if (current_value + 1 > 255) return;
            $(this).val(current_value + 1);
        } else {
            if (current_value - 1 < 0) return;
            $(this).val(current_value - 1);
        }

        $(this).change();
    });

    // Clicking on a saved colour
    $(".saved-colours-list > button").click(function() {
        picker.setColorByHex($(this).attr("data-value"));
        $(this).siblings().removeClass("active");
        $(this).addClass("active");
    });

    // Replace the default button onclick for "Use system picker", which is the first button.
    $(".dialog-buttons").prepend(`<input id="colour-input-system" type="color" value="${current_hex}" style="opacity:0;float:left"/>`);
    $(".dialog-buttons").prepend(`<button id="colour-input-system-button" style="float:left">${get_string("colours_gtk")}</button>`);

    $("#colour-input-system-button").click(function() {
        $("#colour-input-system").click();
    });

    $("#colour-input-system").change(function() {
        picker.setColorByHex($(this).val());
    });

    // Saving the colour - "Save" button is the last on the dialogue.
    var save_btn = $(".dialog-buttons").find("button").last();
    save_btn.click(function() {
        var new_value = picker.getCurColorHex();
        $(`#${id}`).next().find(".current-colour").css("background-color", new_value).attr("title", new_value);
        $(`#${id}`).attr("value", new_value);
    });

    // Saving the colour - move the onclick function to a click handler instead.
    var save_btn_onclick = save_btn.attr("onclick");
    save_btn.click(function() {
        eval(save_btn_onclick);
    });
    save_btn.attr("onclick", "");
}
