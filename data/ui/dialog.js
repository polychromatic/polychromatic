/*****************************
 * Dialogue Boxes
*****************************/
DIALOG_OPEN = false;
DIALOG_TIMEOUT = null;

function open_dialog(title, body, style, buttons, height, width) {
    //
    // Opens an alert dialogue message.
    //
    // Params:
    //  title       Appears at the top of the dialog.
    //  body        HTML content. Use <p> tags.
    //  style       Either: "warning","serious" or null (green).
    //  buttons     List object: [ ["label", "onclick"], [..] ]
    //  height      Max height of window, use em units.
    //  width       Max width of window, use em units.
    //
    button_html = "";
    for (b = 0; b < buttons.length; b++) {
        var label = buttons[b][0];
        var onclick = buttons[b][1] + "; close_dialog();";
        button_html += `<button onclick="${onclick}">${label}</button>`;
    }

    $("dialog").remove();
    $("body").append(`
        <dialog style="display:none">
            <div class="dialog-box in ${style}" style="max-height:${height}; max-width:${width}">
                <h3 class="dialog-title">${title}</h3>
                <div class="dialog-inner">
                    ${body}
                </div>
                <div class="dialog-buttons">
                    ${button_html}
                </div>
            </div>
        </dialog>
    `);

    // Blur background
    $("#modal-overlay").show();
    $("header").addClass("blur");
    $("content").addClass("blur");
    $("footer").addClass("blur");
    $("dialog").show();

    clearInterval(DIALOG_TIMEOUT);
    DIALOG_TIMEOUT = setTimeout(function() {
        $(".dialog-box").removeClass("in");
    }, TRANSITION_SPEED);

    DIALOG_OPEN = true;
}

function close_dialog() {
    //
    // Closes the dialogue box. Always called from dialogue buttons.
    //
    DIALOG_OPEN = false;
    $(".dialog-box").addClass("out");

    // Unblur background
    $("#modal-overlay").hide();
    $("header").removeClass("blur");
    $("content").removeClass("blur");
    $("footer").removeClass("blur");

    DIALOG_TIMEOUT = setTimeout(function() {
        $("#modal-overlay").hide();
        $("dialog").remove();
    }, TRANSITION_SPEED);
}
