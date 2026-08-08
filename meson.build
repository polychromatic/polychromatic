project('polychromatic',
        version : '0.9.8',
        meson_version : '>=0.53.0')

fs = import('fs')
i18n = import('i18n')
python = import('python').find_installation()
py_install_dir = python.get_install_dir()

# Debian/Ubuntu's Python path should be 'dist-packages'
if build_machine.system() == 'linux'
    if fs.is_dir('/usr/lib/python3/dist-packages')
        py_install_dir = 'lib/python3/dist-packages'
    endif
endif

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

# AppStream Metainfo
# The source file is a template. Translations are merged in at build time from
# the message catalogues, so software centres (GNOME Software, KDE Discover)
# show the summary, description and screenshot captions in the user's language.
metainfo_file = i18n.merge_file(
        input : 'sources/app.polychromatic.controller.metainfo.xml.in',
        output : 'app.polychromatic.controller.metainfo.xml',
        type : 'xml',
        po_dir : 'locale',
        install : true,
        install_dir : join_paths(get_option('datadir'), 'metainfo'))

ascli_exe = find_program('appstreamcli', required: false)
if ascli_exe.found()
  test('validate metainfo file',
        ascli_exe,
        args: ['validate',
               '--no-net',
               '--pedantic',
               metainfo_file],
        depends: metainfo_file
  )
endif
