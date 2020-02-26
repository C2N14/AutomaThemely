#!/usr/bin/env python3
import argparse
import json
import logging
import pickle as pkl

from automathemely.autoth_tools.utils import get_local, read_dict, write_dic

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
options = parser.add_mutually_exclusive_group()
options.add_argument('-l', '--list', help='list all current settings', action='store_true', default=False)
options.add_argument('-s', '--setting', help="change a specific setting (e.g. key.subkey=value)")
options.add_argument('-m', '--manage', help='easier to use settings manager GUI', action='store_true',
                     default=False)
options.add_argument('-u', '--update', help='update the sunrise and sunset\'s times manually', action='store_true',
                     default=False)
options.add_argument('-r', '--restart',
                     help='(re)start the scheduler script if it were to not start or stop unexpectedly',
                     action='store_true', default=False)


#   For --list arg
def print_formatted(d, indent=0):
    for key, value in d.items():
        print('{}{}'.format('\t' * indent, key), end='')
        if isinstance(value, dict):
            print('.')
            print_formatted(value, indent + 1)
        else:
            print(' = {}'.format(value))


#   ARGUMENTS FUNCTION
def main():
    from automathemely.autoth_tools.settsmanager import UserSettings

    args = parser.parse_args()
    settings = UserSettings()

    #   LIST
    if args.list:
        logger.info('Printing current settings...')
        print('')
        print_formatted(settings.get_dictionary())
        return

    #   SET
    elif args.setting:
        if not args.setting.count('=') == 1:
            logger.error('Invalid string (None or more than one "=" signs)')
            return

        setts = args.setting.split('=')
        to_set_path = setts[0].strip()
        to_set_val = setts[1].strip()

        if to_set_path == '':
            logger.error('Invalid string (Empty key)')
        elif to_set_path[-1] == '.':
            logger.error('Invalid string (Key ends in dot)')
        if not to_set_val:
            logger.error('Invalid string (Empty value)')
        elif to_set_val.lower() in ['t', 'true']:
            to_set_val = True
        elif to_set_val.lower() in ['f', 'false']:
            to_set_val = False
        else:
            try:
                to_set_val = int(to_set_val)
            except ValueError:
                try:
                    to_set_val = float(to_set_val)
                except ValueError:
                    pass

        if settings.get_setting(to_set_path) is not None:
            settings.set_setting(to_set_path, to_set_val)

            settings.dump()

            # Warning if user disables auto by --setting
            if 'enabled' in to_set_path and to_set_val is False:
                logger.warning('Remember to set all the necessary values with either --settings or --manage')
            logger.info('Successfully set "{}" as "{}"'.format(to_set_path, to_set_val))
            return

        else:
            logger.error('Path "{}" not found'.format(to_set_path))

        return

    #   MANAGE
    elif args.manage:
        from . import settsmanagergui
        #   From here on the manager takes over 'til exit
        settsmanagergui.main()
        return

    #   UPDATE
    elif args.update:
        from . import updsuntimes
        output = updsuntimes.main(us_se)
        if output:
            with open(get_local('sun_hours.time'), 'wb') as file:
                pkl.dump(output, file, protocol=pkl.HIGHEST_PROTOCOL)
            logger.info('Sun hours successfully updated')
        return

    #   RESTART
    elif args.restart:
        from automathemely.autoth_tools.utils import pgrep_any, get_bin
        from subprocess import Popen, DEVNULL
        if pgrep_any(['autothscheduler.py'], use_full=True):
            Popen(['pkill', '-f', 'autothscheduler.py']).wait()
        Popen(['python3', get_bin('autothscheduler.py')], start_new_session=True, stdout=DEVNULL, stderr=DEVNULL)
        logger.info('Restarted the scheduler')
