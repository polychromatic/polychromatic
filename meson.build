project('polychromatic',
        version : '0.3.12',
        meson_version : '>=0.40.0')

# Remove code in 'else' once meson version is above 0.46.0
if meson.version().version_compare('>=0.46.0')
    python = import('python').find_installation()
    py_install_dir = python.get_install_dir()
else
    python3 = import('python3')
    py_install_dir = python3.sysconfig_path('platlib')
endif

i18n = import('i18n')

sass = find_program('sass', 'sassc')
custom_target('css',
              input : 'source/sass/controller.scss',
              output : 'controller.css',
              command : [sass, '@INPUT@', '@OUTPUT@', '--style', 'compressed'],
              build_by_default : true,
              install : true,
              install_dir : join_paths(get_option('datadir'), 'polychromatic', 'ui'))

install_data('polychromatic-controller',
             'polychromatic-tray-applet',
             install_dir : get_option('bindir'))

install_man('man/polychromatic-controller.1',
            'man/polychromatic-tray-applet.1')

install_subdir('data',
               install_dir : join_paths(get_option('datadir'), 'polychromatic'),
               strip_directory : true)

install_subdir('pylib',
               install_dir : join_paths(py_install_dir, 'polychromatic'),
               strip_directory : true)

install_subdir('source/hicolor',
               install_dir : join_paths(get_option('datadir'), 'icons'))

install_data('source/launchers/polychromatic-controller.desktop',
             'source/launchers/polychromatic-tray-applet.desktop',
             install_dir : join_paths(get_option('datadir'), 'applications'))

install_data('source/launchers/polychromatic-tray-applet.desktop',
             install_dir : join_paths(get_option('sysconfdir'), 'xdg/autostart'))

subdir('locale')
