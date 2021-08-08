polychromatic-helper(1)

# NAME

Polychromatic - RGB lighting management software for GNU/Linux

# SYNOPSIS

*polychromatic-helper* [OPTIONS]

# DESCRIPTION

This is the "helper" runtime for handling background tasks, like autostart
behaviours and running of custom effects.

This software does not contain driver code to directly control hardware by
itself. In this version, only OpenRazer is supported.

The user is not expected to interact with this executable.

# OPTIONS

*-v*, *--verbose*
	Prints more details about the application's operation.

*--version*
	Prints version information:
		- Software version
		- Commit hash (when run from the repository directory)
		- Python version

*--autostart*
	To be run when the user logs into the desktop environment.
		- If enabled, start the tray applet.

_--monitor-triggers_
	Unused in this version.

*--run-fx* <PATH>
	Runs a Polychromatic effect stored in JSON format.
	Requires the *-n* or *-s* parameters below to specify the device.

*-n* <DEVICE_NAME>
	Select the desired device name (full string)
	For example, "Razer BlackWidow Chroma"

*-s* <DEVICE_SERIAL>
	Select the desired device by its serial string.
