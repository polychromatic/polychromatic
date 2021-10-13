polychromatic-tray-applet(1)

# NAME

Polychromatic - RGB lighting management software for GNU/Linux

# SYNOPSIS

*polychromatic-tray-applet* [OPTIONS]

# DESCRIPTION

This is the tray applet interface for convenient access to device options
through an AppIndicator or GTK Status Icon.

# OPTIONS

*-h*, *--help*
	Shows the help information.

*-v*, *--verbose*
	Prints more details about the application's operation.

*--version*
	Prints version information:
		- Software version
		- Commit hash (when run from the repository directory)
		- Internal save data revision
		- Python version
		- GTK version

*--locale [lang]*
	Force the application to display in a specific locale.
	For example, "fr_FR" or "nl".

*--force-appindicator*
	Override the user's preferences and start the tray applet using the
	AppIndicator3 bindings.

*--force-ayatana*
	Override the user's preferences and start the tray applet using the
	Ayatana Indicator bindings. This is the default option and is widely compatible
	with most desktop environments.

*--force-gtk-status*
	Override the user's preferences and start the tray applet using the
	legacy GTK Status Icon. This is a deprecated GTK feature, but may work
	on distributions where application indicators are not supported.

# NOTES

	Some desktop enviroments (such as GNOME) have deprecated support for
	indicators and system tray. In this scenario, the user may need to install
	an additional package provided by their distribution that restores the
	functionality, or sacrifice this feature.

	It is observed that on some desktop environments and fast computers,
	a race condition prevents the indicator/applet from displaying as expected
	(including the wrong theme, or large icons). In this scenario, set a delay
	in _preferences.json_ by a few seconds.
