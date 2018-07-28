#!/usr/bin/env python3
from datetime import timedelta
from time import sleep

import pytz
import tzlocal
from astral import Location

from automathemely import get_local, verify_gnome_session


def get_loc_from_ip(logs):
    import requests

    #   Try to reach ipinfo a max of 15 times, if no connection or html response not OK log and wait
    con_err_msg = 'Can\'t reach https://ipinfo.io/ (Network may be down). Waiting 5 minutes to try again.'
    for i in range(15):
        if i == 14:
            return None
        try:
            g = requests.get('https://ipinfo.io/json')
        except (requests.exceptions.ConnectionError, ConnectionAbortedError,
                ConnectionRefusedError, ConnectionResetError):
            if logs:
                logs.warning(con_err_msg)
            else:
                print(con_err_msg)
            sleep(300)
        else:
            if not g.status_code == 200:
                if logs:
                    logs.warning(con_err_msg)
                else:
                    print(con_err_msg)
                sleep(300)
            else:
                return g


def main(us_se, logs=None):
    if us_se['location']['auto_enabled']:
        loc = get_loc_from_ip(logs)
        if loc:
            loc = loc.json()
        else:
            return 'ERROR: Couldn\'t connect to ipinfo, giving up', True

        loc['longitude'] = float(loc['loc'].strip().split(',')[1])
        loc['time_zone'] = tzlocal.get_localzone().zone
        loc['latitude'] = float(loc['loc'].strip().split(',')[0])

    else:
        for k, v in us_se['location']['manual'].items():
            try:
                val = v.strip()
            except AttributeError:
                pass
            else:
                if not val:
                    return 'ERROR: Auto location is not enabled and some manual values are missing', True
        loc = us_se['location']['manual']

    try:
        location = Location()
        location.name = loc['city']
        location.region = loc['region']
        location.latitude = loc['latitude']
        location.longitude = loc['longitude']
        location.timezone = loc['time_zone']
    except ValueError as e:
        return 'ERROR: ' + str(e), True

    sunrise = location.sun()['sunrise'].replace(second=0) + timedelta(minutes=us_se['offset']['sunrise'])
    sunset = location.sun()['sunset'].replace(second=0) + timedelta(minutes=us_se['offset']['sunset'])

    #   Convert to UTC for storage
    return [sunrise.astimezone(pytz.utc), sunset.astimezone(pytz.utc)], False


#   This should only be called when running through systemd
if __name__ == '__main__':
    import json
    import pickle as pkl
    import logging

    logger = logging.getLogger('updsunhours')
    logger.setLevel(logging.WARNING)
    fh = logging.FileHandler(get_local('.updsunhours.log'), mode='w')
    fh.setLevel(logging.WARNING)
    logger.addHandler(fh)

    with open(get_local('user_settings.json'), 'r') as f:
        user_settings = json.load(f)

    output, is_error = main(user_settings, logger)
    if not is_error:
        with open(get_local('sun_hours.time'), 'wb') as file:
            pkl.dump(output, file, protocol=pkl.HIGHEST_PROTOCOL)
    else:
        logger.error(output)
        if user_settings['misc']['notifications'] and verify_gnome_session():
            from automathemely import notify
            notify('There were some errors while updating the sunrise and sunset times, check '
                   + get_local('.updsunhours.log') + ' for more details')
