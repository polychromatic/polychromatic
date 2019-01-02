#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2018-2019 Luke Horwell <code@horwell.me>
#
"""
This module contains "callbacks" when "commands" are issued via the Controller application.

1. Interactions can be called in JavaScript using cmd("name-of-function").
2. Commands are linked 'name-of-function' to UICmd function in the Controller's process_command() function.
3. Functions are issued below, inheriting essential variables for manipulating the page (e.g. controller/webkit)
"""
from . import common
from . import preferences as pref
from time import sleep
from platform import uname, linux_distribution
import os
import sys
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

_ = common.setup_translations(__file__, "polychromatic")
dbg = common.Debugging()

class GTKDialogues():
    """
    Contains code for producing and parsing GTK dialogues.
    """
    def file_picker(dialog_id):
        """
        Opens a file picker and returns the string. If user cancels or the
        operation fails, returns None.

        Params:
            - dialog_id     Dialogue Settings to use (see below)

        Settings:
            - 1             Choose tray icon
            - 2             Choose image for profile/effect
        """

        if dialog_id == 1:
            help_title = _("Custom Tray Icon")
            help_text = _("Choose an icon to use for the tray applet.")
            filter_set = "image"
        else:
            return None

        win = Gtk.Window(title=help_title)
        dialog = Gtk.FileChooserDialog(help_text, win, Gtk.FileChooserAction.OPEN, \
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, \
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        # Setup filters
        if filter_set == "image":
            a = Gtk.FileFilter()
            a.set_name(_("All Images"))
            a.add_mime_type("image/jpeg")
            a.add_mime_type("image/png")
            a.add_mime_type("image/gif")
            a.add_mime_type("image/svg+xml")
            dialog.add_filter(a)

            j = Gtk.FileFilter()
            j.set_name("JPEG " + _("Image"))
            j.add_mime_type("image/jpeg")
            dialog.add_filter(j)

            p = Gtk.FileFilter()
            p.set_name("PNG " + _("Image"))
            p.add_mime_type("image/png")
            dialog.add_filter(p)

            g = Gtk.FileFilter()
            g.set_name("GIF " + _("Image"))
            g.add_mime_type("image/gif")
            dialog.add_filter(g)

            s = Gtk.FileFilter()
            s.set_name("SVG " + _("Image"))
            s.add_mime_type("image/svg+xml")
            dialog.add_filter(s)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            return filename
        else:
            dialog.destroy()
            return None


class UICmd(object):
    """
    Process instructions passed via the frontend (HTML/JS) to the Python layer.

    All parameters are passed as strings within a list. '?' is the delimiter.
    """
    def __init__(self, controller, webkit, devman, get_string_bank, path):
        self.webkit = webkit
        self.controller = controller
        self.update_page = controller.update_page
        self.update_content_view = controller.update_content_view
        self.devman = devman
        self.ani_js_speed = "250"
        self.ani_py_speed = 0.25
        self.get_string = get_string_bank(_)
        self.path = path
        self.data_path = path.data_source

    def close_application(self, params=None):
        """Quits the application"""
        exit()

    def reload_application(self, params=None):
        """Prematurely reloads the application"""
        os.execv(__file__, sys.argv)

    # Common UI controls manipulation
    def _set_title(self, new_title):
        """Sets the title in the upper-left"""
        self.update_page("#title", "html", new_title)

    def _hide(self, element):
        """Alias to hide an element"""
        self.update_page(element, "hide")

    def _show(self, element):
        """Alias to show an element"""
        self.update_page(element, "show")
        self.update_page(element, "removeClass", "start-hidden")

    def _set_img(self, element, path):
        """Alias to set an img's src tag"""
        self.update_page(element, "attr", "src", path)

    def _set_text(self, element, text):
        """Alias to set the HTML inside an element"""
        self.update_page(element, "html", text)

    def _set_value(self, element, value, min_value=None, max_value=None):
        """
        Alias to set a control's value

        Optionally can pass a min_value and/or max_value to enforce on the control.
        """
        self.update_page(element, "val", value)
        if min_value:
            self.update_page(element, "attr", "min", min_value)
        if max_value:
            self.update_page(element, "attr", "max", max_value)

    def _set_toggle(self, element, is_checked):
        """Alias to set a control inside an element"""
        if is_checked:
            self.update_page(element, "attr", "checked", "true")
        else:
            self.update_page(element, "attr", "checked", "false")

    def _set_dropdown_options(self, element, list_of_options):
        """
        Alias to set the options inside a list. List expected in format:
        [["item1", "Item 1"], ["<value>", "<label>"]]
        """
        self.update_page(element, "html", " ")
        for option in list_of_options:
            self.update_page(element, "append", "<option value='{0}'>{1}</option>".format(option[0], option[1]))

    def _set_active_button(self, element, group_class):
        """Alias to add the 'active' class to an element (ID) while removing 'active' from a specified class"""
        self.update_page(group_class, "removeClass", "active")
        self.update_page(element, "addClass", "active")

    def _fade_in(self, element, pause=False):
        """Alias to fade in an element using default animation timings. Can optionally pause Python execution."""
        self.update_page(element, "fadeIn", self.ani_js_speed)
        self.update_page(element, "removeClass", "start-hidden")
        if pause:
            sleep(self.ani_py_speed)

    def _fade_out(self, element, pause=False):
        """Alias to fade out an element using default animation timings. Can optionally pause Python execution."""
        self.update_page(element, "fadeOut", self.ani_js_speed)
        if pause:
            sleep(self.ani_py_speed)

    def _open_dialog(self, dialog_type, title, inner_html, height="10em", width="32em", buttons=[["close_dialog()", _("Close")]]):
        """
        Opens a dialog box based on parameters. The size is automatic based on its contents.

        Params:
          - dialog_type     Styling to apply: info, error, general, warning
          - title           Name of dialog
          - inner_html      HTML to place inside
          - buttons         List containing onclick and labels, e.g. [["cmd()", "Item 1"], ["cmd()", "Item 2"]]
          - height          Desired dialog box height
          - width           Desired dialog box width
        """
        self.update_page("#dialog", "remove")
        html = "<div id='dialog' class='{2}' style='max-height:{0};max-width:{1}'>".format(height, width, dialog_type)
        html += "<h3 id='dialog-title'>{0}</h3>".format(title)
        html += "<div id='dialog-inner'>{0}</div>".format(inner_html)
        html += "<div id='dialog-buttons'>"
        for button in buttons:
            html += "<button onclick='{0}'>{1}</button>".format(button[0], button[1])
        html += "</div>"
        html += "</div>"
        self.update_page("body", "append", html)
        self.webkit.run_js("open_dialog()")

    def _close_dialog(self):
        """Closes a dialog via Python"""
        self.webkit.run_javascript("close_dialog()")

    @staticmethod
    def _make_group(label, content, condensed=False):
        """
        Generates a group for organising the user interface into two columns.

        label           Label that appears on the left.
        contents        HTML that appears on the right.
        """
        return "<div class='group {2}'><div class='left'><label>{0}</label></div><div class='right'>{1}</div></div>".format(label, content, "condensed" if condensed else "")

    @staticmethod
    def _make_group_name(name):
        """
        Generates a group name to represent a group.
        """
        return "<div class='group-name'><span>{0}</span></div>".format(name)

    @staticmethod
    def _make_control_slider(element_id, command, min_value, max_value, step_value, actual_value, suffix, prepend="", append=""):
        """
        Generates a slider control for Python-generated HTML.

        element_id      ID for element, auto appends "-slider" and "-value"
        command         String that goes inside cmd('XXX?value') where XXX is this parameter.
        min_value       Minimum value for control.
        max_value       Maximum value for control.
        step_value      Step value for control.
        actual_value    Initial value for control.
        suffix          Characters that appear at end of value.
        prepend         HTML to add before control.
        append          HTML to add after control.
        """
        if len(element_id) == 0:
            element_id = common.generate_uuid()
        return "<p>{7} <input id='{0}-slider' onchange='cmd(\"{1}?\" + $(this).val())' type='range' min='{2}' max='{3}' step='{4}' value='{5}'> {8} <span id='{0}-value'>{5}</span>{6}</p>".format(
            element_id,
            command,
            min_value,
            max_value,
            step_value,
            actual_value,
            suffix,
            prepend,
            append)

    def _make_control_text(self, element_id, command, initial_value, placeholder, browse_btn=False, prepend="", append=""):
        """
        Generates a text control for Python-generated HTML.

        element_id      ID for element.
        command         String that goes inside cmd('XXX?value') where XXX is this parameter.
        initial_value   Text that appears initially.
        placeholder     Text that appears as an example.
        browse_btn      True if the user may choose from filesystem.
        prepend         HTML to add before control.
        append          HTML to add after control.
        """
        if len(element_id) == 0:
            element_id = common.generate_uuid()
        html = "<p>" + prepend + " "
        html += "<input id='{0}' onkeyup='$(\"#{0}-options\").show();' type='text' placeholder=\"{1}\" value=\"{2}\">".format(
            element_id,
            placeholder,
            initial_value)
        if browse_btn:
            html += self._make_control_button(element_id, "browse?{0}?{1}".format(element_id, 1), _("Browse"), "img/fa/browse.svg")
        html += "<span id='{0}-options' style='display:none'>".format(element_id)
        html += "<button onclick='cmd(\"{0}?\" + $(\"#{1}\").val());$(\"#{1}-options\").hide()'>Save</button>".format(command, element_id)
        html += "</span> " + append + "</p>"
        return html

    @staticmethod
    def _make_control_checkbox(element_id, command, label, initial_state, prepend="", append=""):
        """
        Generates a checkbox control for Python-generated HTML.

        element_id      ID for element.
        command         String that goes inside cmd('XXX?value') where XXX is this parameter.
        label           Label that appears to the right of the control.
        initial_state   Is checkbox initially checked?
        prepend         HTML to add before control.
        append          HTML to add after control.
        """
        if len(element_id) == 0:
            element_id = common.generate_uuid()
        return "<p>{4}<input id='{0}' onchange='cmd(\"{1}?\" + $(this).is(\":checked\"))' type='checkbox' {3}><label for='{0}'>{2}</label> {5}</p>".format(
            element_id,
            command,
            label,
            "checked"
            if initial_state else "",
            prepend,
            append)

    @staticmethod
    def _make_control_radio(element_id, command, label, initial_state, group, prepend="", append=""):
        """
        Generates a checkbox control for Python-generated HTML.

        element_id      ID for element.
        command         String that goes inside cmd('XXX?value') where XXX is this parameter.
        label           Label that appears to the right of the control.
        initial_state   Is checkbox initially checked?
        group           ID for the group this radio belongs to.
        prepend         HTML to add before control.
        append          HTML to add after control.
        """
        if len(element_id) == 0:
            element_id = common.generate_uuid()
        return "<p>{5}<input id='{0}' onchange='cmd(\"{1}?\" + $(this).is(\":checked\"))' type='radio' {3} name='{4}'><label for='{0}'>{2}</label>{6}</p>".format(
            element_id,
            command,
            label,
            "checked" if initial_state == True else "",
            group,
            prepend,
            append)

    def _make_control_button(self, element_id, command, label, icon_path=None, disabled=None, serious=None):
        """
        Generates a button for Python generated HTML.

        element_id      ID for element.
        command         cmd('XXX') where XXX is this parameter.
        label           Text that appears on this button.
        icon_path       (Optional) Path to the icon, e.g. "img/effects/unknown.svg"
        disabled        (Optional) True to disable button initially.
        serious         (Optional) Use red colour scheme.
        """
        if icon_path and icon_path.endswith(".svg"):
            return "<button id='{0}' class='inline {1} {5}' {1} onclick='cmd(&quot;{2}&quot;)'>{3} <span>{4}</span></button>".format(
                element_id,
                "disabled" if disabled else "",
                command,
                self._load_svg("ui/" + icon_path),
                label,
                "serious" if serious else "")
        else:
            return "<button id='{0}' class='{1} {5}' {1} onclick='cmd(&quot;{2}&quot;)'>{3} {4}</button>".format(
                element_id,
                "disabled" if disabled else "",
                command,
                "<img src='" + icon_path + "'/> " if icon_path else "",
                label,
                "serious" if serious else "")

    @staticmethod
    def _make_effect_button(fx_name, label, active, source, custom_icon_path=None, cmd="set-effect"):
        """
        Generates a button for effects.

        fx_name             ID for effect, used in pathnames.
        label               Label to show on button.
        active              True/False if should be enabled
        source              Lighting source (based to function)
        custom_icon_path    (Optional) Show alternate icon instead of effect default.
        function            (Optional) Name of command to execute.
        """
        return "<button id='effect-{0}' class='effect-btn {2}' onclick='cmd(\"{5}?{3}?{0}\")'><img src='{4}'/><span>{1}</span></button>".format(
            fx_name,
            label,
            "active" if active else "",
            source,
            custom_icon_path if custom_icon_path else "img/effects/" + fx_name + ".svg",
            cmd)

    @staticmethod
    def _make_control_dropdown(element_id, onchange_cmd, initial_value, item_list, additional_class=None, prepend="", append=""):
        """
        Generates a dropdown for Python generated HTML.

        element_id          ID for element.
        onchange_cmd        Command to execute when selection changes.
        item_list           Options in dropdown in this format:
                                [["val1", "Label 1"], ["val2", "Label 2"]]
        initial_value       Current value to display.
        additional_class    (Optional) Adds a class to manipulate styling.
        """
        html = "{4} <select id='{0}' class='{3}' value='{1}' onchange='cmd(\"{2}?\" + $(this).val())'> {5}".format(
            element_id,
            initial_value,
            onchange_cmd,
            additional_class,
            prepend,
            append)

        for item in item_list:
            value = str(item[0])
            label = str(item[1])
            html += "<option value='{0}' {2}>{1}</option>".format(value, label, "selected" if value == str(initial_value) else "")

        html += "</select>"
        return html

    @staticmethod
    def _make_colour_selector(current_hex, callback_function, title, device=None):
        """
        Generates a preview box to view/change a colour.

        Params:
            current_hex         Colour hex of current colour.
            callback_function   String inside cmd('XXX?R?G?B') where XXX is the command.
                                This is used when a new custom colour is selected.
            device              (Optional) Pass device to check if greenscale.
        """
        greenscale = "false"
        if device:
            if common.is_device_greenscale(device):
                greenscale = "true"

        return "<div id='{2}' class='colour-selector'><div id='{0}' class='current-colour' style='background-color:{1}'></div> <button onclick='cmd(&quot;open-colour-picker?{0}?{1}?{4}?{2}?{5}&quot;)'>{3}</button></div>".format(
            common.generate_uuid(),
            current_hex,
            callback_function.replace("?", "¿"),
            _("Change..."),
            title,
            greenscale)

    def _load_svg(self, svg_path):
        """
        Loads the contents of an SVG file from data source. If non-existent, returns False.
        """
        svg_path = os.path.join(self.path.data_source, svg_path)
        if not os.path.exists(svg_path):
            return False

        with open(svg_path) as f:
            contents = f.read().replace("\n", "")

        return contents

    def show_colour_selector(self, params):
        """
        Shows a dialogue box prompting to choose a different colour.

        Params:
            uuid            Element ID containing the original colour.
            current_hex     Current colour as Hex #.
            title           Title of the dialogue box.
            callback_fn     (Optional) Callback function to run after saving new colour.
                                If callback function has multiple parameters,
                                they should be seperated with inverted ? marks (¿)
            greenscale      'true' if device can only show green colours.
        """
        uuid = params[0]
        current_hex = params[1]
        title = params[2]
        callback_fn = params[3].replace("¿", "?")
        greenscale = params[4]

        # Load user colours
        saved_colours_html = ""
        saved_colours = pref.load_file(pref.path.colours)
        for colour in saved_colours:
            name = colour["name"]
            hex_code = colour["hex"]
            saved_colours_html += "<button class='colour-btn' onclick='colour_picker.setColorByHex(&quot;{0}&quot;)'><div class='colour-box' style='background-color:{0}'></div> {1}</button>".format(hex_code, name)

        # Set class if device can only output green
        if greenscale in ["true", True]:
            additional_classes = "greenscale"
        else:
            additional_classes = ""

        replace_dict = {
            "hex": current_hex,
            "saved-colours": saved_colours_html,
            "additional-classes": additional_classes
        }

        html = self.controller.get_content_view("colour-picker", replace_dict)
        buttons = [
            ["close_dialog()", _("Cancel")],
            ["cmd(&quot;{1}?&quot; + colour_picker.getCurColorHex());close_dialog();".format(uuid, callback_fn, ), _("Save")]
        ]
        self._open_dialog("general", title, html, "21em", "35em", buttons)
        self.webkit.run_js("colour_picker_init('{0}')".format(current_hex))

    # Specific to devices screen
    def _show_device_error(self, image, title, text):
        """
        When a device cannot be loaded, shows a graphical error in the devices tab.
        Some buttons are shown to aid the user in resolving the problem.

        Params:
            image   Filename (including extension) in <data>/ui/img/error/
            title   Title of error
            text    Text of error
        """
        self._set_title(title)
        self.update_page(".sidebar-container .left .active", "removeClass", "active")

        selector = ".sidebar-container > .right"
        self._hide(selector)
        self.update_content_view("device-error", selector)
        self.update_page("#error-image", "attr", "src", "img/error/" + image)
        self.update_page("#error-title", "html", title)
        self.update_page("#error-text", "html", text)
        self.update_page("#error-image", "show")
        self._fade_in(selector)

    def run_command(self, function, params=""):
        """
        Runs a command passed through the front-end (JS)
        """
        params = params.split("?")
        params.pop(0)
        function(params)

    def devices_init_tab(self, params=[]):
        """
        Loads the devices tab.
        """
        self.update_content_view("devices")

        try:
            import openrazer.client

            if self.devman == openrazer.client.DaemonNotFound:
                self._show_device_error("daemon-missing.svg",
                    _("Daemon Not Running"),
                    _("Polychromatic requires the OpenRazer daemon, but it doesn't appear to be running.") + '<br><br>' + \
                    _("The software will continue to run, but you will not be able to control lighting on any connected Razer devices."))
                return

        except (ImportError, ModuleNotFoundError):
            self._show_device_error("daemon-missing.svg",
                _("OpenRazer Module Missing"),
                _("Polychromatic requires the OpenRazer daemon, but the Python library could not be imported.") + '<br><br>' + \
                _("The software will continue to run, but you will not be able to control lighting on any connected Razer devices."))
            return

        if not self.devman:
            self._show_device_error("daemon-error.svg",
                _("Daemon Initalization Error"),
                _("Polychromatic tried to initialize the OpenRazer device manager, but threw an exception.") + '<br><br>' + \
                _("To diagnose and view the error, run the software from the terminal."))
            return

        # Refuse to continue if the running daemon's version mismatches the library version.
        # This might happen if the user updates OpenRazer but doesn't restart.
        try:
            running_version = int(self.devman._daemon_version.replace('.',''))
            import openrazer_daemon.daemon
            installed_version = int(openrazer_daemon.daemon.__version__.replace('.',''))

            if running_version < installed_version and not version_dev:
                self._show_device_error("daemon-error.svg",
                    _("Restart Required"),
                    _("OpenRazer was recently updated, please restart the daemon to continue.") + '<br><br>' + \
                    _("This is to prevent glitches as the running daemon instance mismatches the installed OpenRazer library."))
                return

        except Exception:
            # Daemon crashed, skip this check.
            running_version = 0
            installed_version = 0

        # Pre-OpenRazer library? My goodness, that's been unsupported for ages.
        if os.path.exists("/usr/lib/python3/dist-packages/razer/interface/keyboard.py") or os.path.exists(os.path.join(sys.path[-1], "/razer/interface/keyboard.py")):
            self._show_device_error("daemon-error.svg",
                _("Incompatible Daemon"),
                _("The Razer 'Chroma' driver/daemon currently installed on your system is no longer supported by Polychromatic.") + '<br><br>' + \
                _("To use this software, remove the older Razer driver and daemon, then install OpenRazer."))
            return

        # Check user is in 'plugdev' as required by daemon
        if len(self.devman.devices) == 0:
            if len(common.get_incompatible_device_list(dbg, self.devman.devices)) > 0 and not common.is_user_in_plugdev_group():
                try:
                    whoami = str(os.getlogin())
                except FileNotFoundError:
                    import pwd
                    whoami = str(pwd.getpwuid(os.getuid())[0])
                except Exception:
                    whoami = _("<username>")

                self._show_device_error("daemon-error.svg",
                    _("Insufficient Privileges for OpenRazer"),
                    _("This user account is not in the 'plugdev' group. The daemon requires this to recognize your device(s).") + '<br><br>' + \
                    _("To see your devices, run this command in the terminal, then log out then back in:") +
                    '<br><code>sudo gpasswd -a ' + whoami + ' plugdev</code>')
                return

        ### End of error message checks ###

        # Populate device list on the sidebar.
        try:
            dbg.stdout("Getting device list...", dbg.action, 1)
            html = ""
            device_id = -1
            for device in self.devman.devices:
                device_id += 1
                dbg.stdout(" -- Found: " + device.name, dbg.debug, 1)
                html += "<button id='device-{0}' class='item {3}' onclick='cmd(\"device-select?{0}?true\")'><img src='{1}'/> <span>{2}</span></button>".format(
                    str(device_id),
                    common.get_device_image(device, self.data_path),
                    device.name.replace("Razer ", ""),
                    "active" if self.controller.active_device == device else "")
        except Exception as e:
            dbg.stdout("Failed to get device list!", dbg.error)
            dbg.stdout("Exception: " + str(e), dbg.error)
            self._show_device_error("wicked.svg",
                _("A serious error has occurred"),
                _("Failed to retrieve device list from the daemon.") + '<br><br>' + \
                _("Try removing all connected Razer devices, and try again. If this keeps happening, please raise an issue with the output of this command:") +
                '<br><code>polychromatic-controller -v</code>')
            return

        try:
            for vid_pid in common.get_incompatible_device_list(dbg, self.devman.devices):
                device_id += 1
                dbg.stdout(" -- Found unrecognised device: {0}:{1}".format(str(vid_pid[0]), str(vid_pid[1])), dbg.debug, 1)
                html += "<button class='item dim' onclick='cmd(\"device-unrecog\")'><img src='{0}'/> <span>{3}: {1}:{2}</span></button>".format(
                    os.path.join(self.data_path, "ui/img/devices/unknown.svg"),
                    str(vid_pid[0]),
                    str(vid_pid[1]),
                    self.get_string["unknown-device"])
        except Exception as e:
            dbg.stdout("Failed to get scan 'lsusb' for unrecognised devices!", dbg.warning)
            dbg.stdout("Exception: " + str(e), dbg.warning)

        self._fade_in("#sidebar-items")
        self.devices_set_device([0, True])

        self._set_active_button("#devices-tab", ".tab")
        self._set_text("#device-list", html)

    def devices_set_device(self, params=[]):
        """
        Sets the active device and shows its settings page.

        Params:
          - int     Device ID (from daemon device list)
          - bool    Fade in (sidebar only)
        """
        target_element = ".sidebar-container > .right"
        fade_in = True if params[1] in [True, "true"] else False

        try:
            device_id = int(params[0])
            device = self.devman.devices[device_id]
            serial = device.serial
            self.controller.active_device = device
            self.controller.active_device_id = device_id
        except IndexError:
            device_id = 0
            device = None
            serial = None
            self.controller.active_device = None
            self.controller.active_device_id = 0

        # No devices to list?
        if len(self.devman.devices) == 0:
            self._show_device_error("no-device.svg",
                _("No Razer Devices Found"),
                _("To begin, plug in a supported Razer device."))
            return

        # Update page title & sidebar
        self._set_title(device.name)
        self._set_active_button("#device-" + str(device_id), ".sidebar-container .item")

        # Populate device summary and current status
        if fade_in:
            self._hide(target_element)
        device_name = device.name
        device_image = common.get_real_device_image(device, "top")
        current_state = pref.get_device_state(device.serial, "main", "effect")

        if current_state:
            current_effect_text = common.get_effect_state_string(current_state)
            current_effect_image = "img/effects/" + current_state + ".svg"
            current_effect_div = ""
        else:
            current_effect_text = ""
            current_effect_image = ""
            current_effect_div = "hidden"

        # Show an icon adjacent to a slider if a device has multiple light sources.
        multiple_sources = common.has_multiple_sources(device)

        def _get_source_icon(source):
            if multiple_sources:
                if os.path.exists(self.data_path + "/ui/img/sources/{0}.svg".format(source)):
                    return "<img class='multiple-brightness' src='img/sources/{0}.svg'/> ".format(source)
                else:
                    return "<img class='multiple-brightness' src='img/fa/lightbulb.svg'/> ".format(source)
            return ""

        # Create controls for brightness controls
        brightness_html = ""
        if device.has("brightness"):
            brightness_html += self._make_control_slider("brightness", "set-brightness?main", 0, 100, 5 , int(device.brightness), "%", _get_source_icon("main"))

        if device.has("lighting_backlight_brightness") and not device.has("lighting_backlight_active"):
            brightness_html += self._make_control_slider("brightness-backlight", "set-brightness?backlight", 0, 100, 5 , int(device.fx.misc.backlight.brightness), "%")
        if device.has("lighting_backlight_active") and not device.has("lighting_backlight_brightness"):
            brightness_html += self._make_control_checkbox("brightness-backlight-toggle", "set-brightness?backlight", _("Backlight"), False if device.fx.misc.backlight.brightness == 0 else True, _get_source_icon("backlight"))

        if device.has("lighting_logo_brightness") and not device.has("lighting_logo_active"):
            brightness_html += self._make_control_slider("brightness-logo", "set-brightness?logo", 0, 100, 5 , int(device.fx.misc.logo.brightness), "%")
        if device.has("lighting_logo_active") and not device.has("lighting_logo_brightness"):
            brightness_html += self._make_control_checkbox("brightness-logo-toggle", "set-brightness?logo", _("Logo"), False if device.fx.misc.logo.brightness == 0 else True, _get_source_icon("logo"))

        if device.has("lighting_scroll_brightness") and not device.has("lighting_scroll_active"):
            brightness_html += self._make_control_slider("brightness-scroll", "set-brightness?scroll", 0, 100, 5 , int(device.fx.misc.scroll_wheel.brightness), "%")
        if device.has("lighting_scroll_active") and not device.has("lighting_scroll_brightness"):
            brightness_html += self._make_control_checkbox("brightness-scroll-toggle", "set-brightness?scroll", _("Scroll Wheel"), False if device.fx.misc.scroll_wheel.brightness == 0 else True, _get_source_icon("scroll"))

        if len(brightness_html) > 0:
            brightness_html = self._make_group(_("Brightness"), brightness_html)

        # Create controls for supported effects
        effects_html = ""
        colour_html = ""

        for source in ["main", "backlight", "logo", "scroll"]:
            source_html = ""
            source_options_html = ""

            if source == "main" and not device.has("lighting"):
                continue
            if source != "main" and not device.has("lighting_" + source):
                continue

            if source == "main":
                prefix = "lighting_"
            else:
                prefix = "lighting_" + source + "_"

            localised_names = {
                "main": _("Main"),
                "backlight": _("Backlight"),
                "logo": _("Logo"),
                "scroll": _("Scroll Wheel")
            }

            current_effect = pref.get_device_state(device.serial, source, "effect")
            current_effect_params = pref.get_device_state(device.serial, source, "effect_params")

            if device.has(prefix + "spectrum"):
                source_html += self._make_effect_button("spectrum", _("Spectrum"), current_effect == "spectrum", source)

            if device.has(prefix + "wave"):
                source_html += self._make_effect_button("wave", _("Wave"), current_effect == "wave", source)

            if device.has(prefix + "reactive"):
                source_html += self._make_effect_button("reactive", _("Reactive"), current_effect == "reactive", source)

            if device.has(prefix + "breath_dual") \
                or device.has(prefix + "breath_random") \
                or device.has(prefix + "breath_single") \
                or device.has(prefix + "breath_triple"):
                    source_html += self._make_effect_button("breath", _("Breath"), current_effect == "breath", source)

            if device.has(prefix + "starlight_dual") \
                or device.has(prefix + "starlight_random") \
                or device.has(prefix + "starlight_single") \
                or device.has(prefix + "starlight_triple"):
                source_html += self._make_effect_button("starlight", _("Starlight"), current_effect == "starlight", source)

            if device.has(prefix + "blinking"):
                source_html += self._make_effect_button("blinking", _("Blinking"), current_effect == "blinking", source)

            if device.has(prefix + "pulsate"):
                source_html += self._make_effect_button("pulsate", _("Pulsate"), current_effect == "pulsate", source)

            if device.has(prefix + "ripple"):
                source_html += self._make_effect_button("ripple", _("Ripple"), current_effect == "ripple", source)

            if device.has(prefix + "static"):
                source_html += self._make_effect_button("static", _("Static"), current_effect == "static", source)

            if source == "main" and device.has("lighting_led_matrix"):
                source_html += self._make_effect_button("custom", _("Custom"), current_effect == "custom", source, "img/fa/effects-circle.svg")

            if len(source_html) > 0:
                if multiple_sources:
                    effects_html += self._make_group(localised_names[source] + ' ' + _("Effect"), source_html)
                else:
                    effects_html += self._make_group(_("Effect"), source_html)

            # Effect Options (where supported) except backlight doesn't support effects.
            effect_options_html = ""
            if not source == "backlight":
                # Wave - can set direction
                if current_effect == "wave":
                    if common.get_device_type(device) == "mouse":
                        left = _("Down")
                        right = _("Up")
                    elif common.get_device_type(device) == "mousemat":
                        left = _("Clockwise")
                        right = _("Anti-clockwise")
                    else:
                        left = _("Left")
                        right = _("Right")

                    for value, label in enumerate([right, left], start=1):
                        effect_options_html += self._make_control_radio("", "set-effect-param?" + source + "?" + str(value), label, True if int(current_effect_params) == value else False, "wave-direction")

                # Reactive - can set speed
                if current_effect == "reactive":
                    for value, label in enumerate([_("Fast"), _("Medium"), _("Slow"), _("Very Slow")], start=1):
                        effect_options_html += self._make_control_radio("", "set-effect-param?" + source + "?" + str(value), label, True if int(current_effect_params) == value else False, "reactive-speed")

                # Breath - can select type (where supported)
                if current_effect == "breath":
                    if device.has("lighting_breath_random"):
                        effect_options_html += self._make_control_radio("", "set-effect-param?" + source + "?random", _("Random"), True if current_effect_params == "random" else False, "breath-type")

                    if device.has("lighting_breath_single"):
                        effect_options_html += self._make_control_radio("", "set-effect-param?" + source + "?single", _("Single Color"), True if current_effect_params == "single" else False, "breath-type")

                    if device.has("lighting_breath_dual"):
                        effect_options_html += self._make_control_radio("", "set-effect-param?" + source + "?dual", _("Dual Colors"), True if current_effect_params == "dual" else False, "breath-type")

                # Ripple - can select speed
                if current_effect == "ripple":
                    if device.has("lighting_ripple_random"):
                        effect_options_html += self._make_control_radio("", "set-effect-param?" + source + "?random", _("Random"), True if current_effect_params == "random" else False, "ripple-type")

                    if device.has("lighting_ripple"):
                        effect_options_html += self._make_control_radio("", "set-effect-param?" + source + "?single", _("Single Color"), True if current_effect_params == "single" else False, "ripple-type")

                # Show effect options, if any.
                if len(effect_options_html) > 0:
                    if multiple_sources:
                        effects_html += self._make_group(localised_names[source] + ' ' + _("Effect Options"), effect_options_html)
                    else:
                        effects_html += self._make_group(_("Effect Options"), effect_options_html)

                # Show colour options
                show_primary_colour = False
                show_secondary_colour = False

                if current_effect in ["reactive", "static"]:
                    show_primary_colour = True

                if current_effect == "breath" and current_effect_params in ["single", "dual"]:
                    show_primary_colour = True

                if current_effect == "breath" and current_effect_params == "dual":
                    show_secondary_colour = True

                if show_primary_colour:
                    primary_colour = pref.get_device_state(serial, source, "colour_primary")
                    if not primary_colour:
                        primary_colour = pref.get("colours", "primary")

                    html = self._make_colour_selector(primary_colour, "set-primary-colour", _("Set Primary Color"))
                    colour_html += self._make_group(_("Primary Color"), html)

                if show_secondary_colour:
                    secondary_colour = pref.get_device_state(serial, source, "colour_secondary")
                    if not secondary_colour:
                        secondary_colour = pref.get("colours", "secondary")

                    html = self._make_colour_selector(primary_colour, "set-secondary-colour", _("Set Secondary Color"))
                    colour_html += self._make_group(_("Secondary Color"), html)

        # Game Mode
        game_mode_html = ""
        if device.has("game_mode_led"):
            html = self._make_control_checkbox("game-mode", "set-game-mode", _("Enabled"), device.game_mode_led)
            game_mode_html = self._make_group(_("Game Mode"), html)

        # Macros
        macros_html = ""
        if device.has("macro_logic"):
            button = self._make_control_button("macro-help", "macro-help", _("Learn More"))
            macros_html = self._make_group(_("Macros"), button)

        # DPI
        dpi_html = ""
        if device.has("dpi"):
            current_value = device.dpi[0] # (X,Y)
            dpi_range = common.get_dpi_range(device)
            min_value = dpi_range[0]
            max_value = device.max_dpi

            # Two methods to set DPI - dropdown (presets) or slider (custom) can be toggled.
            if current_value in dpi_range:
                show_dropdown = True
            else:
                show_dropdown = False

            # Dropdown
            dropdown_list = []
            for value in dpi_range:
                dropdown_list.append([value, value])
            html = "<div id='dpi-presets-container' {0}>".format("hidden" if not show_dropdown else "")
            html += self._make_control_dropdown("dpi-presets", "set-dpi", current_value, dropdown_list)
            html += "<a style='display:block;padding-top:0.5em' onclick='swap_elements(&quot;#dpi-presets-container&quot;, &quot;#dpi-slider-container&quot;);'>{0}</a>".format(_("Set Custom DPI"))
            html += "</div>"

            # Slider
            html += "<div id='dpi-slider-container' {0}>".format("hidden" if show_dropdown else "")
            html += self._make_control_slider("dpi", "set-dpi", dpi_range[0], dpi_range[5], 100, current_value, "", "<img src='img/effects/dpi-slow.svg'/>", "<img src='img/effects/dpi-fast.svg'/>")
            html += "<a onclick='swap_elements(&quot;#dpi-slider-container&quot;, &quot;#dpi-presets-container&quot;);'>{0}</a>".format(_("Use Presets"))
            html += "</div>"

            dpi_html = self._make_group(_("DPI"), html)

        # Poll Rate
        poll_rate_html = ""
        if device.has("poll_rate"):
            current_value = device.poll_rate
            html = self._make_control_dropdown("polling-rate", "set-poll-rate", current_value, [[125, "125 Hz"], [500, "500 Hz"], [1000, "1000 Hz"]])
            poll_rate_html = self._make_group(_("Poll Rate"), html)

        # Display the page
        replace_dict = {
            "device_name": device_name,
            "device_image": device_image,
            "current_effect": current_effect_text,
            "current_effect_image": current_effect_image,
            "current_effect_div": current_effect_div,
            "brightness": brightness_html,
            "effects": effects_html,
            "colours": colour_html,
            "game_mode": game_mode_html,
            "macros": macros_html,
            "dpi": dpi_html,
            "poll_rate": poll_rate_html
        }

        self.update_content_view("device-controls", target_element, replace_dict)
        self._fade_in(target_element)

    def devices_show_device_info(self, params=[]):
        """
        Shows the devices info screen containing details about a device.

        Params:
            - int   (Optional) Device ID from daemon device manager.
                    Defaults to active device.
        """
        if len(params) > 0:
            device = self.devman.devices[int(params[0])]
        else:
            device = self.controller.active_device

        # Gather device info
        title = _("Device Info for") + ' ' + device.name
        formfactor_icon = common.get_device_type(device)
        formfactor = formfactor_icon.capitalize()

        try:
            serial = device.serial
        except Exception:
            serial = _("n/a")

        vidpid = common.get_device_vid_pid(device)
        vidpid = "{0}:{1}".format(vidpid[0], vidpid[1])

        if device.type == "keyboard":
            try:
                keyboard_layout_html = "<tr><td>{0}</td><td>{1}</td></tr>".format(_("Keyboard Layout"), device.keyboard_layout)
            except Exception:
                keyboard_layout_html = _("Unknown")
        else:
            keyboard_layout_html = ""

        try:
            firmware = device.firmware_version
        except Exception:
            firmware = _("n/a")

        if device.macro:
            macro = _("Supported")
            macro_class = "yes"
        else:
            macro = _("Unsupported")
            macro_class = "no"

        try:
            rows = int(device.fx.advanced.rows)
            cols = int(device.fx.advanced.cols)
            matrix = "{0} {1}, {2} {3}".format(str(rows), common.get_plural(rows, _("row"), _("rows")), str(cols), common.get_plural(cols, _("column"), _("columns")))
            matrix_class = "yes"
        except Exception:
            matrix = _("Unsupported")
            matrix_class = "no"

        # Populate capabilities table
        capabilities_html = ""

        sorted_cap = list(device.capabilities.keys())
        sorted_cap.sort()

        for capability in sorted_cap:
            if device.capabilities[capability] == True:
                supported = _("Yes")
                supported_class = "yes"
            else:
                supported = _("No")
                supported_class = "no"

            capabilities_html += "<tr><td><code>{0}</code></td><td class='center {2}'>{1}</td></tr>".format(
                capability, supported, supported_class)

        replace_dict = {
            "device_image": common.get_real_device_image(device),
            "formfactor": formfactor,
            "formfactor_icon": formfactor_icon,
            "serial": serial,
            "firmware": firmware,
            "macro": macro,
            "macro_class": macro_class,
            "matrix": matrix,
            "matrix_class": matrix_class,
            "vidpid": vidpid,
            "keyboard_layout": keyboard_layout_html,
            "capabilities": capabilities_html
        }

        html = self.controller.get_content_view("device-info-dialog", replace_dict)
        self._open_dialog("info", title, html, "80vh", "80vw")

    def devices_set_overview(self, params=[]):
        """
        Shows the overview screen listing all devices.
        Params:
          - None
        """
        target_element = ".sidebar-container > .right"
        self._hide(target_element)
        self._set_active_button("#device-overview", ".sidebar-container .item")
        self._set_title(_("All Devices"))

        devices_html = ""

        device_id = -1
        for device in self.devman.devices:
            device_id = device_id + 1
            device_name = device.name
            device_serial = device.serial
            device_image = common.get_real_device_image(device, "top")

            # Determine states to display
            current_state_html = ""
            for source in common.get_supported_lighting_sources(device):
                # -- Effect
                current_state = pref.get_device_state(device.serial, source, "effect")
                if current_state:
                    current_effect_text = common.get_effect_state_string(current_state)
                    current_effect_image = "img/effects/" + current_state + ".svg"
                    current_state_html += "<div class='status'><img src='{1}'/><span>{0}</span></div>".format(current_effect_text, current_effect_image)

                # -- Brightness
                current_brightness = common.get_brightness(device, source)
                current_brightness_icon = common.get_source_icon(device, source)

                if type(current_brightness) == int:
                    current_state_html += "<div class='status'><img src='{1}'/><span>{0}%</span></div>".format(current_brightness, current_brightness_icon)
                elif type(current_brightness) == bool:
                    if current_brightness == True:
                        string = _("On")
                    else:
                        string = _("Off")

                    current_state_html += "<div class='status'><img src='{1}'/><span>{0}</span></div>".format(string, current_brightness_icon)

            html = "<div class='device'>"
            html += "<div class='device-image'>"
            html += "<img src='{0}'>".format(device_image)
            html += "</div>"
            html += "<div class='device-details'>"
            html += "<h3>{0}</h3>".format(device_name)
            html += "<code>{0}</code>".format(device_serial)
            html += "<div class='statuses'>{0}</div>".format(current_state_html)
            html += "</div>"
            html += "<div class='device-actions'>"
            html += "<button onclick='cmd(\"device-info?{0}\")'>{1}</button>".format(str(device_id), _("Device Info"))
            html += "<button onclick='cmd(\"device-select?{0}?true\")'>{1}</button>".format(str(device_id), _("Configure"))
            html += "</div>"
            html += "</div>"
            devices_html += html

        if len(self.devman.devices) == 0:
            self.devices_init_tab()

        # Add controls to set brightness/effect on all devices (where supported)
        brightness_slider = self._make_effect_button("brightness", _("Off"), False, None, "img/brightness/0.svg", "set-all-brightness?0")
        brightness_slider += self._make_effect_button("brightness", "25%", False, None, "img/brightness/25.svg", "set-all-brightness?25")
        brightness_slider += self._make_effect_button("brightness", "50%", False, None, "img/brightness/50.svg", "set-all-brightness?50")
        brightness_slider += self._make_effect_button("brightness", "75%", False, None, "img/brightness/75.svg", "set-all-brightness?75")
        brightness_slider += self._make_effect_button("brightness", "100%", False, None, "img/brightness/100.svg", "set-all-brightness?100")

        effect_buttons = self._make_effect_button("spectrum", _("Spectrum"), False, None, None, "set-all-effect")
        effect_buttons += self._make_effect_button("wave", _("Wave"), False, None, None, "set-all-effect")
        effect_buttons += self._make_effect_button("breath", _("Breath"), False, None, None, "set-all-effect")
        effect_buttons += self._make_effect_button("reactive", _("Reactive"), False, None, None, "set-all-effect")
        effect_buttons += self._make_effect_button("static", _("Static"), False, None, None, "set-all-effect")

        replace_dict = {
            "device-list": "<div class='device-overview-container'>" + devices_html + "</div>",
            "brightness-slider": brightness_slider,
            "effect-buttons": effect_buttons
        }
        self.update_content_view("device-overview", target_element, replace_dict)
        self._fade_in(target_element)

    def devices_set_unknown(self, params=[]):
        """
        Shows a message for devices not known.
        Params:
          - None
        """
        self._show_device_error("unrecog-device.svg",
            _("Unrecognized Razer Device"),
            _("Polychromatic detected a Razer device, but the OpenRazer daemon did not register it.") + '<br><br>' + _("Either the device is unsupported or there is a problem with your OpenRazer installation."))
        return

    def set_effect(self, params=[]):
        """
        Set device effect for the active device.

        Params:
          - source  Light source to apply, e.g. "main"
          - effect  Effect name
        """
        device = self.controller.active_device
        source = params[0]
        effect = params[1]

        # Use default params and last known colours.
        effect_params = None
        primary_colours = pref.get_device_state(device.serial, source, "colour_primary")
        secondary_colours = pref.get_device_state(device.serial, source, "colour_secondary")

        common.set_lighting_effect(pref, device, source, effect, effect_params, primary_colours, secondary_colours)

        # Reload devices page
        self.devices_set_device([self.controller.active_device_id, False])

    def set_effect_param(self, params=[]):
        """
        Set effect parameter for active device.

        Params:
          - source          Light source to apply, e.g. "main"
          - effect_param    Effect parameter name
          - checked         Ignored as radio is always 'on'.
        """
        # Recall previously used effect and colours
        device = self.controller.active_device
        source = params[0]
        effect = pref.get_device_state(device.serial, source, "effect")
        effect_params = params[1]
        primary_colours = pref.get_device_state(device.serial, source, "colour_primary")
        secondary_colours = pref.get_device_state(device.serial, source, "colour_secondary")

        # Apply new effect settings
        common.set_lighting_effect(pref, device, source, effect, effect_params, primary_colours, secondary_colours)

        # Reload devices page
        self.devices_set_device([self.controller.active_device_id, False])

    def set_brightness(self, params=[]):
        """
        Sets the brightness for active device.

        Params:
          - source          Light source to apply, e.g. "main"
          - value           Value or true/false (from JS)
        """
        device = self.controller.active_device
        source = params[0]
        value = params[1]
        togglable = False

        if value == "true":
            value = 1
            togglable = True
        elif value == "false":
            value = 0
            togglable = True

        common.set_brightness(pref, device, source, value)

        if not togglable:
            self._set_text("#brightness-value", value)

    def set_gamemode(self, params=[]):
        """
        Enables/disables the game mode setting.

        Params:
          - boolean         true/false
        """
        device = self.controller.active_device

        if params[0] == "true":
            enabled = True
        else:
            enabled = False

        device.game_mode_led = enabled

    def set_dpi(self, params=[]):
        """
        Sets the DPI for active device, which should be a mouse.

        Params:
          - value       DPI level from JS
        """
        # TODO: Add checks and show daemon error dialog.
        device = self.controller.active_device
        dpi_X = params[0]
        dpi_Y = params[0]

        device.dpi = (int(dpi_X), int(dpi_Y))

        self._set_value("#dpi-presets", dpi_X)
        self._set_value("#dpi-slider", dpi_X)
        self._set_text("#dpi-value", dpi_X)

    def set_poll_rate(self, params=[]):
        """
        Sets the polling rate for active device, which should be a mouse.

        Params:
          - value       Polling rate value, e.g. 125
        """
        device = self.controller.active_device
        value = int(params[0])
        device.poll_rate = value

    def set_all_effect(self, params=[]):
        """
        Sets an effect (with defaults) to all connected devices.

        Params:
          - effect      Effect name (as identified by Polychromatic)
        """
        effect = params[1]
        for device in self.devman.devices:
            for source in common.get_supported_lighting_sources(device):
                try:
                    successful = common.set_lighting_effect(pref, device, source, effect)
                except Exception:
                    successful = False

                if successful == False:
                    self._fade_in("#unsupported-all-effect")

    def set_all_brightness(self, params=[]):
        """
        Sets the brightness for all connected devices. For devices with only an
        "active" toggle, this is either on/off.

        Params:
          - value       Brightness %
        """
        value = int(params[0])
        for device in self.devman.devices:
            for source in common.get_supported_lighting_sources(device):
                common.set_brightness(pref, device, source, value)

    def set_primary_colour(self, params=[]):
        """
        Sets the primary colour of the current active effect.

        Params:
          - hex     New colour hex
        """
        colour_hex = params[0]
        active_device = self.controller.active_device

        self.update_page("#set-primary-colour", "html", self._make_colour_selector(colour_hex, "set-primary-colour", _("Set Primary Color"), active_device))
        common.save_colours_to_all_sources(pref, active_device, "colour_primary", colour_hex)
        common.repeat_last_effect(pref, active_device)

    def set_secondary_colour(self, params=[]):
        """
        Sets the primary colour of the current active effect.

        Params:
          - hex     New colour hex
        """
        colour_hex = params[0]
        active_device = self.controller.active_device

        self.update_page("#set-secondary-colour", "html", self._make_colour_selector(colour_hex, "set-secondary-colour", _("Set Secondary Color"), active_device))
        common.save_colours_to_all_sources(pref, active_device, "colour_secondary", colour_hex)
        common.repeat_last_effect(pref, active_device)

    def open_uri(self, params=[]):
        """
        Opens a URI from within the application. Could be a URL or file/directory.

        Params:
          - uri     Path to file or URL resource
        """
        uri = params[0]
        dbg.stdout("Opening URI:" + uri, dbg.action, 1)
        result = os.system("xdg-open '{0}'".format(uri))

        if result > 0:
            self._open_dialog("serious", _("Failed to open URI"), _("The process returned exit code") + " {0}.".format(str(result)))

    def preferences_init_tab(self, params=[]):
        """
        Loads the Preferences tab to a specific tab.
        """
        self._set_active_button("#preferences-tab", ".tab")
        self.update_content_view("preferences")
        self._hide("#preferences-content")
        self._fade_in("#sidebar-items")

        self.preferences_set_tab([0])

    def preferences_set_tab(self, params=[]):
        """
        Loads a tab inside the Preferences tab.

        Params:
            - int   ID of section to show. If blank, then 0 (about).
        """
        try:
            section_id = params[0]
        except Exception:
            section_id = 0

        def _add_version(label, key, index, text=""):
            """Produces HTML for displaying version info. Tries 'key' in 'index' dict unless 'text' is specified."""
            if text:
                value = text
            else:
                try:
                    value = index[key]
                except KeyError:
                    value = _("Unknown")

            return self._make_group(label, "<code class='transparent' style='margin:0'>{0}</code>".format(value), True)

        def _add_online_link(logo, url):
            """Produces HTML for a social link, used on about pages"""
            return "<a class='social-link' onclick='cmd(&quot;open-uri?{1}&quot;)' title='{1}'><img src='img/logo/{0}.svg'/></a>".format(logo, url)

        def _add_link(uri, label):
            """Produces HTML For a link, used on the daemon page"""
            return self._make_group(label, "<a onclick='cmd(\"open-uri?{0}\")'>{0}</a>".format(uri), True)

        def _add_config_checkbox(group, setting, label, default_state, reload_tab=None):
            """Produces HTML for setting a boolean preference"""
            current_state = pref.get(group, setting, default_state)
            return self._make_control_checkbox(common.generate_uuid(), "pref-set?{0}?{1}?{2}".format(group, setting, "true" if reload_tab else "false"), label, current_state)

        def _add_config_dropdown(group, setting, options, reload_tab=None):
            """Produces HTML for setting a predefined string preference"""
            current_value = pref.get(group, setting, options[0][0])
            return self._make_control_dropdown(common.generate_uuid(), "pref-set?{0}?{1}?{2}".format(group, setting, "true" if reload_tab else "false"), current_value, options)

        def _add_config_text(group, setting, placeholder, browse_btn=False, reload_tab=None):
            """Produces HTML for setting a custom string preference"""
            current_value = pref.get(group, setting, "")
            return self._make_control_text(common.generate_uuid(), "pref-set?{0}?{1}?{2}".format(group, setting, "true" if reload_tab else "false"), current_value, placeholder, browse_btn)

        def about_section():
            self._set_title(_("About the Application"))

            # Logo & Online Links
            html = "<div class='program-logo'><img src='img/logo/polychromatic.svg'/><span>polychromatic</span></div>"
            html += "<div class='program-links'>"
            html += "<p><a onclick='cmd(&quot;open-uri?{0}&quot;)'>{0}</a></p>".format("https://polychromatic.app")
            html += "<p>"
            html += _add_online_link("github", "https://github.com/polychromatic/polychromatic")
            html += _add_online_link("facebook", "https://facebook.com/p0lychromatic")
            html += _add_online_link("twitter", "https://twitter.com/p0lychromatic")
            html += "</p>"
            html += "</div>"

            # Gather version data
            versions = {}
            changelog_url = "https://github.com/polychromatic/polychromatic/releases"

            if self.controller.versions:
                versions = {
                    "polychromatic": self.controller.version,
                    "polychromatic_pref": pref.version,
                    "gi": self.controller.versions["gi"],
                    "gtk": self.controller.versions["gtk"],
                    "webkit": self.controller.versions["webkit"],
                    "python": "{0}.{1}.{2}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
                }
            else:
                self._open_dialog("serious", _("Incompatible Version"), _("Some of the modules could not have their versions determined."))

            try:
                versions["openrazer"] = self.devman.version
                versions["openrazer_daemon"] = self.devman.daemon_version
            except NameError as e:
                self._open_dialog("serious", _("Incompatible Version"), _("Some of the modules could not have their versions determined."))

            # Application
            ver_app = _add_version(_("Version"), "polychromatic", None, versions["polychromatic"] + " <a onclick='cmd(\"open-uri?{1}\")'>({0})</a>".format(_("Changelog"), changelog_url))
            ver_app += _add_version(_("Configuration"), "polychromatic_pref", versions)

            # Dependencies
            ver_deps = _add_version(_("OpenRazer"), "openrazer", versions)
            ver_deps += _add_version("Python", "python", versions)
            ver_deps += _add_version("WebKit2", "webkit", versions)
            ver_deps += _add_version("PyGObject", "gi", versions)
            ver_deps += _add_version("GTK", "gtk", versions)

            # Internals
            html += self._make_group_name(_("Application")) + ver_app
            html += self._make_group_name(_("Dependencies")) + ver_deps

            return html

        def general_section():
            self._set_title(_("General"))
            html = ""

            # Behaviour
            html += self._make_group_name(_("Behavior"))
            grp = _add_config_checkbox("effects", "activate_on_click", _("Automatically activate selected effects."), False)
            grp += _add_config_checkbox("profiles", "activate_on_click", _("Automatically activate selected profiles."), False)
            html += self._make_group(_("Sidebar"), grp)

            # Editor
            html += self._make_group_name(_("Editor"))
            grp = _add_config_checkbox("effects", "live_preview", _("While editing, show changes on the actual hardware."), True)
            html += self._make_group(_("Preview"), grp)

            return html

        def tray_section():
            self._set_title(_("Tray Applet"))
            html = self._make_group_name(_("Icon"))

            # Get options
            current_option = pref.get("tray_icon", "type")
            icon_types = [
                ["builtin", _("Built-in Icon")],
                ["gtk", _("GTK Icon Name")],
                ["custom", _("Custom Image")]
            ]

            # Preview
            inner_html = "<img id='tray-icon-preview' src='{0}'/>".format(common.get_tray_icon(dbg, pref, self.path))
            html += self._make_group(_("Preview"), inner_html)

            # Set icon type
            inner_html = _add_config_dropdown("tray_icon", "type", icon_types, 2)
            html += self._make_group(_("Icon Type"), inner_html)

            # Set icon parameters
            icon_type = pref.get("tray_icon", "type", "bulitin")
            inner_html = ""

            if icon_type == "builtin":
                icon_index = pref.load_file(os.path.join(self.path.data_source, "tray/icons.json"))
                icons = sorted(list(icon_index.keys()))
                options = []
                for uuid in icons:
                    icon_name = icon_index[uuid]["name"]
                    options += [[uuid, icon_name]]
                inner_html = _add_config_dropdown("tray_icon", "icon_id", options, 2)

            elif icon_type == "gtk":
                inner_html = _add_config_text("tray_icon", "gtk_icon_name", _("Example: ibus-keyboard"), False, True)

            elif icon_type == "custom":
                inner_html = _add_config_text("tray_icon", "custom_image_path", _("/path/to/image"), True, True)

            else:
                dbg.stdout("Invalid icon type! Resetting...", dbg.error)
                pref.set("tray_icon", "type", "builtin")
                pref.set("tray_icon", "icon_id", "0")

            html += self._make_group(_("Icon Image"), inner_html)

            # Compatibility
            html += self._make_group_name(_("Advanced"))
            html += self._make_group(_("Compatibility"), _add_config_checkbox("tray_icon", "force_fallback", _("Force GTK Status icon instead of AppIndicator (fallback)"), False))
            html += self._make_group(_("Apply Changes"), self._make_control_button("", "restart?tray", _("Restart Tray Applet")))

            return html

        def colours_section():
            self._set_title(_("Saved Colors"))

            # Default Colours
            col_primary = self._make_colour_selector(pref.get("colours", "primary", "#00FF00"), "pref-set?colours?primary?true", _("Default Primary Color"))
            col_secondary = self._make_colour_selector(pref.get("colours", "secondary", "#00FFFF"), "pref-set?colours?secondary?true", _("Default Secondary Color"))

            html = self._make_group_name(_("Default Colors"))
            html += "<p class='info'>{0}</p>".format(_("These colors will be chosen when setting effects from 'All Devices' or the tray applet."))
            html += self._make_group(_("Primary Color"), col_primary, True)
            html += self._make_group(_("Secondary Color"), col_secondary, True)

            return html

        def daemon_section():
            self._set_title(_("OpenRazer Daemon"))

            # Logo & Online Links
            html = "<div class='program-logo openrazer'><img src='img/logo/openrazer.svg'/><span>OpenRazer</span></div>"
            html += "<div class='program-links'>"
            html += "<p><a onclick='cmd(&quot;open-uri?{0}&quot;)'>{0}</a></p>".format("https://openrazer.github.io")
            html += "<p>"
            html += _add_online_link("github", "https://github.com/openrazer/openrazer")
            html += _add_online_link("telegram", "https://t.me/joinchat/AMhHjj9TxhnBYO2EklBL9Q")
            html += _add_online_link("matrix", "https://matrix.to/#/#openrazer:matrix.org")
            html += _add_online_link("facebook", "https://facebook.com/openrazer")
            html += _add_online_link("twitter", "https://twitter.com/openrazer")
            html += "</p>"
            html += "<p>{0}</p>".format(_("The daemon is the software that communicates between Polychromatic and the driver."))
            html += "</div>"

            # Display OpenRazer version information
            try:
                versions = {
                        "openrazer": self.devman.version,
                        "openrazer_daemon": self.devman.daemon_version,
                        "distro": " ".join(linux_distribution()),
                        "kernel": uname().release
                }
                ver_html = self._make_group_name(_("Version"))
                ver_html += _add_version(_("Device Manager"), "openrazer", versions)
                ver_html += _add_version(_("Daemon"), "openrazer_daemon", versions)

                ver_html += self._make_group_name(_("System"))
                ver_html += _add_version(_("Distro"), "distro", versions)
                ver_html += _add_version(_("Kernel"), "kernel", versions)
                html += ver_html
            except NameError:
                self._open_dialog("serious", _("Incompatible Version"), _("Some of the modules could not have their versions determined."))

            # Logs
            home_dir = os.environ["HOME"]
            html += self._make_group_name(_("Configuration"))
            html += _add_link(home_dir + "/.config/openrazer/razer.conf", _("Configuration"))
            html += _add_link(home_dir + "/.local/share/openrazer/logs/razer.log", _("Log"))

            return html

        sections = {
            "0": about_section,
            "1": general_section,
            "2": tray_section,
            "3": colours_section,
            "4": daemon_section,
            "5": schedule_section
        }

        self.current_tab = section_id
        self._set_active_button("#pref-item-" + str(section_id), ".item")
        self._hide("#preferences-content")
        self.update_page("#preferences-content", "html", sections[str(section_id)]())
        self._fade_in("#preferences-content")

    def preferences_set_pref(self, params=[]):
        """
        Saves a preference to file. Auto reloads page if in Preferences tab.

        Params:
            - group         Preference Group
            - setting       Preference Setting
            - reload_tab    True if current tab should be reloaded.
            - value         New value to set as string. Data type independent.
                            - Checkbox: "true", "false"
                            - Value: "text"
        """
        group = params[0]
        setting = params[1]
        reload_tab = params[2]
        value = params[3]
        dbg.stdout("Updating preference: '{0}' => '{1}' to value '{2}'".format(group, setting, value), dbg.action, 1)
        pref.set(group, setting, value)

        if reload_tab == "true":
            self.preferences_set_tab([self.current_tab])

    def browse_input(self, params=[]):
        """
        Shows a file browser dialog and updates a text box control.

        Params:
            - element_id    Element to set path to.
            - dialog_id     Integer representing dialogue settings to use.
        """
        element_id = params[0]
        dialog_id = int(params[1])
        browse_path = GTKDialogues.file_picker(dialog_id)

        if browse_path:
            self.update_page("#" + element_id, "val", browse_path)
            self.update_page("#" + element_id + "-options", "show")

    def restart_component(self, params=[]):
        """
        Restarts a component used by Polychromatic.

        Params:
            - name      Component to reload.
                        - tray          Tray Applet
                        - openrazer     OpenRazer Daemon
        """
        component = params[0]

        if component == "tray":
            return common.restart_tray_applet(dbg, self.path)
