# Polychromatic

A graphical front end to manage your Razer perihperals on GNU/Linux.

Powered by the [Chroma Linux Drivers](http://pez2001.github.io/razer_chroma_drivers/) daemon.


## Features

### Controller

![Screenshot of Controller](source/screenshots/controller.jpg)

An application that allows you to configure your Razer peripheral.

(Currently designed for one device at a time, but [this will change eventually](https://github.com/lah7/polychromatic/issues/3)).

Also includes application profile support and customisation options:

* Changing the indicator icon.
* Specifying preferred colours.
* Setting effects or profiles at log-in.
 * _Currently requires Tray Applet to run on start-up._


### Tray Applet

![Screenshot of Tray Applet](source/screenshots/tray.jpg)

Quickly set effects, brightness, keyboard features or load saved profiles
from your desktop indicators / notification area.


## Installation

### Razer Chroma Drivers
This application complements the [razer-chroma-drivers](http://pez2001.github.io/razer_chroma_drivers/) project, which currently need to be compiled, built and installed first.

Ubuntu and Debian users can use these pre-compiled packages for convenience:

 * [razer-chroma-driver_20160612_ubuntu_amd64.deb](https://github.com/lah7/polychromatic/releases/download/v0.2.0/razer-chroma-driver_20160612_ubuntu_amd64.deb)
 * [razer-chroma-driver_20160612_debian_amd64.deb](https://github.com/lah7/polychromatic/releases/download/v0.2.0/razer-chroma-driver_20160612_debian_amd64.deb)

These packages are provided **as-is**!

### Packages

#### Ubuntu / Linux Mint

Polychromatic can be installed from this PPA, which also keeps the application up-to-date.

    sudo add-apt-repository ppa:lah7/polychromatic
    sudo apt update
    sudo apt install polychromatic

* **razer-chroma-drivers** must be installed first.
* **Optionally**, you may wish to add the `polychromatic-tray-applet` program to your start-up programs.


#### Ubuntu 14.04, 15.10, Linux Mint 17 (and earlier)

Polychromatic depends on a newer version of WebKit2 which is not available in earlier releases.

Instead, [the legacy branch](https://github.com/lah7/polychromatic/tree/legacy) contains
a much earlier version (v0.1.0 / v0.2.0.1) and will not receive any further updates.


#### Debian

Add this line to your `/etc/apt/sources.list`:

    deb http://ppa.launchpad.net/lah7/polychromatic/ubuntu trusty main

Then add the public key to verify the packages:

    gpg --keyserver hkp://keyserver.ubuntu.com:11371 --recv-keys A4BFC960
    gpg --armor --export A4BFC960 | sudo apt-key add -

Followed by updating your Apt sources:

    sudo apt-get update

The packages are built against Ubuntu, but the [the legacy branch](https://github.com/lah7/polychromatic/tree/legacy)
is compatible with Debian 8.

Otherwise, standalone packages are available from the [releases page](https://github.com/lah7/polychromatic/releases/latest/).


### Manual Installation / Other Distributions

See further below for which dependencies you will require to install first.

    git clone https://github.com/lah7/polychromatic.git
    cd polychromatic
    git checkout stable
    sudo ./install/install.sh

**If you'd like to use the latest development version** (but potentially unstable), skip this line: `git checkout stable`.

To update your installation at a later date:

    ./install/update.sh


### Dependencies

**All:**
* [Razer Python Modules](https://github.com/pez2001/razer_chroma_drivers)

**Arch:**
* [webkitgtk](https://www.archlinux.org/packages/extra/x86_64/webkitgtk/)
* [python-gobject](https://www.archlinux.org/packages/extra/x86_64/python-gobject/)
* [python-setproctitle](https://www.archlinux.org/packages/community/x86_64/python-setproctitle/)
* [libappindicator](https://aur.archlinux.org/pkgbase/libappindicator/?comments=all)

**Debian and Ubuntu 16.04+:**
* [gir1.2-webkit2-4.0](https://packages.debian.org/sid/gir1.2-webkit2-4.0)
* [python3-gi](https://packages.debian.org/sid/python3-gi)
* [python3-setproctitle](https://packages.debian.org/sid/python3-setproctitle)
* [gir1.2-appindicator3-0.1](https://packages.debian.org/sid/gir1.2-appindicator3-0.1)


### Translations
If you'd like to translate this application into other languages, take a look
[at this wiki page](https://github.com/lah7/polychromatic/wiki/How-to-translate-the-application.).

