#!/usr/bin/env python3
import logging
import time
from datetime import datetime

from schedule import Scheduler, CancelJob

from automathemely.autoth_tools.utils import get_local
from automathemely import info_or_lower_handler, warning_or_higher_handler, scheduler_file_handler, timed_simple_format


logger = logging.getLogger('autothscheduler.py')
logger.propagate = False

logger.addHandler(scheduler_file_handler)
logger.addHandler(info_or_lower_handler)
logger.addHandler(warning_or_higher_handler)

for handler in logger.handlers[:]:
    handler.setFormatter(logging.Formatter(timed_simple_format))


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
    sunrise, sunset = (sunrise.astimezone(tzlocal.get_localzone()).time(),
                       sunset.astimezone(tzlocal.get_localzone()).time())

    if sunrise < now < sunset:
        return ':'.join(str(sunset).split(':')[:-1])
    else:
        return ':'.join(str(sunrise).split(':')[:-1])


def run_automathemely():
    from automathemely.autoth_tools.utils import verify_gnome_session
    # You can't change the theme if the gnome session is not active (E. g. when you close a laptop's lid)
    verify_gnome_session(True)

    from subprocess import check_output, PIPE, CalledProcessError
    try:
        check_output('automathemely', stderr=PIPE)
    except CalledProcessError as e:
        logger.error('Exception while running AutomaThemely')
        logger.error(str(e.stderr, 'utf-8'))

    return CancelJob


class SafeScheduler(Scheduler):
    def __init__(self, reschedule_on_failure=False):
        self.reschedule_on_failure = reschedule_on_failure
        super().__init__()

    def _run_job(self, job):
        # noinspection PyBroadException
        try:
            super()._run_job(job)
        except Exception as e:
            logger.error('Exception while running AutomaThemely')
            logger.exception(e)
            job.last_run = datetime.now()
            # job._schedule_next_run()


scheduler = SafeScheduler()

while True:
    scheduler.every().day.at(get_next_run()).do(run_automathemely())

    while True:
        if not scheduler.jobs:
            logger.info('Running...')
            break
        scheduler.run_pending()
        time.sleep(1)
