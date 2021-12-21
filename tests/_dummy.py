from pylib.backends._backend import Backend as Backend

import os


class DummyMatrix(Backend.DeviceItem.Matrix):
    """
    A simulated matrix that does absolutely nothing.
    """
    def __init__(self, *args):
        pass

    def set(self, x, y, r, g, b):
        pass

    def draw(self):
        pass

    def clear(self):
        pass


class DummyDPI(Backend.DeviceItem.DPI):
    """
    Simulate DPI tracked using a text file.
    """
    def __init__(self, serial):
        super().__init__()
        self.x = 800
        self.y = 1800
        self.min = 100
        self.max = 16000

        self.path = os.path.expanduser(f"~/.cache/polychromatic/test_dpi_{serial}")

        # Write initial DPI files
        dpi_dir = os.path.dirname(self.path)
        if not os.path.exists(dpi_dir):
            os.makedirs(dpi_dir)
        self.set(self.x, self.y)

    def refresh(self):
        with open(self.path, "r") as f:
            self.x = int(f.readline())
            self.y = int(f.readline())

    def set(self, x, y):
        with open(self.path, "w") as f:
            f.write(str(self.x) + "\n")
            f.write(str(self.y) + "\n")


class DummyBackend(Backend):
    """
    Simulates an imaginary backend with a few devices for testing logic.

    Refer to the docstrings for the specifications for each device. There are
    some 'unknown devices' too, for a scenario where the device is not supported,
    or not set up properly.
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.backend_id = "dummy"
        self.logo = "polychromatic.svg"
        self.version = "9.9.9"
        self.project_url = "https://polychromatic.app"
        self.bug_url = "https://github.com/polychromatic/polychromatic/issues"
        self.releases_url = "https://github.com/polychromatic/polychromatic/releases"
        self.license = "GPLv3"

    def init(self):
        return True

    def get_unsupported_devices(self):
        unknown_devices = []
        for i in range(0, 3):
            device = Backend.UnknownDeviceItem()
            device.name = "Unknown Device " + str(i)
            device.form_factor = self.get_form_factor()
            unknown_devices.append(device)
        return unknown_devices

    def _get_keyboard_device(self):
        """
        - 1 Zone
        - RGB Support
        - Implements every option type/combo:
            - None          EffectOption
            - Static        EffectOption with colour only
            - Wave          EffectOption with parameters only               <<<
        """
        device = Backend.DeviceItem()
        device.name = "Dummy Keyboard"
        device.form_factor = self.get_form_factor("keyboard")
        device.serial = "DUMMY0001"
        device.keyboard_layout = "en_GB"
        device.matrix = DummyMatrix()

        zone = Backend.DeviceItem.Zone()
        zone.zone_id = "main"
        zone.label = "Main Zone"
        device.zones.append(zone)

        class Nothing(Backend.EffectOption):
            def __init__(self):
                super().__init__()
                self.uid = "none"
                self.label = "None"

            def apply(self):
                pass

        class Static(Backend.EffectOption):
            def __init__(self):
                super().__init__()
                self.uid = "static"
                self.label = "Static"
                self.active = True
                self.colours_required = 1
                self.colours = ["#00FF00"]

            def apply(self):
                pass

        class Wave(Backend.EffectOption):
            def __init__(self):
                super().__init__()
                self.uid = "wave"
                self.label = "Wave"

                param_1 = Backend.EffectOption.Parameter()
                param_1.data = 1
                param_1.label = "Left"

                param_2 = Backend.EffectOption.Parameter()
                param_2.data = 2
                param_2.label = "Right"
                param_2.active = True

                self.parameters = [param_1, param_2]

            def apply(self, data):
                pass

        for option in [Nothing, Static, Wave]:
            zone.options.append(option())

        return device

    def _get_mouse_device(self):
        device = Backend.DeviceItem()
        device.name = "Dummy Mouse"
        device.form_factor = self.get_form_factor("mouse")
        device.serial = "DUMMY0002"
        device.dpi = DummyDPI(device.serial)
        return device

    def _get_headset_device(self):
        device = Backend.DeviceItem()
        device.name = "Dummy Headset"
        device.form_factor = self.get_form_factor("headset")
        device.serial = "DUMMY0003"
        return device

    def get_devices(self):
        return [
            self._get_keyboard_device(),
            self._get_mouse_device(),
            self._get_headset_device(),
        ]

    def get_device_by_name(self, name):
        names = {
            "Dummy Keyboard": self._get_keyboard_device,
            "Dummy Mouse": self._get_mouse_device,
            "Dummy Headset": self._get_headset_device,
        }
        return names[name]()

    def get_device_by_serial(self, serial):
        serials = {
            "DUMMY0001": self._get_keyboard_device,
            "DUMMY0002": self._get_mouse_device,
            "DUMMY0003": self._get_headset_device,
        }
        return serials[serial]()

    def troubleshoot(self):
        return None

    def restart(self):
        return True
