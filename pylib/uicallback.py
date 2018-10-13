#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2018 Luke Horwell <code@horwell.me>
#
"""
This module contains "callbacks" when "commands" are issued via the Controller application.

1. Interactions can be called in JavaScript using cmd("name-of-function").
2. Commands are linked 'name-of-function' to UICmd function in the Controller's process_command() function.
3. Functions are issued below, inheriting essential variables for manipulating the page (e.g. controller/webkit)
"""
from . import common
from . import preferences as pref
import os
import sys
from time import sleep

_ = common.setup_translations(__file__, "polychromatic")
dbg = common.Debugging()

class UICmd(object):
    """
    Process instructions passed via the frontend (HTML/JS) to the Python layer.

    All parameters are passed as strings within a list. '?' is the delimiter.
    """
    def __init__(self, controller, webkit, devman, get_string_bank, data_source):
        self.webkit = webkit
        self.controller = controller
        self.update_page = controller.update_page
        self.update_content_view = controller.update_content_view
        self.devman = devman
        self.ani_js_speed = "250"
        self.ani_py_speed = 0.25
        self.get_string = get_string_bank(_)
        self.data_path = data_source

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
          - dialog_type     Styling to apply: info, error, general
          - title           Name of dialog
          - inner_html      HTML to place inside
          - buttons         List containing onclick and labels, e.g. [["cmd()", "Item 1"], ["cmd()", "Item 2"]]
          - height          Desired dialog box height
          - width           Desired dialog box width
        """
        self.update_page("#dialog", "remove")
        html = "<div id='dialog' style='max-height:{0};max-width:{1}'>".format(height, width)
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
    def _make_group(label, content):
        """
        Generates a group for organising the user interface into two columns.

        label           Label that appears on the left.
        contents        HTML that appears on the right.
        """
        return "<div class='group'><div class='left'><label>{0}</label></div><div class='right'>{1}</div></div>".format(label, content)

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

    @staticmethod
    def _make_control_button(element_id, command, label, icon_path=None, disabled=None):
        """
        Generates a button for Python generated HTML.

        element_id      ID for element.
        command         cmd('XXX') where XXX is this parameter.
        label           Text that appears on this button.
        icon_path       (Optional) Path to the icon, e.g. "img/effects/unknown.svg"
        disabled        (Optional) True to disable button initially.
        """
        return "<button id='{0}' class='{1}' {1} onclick='{2}'>{3}{4}</button>".format(
            element_id,
            "disabled" if disabled else "",
            command,
            "<img src='" + icon_path + "'/> " if icon_path else "",
            label)

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
    def _make_colour_selector(current_colour, callback_function):
        """
        Generates a preview box to view/change a colour.

        Params:
            current_colour      List in format: [red, green, blue] of current colour.
            callback_function   String inside cmd('XXX?R?G?B') where XXX is the command.
                                This is used when a new custom colour is selected.
        """
        return "<div class='colour-selector'><div id='{0}' class='current-colour' style='background-color:{1}'></div> <button onclick='cmd($quot;open-colour-picker?{0}?{2})'>{3}</button></div>".format(
            common.generate_uuid(),
            common.colour_to_hex(current_colour),
            callback_function, _("Change..."))

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
        self.update_page(selector, "hide")
        self.update_content_view("device-error", selector)
        self.update_page("#error-image", "attr", "src", "img/error/" + image)
        self.update_page("#error-title", "html", title)
        self.update_page("#error-text", "html", text)
        self.update_page("#error-image", "show")
        self.update_page(selector, "fadeIn", self.ani_js_speed)

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
        self._set_active_button("#device-" + str(device_id), "#device-list .item")

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
        def _make_effect_button(fx_name, label, active, source, custom_icon_path=None):
            return "<button id='effect-{0}' class='effect-btn {2}' onclick='cmd(\"set-effect?{3}?{0}\")'><img src='{4}'/><span>{1}</span></button>".format(
                fx_name, label, "active" if active else "", source, custom_icon_path if custom_icon_path else "img/effects/" + fx_name + ".svg")

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
                source_html += _make_effect_button("spectrum", _("Spectrum"), current_effect == "spectrum", source)

            if device.has(prefix + "wave"):
                source_html += _make_effect_button("wave", _("Wave"), current_effect == "wave", source)

            if device.has(prefix + "reactive"):
                source_html += _make_effect_button("reactive", _("Reactive"), current_effect == "reactive", source)

            if device.has(prefix + "breath_dual") \
                or device.has(prefix + "breath_random") \
                or device.has(prefix + "breath_single") \
                or device.has(prefix + "breath_triple"):
                    source_html += _make_effect_button("breath", _("Breath"), current_effect == "breath", source)

            if device.has(prefix + "starlight_dual") \
                or device.has(prefix + "starlight_random") \
                or device.has(prefix + "starlight_single") \
                or device.has(prefix + "starlight_triple"):
                source_html += _make_effect_button("starlight", _("Starlight"), current_effect == "starlight", source)

            if device.has(prefix + "blinking"):
                source_html += _make_effect_button("blinking", _("Blinking"), current_effect == "blinking", source)

            if device.has(prefix + "pulsate"):
                source_html += _make_effect_button("pulsate", _("Pulsate"), current_effect == "pulsate", source)

            if device.has(prefix + "ripple"):
                source_html += _make_effect_button("ripple", _("Ripple"), current_effect == "ripple", source)

            if device.has(prefix + "static"):
                source_html += _make_effect_button("static", _("Static"), current_effect == "static", source)

            if source == "main" and device.has("lighting_led_matrix"):
                source_html += _make_effect_button("custom", _("Custom"), current_effect == "custom", source, "img/fa/effects-circle.svg")

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
                        effects_html += self._make_group(_("Effects Options"), effect_options_html)

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
                        primary_colour = [0, 255, 0]

                    html = self._make_colour_selector(primary_colour, "set-primary-colour")
                    colour_html += self._make_group(_("Primary Color"), html)

                if show_secondary_colour:
                    secondary_colour = pref.get_device_state(serial, source, "colour_secondary")
                    if not secondary_colour:
                        secondary_colour = [0, 255, 0]

                    html = self._make_colour_selector(primary_colour, "set-secondary-colour")
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
        if fade_in:
            self._fade_in(target_element)

    def devices_show_device_info(self, params=[]):
        """
        Shows the devices info screen containing details about the active device.
        """
        device = self.controller.active_device
        title = _("Device Info for") + ' ' + device.name

        # Gather device info
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
        pass

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
