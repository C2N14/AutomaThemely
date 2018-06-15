#!/usr/bin/env python3
from time import sleep
from datetime import timedelta
import os

from astral import Location
from crontab import CronTab

from automathemely import get_bin, get_local, get_root, get_resource


def log_print(log, sys_log):
    print(log)
    if sys_log:
        from syslog import syslog
        syslog('"' + os.path.basename(__file__) + ' (crontab): {}"'.format(log))


def main(us_se, sys_log=False):
    if us_se['location']['auto_enabled']:
        import requests

        # Try to reach freegeoip, if no connection or html response not OK log and wait
        con_err_msg = 'Can\'t reach https://freegeoip.net/ (Network may be down). Waiting 5 minutes to try again.'
        while True:
            try:
                g = requests.get('https://freegeoip.net/json/')
            except (requests.exceptions.ConnectionError, ConnectionAbortedError,
                    ConnectionRefusedError, ConnectionResetError):
                log_print(con_err_msg, sys_log)
                sleep(300)
            else:
                if not g.status_code == 200:
                    log_print(con_err_msg, sys_log)
                    sleep(300)
                else:
                    break
        loc = g.json()
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
        location.region = loc['region_name']
        location.latitude = loc['latitude']
        location.longitude = loc['longitude']
        location.timezone = loc['time_zone']
    except ValueError as e:
        return 'ERROR: ' + str(e), True

    sunrise = location.sun()['sunrise'].replace(second=0) + timedelta(minutes=us_se['offset']['sunrise'])
    sunset = location.sun()['sunset'].replace(second=0) + timedelta(minutes=us_se['offset']['sunset'])

    sr = {'hr': sunrise.strftime('%H'), 'mn': sunrise.strftime('%M')}
    ss = {'hr': sunset.strftime('%H'), 'mn': sunset.strftime('%M')}
    tabs = ['sunrise_change_theme', 'sunset_change_theme', 'update_sunhours_daily', 'update_sunhours_reboot']
    exists = dict.fromkeys(tabs, False)
    cron = CronTab(user=True)

    for tab in cron:
        if tab.comment == 'sunrise_change_theme':
            exists['sunrise_change_theme'], exists['any'] = True, True
            tab.hour.on(sr['hr'])
            tab.minute.on(sr['mn'])
        elif tab.comment == 'sunset_change_theme':
            exists['sunset_change_theme'], exists['any'] = True, True
            tab.hour.on(ss['hr'])
            tab.minute.on(ss['mn'])

        elif tab.comment == 'update_sunhours_daily':
            exists['update_sunhours_daily'], exists['any'] = True, True
        elif tab.comment == 'update_sunhours_reboot':
            exists['update_sunhours_reboot'] = True

    main_cmd = get_bin('cron-trigger') + ' "' + get_bin('run.py') + '" >>  ' + get_local('automathemely.log')
    updsun_cmd = get_bin('cron-trigger') + ' "' + get_root('autoth_tools/updsunhours.py') + '" >>  '\
                                                + get_local('.updsunhours.log')

    if not exists['sunrise_change_theme']:
        job = cron.new(
            command=main_cmd,
            comment='sunrise_change_theme')
        job.hour.on(sr['hr'])
        job.minute.on(sr['mn'])
    if not exists['sunset_change_theme']:
        job = cron.new(
            command=main_cmd,
            comment='sunset_change_theme')
        job.hour.on(ss['hr'])
        job.minute.on(ss['mn'])

    if not exists['update_sunhours_daily']:
        job = cron.new(
            command=updsun_cmd,
            comment='update_sunhours_daily')
        job.setall('@daily')
    if not exists['update_sunhours_reboot']:
        job = cron.new(
            command=updsun_cmd,
            comment='update_sunhours_reboot')
        job.setall('@reboot')

    cron.write()

    # To make sure it'll still work if it starts a little too soon
    return [sunrise - timedelta(seconds=1), sunset - timedelta(seconds=1)], False


# This should only be called when running through crontab
if __name__ == '__main__':
    import json
    import pickle as pkl
    import notify2

    with open(get_local('user_settings.json'), 'r') as f:
        user_settings = json.load(f)

    output, is_error = main(user_settings, True)
    if not is_error:
        with open(get_local('sun_hours.time'), 'wb') as file:
            pkl.dump(output, file, protocol=pkl.HIGHEST_PROTOCOL)
    else:
        log_print(output, True)
        if user_settings['misc']['notifications']:
            notify2.init('AutomaThemely')
            n = notify2.Notification('AutomaThemely',
                                     'There were some errors while updating the sunrise and sunset times, '
                                     'check .updsunhours.log for more details', get_resource('app_icon.svg'))
            try:
                n.show()
            except TypeError as error:
                print('You should most likely just ignore this error (check documentation), but just in case it is:\n',
                      str(error))
                # Really weird bug with notify2 where it requires some sort of id not specified in documentation
