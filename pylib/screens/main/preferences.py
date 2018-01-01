#!/usr/bin/env python3
#
# Polychromatic is licensed under the GPLv3.
# Copyright (C) 2017 Luke Horwell <luke@ubuntu-mate.org>
#

"""
Polychromatic Pages Module: Preferences (subpage of main)

Contains options for configuring the application.
"""

from ... import common as common
from time import sleep as sleep
import os
import sys

from platform import linux_distribution
from subprocess import Popen as background_process
import requests

_ = common.setup_translations(__file__, "polychromatic")
fade_speed = common.fade_speed
fade_interval = common.sleep_interval

def print_sidebar(self, active_sidebar):
    categories = [
        # [<sidebar id>, <label>, <icon path>]
        [0, _("About"), "logo/polychromatic.svg"],
        [1, _("General"), "ui/generic-application.svg"],
        [2, _("Tray Applet"), "ui/profile-default.svg"],
        [3, _("Colors"), "effects/static.svg"],
        [4, _("Daemon"), "states/unknown.svg"]
    ]

    html_sidebar = ""
    for category in categories:
        html_sidebar += self.ui.print_sidebar_item(category[0], category[2], category[1], ("active" if active_sidebar == category[0] else ""))

    return html_sidebar


def print_contents(self, active_sidebar):
    subpages = {
        0: _print_about_tab,
        1: _print_general_tab,
        2: _print_tray_tab,
        3: _print_colours_tab,
        4: _print_daemon_tab
    }

    try:
        return subpages[active_sidebar](self)
    except Exception as e:
        self.dbg.stdout("Failed to populate content!", self.dbg.error)
        self.dbg.stdout("Exception: " + str(e), self.dbg.error)

    return ""


def process_command(self, cmd):
    """
    Process a command specific to this subpage.
    """
    # About page
    if cmd == "update-check":
        """
        For git clone'd repositories, run the update.sh script to check for updates.
        """
        update_script = os.path.join(self.path.data_source + "/../install/update.sh")
        if os.path.exists("/usr/bin/x-terminal-emulator"):
            background_process('x-terminal-emulator -e "{0}"'.format(update_script), shell=True)
        else:
            background_process('xterm -e "{0}"'.format(update_script), shell=True)
        return True

    elif cmd == "fetch-changelog":
        """
        Downloads and shows the latest changelog.
        """
        self.update_page("#loading-changelog", "show")
        def fetch_failed(reason):
            failed_dialog_uuid = self.ui.JavaScript.generate_alert_dialog(self.update_page, _("Failed to retrieve changelog"), reason, _("OK"), None, "", "30em", "8em")
            self.update_page("#loading-changelog", "hide")
            self.controller.run_javascript("dialog_open('{0}')".format(failed_dialog_uuid))

        try:
            r = requests.get("https://raw.githubusercontent.com/lah7/polychromatic/master/CHANGELOG")

            if r.status_code == 200:
                html = ""
                ver = 0
                for line in r.text.split("\n"):
                    if line.startswith("#"):
                        ver = line[1:].strip()
                        if ver == self.controller.version:
                            html += "<h3><span class='fa fa-arrow-right'></span> {0}</h3>".format(ver)
                        else:
                            html += "<h3>{0}</h3>".format(ver)
                        html += "<p><a onclick='cmd(\"{0}\")'>".format("open?https://github.com/lah7/polychromatic/releases/tag/v" + ver) + _("View Release Notes") + "</a></p>"
                    elif line == '':
                        continue
                    else:
                        if ver == self.controller.version:
                            html += "<li style='color:lime'>{0}</li>".format(line.split('*')[1])
                        else:
                            html += "<li>{0}</li>".format(line.split('*')[1])

                changelog_uuid = self.ui.JavaScript.generate_alert_dialog(self.update_page,
                    _("What's New?"),
                    "<div id='changelog-body'>{0}</div>".format(html),
                    _("Close"), None,
                    "", "60%", "70%")
                self.controller.run_javascript("dialog_open('{0}')".format(changelog_uuid))
            else:
                fetch_failed(_("A communication error occurred. Check your connection, or try visiting the project's webpage instead."))

        except Exception:
            fetch_failed(_("An exception occurred while processing this request. Please try again, or visit the project's webpage instead."))

        return True

    elif cmd.startswith("pref-set"):
        """
        Sets a new value for preferences.json

        Expects:    ?<group>?<setting>?<value>
        """
        cmd = cmd.split("?")
        group = cmd[1]
        setting = cmd[2]
        value = cmd[3]
        self.pref.set(group, setting, value)
        self.dbg.stdout("Set '{0}/{1}' to {2}".format(group, setting, str(value)), self.dbg.action, 1)
        return True

    elif cmd.startswith("pref-toggle"):
        """
        Toggles a boolean for a key in preferences.json

        Expects:    ?<group>?<setting>
        """
        cmd = cmd.split('?')
        group = cmd[1]
        setting = cmd[2]
        value = not self.pref.get(group, setting, False)
        self.dbg.stdout("Set '{0}' -> {1}' = {2}".format(group, setting, str(value)), self.dbg.action, 1)
        self.pref.set(group, setting, value)
        return True

    elif cmd == "open-config-folder":
        """
        Opens Polychromatic's configuration folder.
        """
        os.system("xdg-open '{0}'".format(self.path.root))
        return True

    # Tray Icon
    elif cmd.startswith("select-tray-icon-uuid?"):
        """
        Sets the tray icon preference to one of the built-in ones.
        It will also validate that the specified name is valid.

        Expects:    ?<uuid>
        """
        uuid = cmd.split("?")[1]
        self.pref.set("tray_icon", "type", "builtin")
        self.pref.set("tray_icon", "value", str(uuid))

        self.update_page(".tray-uuid", "removeClass", "selected")
        self.update_page("#tray-uuid-" + uuid, "addClass", "selected")
        self.update_page(".tray_icon", "prop", "checked", "false")

        self.update_page("input.invalid", "removeClass", "invalid")
        self.update_page("label.invalid", "fadeOut", fade_speed)

        self.update_page("#tray-builtin-icon", "prop", "checked", "true")
        icon_path = common.get_tray_icon(self.dbg, self.pref, self.path)
        self.update_page(".gtk-preview", "attr", "src", "file://" + icon_path)
        common.restart_tray_applet(self.dbg, self.path)
        return True

    elif cmd.startswith("select-tray-icon-gtk?"):
        """
        Sets the tray icon preference to a GTK icon name.
        It will also validate that the specified icon name exists.

        Expects:    ?<name>
        """
        gtk_name = cmd.split("?")[1]
        self.pref.set("tray_icon", "type", "gtk")
        self.pref.set("tray_icon", "value", str(gtk_name))

        self.update_page(".tray-uuid", "removeClass", "selected")
        self.update_page(".tray_icon", "prop", "checked", "false")
        self.update_page("#tray-gtk-icon", "prop", "checked", "true")

        self.update_page("input.invalid", "removeClass", "invalid")
        self.update_page("label.invalid", "fadeOut", fade_speed)

        icon_path = common.get_path_from_gtk_icon_name(gtk_name)
        self.update_page(".gtk-preview", "attr", "src", "file://" + icon_path)

        self.update_page("input", "removeClass", "invalid")
        if not os.path.exists(icon_path):
            self.update_page("#tray-icon-gtk", "addClass", "invalid")
            self.update_page("#tray-icon-gtk-invalid", "fadeIn", fade_speed)
        else:
            self.update_page("#tray-icon-gtk", "removeClass", "invalid")
            self.update_page("#tray-icon-gtk-invalid", "fadeOut", fade_speed)
            self.dbg.stdout("Using GTK icon file: " + icon_path, self.dbg.success, 1)
            common.restart_tray_applet(self.dbg, self.path)
        return True

    elif cmd.startswith("select-tray-icon-custom?"):
        """
        Sets the tray icon preference to a custom path.
        It will also validate that the specified path exists.

        Expects:    ?<path>
        """
        path = cmd.split("?")[1]
        self.pref.set("tray_icon", "type", "custom")
        self.pref.set("tray_icon", "value", str(path))

        self.update_page(".tray-uuid", "removeClass", "selected")
        self.update_page(".tray_icon", "prop", "checked", "false")
        self.update_page("#tray-custom-icon", "prop", "checked", "true")
        self.update_page(".gtk-preview", "attr", "src", "file://" + path)

        self.update_page("input.invalid", "removeClass", "invalid")
        self.update_page("label.invalid", "fadeOut", fade_speed)

        if not os.path.exists(path):
            self.update_page("#tray-icon-path", "addClass", "invalid")
            self.update_page("#tray-icon-path-invalid", "fadeIn", fade_speed)
        else:
            self.update_page("#tray-icon-path", "removeClass", "invalid")
            self.update_page("#tray-icon-path-invalid", "fadeOut", fade_speed)
            common.restart_tray_applet(self.dbg, self.path)
        return True

    elif cmd == "restart-tray":
        """
        Restarts the tray applet to re-apply any new settings.
        """
        common.restart_tray_applet(self.dbg, self.path)
        return True

    ## Managing colours
    elif cmd == "pref-colour-new":
        """
        Creates a new colour in index for editing.
        """
        colour_index = self.pref.load_file(self.path.colours)
        uuid = self.pref.generate_uuid()
        colour_index[uuid] = {}
        colour_index[uuid]["name"] = _("New Color")
        colour_index[uuid]["col"] = [0, 255, 0]
        self.pref.save_file(self.path.colours, colour_index)
        _populate_colours_table(self)
        self.process_command("pref-colour-edit?" + uuid)
        return True

    elif cmd.startswith("pref-colour-edit"):
        """
        Sets the UI for editing a colour.

        Expects:    ?colour_id
        Where:
            colour_id   UUID from index
        """
        uuid = cmd.split("?")[1]
        colour_index = self.pref.load_file(self.path.colours)

        try:
            name = colour_index[uuid]["name"]
            col = colour_index[uuid]["col"]
            red = col[0]
            green = col[1]
            blue = col[2]
        except:
            name = _("Unknown Color")
            red = 0
            green = 255
            blue = 0

        self.update_page(".colour-table-item", "removeClass", "active")
        self.update_page("#colour-item-" + uuid, "addClass", "active")
        self.update_page("#colour-right", "fadeIn", "fast")
        self.update_page("#colour-edit-preview", "css", "background-color", "rgba({0},{1},{2},1)".format(red, green, blue))
        self.update_page("#colour-edit-name", "val", name)
        self.update_page("#colour-save", "attr", "onclick", "cmd('pref-colour-save?{0}?' + $('#colour-edit-name').val() + '?' + $('#colour-edit-preview').css('background-color'))".format(uuid))
        self.update_page("#colour-delete", "attr", "onclick", "cmd('pref-colour-del?{0}')".format(uuid))
        return True

    elif cmd.startswith("pref-colour-save"):
        """
        Takes the values and sets the new colour in the index.
            colour_id   = UUID from index
            name        = Name to describe to this colour
            rgba        = background-color string (rgba)
        """
        cmd = cmd.split("?")
        uuid = cmd[1]
        name = cmd[2]
        rgb = cmd[3].split("(")[1].split(")")[0].split(",")
        red = int(rgb[0])
        green = int(rgb[1])
        blue = int(rgb[2])
        self.update_page("#colour-right", "fadeOut", "fast")
        _populate_colours_table(self)

        self.dbg.stdout("Saving colour '{1}' (id: {0}) with RGB {2}, {3}, {4} ...".format(uuid, name, red, green, blue), self.dbg.action, 1)
        try:
            colour_index = self.pref.load_file(self.path.colours)
            colour_index[uuid] = {}
            colour_index[uuid]["name"] = name
            colour_index[uuid]["col"] = [red, green, blue]
            self.pref.save_file(self.path.colours, colour_index)
            self.update_page("#colour-right", "fadeOut", "fast")
            _populate_colours_table(self)
        except Exception as e:
            print("Saving colour failed! Exception: " + str(e))
        return True

    elif cmd.startswith("pref-colour-del"):
        """
        Expects these parameters separated by '?' in order:
            colour_id   = UUID from index
        """
        uuid = cmd.split("?")[1]
        self.dbg.stdout("Deleting colour ID: {0} ...".format(uuid), self.dbg.action, 1)
        try:
            colour_index = self.pref.load_file(self.path.colours)
            colour_index.pop(uuid)
            self.pref.save_file(self.path.colours, colour_index)
            self.update_page("#colour-right", "fadeOut", "fast")
            _populate_colours_table(self)
        except Exception as e:
            print("Deleting colour failed! Exception: " + str(e))
        return True

    elif cmd == "pref-colour-reset":
        self.dbg.stdout("Resetting colour configuration...", self.dbg.action, 1)
        self.pref.reset_config(self.path.colours)
        _populate_colours_table(self)
        self.update_page("#colour-right", "fadeOut", "fast")
        return True

    return False


# Tab Contents
def _print_about_tab(self):
    """
    About - displays details about the app itself.
    """
    # Data values
    version = self.controller.version
    pref_version = self.pref.version
    distro = linux_distribution()[0]
    dev_build = False
    auto_updates = False

    # For Apt, check for the source file to determine builds.
    if distro == "Ubuntu" or distro == "Debian":
        codename = linux_distribution()[2]

        source_file = "/etc/apt/sources.list.d/lah7-ubuntu-polychromatic-" + codename + ".list"
        if os.path.exists(source_file) and os.path.getsize(source_file) > 0:
            auto_updates = True

        source_file = "/etc/apt/sources.list.d/lah7-ubuntu-polychromatic-daily-" + codename + ".list"
        if os.path.exists(source_file) and os.path.getsize(source_file) > 0:
            auto_updates = True
            dev_build = True

    if version.endswith("-dev"):
        auto_updates = False
        dev_build = True

    # Frontend
    html = "<img class='about-logo' src='../img/logo/polychromatic.svg'/> <h1 id='about-text'>polychromatic</h1>"
    html += self.ui.print_about_label(_("Version:"), "v" + version)
    html += self.ui.print_about_label(_("Configuration:"), "v" + str(pref_version))
    html += self.ui.print_link("https://polychromatic.github.io", "https://polychromatic.github.io")
    html += self.ui.print_page_break()

    if auto_updates and not dev_build:
        html += "<div class='about-update-status'><span class='fa fa-check-circle'></span> {0}</div>".format(
            _("You are set for automatic updates (via PPA)"))

    if auto_updates and dev_build:
        html += "<div class='about-update-status'><span class='fa fa-check-circle'></span> {0}</div>".format(
            _("You have opted for development packages."))

    if not auto_updates:
        html += self.ui.print_button(_("Check for Updates"), "update-button", "update-check")

    html += self.ui.print_button(_("View Change Log"), "changelog-button", "fetch-changelog")
    html += self.ui.print_loading_text("loading-changelog", _("Retrieving data..."))
    html += self.ui.print_page_break()

    html += "<div id='social-links'>"
    html += self.ui.print_link("<span class='fa fa-github-square'></span> " + _("View on GitHub"), "https://github.com/polychromatic")
    html += self.ui.print_link("<span class='fa fa-facebook-square'></span> " + _("Like on Facebook"), "https://facebook.com/p0lychromatic")
    html += self.ui.print_link("<span class='fa fa-twitter-square'></span> " + _("Follow on Twitter"), "https://twitter.com/p0lychromatic")
    html += "</div>"

    return html


def _print_general_tab(self):
    """
    General - options for UI settings
    """
    # Profile Editor
    html = self.ui.print_control_category(_("Profiles"))
    html += self.ui.print_checkbox(_("Enable live switching"), "live_switch", "editor", "live_switch", False, _("Activate profiles instantly as soon as you click on them."))
    html += self.ui.print_checkbox(_("Enable live preview"), "live_preview", "editor", "live_preview", False, _("While editing, show changes on the actual device."))

    # General UI
    html += self.ui.print_control_category(_("Interface"))
    html += self.ui.print_checkbox(_("Enable 2x scaling"), "scale2x", "editor", "scale2x", False, _("For compatiblity with HIDPI screens on some desktop environments. Requires restart."))

    # Advanced
    html += self.ui.print_control_category(_("Advanced"))
    html += self.ui.print_button("Open Configuration Folder", "open-config", "open-config-folder", "fa-folder")

    reset_all_dialog_uuid = self.ui.JavaScript.generate_confirmation_dialog(
        self.update_page,
        _("Reset Everything"),
        _("This will erase all your preferences, profiles and settings. This cannot be undone.") + '<br><br>' + \
        _("The application will restart."),
        _("Reset Polychromatic"), "cmd(\'pref-reset-all\')",
        _("Cancel"), None,
        "serious", "50vw", "25vh")
    html += self.ui.print_button(_("Reset Everything"), "reset-everything", "dialog_open('{0}')".format(reset_all_dialog_uuid), None, False, "serious", True)

    return html


def _print_tray_tab(self):
    """
    Tray Applet - customise the icon
    """
    # Get data, or if it's the first time, set default icon based on desktop environment.
    if not self.pref.exists("tray_icon", "type"):
        common.set_default_tray_icon(self.pref)

    icon_type = self.pref.get("tray_icon", "type", "builtin")
    icon_value = self.pref.get("tray_icon", "value", "0")

    # Preview Area
    html = self.ui.print_control_category(_("Preview"))
    icon_path = common.get_tray_icon(self.dbg, self.pref, self.path)
    bg_colours = common.get_tray_icon_preview_bg_colours()
    html += "<div class='gtk-preview-panel' style='background-color:{1}'><img class='gtk-preview' src='{0}'/></div>".format(icon_path, bg_colours[0])
    html += "<div class='gtk-preview-panel' style='background-color:{1}'><img class='gtk-preview' src='{0}'/></div>".format(icon_path, bg_colours[1])

    html += self.ui.print_control_category(_("Customise Icon"))
    # => Built-in Icons
    html += self.ui.print_radio(_("Built-in Icon"), "tray-builtin-icon", "tray_icon", "type", "builtin", False, None,
                                    "cmd('select-tray-icon-uuid?0');" \
                                    "$('.tray-uuid').removeClass('selected');" \
                                    "$('#tray-uuid-0').addClass('selected');")

    html += "<div id='tray-builtin-suboptions' class='tray-suboptions'>"
    html += "<div id='tray-icon-previews'>"
    def add_icon(uuid):
        icon_name = icon_index[uuid]["name"]
        icon_path = os.path.join(self.path.data_source, "tray", icon_index[uuid]["path"])
        icon_info = icon_index[uuid]["info"]
        onclick_cmd = "cmd('select-tray-icon-uuid?{0}'); $('.tray-uuid').removeClass('selected'); $('#tray-uuid-{0}').addClass('selected');".format(uuid)
        return "<button id='tray-uuid-{0}' class='tray-uuid btn {3}' onclick=\"{1}\"><img src='{2}'/></button>".format(
            uuid,
            onclick_cmd,
            icon_path,
            "selected" if uuid == icon_value else "")

    icon_index = self.pref.load_file(os.path.join(self.path.data_source, "tray/icons.json"))
    icons = sorted(list(icon_index.keys()))
    for uuid in icons:
        html += add_icon(uuid)
    html += "</div><br/>"
    html += "</div>"

    # => GTK Name
    html += self.ui.print_radio(_("GTK Icon"), "tray-gtk-icon", "tray_icon", "type", "gtk", False, _("Use an icon provided by a GTK theme."),
                                    "cmd('select-tray-icon-gtk?' + $('#tray-icon-gtk').val());")
    html += "<div id='tray-gtk-suboptions' class='tray-suboptions'>"
    html += "<input id='tray-icon-gtk' class='pref-input' type='text' value='{0}'/>".format(icon_value if icon_type == "gtk" else "")
    html += "<button id='tray-icon-gtk-ok' class='btn' onclick='cmd(\"select-tray-icon-gtk?\" + $(\"#tray-icon-gtk\").val());'><span class='fa fa-check'></span></button>"
    html += "<br>"
    html += self.ui.print_invalid_label("tray-icon-gtk-invalid", _("This does not appear to be a valid GTK icon."))
    html += self.ui._get_helptext_html(_("Examples: ibus-keyboard, gnome-desktop-config"))
    html += "</div><br/>"

    # => Custom Path
    html += self.ui.print_radio(_("Custom Path"), "tray-custom-icon", "tray_icon", "type", "custom", False, None,
                                    "cmd('select-tray-icon-custom?' + $('#tray-icon-path').val());")
    html += "<div id='tray-custom-suboptions' class='tray-suboptions'>"
    html += "<input id='tray-icon-path' class='pref-input' type='text' value='{0}'/>".format(icon_value if icon_type == "custom" else "")
    html += "<button class='btn' onclick='cmd(\"browse?1?tray-icon-path\");'><span class='fa fa-folder-open'></span> {0}</button>".format(_("Browse"))
    html += "<button id='tray-icon-path-ok' class='btn' onclick='cmd(\"select-tray-icon-custom?\" + $(\"#tray-icon-path\").val());'><span class='fa fa-check'></span></button>"
    html += self.ui.print_invalid_label("tray-icon-path-invalid", _("File not found."))
    html += "</div>"

    return html


def _print_colours_tab(self):
    """
    Colours - set up a list of colours
    """
    html = self.ui.print_control_category(_("Colours"))
    html += "<div id='colour-left'>"
    html += "<div id='colour-table'>{0}</div>".format(_populate_colours_table(self, True))
    html += "<br>"
    html += self.ui.print_button(_("New"), "colour-new", "pref-colour-new", "fa-plus", False)
    reset_colour_dialog_uuid = self.ui.JavaScript.generate_confirmation_dialog(
        self.controller.update_page,
        _("Reset Colors"),
        _("Are you sure you want to reset all the colors to their defaults?"),
        _("Restore Defaults"), "cmd(\'pref-colour-reset\')",
        _("Cancel"), None,
        "serious", "50vw", "20vh")
    html += self.ui.print_button(_("Restore Defaults"), "colour-reset", "dialog_open('" + reset_colour_dialog_uuid + "');", "fa-repeat", False, "btn-dim serious", True)
    html += "<br><br>"
    html += "</div>"

    html += "<div id='colour-right' style='display:none'>"
    html += "<div id='colour-edit-preview' class='colour-preview' style='background-color:rgb(0,255,0)'></div>"
    html += self.ui.print_button(_("Choose..."), "colour-edit", "colour-pick?colour-edit", None, False)
    html += "<input id='colour-edit-name' class='pref-input' type='text'/>"
    html += self.ui.print_button(_("Save"), "colour-save", "", "fa-check", False)
    html += self.ui.print_button(_("Delete"), "colour-delete", "", "fa-trash", False, "serious")
    html += "</div>"

    return html


def _print_daemon_tab(self):
    """
    Daemon - see status info for OpenRazer
    """
    html = "<img class='about-logo' src='../img/logo/openrazer.svg'/> <h1 id='about-text'>OpenRazer</h1>"
    html += self.ui.print_about_label(_("The daemon is the software that communicates between the front-end applications and the driver."), "")
    html += self.ui.print_about_label(_("Daemon Version:"), str(self.controller.devman.version))
    html += self.ui.print_about_label(_("Razer Python Library:"), str(self.controller.devman.daemon_version))
    #~ html += self.ui.print_about_label(_("Supported Devices:"), str(len(self.controller.devman.supported_devices)))

    html += self.ui.print_page_break()

    html += self.ui.print_button(_("Website"), "daemon-website", "open?https://openrazer.github.io/", "fa-globe")
    html += self.ui.print_button(_("Project"), "daemon-project", "open?https://github.com/openrazer/openrazer", "fa-github")
    html += self.ui.print_page_break()
    html += self.ui.print_button(_("Issues"), "daemon-issues", "open?https://github.com/openrazer/openrazer/issues", "fa-question-circle")
    html += self.ui.print_button(_("Troubleshooting"), "daemon-troubleshoot", "open?https://github.com/openrazer/openrazer/wiki/Troubleshooting", None)
    html += self.ui.print_button(_("Device/Daemon Support"), "daemon-support", "open?https://github.com/openrazer/openrazer#device-support", None)

    html += self.ui.print_page_break()
    html += self.ui.print_control_category(_("Logs"))
    html += self.ui.print_about_label(_("Useful for diagnosing issues and debugging daemon-related operations."), "")
    html += self.ui.print_button('<code>~/.config/openrazer/</code>', "config-folder", "run?xdg-open /home/$USER/.config/openrazer/", "fa-folder-open")
    html += self.ui.print_button('<code>~/.local/share/openrazer/</code>', "config-local", "run?xdg-open /home/$USER/.local/share/openrazer/", "fa-folder-open")
    html += self.ui.print_page_break()
    html += self.ui.print_button('<code>~/.local/share/openrazer/logs/razer.log</code>', "log-open", "run?xdg-open /home/$USER/.local/share/openrazer/logs/razer.log", "fa-file-text-o")
    html += self.ui.print_button(_("Watch"), "log-watch", "run?x-terminal-emulator -e tail -f /home/$USER/.local/share/openrazer/logs/razer.log", "fa-search")

    html += self.ui.print_page_break()
    html += self.ui.print_control_category(_("Daemon Service"))
    html += self.ui.print_about_label(_("If you have re-plugged devices, or are experiencing glitches, try restarting the daemon service."), "")
    html += self.ui.print_button(_("Restart"), "restart-daemon", "restart-daemon")

    html += self.ui.print_page_break()
    return html


# Re-used Functions
def _populate_colours_table(self, get_html_only=False):
    self.update_page("#colour-table", "html", " ")
    colour_index = self.pref.load_file(self.path.colours)
    uuids = list(colour_index.keys())
    uuids.sort(key=int)

    html_buffer = ""
    for uuid in uuids:
        try:
            name = colour_index[uuid]["name"]
            red = colour_index[uuid]["col"][0]
            green = colour_index[uuid]["col"][1]
            blue = colour_index[uuid]["col"][2]
            rgba = "rgba({0},{1},{2},1)".format(red, green, blue)

            html_buffer += "<a onclick='cmd(\"pref-colour-edit?{0}\")'>".format(uuid)
            html_buffer += "<div id='colour-item-{0}' class='colour-table-item'>".format(uuid)
            html_buffer += "<div class='preview' style='background-color:rgba({0},{1},{2},1)'></div>".format(red, green, blue)
            html_buffer += "<label class='name'>{0}</label>".format(name)
            html_buffer += "<label class='value'>{0}, {1}, {2}</label>".format(red, green, blue)
            html_buffer += "</div></a>"

        except Exception:
            self.dbg.stdout("Invalid colour entry: {0}".format(uuid), self.dbg.action, 0)
            continue

    if get_html_only:
        return html_buffer
    else:
        self.update_page("#colour-table", "html", html_buffer)
