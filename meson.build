project('polychromatic')

python3 = import('python3')
i18n = import('i18n')

lessc = find_program(['lessc'])
custom_target('css',
              output: 'controller.css',
              input: 'data/pages/controller.less',
              command: [lessc, '@INPUT@', '@OUTPUT'])

subdir('locale')

install_data(['polychromatic-controller', 'polychromatic-tray-applet'],
             install_dir : get_option('bindir'))
install_man(['man/polychromatic-controller.1', 'man/polychromatic-tray-applet.1'])

install_subdir('data', install_dir : join_paths(get_option('datadir'), 'polychromatic'), strip_directory : true)
install_subdir('pylib', install_dir : join_paths(python3.sysconfig_path('platlib'), 'polychromatic'), strip_directory : true)
install_subdir('install/hicolor', install_dir : join_paths(get_option('datadir'), 'icons'))

install_data(['install/polychromatic-controller.desktop', 'install/polychromatic-tray-applet.desktop'],
             install_dir : join_paths(get_option('datadir'), 'share/applications'))
install_data('install/polychromatic-tray-applet.desktop',
             install_dir : join_paths(get_option('sysconfdir'), 'xdg/autostart'))
