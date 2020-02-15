/*****************************
 * Controls
*****************************/
function group(label, content, condensed) {
    //
    // Creates a group to organise the user interface into 2 columns.
    //
    return `<div class='group ${condensed ? "condensed" : ""}'>
                <div class='left'>
                    <label>${label}</label>
                </div>
                <div class='right'>
                    ${content}
                </div>
            </div>`;
}

function group_title(label) {
    //
    // Creates a group heading to represent a group
    //
    return `<div class='group-name'>
                <span>${label}</span>
            </div>`;
}

function help_text(text) {
    //
    // Creates a help text to describe a group of controls. Normally placed under a group_title.
    //
    return `<p class="group-hint">${text}</p>`;
}

function slider(id, onchange, min, max, step, value, suffix) {
    //
    // Creates a range control.
    //
    return `<input id="${id}" onchange="${onchange ? onchange : ''}" type="range" min="${min}" max="${max}" step="${step}" value="${value}" onwheel="_onwheel(event, this)">
            <span id="${id}-value">${value}</span>${suffix}`;
}

function textbox(id, value, placeholder) {
    //
    // Creates a text box for simple input.
    //
    return `<input id="${id}" type="text" placeholder="${placeholder}" value="${value}" />`;
}

function filebox(id, title, accepted_formats, start_path, onchange) {
    //
    // Creates a file chooser for selecting files from the filesystem.
    //
    // FIXME: Not fully implemented
    return `<input id="${id}" type="file" accept="image/png, image/jpeg"/>`;
}

function checkbox(id, label, checked, onchange) {
    //
    // Creates a checkbox for toggling a boolean.
    //
    return `<div class="checkbox-item">
                <input id="${id}" type="checkbox" ${checked ? "checked" : ""} onchange="${onchange ? onchange : ''}"/>
                <label for="${id}">${label}</label>
            </div>`;
}

function radio(id, label, checked, group_id, onchange) {
    //
    // Creates a radio button for choosing from a set of options.
    //
    return `<div class="radio-item">
                <input id="${id}" type="radio" ${checked ? "checked" : ""} name="${group_id}" onchange="${onchange ? onchange : ""}"/>
                <label for="${id}">${label}</label>
            </div>`;
}

function button(id, onclick, label, svg_name, disabled, serious) {
    //
    // Creates a generic button.
    //
    // An icon name can be specified to use an SVG icon from the "ui/img/button" directory, e.g. "bin".
    //
    var classes = "";
    var svg_html = "";

    if (disabled === true)
        classes += "disabled";

    if (serious === true)
        classes += "serious";

    if (typeof(svg_name) == "string") {
        svg_html = BUTTON_SVGS[svg_name];
    }

    return `<button id="${id}" class="inline ${classes}" ${disabled ? "disabled" : ""} onclick="${onclick}">
                ${svg_html} <span>${label}</span>
            </button>`;
}

function button_large(id, onclick, label, img, disabled, active) {
    //
    // Create a larger button used for iconic selections, like choosing an effect.
    //
    // The parameters are identical to button(), but can also act like radio buttons using 'active'.
    // The icons are placed inside an <img> tag, as opposed to <svg>.
    //
    var classes = "";
    var img_html = "";

    if (disabled === true)
        classes += "disabled";

    if (active === true)
        classes += "active";

    if (img != null) {
        img_html = `<img src="${img}"/>`;
    }

    return `<button id="${id}" class="effect-btn ${classes}" onclick="${onclick}">
                ${img_html} <span>${label}</span>
            </button>`;
}

function button_colour(id, onclick, label, hex) {
    //
    // Create a larger button designed for choosing colours on the Apply yo All page.
    //
    return `<button id="${id}" class="effect-btn colour-btn" onclick="${onclick}">
                <div class="colour-block" style="background-color:${hex}"></div> <span>${label}</span>
            </button>`;
}

function dropdown(id, onchange, current_value, item_list, disabled) {
    //
    // Creates a dropdown for toggling options.
    //
    // item_list format: [[label, value, disabled], [..], [..]]
    //
    var items_html = "";
    for (i = 0; i < item_list.length; i++) {
        var label = item_list[i][0];
        var value = item_list[i][1];
        var greyed = item_list[i][2];
        items_html += `<option value="${value}" ${current_value == value ? "selected" : ""} class="${greyed ? "disabled" : ""}">
                            ${label}
                        </option>`;
    }

    return `<select id="${id}" class="${disabled ? "disabled" : ""}" onchange="${onchange}" onwheel="_onwheel(event, this)">${items_html}</select>`;
}

function colour_picker(id, onchange, current_hex, title, monochromatic) {
    //
    // Creates a control that allows the user to choose a colour.
    //
    return `<input id="${id}" type="hidden" value="${current_hex}"/>
            <div class="colour-selector">
                <div class="current-colour" title="${current_hex}" style="background-color:${current_hex}"></div>
                <button class="change-colour" onclick="open_colour_picker('${id}', '${title}', '${current_hex}', '${onchange}', ${monochromatic})">${get_string("change")}</button>
            </div>`;
}

function icon_picker(id, icon_set, current_value) {
    //
    // Creates a control that allows the user to pick an image from a built-in
    // collection (e.g. emblems) or optionally choose a custom file.
    //
    // id               Element ID of the hidden text field.
    // icon_set         The variable containing the JSON list of icon paths.
    // save_as_base64   Boolean whether the selection should be stored as base64 (embedded) or an ID/path.
    // current_value    Either: a relative path to data dir, absolute path or base64 encoded string.
    //
    return `<input id="${id}" type="hidden" value="${current_value}"/>
            <div class="icon-selector">
                <div class="current-icon">
                    <img class="current-icon-preview" src="${current_value}"/>
                </div>
                <button class="change-icon" onclick="open_icon_picker('${id}', '${icon_set.join(",")}')">${get_string("change")}</button>
            </div>`;
}

function _onwheel(event, element) {
    //
    // Emulate the scrolling behaviour in toolkits like GTK and Qt.
    //
    // Supports: <select>, <input> range, .tab, .sidebar-item
    //
    var type = element.type;
    var scroll_down = event.deltaY > 0;

    if (scroll_down === true) {
        switch(type) {
            case "select-one":
                try {
                    $(element).children()[element.selectedIndex + 1].selected = true;
                } catch {}
                break;
            case "range":
                element.stepDown();
                element.onchange();
                break;
            case "submit":
                $(element).parent().find(".active").next().click();
                break;
        }
    } else {
        switch(type) {
            case "select-one":
                try {
                    $(element).children()[element.selectedIndex - 1].selected = true;
                } catch {}
                break;
            case "range":
                element.stepUp();
                element.onchange();
                break;
            case "submit":
                $(element).parent().find(".active").prev().click();
                break;
        }
    }
}
