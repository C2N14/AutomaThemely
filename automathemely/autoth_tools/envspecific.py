# from automathemely import get_resource
from os import walk
from collections import defaultdict
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

# GTK, Cinnamon's desktop and GNOME shell themes all share the same dirs, but have different structures and conditions
HOME = Path.home()
PATH_CONSTANTS = {
    'general-themes': [
        '/usr/share/themes/',
        str(HOME.joinpath('.local/share/themes/')),
        str(HOME.joinpath('.themes/'))
    ],
    'icons-themes': [
        '/usr/share/icons/',
        str(HOME.joinpath('.local/share/icons/')),
        str(HOME.joinpath('.icons/'))
    ],
    'lookandfeel-themes': [
        '/usr/share/plasma/look-and-feel/',
        str(HOME.joinpath('.local/share/plasma/look-and-feel/'))
    ],
    'shell-user-extensions': str(HOME.joinpath('.local/share/gnome-shell/extensions/')),
    'kde-gtk-config': {
        'gtk3': str(HOME.joinpath('.config/gtk-3.0/settings.ini')),
        'gtk2': str(HOME.joinpath('.gtkrc-2.0'))
    }
}
SUPPORTED_DESKENVS = ['gnome', 'kde', 'xfce', 'cinnamon']

# Just a nitpick for displaying them correctly in logs and notifications
UPPERCASE_NAMES = ['gnome', 'kde', 'xfce', 'gtk']
CAPITALIZED_NAMES = ['cinnamon', 'shell', 'desktop']
MISC_NAMES = {
    'lookandfeel': 'Look and Feel'
}


def correct_name_case(name):
    if name in UPPERCASE_NAMES:
        return name.upper()
    elif name in CAPITALIZED_NAMES:
        return name.capitalize()
    elif name in MISC_NAMES:
        return MISC_NAMES[name]
    else:
        return name


# NOTE: Lists must have the same type of content for this to work
def sort_remove_dupes(lis):
    lis = list(set(lis))

    if isinstance(lis[0], str):
        return sorted(lis, key=str.lower)

    elif isinstance(lis[0], tuple):
        return sorted(lis, key=lambda s: s[0].lower())

    else:
        return sorted(list(set(lis)))


def walk_filter_dirs(dirs, filtering_func, return_parent=False):
    filtered_dirs = list()
    for directory in dirs:
        scan = next(walk(directory), None)
        if scan:
            for subdir in scan[1]:
                if filtering_func(scan[0], subdir):
                    if return_parent:
                        filtered_dirs.append((subdir, scan[0]))
                    else:
                        filtered_dirs.append(subdir)

    return filtered_dirs


def get_installed_themes(desk_env):
    types = defaultdict(bool)
    themes = defaultdict(list)

    # return a dictionary with: {'gtk': [], 'icons': [], 'shell': []} or None
    if desk_env == 'gnome':
        types['gtk'] = True
        types['icons'] = True
        types['shell'] = True

    # return a dictionary with: {'lookandfeel': [], 'gtk': []} or None
    elif desk_env == 'kde':
        types['lookandfeel'] = True
        types['gtk'] = True

    # return a dictionary with: {'gtk': [], 'icons': []} or None
    elif desk_env == 'xfce':
        types['gtk'] = True
        types['icons'] = True

    # return a dictionary with: {'gtk': [], 'desktop': [], 'icons': []} or None
    elif desk_env == 'cinnamon':
        types['gtk'] = True
        types['desktop'] = True
        types['icons'] = True

    elif desk_env == 'custom':
        return

    else:
        raise Exception('Invalid Desktop Environment "{}"'.format(desk_env))

    # Actually start scanning for themes
    if types['gtk']:
        t_list = walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent, t: Path(parent)
                                  .joinpath(t).glob('gtk-3.*/gtk.css') and t.lower() != 'default')
        # t_list = walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent_dir, theme: glob(
        #     '{}{}/gtk-3.*/gtk.css'.format(parent_dir, theme)) and theme.lower() != 'default')
        themes['gtk'] = [(t,) for t in sort_remove_dupes(t_list)]

    if types['icons']:
        t_list = walk_filter_dirs(PATH_CONSTANTS['icons-themes'], lambda parent, t: Path(parent)
                                  .joinpath(t, 'index.theme').is_file() and t.lower() != 'default')
        # t_list = walk_filter_dirs(PATH_CONSTANTS['icons-themes'], lambda parent_dir, theme: os.path.isfile(
        #     '{}{}/index.theme'.format(parent_dir, theme)) and theme.lower() != 'default')
        themes['icons'] = [(t,) for t in sort_remove_dupes(t_list)]

    if types['desktop']:
        # I guess a hidden default?
        t_list = ['cinnamon']
        t_list += walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent, t: Path(parent)
                                   .joinpath(t, 'cinnamon').is_dir())
        # t_list += walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent_dir, theme: os.path.isdir(
        #     '{}{}/cinnamon'.format(parent_dir, theme)))
        themes['desktop'] = [(t,) for t in sort_remove_dupes(t_list)]

    if types['lookandfeel']:
        import configparser
        import json
        t_list = walk_filter_dirs(PATH_CONSTANTS['lookandfeel-themes'], lambda parent, t: Path(parent)
                                  .joinpath(t, 'metadata.desktop').is_file() or Path(parent)
                                  .joinpath(t, 'metadata.json').is_file(), return_parent=True)
        # t_list = walk_filter_dirs(PATH_CONSTANTS['lookandfeel-themes'], lambda parent_dir, theme: os.path.isfile(
        #     '{}{}/metadata.desktop'.format(parent_dir, theme)) or os.path.isfile(
        #     '{}{}/metadata.json'.format(parent_dir, theme)), return_parent=True)
        t_list = sort_remove_dupes(t_list)

        for t in t_list:
            parent_dir = t[1]
            theme = t[0]
            # Prioritize .desktop metadata files to .json ones just like systemsettings
            if Path(parent_dir).joinpath(theme, 'metadata.desktop').is_file():
                # if os.path.isfile('{}{}/metadata.desktop'.format(t[1], t[0])):
                metadata = configparser.ConfigParser()
                metadata.read(str(Path(parent_dir).joinpath(theme, 'metadata.desktop')))
                t_name = metadata['Desktop Entry']['Name']

            # Has to be JSON because it was already filtered before
            else:
                with Path(parent_dir).joinpath(theme, 'metadata.json').open() as f:
                    # with open('{}{}/metadata.json'.format(t[1], t[0])) as f:
                    metadata = json.load(f)
                t_name = metadata['KPlugin']['Name']

            themes['lookandfeel'].append((t[0], t_name))

    if types['shell']:
        # This is explained in the function below
        t_list = ['default']
        t_list += walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent, t: Path(parent)
                                   .joinpath(t, 'gnome-shell', 'gnome-shell.css').is_file() and t.lower() != 'default')
        # t_list += walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent_dir, theme: os.path.isfile(
        #     '{}{}/gnome-shell/gnome-shell.css'.format(parent_dir, theme)) and theme.lower() != 'default')

        themes['shell'] = [(t,) for t in sort_remove_dupes(t_list)]

    return themes


def set_theme(desk_env, t_type, theme):
    # breakpoint()
    if desk_env not in SUPPORTED_DESKENVS:
        raise Exception('Invalid desktop environment!')

    elif not theme:
        logger.error('{}\'s {} theme not set '.format(correct_name_case(desk_env), correct_name_case(t_type)))
        return

    if t_type in ['gtk', 'icons']:
        from gi.repository import Gio
        if desk_env == 'cinnamon':
            gsettings_string = 'org.cinnamon.desktop.interface'
        else:
            gsettings_string = 'org.gnome.desktop.interface'

        gsettings = Gio.Settings.new(gsettings_string)

    # Safety fallback, shouldn't happen
    else:
        gsettings = None

    if t_type == 'gtk':

        # Easy peasy
        # For GNOME and Cinnamon
        gsettings['gtk-theme'] = theme

        # For XFCE
        if desk_env == 'xfce':
            from subprocess import run, CalledProcessError
            try:
                # noinspection SpellCheckingInspection
                run(['xfconf-query', '-c', 'xsettings', '-p', '/Net/ThemeName', '-s', theme])
            except CalledProcessError:
                logger.error('Could not apply GTK theme')
                return

        # Switching GTK themes in KDE is a little bit more complicated than the others...
        # For KDE
        elif desk_env == 'kde':
            from subprocess import run
            import configparser
            import fileinput
            import sys
            from automathemely.autoth_tools.utils import get_bin

            # Set GTK3 theme
            # This would usually be done with kwriteconfig but since there is no way to notify GTK3 apps that the
            # theme has changed in KDE like with GTK2 anyway we might as well do it this way
            parser = configparser.ConfigParser(strict=False)
            parser.optionxform = lambda option: option
            parser.read_file(PATH_CONSTANTS['kde-gtk-config']['gtk3'])

            parser['Settings']['gtk-theme-name'] = theme
            with open(PATH_CONSTANTS['kde-gtk-config']['gtk3'], 'w') as f:
                parser.write(f, space_around_delimiters=False)

            # Search for gtk2 config file in theme dir in PATH_CONSTANTS dirs
            # As if it wasn't messy enough already...
            match = walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent_dir, t: Path(parent_dir)
                                     .joinpath(t).glob('gtk-2.*/gtkrc') and t.lower() != 'default', return_parent=True)

            # match = walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent_dir, t: glob(
            #     '{}{}/gtk-2.*/gtkrc'.format(parent_dir, t)) and t.lower() != 'default', return_parent=True)
            #

            if not match:
                logger.warning('The selected GTK theme does not contain a GTK2 theme, so some applications may '
                               'look odd')
            else:
                # If there are several themes with the same name in different directories, only get the first one
                # to match according to the dirs hierarchy in PATH_CONSTANTS
                theme_parent = match[0][1]

                if not Path(PATH_CONSTANTS['kde-gtk-config']['gtk2']).is_file():
                    logger.warning('GTK2 config file not found, set a theme from System Settings at least once and '
                                   'try again')

                # Write GTK2 config
                else:
                    line_replaced, previous_is_autogen_comment = False, False
                    for line in fileinput.input(PATH_CONSTANTS['kde-gtk-config']['gtk2'], inplace=True):

                        if line.startswith('# Configs for GTK2 programs'):
                            previous_is_autogen_comment = True
                            sys.stdout.write(line)

                        # Even in kde-config-gtk they don't seem to agree if this may not actually be needed, but
                        # just in case here it is
                        elif line.startswith('include'):
                            print('include "{}"'.format(str(Path(theme_parent).joinpath(theme, 'gtk-2.0', 'gtkrc'))))

                        # This is the one that matters
                        elif line.startswith('gtk-theme-name='):
                            print('gtk-theme-name="{}"'.format(theme))
                            line_replaced = True

                        else:
                            if previous_is_autogen_comment and not line.startswith('# Edited by AutomaThemely'):
                                print('# Edited by AutomaThemely')
                                previous_is_autogen_comment = False
                            sys.stdout.write(line)

                    if not line_replaced:
                        logger.warning('GTK2 config file is invalid, set a theme from System Settings at least '
                                       'once and try again')
                    else:
                        # Send signal to GTK2 apps to refresh their themes
                        run([get_bin('kde-refresh-gtk2')])

    elif t_type == 'icons':

        # For GNOME and Cinnamon
        gsettings['icon-theme'] = theme

        # For XFCE
        if desk_env == 'xfce':
            from subprocess import run, CalledProcessError
            try:
                # noinspection SpellCheckingInspection
                run(['xfconf-query', '-c', 'xsettings', '-p', '/Net/IconThemeName', '-s', theme])
            except CalledProcessError:
                logger.error('Could not apply icons theme')
                return

    elif t_type == 'shell':
        # This is WAY out of my level, I'll just let the professionals handle this one...
        try:
            import gtweak
        except ModuleNotFoundError:
            logger.error('GNOME Tweaks not installed')
            return

        from gtweak.gshellwrapper import GnomeShellFactory
        from gtweak.defs import GSETTINGS_SCHEMA_DIR, LOCALE_DIR
        # This could probably be implemented in house but since I'm already importing from gtweak I guess it'll stay
        # this way for now
        from gtweak.gsettings import GSettingsSetting

        gtweak.GSETTINGS_SCHEMA_DIR = GSETTINGS_SCHEMA_DIR
        gtweak.LOCALE_DIR = LOCALE_DIR
        shell = GnomeShellFactory().get_shell()
        shell_theme_name = 'user-theme@gnome-shell-extensions.gcampax.github.com'
        shell_theme_schema = 'org.gnome.shell.extensions.user-theme'
        shell_theme_schema_dir = Path(PATH_CONSTANTS['shell-user-extensions']).joinpath(shell_theme_name, 'schemas')

        if not shell:
            logger.error('GNOME Shell not running')
            return
        else:
            # noinspection PyBroadException
            try:
                shell_extensions = shell.list_extensions()
            except Exception:
                logger.error('GNOME Shell extensions could not be loaded')
                return
            else:
                # noinspection PyBroadException
                try:
                    if shell_theme_name in shell_extensions and shell_extensions[shell_theme_name]['state'] == 1:
                        # If shell user-theme was installed locally e. g. through extensions.gnome.org
                        if Path(shell_theme_schema_dir).is_dir():
                            user_shell_settings = GSettingsSetting(shell_theme_schema,
                                                                   schema_dir=str(shell_theme_schema_dir))
                        # If it was installed as a system extension
                        else:
                            user_shell_settings = GSettingsSetting(shell_theme_schema)
                    else:
                        logger.error('GNOME Shell user theme extension not enabled')
                        return
                except Exception:
                    logger.error('Could not load GNOME Shell user theme extension')
                    return
                else:
                    # To set the default theme you have to input an empty string, but since that won't work with the
                    # Setting Manager's ComboBoxes we set it by this placeholder name
                    if theme == 'default':
                        theme = ''

                    # Set the GNOME Shell theme
                    user_shell_settings.set_string('name', theme)

    elif t_type == 'lookandfeel':
        from subprocess import run, CalledProcessError
        try:
            # noinspection SpellCheckingInspection
            run(['lookandfeeltool', '-a', '{}'.format(theme)], check=True)
        except CalledProcessError:
            logger.error('Could not apply Look and Feel theme')
            return

    elif t_type == 'desktop':
        from gi.repository import Gio
        cinnamon_settings = Gio.Settings.new('org.cinnamon.theme')
        cinnamon_settings['name'] = theme
