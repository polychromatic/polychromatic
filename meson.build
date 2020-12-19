project('polychromatic',
        version : '0.6.0',
        meson_version : '>=0.40.0')

# Split packaging supported
build_shared_files = get_option('build_shared_files')
build_controller = get_option('build_controller')
build_tray_applet = get_option('build_tray_applet')
build_cli = get_option('build_cli')

# TODO: Remove code in 'else' once meson version is above 0.46.0
if meson.version().version_compare('>=0.46.0')
    python = import('python').find_installation()
    py_install_dir = python.get_install_dir()
else
    python3 = import('python3')
    py_install_dir = python3.sysconfig_path('platlib')
endif

# FIXME: Debian/Ubuntu Python path should be 'dist-packages'
if build_machine.system() == 'linux'
    if run_command('[', '-d', '/usr/lib/python3/dist-packages', ']').returncode() == 0
        py_install_dir = 'lib/python3/dist-packages'
    endif
endif

i18n = import('i18n')


# Shared files - common (or required) for all Polychromatic interfaces
if build_shared_files == true
    install_subdir('data/img',
        install_dir : join_paths(get_option('datadir'), 'polychromatic', 'img'),
        strip_directory : true)

    install_data(['pylib/__init__.py',
                  'pylib/common.py',
                  'pylib/effects.py',
                  'pylib/fileman.py',
                  'pylib/fx.py',
                  'pylib/locales.py',
                  'pylib/middleman.py',
                  'pylib/preferences.py',
                  'pylib/procpid.py'],
        install_dir : join_paths(py_install_dir, 'polychromatic'))

    install_subdir('pylib/backends',
        install_dir : join_paths(py_install_dir, 'polychromatic', 'backends'),
        strip_directory : true)

    install_subdir('pylib/troubleshoot',
        install_dir : join_paths(py_install_dir, 'polychromatic', 'troubleshoot'),
        strip_directory : true)

    install_data('polychromatic-helper',
        install_dir : get_option('bindir'))

    install_man('man/polychromatic-helper.1')

    install_subdir('source/hicolor',
        install_dir : join_paths(get_option('datadir'), 'icons'))

    install_data('source/launchers/polychromatic-autostart.desktop',
        install_dir : join_paths(get_option('sysconfdir'), 'xdg/autostart'))
endif


# Controller - a PyQt5 application to visually manage devices and features
if build_controller == true
    sass = find_program('sassc')
    run_command('scripts/build-styles.sh')

    install_subdir('data/qt',
        install_dir : join_paths(get_option('datadir'), 'polychromatic', 'qt'),
        strip_directory : true)

    install_subdir('pylib/controller',
        install_dir : join_paths(py_install_dir, 'polychromatic', 'controller'),
        strip_directory : true)

    install_subdir('pylib/qt',
        install_dir : join_paths(py_install_dir, 'polychromatic', 'qt'),
        strip_directory : true)

    install_data('polychromatic-controller',
        install_dir : get_option('bindir'))

    install_man('man/polychromatic-controller.1')

    install_data('source/launchers/polychromatic.desktop',
                install_dir : join_paths(get_option('datadir'), 'applications'))
endif


if build_tray_applet == true
    install_data('polychromatic-tray-applet',
        install_dir : get_option('bindir'))

    install_man('man/polychromatic-tray-applet.1')
endif


if build_cli == true
    install_data('polychromatic-cli',
        install_dir : get_option('bindir'))

    install_man('man/polychromatic-cli.1')
endif

subdir('locale')
