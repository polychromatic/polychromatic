polychromatic-cli(1)

# NAME

Polychromatic - RGB lighting management software for GNU/Linux

# SYNOPSIS

*polychromatic-cli* [OPTIONS]

# DESCRIPTION

This is the command line interface for configuring device options and retrieving
status information from connected hardware.

# OPTIONS

## DEVICE SELECTION

	Use the following arguments to select the devices to read/set changes to.
	Omitting these arguments selects all devices.

	*-d*, *--device* <ID>
		Select the device by form factor.

		- accessory
		- display
		- fan
		- gpu
		- headset
		- keyboard
		- keypad
		- laptop
		- mouse
		- mousemat
		- ram
		- speaker
		- stand

	*-n*, *--name* <NAME>
		Select a device by its full name, such as "Razer BlackWidow Chroma"

	*-s*, *--serial* <SERIAL>
		Select a device by its serial string.

## DEVICE INFORMATION

	*-l*, *--list-devices*
		List the selected device(s) and their zone(s)

	*-k*, *--list-options*
		List supported parameters and current settings in a table.

## DEVICE OPERATION

	*-z*, *--zone* <ID>
		Make a change to the specified zone. Some hardware have multiple
		lighting regions. When omitted, all zones will be selected.

	*-o*, *--option* <ID>
		Set an option on the device. For example, "static"

		Some options require a _--parameter_ and/or _--colour_, see below.

	*-p*, *--parameter* <ID>
		Set a parameter for the specified option if applicable. For example,
		for a wave effect, use "right" or its numerical value (1).

		Numerical values are useful when setting multiple devices simultaneously
		that do not share the same ID, such as a mouse's wave is "up" (1) or
		"down" (2) instead of "right" (1) and "left" (2).

	*-c*, *--colours* <#RRGGBB>[,#RRGGBB...]
		Set a colour for the specified option if applicable.

		The input only accepts 6 byte hexadecimal values, such as #00FF00.
		The hash must be escaped or wrapped in quotes to avoid being interpreted
		as a comment by your shell. Alternately, the hash can be omitted.

		Multiple colours may be specified using a comma.

	*-e*, *--effect* <NAME/PATH>
		Plays a custom software effect by its name or an absolute path to
		the file.

		Not to be confused with an _--option_ for hardware effects, see above.

	*--dpi* <X>[,Y]
		Sets the DPI (dots per inch) of a mouse. The axis can be set
		independently, otherwise the same value will be used for both X/Y.

		DPI is responsible for the speed of the mouse cursor.

# MISCELLANEOUS

	*-h*, *--help*
		Shows the help information.

	*-v*, *--verbose*
		Prints more details about the application's operation.

	*--version*
		Prints version information:
			- Software version
			- Commit hash (when run from the repository directory)
			- Python version

	*--no-pretty-column*
		Disables the pretty column function of the program. This may be required
		for compatibility with specific terminals and consoles.

	*--locale [lang]*
		Force the application to display in a specific locale.
		For example, "fr_FR" or "nl".
