#!/usr/bin/env python3
import sys
import json
from os import getuid, path, chdir, makedirs
from pathlib import Path
from datetime import datetime
import notify2
import pickle as pkl
import pytz
import subprocess
import shutil
from automathemely import get_resource, get_local, __version__ as version


def check_root():  # Prevent from being run as root for security and compatibility reasons
    if getuid() == 0:
        sys.exit("This shouldn't be run as root unless told otherwise!")


def notify_exit(message, exit_after=False):
    n = notify2.Notification('AutomaThemely', message, get_resource('automathemely.svg'))
    try:
        n.show()
    except TypeError as error:
        print('You should most likely just ignore this error (check documentation), but just in case it is:\n',
              str(error))
        # Really weird bug with notify2 where it requires some sort of id not specified in any documentation
    if exit_after:
        sys.exit(message)


def main():
    check_root()
    notify2.init('AutomaThemely')

    # Set workspace as the directory of the script, and import tools package
    workspace = Path(path.dirname(path.realpath(__file__)))
    chdir(str(workspace))
    sys.path.append('..')
    import autoth_tools

    # Test for settings file and if it doesn't exist copy it from defaults
    if not Path(get_local('user_settings.json')).is_file():
        if not Path(get_local()).is_dir():
            makedirs(get_local())
        shutil.copy2(get_resource('default_user_settings.json'), get_local('user_settings.json'))
        notify_exit('No valid config file found, creating one...', True)

    with open(get_local('user_settings.json'), 'r') as f:
        user_settings = json.load(f)

    # If settings files versions don't match (in case of an update for instance), overwrite values of
    # default_settings with user_settings and use that instead
    if user_settings['version'] != version:
        with open(get_resource('default_user_settings.json'), 'r') as f:
            default_settings = json.load(f)
        default_settings.update(user_settings)
        user_settings = default_settings
        user_settings['version'] = version

    # If any argument is given, pass it/them to the arg manager module
    if len(sys.argv) > 1:
        output, exit_after = autoth_tools.argmanager.main(user_settings)
        if output:
            if user_settings['misc']['notifications']:
                notify_exit(output, exit_after)
            else:
                sys.exit(output)

    if not Path(get_local('sun_hours.time')).is_file():
        from automathemely.autoth_tools import updsunhours
        message = 'No valid times file found, creating one...'
        if user_settings['misc']['notifications']:
            notify_exit(message)
        print(message)
        updsunhours.main(user_settings)
        output, is_error = updsunhours.main(user_settings)
        if not is_error:
            with open(get_local('sun_hours.time'), 'wb') as file:
                pkl.dump(output, file, protocol=pkl.HIGHEST_PROTOCOL)
        else:
            if user_settings['misc']['notifications']:
                notify_exit(output)
                print(output)

        sys.exit()

    with open(get_local('sun_hours.time'), 'rb') as file:
        sunrise, sunset = pkl.load(file)
    now = datetime.now(pytz.utc)

    theme_type = None
    if now <= sunrise:
        theme_type = 'dark'
    elif sunrise < now < sunset:
        theme_type = 'light'
    elif now >= sunset:
        theme_type = 'dark'

    change_theme = user_settings['themes'][theme_type]
    current_theme = subprocess.check_output('gsettings get org.gnome.desktop.interface gtk-theme', shell=True) \
        .decode('utf-8').replace("'", '').strip()

    # Check if there is a set theme
    if not change_theme:
        message = 'ERROR: No {} theme set'.format(theme_type)
        if user_settings['misc']['notifications']:
            notify_exit(message, True)
        else:
            sys.exit(message)

    # Check if theme is different before trying to do anything
    if change_theme != current_theme:
        message = 'Switching to {} theme...'.format(theme_type)
        if user_settings['misc']['notifications']:
            notify_exit(message)
        else:
            print(message)

        subprocess.run('/usr/bin/gsettings set org.gnome.desktop.interface gtk-theme ' + change_theme, shell=True)

        # Change atom theme
        if user_settings['extras']['atom']['enabled']:
            import getpass
            username = getpass.getuser()

            i = 0
            with open('/home/{}/.atom/config.cson'.format(username)) as fileIn, open(
                    '/home/{}/.atom/config.cson.tmp'.format(username), 'w') as fileOut:
                # First look for line with "themes", then go from bottom to top writing lines
                for item in fileIn:
                    if i == 1:
                        # Make sure it has the same spaces as the original file
                        item = ' ' * (len(item) - len(item.lstrip(' '))) + '"' \
                               + user_settings['atom']['themes'][theme_type]['syntax'] + '"'
                        i -= 1
                    if i == 2:
                        # Make sure it has the same spaces as the original file
                        item = ' ' * (len(item) - len(item.lstrip(' '))) + '"' \
                               + user_settings['atom']['themes'][theme_type]['theme'] + '"'
                        i -= 1
                    if item.strip().startswith('themes:'):
                        i = 2

                    fileOut.write(item)

            shutil.move('/home/'+username+'/.atom/config.cson.tmp', '/home/'+username+'/.atom/config.cson')


if __name__ == '__main__':
    main()
