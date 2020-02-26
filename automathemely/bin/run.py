#!/usr/bin/env python3
import json
import logging
import pickle as pkl
import shutil
import sys
from datetime import datetime
from os import chdir, getuid
from pathlib import Path

import pytz
import tzlocal

logger = logging.getLogger(__name__)


def check_root():  # Prevent from being run as root for security and compatibility reasons
    if getuid() == 0:
        logger.critical('This shouldn\'t be run as root unless told otherwise!')
        sys.exit()


def main():

    check_root()

    import automathemely

    from automathemely.autoth_tools import argmanager, extratools, envspecific, updsuntimes

    from automathemely import __version__ as version
    from automathemely.autoth_tools.utils import get_resource, get_local, merge_dict
    from automathemely.autoth_tools.settsmanager import UserSettings

    #   Set workspace as the directory of the script
    workspace = Path(__file__).resolve().parent
    chdir(str(workspace))
    sys.path.append('..')

    first_time_run = False
    settings = UserSettings()

    #   Test for settings file
    if not Path(get_local('user_settings.json')).is_file():
        # By default notifications are enabled
        from automathemely import notifier_handler
        logging.getLogger().addHandler(notifier_handler)
        logger.info('No valid config file found, is it your first time running?')
        first_time_run = True
    else:
        # Don't try merging the default settings with the user settings yet, for the versions may not be compatible
        settings.load(merge=False)

    logger.debug('Program version = {}'.format(version))
    logger.debug('File version = {}'.format(settings.get_setting('version')))

    if settings.get_setting('version') != version:
        from pkg_resources import parse_version

        # Hardcoded attempt to try to import old structure to new structure...
        if parse_version(str(settings.get_setting('version'))) <= parse_version('1.2'):
            settings.set_setting('themes', {
                'gnome': {
                    'light': settings.get_setting('themes.light'),
                    'dark': settings.get_setting('themes.dark')
                    }
                })

        settings.set_setting('version', version)

    # Now we can merge settings
    settings.merge_with_default()

    if settings.get_setting('misc.notifications'):
        # Not exactly sure why this is needed but alright...
        automathemely.notifier_handler.setFormatter(logging.Formatter(automathemely.default_simple_format))
        # Add the notification handler to the root logger
        logging.getLogger().addHandler(automathemely.notifier_handler)

    #   If any argument is given, pass it/them to the arg manager module
    if len(sys.argv) > 1:
        automathemely.autoth_tools.argmanager.main()
        return

    # We don't want to proceed until we have given the user the chance to review its settings
    if first_time_run:
        return

    if not Path(get_local('sun_times')).is_file():
        logger.info('No valid times file found, creating one...')
        output = updsuntimes.main()
        if output:
            with open(get_local('sun_times'), 'wb') as file:
                pkl.dump(output, file, protocol=pkl.HIGHEST_PROTOCOL)

    local_tz = tzlocal.get_localzone()

    with open(get_local('sun_times'), 'rb') as file:
        sunrise, sunset = pkl.load(file)

    #   Convert to local timezone and ignore date
    now = datetime.now(pytz.utc).astimezone(local_tz).time()
    sunrise, sunset = sunrise.astimezone(local_tz).time(), sunset.astimezone(local_tz).time()

    if sunrise < now < sunset:
        t_color = 'light'
    else:
        t_color = 'dark'

    logger.info('Switching to {} themes...'.format(t_color))

    #   Change desktop environment theme
    # desk_env = user_settings['desktop_environment']
    desk_env = settings.get_setting('desktop_environment')
    if desk_env != 'custom':
        # for t_type in user_settings['themes'][desk_env][t_color]:
        for t_type in settings.get_setting('themes.{}.{}'.format(desk_env, t_color)):
            # theme = user_settings['themes'][desk_env][t_color][t_type]
            theme = settings.get_setting('themes.{}.{}.{}'.format(desk_env, t_color, t_type))

            envspecific.set_theme(desk_env, t_type, theme)

    #   Run user scripts
    s_time = 'sunrise' if t_color == 'light' else 'sunset'
    extratools.run_scripts(settings.get_setting('extras.scripts.{}'.format(s_time)),
                           notifications_enabled=settings.get_setting('misc.notifications'))

    #   Change extra themes
    for k, v in settings.get_setting('extras').items():
        if k != 'scripts' and v['enabled']:
            extratools.set_extra_theme(k, t_color)


if __name__ == '__main__':
    main()
