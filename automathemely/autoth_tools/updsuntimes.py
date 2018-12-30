#!/usr/bin/env python3
from datetime import timedelta
from time import sleep

import pytz
import tzlocal
from astral import Location

from automathemely.autoth_tools.utils import get_local, verify_gnome_session

import logging

logger = logging.getLogger(__name__)


def get_loc_from_ip():
    import requests

    #   Try to reach ipinfo a max of 15 times, if no connection or html response not OK log and wait
    con_err_msg = 'Can\'t reach https://ipinfo.io/ (Network may be down). Waiting 5 minutes to try again...'
    for i in range(15):
        try:
            g = requests.get('https://ipinfo.io/json')
        except (requests.exceptions.ConnectionError, ConnectionAbortedError,
                ConnectionRefusedError, ConnectionResetError):
            logger.warning(con_err_msg)
            sleep(300)
        else:
            if not g.status_code == 200:
                logger.warning(con_err_msg)
                sleep(300)
            else:
                return g

    return


def main(us_se):

    if 'location' not in us_se:
        logger.error('Invalid config file')
        return

    if us_se['location']['auto_enabled']:
        loc = get_loc_from_ip()
        if loc:
            loc = loc.json()
        else:
            logger.error('Couldn\'t connect to ipinfo, giving up')
            return

        loc['latitude'], loc['longitude'] = (float(x) for x in loc['loc'].strip().split(','))
        loc['time_zone'] = tzlocal.get_localzone().zone

    else:
        for k, v in us_se['location']['manual'].items():
            try:
                val = v.strip()
            except AttributeError:
                pass
            else:
                if not val:
                    logger.error('Auto location is not enabled and some manual values are missing')
                    return
        loc = us_se['location']['manual']

    try:
        location = Location()
        location.name = loc['city']
        location.region = loc['region']
        location.latitude = loc['latitude']
        location.longitude = loc['longitude']
        location.timezone = loc['time_zone']
    except ValueError as e:
        logger.error(str(e))
        return

    sunrise = location.sun()['sunrise'].replace(second=0) + timedelta(minutes=us_se['offset']['sunrise'])
    sunset = location.sun()['sunset'].replace(second=0) + timedelta(minutes=us_se['offset']['sunset'])

    #   Convert to UTC for storage
    return sunrise.astimezone(pytz.utc), sunset.astimezone(pytz.utc)


#   This should only be called when running through systemd
if __name__ == '__main__':
    import json
    import pickle as pkl
    import logging

    # When importing automathemely we inherit the root logger, so we need to configure it for our purposes
    from automathemely import main_file_handler, notifier_handler, updsun_file_handler, \
        default_simple_format, timed_simple_format

    # I know there also is logging.root, but I found it has some weird behaviours
    root_logger = logging.getLogger()

    # We don't need these two
    root_logger.removeHandler(main_file_handler)
    root_logger.removeHandler(notifier_handler)
    # Log here instead
    root_logger.addHandler(updsun_file_handler)

    # Format the remaining handlers to display time
    for handler in root_logger.handlers[:]:
        handler.setFormatter(logging.Formatter(timed_simple_format))

    # This logger is specifically for displaying a notification if something went wrong
    run_as_main_logger = logging.getLogger('updsuntimes.py')

    notifier_handler.setLevel(logging.WARNING)
    notifier_handler.setFormatter(logging.Formatter(default_simple_format))
    run_as_main_logger.addHandler(notifier_handler)

    with open(get_local('user_settings.json'), 'r') as f:
        user_settings = json.load(f)

    # output = main(user_settings)
    output = main(dict())
    if output:
        with open(get_local('sun_times'), 'wb') as file:
            pkl.dump(output, file, protocol=pkl.HIGHEST_PROTOCOL)
    else:
        # if verify_gnome_session():
        run_as_main_logger.warning('There were some errors while updating the sunrise and sunset times, check {} for '
                                   'more details'.format(get_local('.updsuntimes.log')))
