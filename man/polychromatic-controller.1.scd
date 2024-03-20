polychromatic-controller(1)

# NAME

Polychromatic - RGB lighting management software for GNU/Linux

# SYNOPSIS

*polychromatic-controller* [OPTIONS]

# DESCRIPTION

This is the main graphical user interface portion of Polychromatic, based on
PyQt6. All features of the software are accessible here.

# OPTIONS

*-h*, *--help*
	Shows the help information.

*-v*, *--verbose*
	Prints more details about the application's operation.

*--version*
	Prints version information:
		- Software version
		- Commit hash (when run from the repository directory)
		- Python version
		- Qt version

*--locale [lang]*
	Force the application to display in a specific locale.
	For example, "fr_FR" or "nl".

*--open [tab/dialog]*
	Opens the software to a specific a tab or dialog.

	_Tab_: devices, effects

	_Dialog_: preferences, troubleshoot, colours

	After a dialog is closed, the software will quit.
