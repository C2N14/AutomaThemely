#!/usr/bin/env python3
import logging
import time
from datetime import datetime

from schedule import Scheduler, CancelJob

from automathemely import get_local

logger = logging.getLogger('scheduler')
logger.setLevel(logging.INFO)
try:
    fh = logging.FileHandler(get_local('automathemely.log'), mode='w')
except FileNotFoundError as e:
    logger.exception(e)
else:
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)


def get_next_run():
    import pickle
    import tzlocal
    import pytz
    try:
        with open(get_local('sun_hours.time'), 'rb') as file:
            sunrise, sunset = pickle.load(file)
    except FileNotFoundError:
        import sys
        logger.error('Could not find times file, exiting...')
        sys.exit()

    now = datetime.now(pytz.utc).astimezone(tzlocal.get_localzone()).time()
    sunrise, sunset = sunrise.astimezone(tzlocal.get_localzone()).time(), \
                      sunset.astimezone(tzlocal.get_localzone()).time()

    if sunrise < now < sunset:
        return ':'.join(str(sunset).split(':')[:-1])
    else:
        return ':'.join(str(sunrise).split(':')[:-1])


def run_automathemely():
    from automathemely import verify_gnome_session
    # You can't change the theme if the gnome session is not active (E. g. when you close a laptop's lid)
    verify_gnome_session(True)
    from subprocess import run
    try:
        run('automathemely')
    except Exception as e:
        logger.exception(e)
    return CancelJob


class SafeScheduler(Scheduler):
    def __init__(self, reschedule_on_failure=False):
        self.reschedule_on_failure = reschedule_on_failure
        super().__init__()

    def _run_job(self, job):
        # noinspection PyBroadException
        try:
            super()._run_job(job)
        except Exception:
            logger.exception('AutomaThemely ({}):'.format(datetime.now()))
            job.last_run = datetime.now()
            # job._schedule_next_run()


scheduler = SafeScheduler()

while True:
    scheduler.every().day.at(get_next_run()).do(run_automathemely())

    while True:
        if not scheduler.jobs:
            logger.info('{} - Running...'.format(str(datetime.now())))
            break
        scheduler.run_pending()
        time.sleep(1)
