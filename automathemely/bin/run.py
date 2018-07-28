#!/usr/bin/env python3
import json
import pickle as pkl
import shutil
import sys
from datetime import datetime
from os import getuid, path, chdir, makedirs
from pathlib import Path

import pytz
import tzlocal

from automathemely import get_resource, get_local, notify, __version__ as version


def check_root():  # Prevent from being run as root for security and compatibility reasons
    if getuid() == 0:
        sys.exit("This shouldn't be run as root unless told otherwise!")


def notify_print_exit(message, enabled, exit_after=True, is_error=False):
    if enabled:
        notify(message)
    if exit_after:
        if is_error:
            sys.exit(message)
        else:
            print(message)
            sys.exit()
    else:
        print(message)


def main():
    check_root()

    #   Set workspace as the directory of the script, and import tools package
    workspace = Path(path.dirname(path.realpath(__file__)))
    chdir(str(workspace))
    sys.path.append('..')
    import autoth_tools

    #   Test for settings file and if it doesn't exist copy it from defaults
    if not Path(get_local('user_settings.json')).is_file():
        if not Path(get_local()).is_dir():
            makedirs(get_local())
        shutil.copy2(get_resource('default_user_settings.json'), get_local('user_settings.json'))
        notify_print_exit('No valid config file found, creating one...', enabled=True, is_error=False)

    with open(get_local('user_settings.json'), 'r') as f:
        user_settings = json.load(f)

    #   If settings files versions don't match (in case of an update for instance), overwrite values of
    #   default_settings with user_settings and use that instead
    if user_settings['version'] != version:
        with open(get_resource('default_user_settings.json'), 'r') as f:
            default_settings = json.load(f)
        default_settings.update(user_settings)
        user_settings = default_settings
        user_settings['version'] = version

    n_enabled = user_settings['misc']['notifications']
    #   If any argument is given, pass it/them to the arg manager module
    if len(sys.argv) > 1:
        output, is_error = autoth_tools.argmanager.main(user_settings)
        if output:
            notify_print_exit(output, enabled=n_enabled, is_error=is_error)

    if not Path(get_local('sun_hours.time')).is_file():
        notify_print_exit('No valid times file found, creating one...', enabled=n_enabled, exit_after=False)
        output, is_error = autoth_tools.updsunhours.main(user_settings)
        if is_error:
            notify_print_exit(output, enabled=n_enabled, is_error=True)
        else:
            with open(get_local('sun_hours.time'), 'wb') as file:
                pkl.dump(output, file, protocol=pkl.HIGHEST_PROTOCOL)

    local_tz = tzlocal.get_localzone()

    with open(get_local('sun_hours.time'), 'rb') as file:
        sunrise, sunset = pkl.load(file)

    #   Convert to local timezone and ignore date
    now = datetime.now(pytz.utc).astimezone(local_tz).time()
    sunrise, sunset = sunrise.astimezone(local_tz).time(), sunset.astimezone(local_tz).time()

    if sunrise < now < sunset:
        theme_type = 'light'
    else:
        theme_type = 'dark'

    from gi.repository import Gio
    g_settings = Gio.Settings.new('org.gnome.desktop.interface')

    change_theme = user_settings['themes'][theme_type]
    current_theme = g_settings['gtk-theme']

    #   Check if there is a theme set to change to
    if not change_theme:
        notify_print_exit('ERROR: No {} theme set'.format(theme_type), enabled=n_enabled, is_error=True)

    #   Check if theme is different before trying to do anything
    if change_theme != current_theme:
        notify_print_exit('Switching to {} theme...'.format(theme_type), enabled=n_enabled, exit_after=False)

        g_settings['gtk-theme'] = change_theme

        #   Change extra themes
        for k, v in user_settings['extras'].items():
            if v['enabled']:
                is_error = autoth_tools.extratools.set_extra_theme(user_settings, k, theme_type)
                if is_error:
                    notify_print_exit('ERROR: {} {} is enabled but cannot be found/set'.format(v, theme_type),
                                      enabled=n_enabled, is_error=True, exit_after=False)


if __name__ == '__main__':
    main()
