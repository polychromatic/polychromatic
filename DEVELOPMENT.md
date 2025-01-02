# Polychromatic Development

## Dependencies

Polychromatic is a Python application. You should install these using your
distro's package manager. Running from a virtual environment is not
practiced for this project.

| Library           | Purpose                                                |
| ----------------- | ------------------------------------------------------ |
| `colorama`        | Colour output in the terminal
| `colour`          | Manipulating colours
| `requests`        | For making HTTP requests online
| `setproctitle`    | Sets the process name
| PyQt6*            | GUI toolkit for `polychromatic-controller`
| PyQt6 SVG         | SVG support for Qt 6
| PyQt6 WebEngine   | Renders the effect editor
| GTK 3 AppIndicator| Tray applet support

_*_ PyQt6 needs to support loading *.ui files via `uic`.
Some distros have this as part of `pyqt6` but others (such as Debian/Ubuntu)
provide this in a separate `pyqt6-dev-tools` package.

**In addition, to build and run directly from the repository:**

| Library           | Purpose                                                |
| ----------------- | ------------------------------------------------------ |
| `ninja`           | Build system
| `meson`           | Build system
| `intltool`        | Compiling translations
| `git`             | Version control


## Running the application

Assuming all your [dependencies](#dependencies) are installed,
the application is ready to be run directly from the repository.

Use `polychromatic-controller-dev` to isolate your configuration and cache
into a `savedatadev` directory. To isolate the tray applet and
command line interfaces, set this environment variable:

    export POLYCHROMATIC_DEV_CFG=true

Then run the desired application:

    ./polychromatic-controller-dev
    ./polychromatic-tray-applet
    ./polychromatic-cli

While most of the project isn't compiled like conventional software, there are
a couple of pieces that do require assembly:

    ./scripts/build-locales.sh
    ./scripts/build-man-pages.sh


## Building

If you have custom installation requirements or packaging for another distro,
Polychromatic can be put together using [Meson] and [Ninja].

```
git clone https://github.com/polychromatic/polychromatic.git
cd polychromatic
meson setup build
ninja -C build install
```

[Meson]: https://mesonbuild.com/
[Ninja]: https://ninja-build.org/
