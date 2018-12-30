# from automathemely import get_resource
import os
from collections import defaultdict
from glob import glob
from pathlib import Path

import logging
logger = logging.getLogger(__name__)

# GTK, Cinnamon's desktop and GNOME shell themes all share the same dirs, but have different structures and conditions
PATH_CONSTANTS = {
    'general-themes': [
        '/usr/share/themes/',
        os.path.join(str(Path.home()), '.local/share/themes/'),
        os.path.join(str(Path.home()), '.themes/')
    ],
    'icons': [
        '/usr/share/icons/',
        os.path.join(str(Path.home()), '.local/share/icons/'),
        os.path.join(str(Path.home()), '.icons/')
    ],
    'lookandfeel': [
        '/usr/share/plasma/look-and-feel/',
        os.path.join(str(Path.home()), '.local/share/plasma/look-and-feel/')
    ]
}


#   Old code to get GNOME GTK Themes

# def get_installed_themes():
#     themes = []
#     # All paths that I know of that can contain GTK themes
#     gtk_paths = [
#         '/usr/share/themes/',
#         os.path.join(str(Path.home()), '.themes/'),
#         os.path.join(str(Path.home()), '.local/share/themes/')
#     ]
#     for directory in gtk_paths:
#         t = [d.replace(directory, '').replace('/', '') for d in glob('{}*/'.format(directory))]
#         themes += t
#     themes.sort()
#     return themes


def sort_remove_dupes(l):
    return sorted(list(set(l)))


def walk_filter_dirs(dirs, filtering_func, return_parent=False):
    filtered_dirs = list()
    for directory in dirs:
        scan = next(os.walk(directory), None)
        if scan:
            for subdir in scan[1]:
                if filtering_func(scan[0], subdir):
                    if return_parent:
                        filtered_dirs.append([subdir, scan[0]])
                    else:
                        filtered_dirs.append(subdir)

    return filtered_dirs


# TODO: Find out how to get these such as the function above
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
        t_list = walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent_dir, theme: glob(
            '{}{}/gtk-3.*/gtk.css'.format(parent_dir, theme)) and theme.lower() != 'default')
        themes['gtk'] = [(t,) for t in sort_remove_dupes(t_list)]

    if types['icons']:
        # TODO: Is this enough of a check for valid themes for all the desk envs?
        t_list = walk_filter_dirs(PATH_CONSTANTS['icons'], lambda parent_dir, theme: os.path.isfile(
            '{}{}/index.theme'.format(parent_dir, theme)) and theme.lower() != 'default')
        themes['icons'] = [(t,) for t in sort_remove_dupes(t_list)]

    if types['desktop']:
        t_list = walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent_dir, theme: os.path.isdir(
            '{}{}/cinnamon'.format(parent_dir, theme)))
        themes['desktop'] = [(t,) for t in sort_remove_dupes(t_list)]

    if types['lookandfeel']:
        import configparser
        import json
        t_list = walk_filter_dirs(PATH_CONSTANTS['lookandfeel'], lambda parent_dir, theme: os.path.isfile(
            '{}{}/metadata.desktop'.format(parent_dir, theme)) or os.path.isfile(
            '{}{}/metadata.json'.format(parent_dir, theme)), return_parent=True)
        t_list = sort_remove_dupes(t_list)

        for t in t_list:
            # Prioritize .desktop metadata files to .json ones just like systemsettings
            if os.path.isfile('{}{}/metadata.desktop'.format(t[1], t[0])):
                metadata = configparser.ConfigParser()
                metadata.read('{}{}/metadata.desktop'.format(t[1], t[0]))
                t_name = metadata['Desktop Entry']['Name']

            # Has to be JSON because it was already filtered before
            else:
                with open('{}{}/metadata.json'.format(t[1], t[0])) as f:
                    metadata = json.load(f)
                t_name = metadata['KPlugin']['Name']

            themes['lookandfeel'].append((t[0], t_name))

    if types['shell']:
        t_list = ['default']
        t_list += walk_filter_dirs(PATH_CONSTANTS['general-themes'], lambda parent_dir, theme: os.path.isfile(
            '{}{}/gnome-shell/gnome-shell.css'.format(parent_dir, theme)) and theme.lower() != 'default')

        themes['shell'] = [(t,) for t in sort_remove_dupes(t_list)]

        # try:
        #     import gtweak
        # except ModuleNotFoundError:
        #     print('ERROR: GNOME Tweaks not installed')
        #     return
        #
        # from gtweak.gshellwrapper import GnomeShellFactory
        # from gtweak.defs import GSETTINGS_SCHEMA_DIR, LOCALE_DIR
        #
        # gtweak.GSETTINGS_SCHEMA_DIR = GSETTINGS_SCHEMA_DIR
        # gtweak.LOCALE_DIR = LOCALE_DIR
        # shell = GnomeShellFactory().get_shell()

    return themes


# TODO: Find out how to set these such as how it currently works in run.py
def set_theme(desk_env, t_type, theme):
    if desk_env == 'gnome':
        if t_type == 'gtk':
            pass

        elif t_type == 'icons':
            pass

        elif t_type == 'shell':
            pass

    elif desk_env == 'kde':
        if t_type == 'plasma':
            pass

        elif t_type == 'icons':
            pass

    elif desk_env == 'xfce':
        if t_type == 'gtk':
            pass

        elif t_type == 'icons':
            pass

    else:
        raise Exception('Invalid Desktop Environment "{}"'.format(desk_env))
