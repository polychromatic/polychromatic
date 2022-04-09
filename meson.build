project('polychromatic',
        version : '0.8.0',
        meson_version : '>=0.47.0')

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

# Compile Qt styles
# - This needs to run externally because there is a concatination situation
#   since SASS cannot process Qt's gradient syntax.
sass = find_program('sassc')
run_command('scripts/build-styles.sh', check: true)

install_data('polychromatic-controller',
             'polychromatic-tray-applet',
             'polychromatic-cli',
             'polychromatic-helper',
             install_dir : get_option('bindir'))

install_man('man/polychromatic-controller.1',
            'man/polychromatic-tray-applet.1',
            'man/polychromatic-cli.1',
            'man/polychromatic-helper.1')

install_subdir('data',
               install_dir : join_paths(get_option('datadir'), 'polychromatic'),
               strip_directory : true)

install_subdir('polychromatic',
               install_dir : join_paths(py_install_dir, 'polychromatic'),
               strip_directory : true)

install_subdir('sources/hicolor',
               install_dir : join_paths(get_option('datadir'), 'icons'))

install_data('sources/launchers/polychromatic.desktop',
             install_dir : join_paths(get_option('datadir'), 'applications'))

install_data('sources/launchers/polychromatic-autostart.desktop',
             install_dir : join_paths(get_option('sysconfdir'), 'xdg/autostart'))

subdir('locale')
