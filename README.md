![Polychromatic](.readme/logo.png)

A front-end for customising the functionality of your Razer perpherials under GNU/Linux.

## Features

### Controller
| Screenshot | Features |
| ---------- | -------- |
| ![controller-kbd-options](https://cloud.githubusercontent.com/assets/13032135/20988307/1d61f118-bcc8-11e6-8455-66473f62ab25.png) | <ul><li>Set effects, brightness, colours and modes supported by the device.</li><li>Create application profiles.</li><li>Specify preferences - such as default colours.</li><li>View all connected devices and configure the daemon-specific settings.</li></ul>
|

### Tray Applet
| Screenshot | Features |
| ---------- | -------- |
| ![tray](https://cloud.githubusercontent.com/assets/13032135/20988404/85d08462-bcc8-11e6-8e9c-be3eaf976df1.jpg) | <ul><li>Quickly set supported effects, brightness and modes.</li><li>Change colours and application profiles on-the-fly.</li><li>Apply settings automatically when you log-in</li></ul>
|

[View all screenshots](.readme/Screenshots.md)

------------

## Device Support

See the [daemon's device support table](https://github.com/terrycain/razer-drivers#device-support) to check whether your device is supported by the daemon. Once it works with the daemon, it's likely to work in Polychromatic too.

However, not all newly supported devices will work straight away. These devices have known issues:

| Keyboard | Mouse | Mousemat | Keypad | Headset |
|   :---:  | :---: |   :---:  | :---:  | :---:   |
| ![Keyboard](.readme/status/keyboard-ok.png) | ![Mouse](.readme/status/mouse-warn.png) | ![Mousemat](.readme/status/mousemat-ok.png) | ![Keypad](.readme/status/keypad-warn.png) | ![Headset](.readme/status/headset-warn.png)

#### Known Issues
* **Mice**
  * No support for setting the `scroll_wheel` or `logo`. These devices cannot be configured yet:
    * [DeathAdder Chroma](https://github.com/lah7/polychromatic/issues/41)
    * [Razer Naga](https://github.com/terrycain/razer-drivers/issues/106)
  * No option for reading/setting DPI for supported mice.
* **Keypad**
  * Profile support is not possible as the daemon does not support the matrix yet (like keyboards do).
  * Header may appear garbled.
* **Headset**
  * Header may appear garbled.

When the daemon supports new devices, they may or may not work. Stay tuned for updates!

-------------

## Driver Installation

### ![Chroma Drivers](.readme/chroma-drivers.png) Razer Drivers for Linux
This application is powered by the [razer-drivers](http://terrycain.github.io/razer-drivers/) driver and daemon.

Ubuntu and Linux Mint users can install the drivers and daemon via this PPA:

    sudo add-apt-repository ppa:terrz/razerutils
    sudo apt update
    sudo apt install python3-razer razer-kernel-modules-dkms razer-daemon razer-doc

Please see the [project page](http://terrycain.github.io/razer-drivers/#download) for installation for your distribution.


## Polychromatic Installation

#### ![Ubuntu](.readme/ubuntu.png) Ubuntu 16.04+ / Linux Mint 18+

Polychromatic can be installed via this PPA:

    sudo add-apt-repository ppa:lah7/polychromatic
    sudo apt update
    sudo apt install polychromatic

The PPA is recommended as it keeps the application up-to-date.


#### ![Ubuntu](.readme/ubuntu.png) Ubuntu 14.04 / Linux Mint 17

Earlier distributions will not be able to use the latest version of this software as it
depends on a newer version of WebKit2 which is not available in earlier releases.

Instead, [the legacy branch](https://github.com/lah7/polychromatic/tree/legacy) contains
an older version (v0.1.0 / v0.2.0.1) that will not receive further updates as it requires
the original driver/daemon:

* [razer-chroma-driver_20160612_ubuntu_amd64.deb](https://github.com/lah7/polychromatic/releases/download/v0.2.0/razer-chroma-driver_20160612_ubuntu_amd64.deb)
* [polychromatic_0.1.0_all.deb](https://github.com/lah7/polychromatic/releases/download/v0.2.0/polychromatic_0.1.0_all.deb)


#### ![Debian](.readme/debian.png) Debian 8+

**WebKit2 Dependency**

 * Debian 8 "Jessie" provides an old version of `gir1.2-webkit2-4.0` which is incompatible with Polychromatic.
 * Please enable `jessie-backports` and update `gir1.2-webkit2-4.0` to at least v2.12.

Packages built for Ubuntu are also compatible with Debian.

Add this line to your `/etc/apt/sources.list`:

    deb http://ppa.launchpad.net/lah7/polychromatic/ubuntu trusty main

Then add the public key to verify the packages:

    gpg --keyserver hkp://keyserver.ubuntu.com:11371 --recv-keys A4BFC960
    gpg --armor --export A4BFC960 | sudo apt-key add -

Followed by updating your Apt sources:

    sudo apt-get update

Otherwise, standalone packages are available from the [releases page](https://github.com/lah7/polychromatic/releases/latest/), or
by following a manual installation below.


#### ![Arch](.readme/arch.png) Arch Linux

Packages for Arch are maintained by [z3ntu](https://github.com/z3ntu). You can install using an AUR wrapper, like as follows:

    yaourt -S polychromatic
    pacaur -S polychromatic

There are two packages:

* [`polychromatic`](https://aur.archlinux.org/packages/polychromatic/) - Latest stable version.
* [`polychromatic-git`](https://aur.archlinux.org/packages/polychromatic-git/) - Latest development version.


#### ![Other Distributions](.readme/linux.png) Other Distributions / Manual Installation

See further below for which dependencies you will require to install first.

    git clone https://github.com/lah7/polychromatic.git
    cd polychromatic
    git checkout stable
    sudo ./install/install.sh

**If you'd like to use the latest development version** (but potentially unstable), skip this line: `git checkout stable`.

You can update your installation by clicking "Check for Updates" in the preferences, or by running:

    ./install/update.sh


### Dependencies

**All:**
* [python3-razer](https://github.com/terrycain/razer-drivers)
* [razer-daemon](https://github.com/terrycain/razer-drivers)

**Arch:**
* [webkitgtk](https://www.archlinux.org/packages/extra/x86_64/webkitgtk/)
* [python-gobject](https://www.archlinux.org/packages/extra/x86_64/python-gobject/)
* [python-setproctitle](https://www.archlinux.org/packages/community/x86_64/python-setproctitle/)
* [python-requests](https://www.archlinux.org/packages/extra/any/python-requests/)
* [libappindicator](https://aur.archlinux.org/pkgbase/libappindicator/?comments=all)

**Debian and Ubuntu 16.04+:**
* [gir1.2-webkit2-4.0](https://packages.debian.org/sid/gir1.2-webkit2-4.0) (>= 2.12.0)
* [python3-gi](https://packages.debian.org/sid/python3-gi)
* [python3-setproctitle](https://packages.debian.org/sid/python3-setproctitle)
* [python3-requests](https://packages.debian.org/sid/python3-requests)
* [gir1.2-appindicator3-0.1](https://packages.debian.org/sid/gir1.2-appindicator3-0.1)


## Something not working?

* Check that the driver and daemon are [properly installed](https://github.com/terrycain/razer-drivers#installation) for your distribution.
* Check that your [device has daemon support](https://github.com/terrycain/razer-drivers#device-support).
* For DBUS, daemon or driver bugs, [see if an issue](https://github.com/terrycain/razer-drivers/issues) has been raised on the [razer-drivers repository](https://github.com/terrycain/razer-drivers), otherwise [please create a new issue there](https://github.com/terrycain/razer-drivers/issues/new).

For visual or functional problems with Polychromatic, [please raise an issue here instead](https://github.com/lah7/polychromatic/issues/new).


## Translations

If you'd like to translate this application, take a look
[at this wiki page](https://github.com/lah7/polychromatic/wiki/How-to-translate-the-application).

