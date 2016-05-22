# Polychromatic

A graphical front end for managing the [Chroma Linux Drivers](http://pez2001.github.io/razer_chroma_drivers/) for Razer peripherals on GNU/Linux.


## Features

### Controller

![Screenshot of Controller](source/screenshots/controller.jpg)

A central place to change the behaviour of your Razer peripheral: Effects, brightness, toggling gaming mode or activating macro keys.

Also includes profile support and customisation options:

* Changing the indicator icon.
* Specifying preferred colours.
* Setting effects or profiles at log-in.
 * _Currently requires Tray Applet to run on start-up._


### Tray Applet

![Screenshot of Tray Applet](source/screenshots/tray.jpg)

Set effects, brightness, game mode and macro features, plus load your saved profiles from the tray.


## Installation
The GUI utilites have been recently been split from the [main razer-chroma-drivers repository](http://pez2001.github.io/razer_chroma_drivers/) and is undergoing new developments.

### [v0.1.0](https://github.com/lah7/polychromatic/releases/tag/v0.1.0)
This version is the same as the original "Chroma" GUI utility and is stable for configuring one of the [supported Razer keyboards](http://pez2001.github.io/razer_chroma_drivers/#support).

* On Debian/Ubuntu, [download deb package](https://github.com/lah7/polychromatic/releases/download/v0.1.0/polychromatic-v0.1.0-ubuntu.deb).
* For other distributions, [download a copy of the source code](https://github.com/lah7/polychromatic/archive/v0.1.0.tar.gz) and run `./install/install.sh`. See below for any dependencies you may need to install first.
* [See the release page for further details.](https://github.com/lah7/polychromatic/releases/tag/v0.1.0)


### Unstable
The `master` branch has the latest changes, but are considered **unstable**.

    git clone https://github.com/lah7/polychromatic.git
    cd polychromatic
    sudo ./install/install.sh

To update your clone:

    git pull --rebase
    sudo ./install/install.sh


### Dependencies

* [Razer Python Modules](https://github.com/pez2001/razer_chroma_drivers)
* gir1.2-webkit-3.0
* python3-gi
* gir1.2-appindicator3-0.1

