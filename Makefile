PREFIX = /usr
DESTDIR = /
PYTHONDIR = $(shell python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib()[4:])")

all:
	@echo "---------------------------------------------------------"
	@echo "This makefile is used for creating packages."
	@echo "You should install from a package or by running ./install/install.sh"
	@echo ""
	@echo "You are on your own if you 'make install' here."
	@echo "---------------------------------------------------------"
	@echo "Setting the PREFIX and the DESTDIR is supported."
	@echo ""
	@echo "Defaults are:"
	@echo "   - PREFIX=$(PREFIX)"
	@echo "   - DESTDIR=$(DESTDIR)"
	@echo "   - PYTHONDIR=$(PREFIX)$(PYTHONDIR)"
	@echo ""
	@echo "Example: 'make DESTDIR=/tmp PREFIX=/usr install'"
	@echo ""

install:
	@install -dm755 $(DESTDIR)$(PREFIX)/share/polychromatic
	@install -dm755 $(DESTDIR)$(PREFIX)$(PYTHONDIR)/polychromatic
	@install -dm755 $(DESTDIR)$(PREFIX)/share/icons/hicolor
	@install -dm755 $(DESTDIR)$(PREFIX)/share/locale
	@install -Dm755 polychromatic-controller $(DESTDIR)$(PREFIX)/bin/polychromatic-controller
	@install -Dm755 polychromatic-tray-applet $(DESTDIR)$(PREFIX)/bin/polychromatic-tray-applet
	@install -Dm644 man/polychromatic-controller.1 $(DESTDIR)$(PREFIX)/share/man/man1/polychromatic-controller.1
	@install -Dm644 man/polychromatic-tray-applet.1 $(DESTDIR)$(PREFIX)/share/man/man1/polychromatic-tray-applet.1
	@cp -r data/* $(DESTDIR)$(PREFIX)/share/polychromatic/
	@cp -r pylib/* $(DESTDIR)$(PREFIX)$(PYTHONDIR)/polychromatic/
	@cp -r install/hicolor/* $(DESTDIR)$(PREFIX)/share/icons/hicolor/
	@cp -r locale/* $(DESTDIR)$(PREFIX)/share/locale/
	@rm $(DESTDIR)$(PREFIX)/share/locale/*.pot
	@rm $(DESTDIR)$(PREFIX)/share/locale/*/LC_MESSAGES/*.po
	@install -Dm644 install/polychromatic-controller.desktop $(DESTDIR)$(PREFIX)/share/applications/polychromatic-controller.desktop
	@install -Dm644 install/polychromatic-tray-applet.desktop $(DESTDIR)$(PREFIX)/share/applications/polychromatic-tray-applet.desktop
	@install -Dm644 install/polychromatic-tray-applet.desktop $(DESTDIR)/etc/xdg/autostart/polychromatic-tray-applet.desktop

.PHONY: all install
