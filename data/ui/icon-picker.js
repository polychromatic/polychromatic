/*****************************
 * Icon Picker
*****************************/
// The CUSTOM_ICON_PATH variable references where custom files are stored.
// The CUSTOM_ICONS variable lists all of the files inside this folder.
var ICON_PICKER_ID;

function open_icon_picker(id, show_tray_tab) {
    //
    // Opens an icon picker dialogue. This shows a set of built-in icons to the
    // user as well as the option to add their own.
    //
    // Params:
    //  id              Element ID of the hidden text field.
    //  show_tray_tab   Show a tab for choosing icons designed for the tray area.
    //
    ICON_PICKER_ID = id;

    var emblem_icons_html = _get_builtin_icon_html(ICONS_EMBLEMS);
    var custom_icons_html = _get_custom_icon_html();

    var content = `
        <div class="icon-picker-container">
            <div class="tabs vertical">
                <button id="tab-emblems" class="active">${LOCALES["emblems"]}</button>
                <button id="tab-custom">${LOCALES["custom"]}</button>
            </div>
            <div id="tab-emblems-content" class="icon-picker-content">
                ${emblem_icons_html}
            </div>
            <div id="tab-custom-content" class="icon-picker-content" style="display:none">
                ${custom_icons_html}
            </div>
        </div>
    `;

    open_dialog(LOCALES["icon_picker_title"], content, null, [[LOCALES["cancel"], ""], [LOCALES["choose"], ""]], "24em", "24em");

    // Add an additional tab when choosing tray icons.
    if (show_tray_tab === true) {
        var tray_icons_html = _get_builtin_icon_html(ICONS_TRAY);
        $(".icon-picker-container .tabs").prepend(`<button id="tab-tray">${LOCALES["tray"]}</button>`);
        $(".icon-picker-container").append(`<div id="tab-tray-content" class="icon-picker-content">${tray_icons_html}</div>`);
        $(".icon-picker-container .tabs button").removeClass("active");
        $(".icon-picker-container .tabs #tab-tray").addClass("active");
        $("#tab-emblems-content").hide();
    }

    // Tab Selection
    function _icon_picker_tab_onclick() {
        $(".icon-picker-container .tabs button").removeClass("active");
        $(this).addClass("active");
        $(".icon-picker-content").hide();
        $("#tab-" + $(this).attr("id").split("tab-")[1] + "-content").show();
    }
    $("#tab-tray").on("click", _icon_picker_tab_onclick);
    $("#tab-emblems").on("click", _icon_picker_tab_onclick);
    $("#tab-custom").on("click", _icon_picker_tab_onclick);

    // Remember previous value in case user reverts.
    var current_value = $("#" + ICON_PICKER_ID).val();

    // Deactive "Choose" button until new icon is chosen
    var choose_button = $(".dialog-buttons button").last();
    var revert_button = $(".dialog-buttons button").first();
    choose_button.addClass("disabled").attr("disabled", true);

    // Initialise button events
    _custom_icons_changed();
}

function _get_builtin_icon_html(icon_set) {
    //
    // Parses the icons for emblems.
    //
    var output = "";
    for (i = 0; i < icon_set.length; i++) {
        var path = icon_set[i];
        output += `<button class="icon" data-path="${path}"><img src="../${path}"/></button>`;
    }

    return output
}

function _get_custom_icon_html() {
    //
    // Parses the icons for custom icons added by the user.
    //
    var output = "";
    for (i = 0; i < CUSTOM_ICONS.length; i++) {
        var basename = CUSTOM_ICONS[i];
        var path = CUSTOM_ICON_PATH + "/" + basename;
        output += `<button class="icon" data-path="${path}" data-is-custom="true">
            <img src="${path}"/>
            <a class="delete" onclick="remove_custom_icon(&quot;${basename}&quot;)">
                ${get_svg("remove")}
            </a>
        </button>`;
    }

    output += `<button class="icon add" onclick="add_custom_icon()" title="${LOCALES["add_graphic"]}">${get_svg("plus")}</button>`;

    return output
}

function add_custom_icon() {
    //
    // Tells the Controller that the user wishes to add an image to their
    // custom collection. This will reload the custom tab.
    //
    send_data("add_custom_icon", {});
}

function remove_custom_icon(filename) {
    //
    // Tells the Controller that the user wishes to remove a specific image
    // from their custom collection. This will reload the custom tab.
    //
    send_data("remove_custom_icon", {"filename": filename});
}

function _custom_icons_changed(data) {
    //
    // Callback in the Controller when a custom icon has been added/removed.
    //
    $("#tab-custom-content").html(_get_custom_icon_html());

    var choose_button = $(".dialog-buttons button").last();
    var revert_button = $(".dialog-buttons button").first();

    // Changing icon selection
    $(".icon-picker-container .icon").on("click", function() {
        $(".icon-picker-container .icon").removeClass("active");
        $(this).addClass("active");
        choose_button.removeClass("disabled").removeAttr("disabled");
    });

    // Save changes after selecting icon
    $(choose_button).on("click", function() {
        var new_icon = $(".icon-picker-container .icon.active");
        var new_path = new_icon.attr("data-path");
        var is_custom = new_icon.attr("data-is-custom");
        var new_preview;

        if (is_custom === "true") {
            new_preview = "file://" + new_path
        } else {
            new_preview = "../" + new_path;
        }

        $("#" + ICON_PICKER_ID).val(new_path);
        $("#" + ICON_PICKER_ID).next().find(".current-icon-preview").attr("src", new_preview);

        // To actually save the changes to file, run the hidden ID box's function
        eval($("#" + ICON_PICKER_ID).attr("data-save-fn"));
    });

    // Don't enable the "Choose" button after removing a custom item
    $("#tab-custom-content .delete").on("click", function() {
        setTimeout(function() {
            choose_button.addClass("disabled").attr("disabled", true);
        }, 50);
    });

    // Hovering over the delete button changes the styling of the parent button
    $("#tab-custom-content .delete").on("mouseenter", function() {
        $(this).parent().addClass("delete-hover");
    });

    $("#tab-custom-content .delete").on("mouseleave", function() {
        $(this).parent().removeClass("delete-hover");
    });
}
