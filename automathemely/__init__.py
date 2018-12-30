import os.path
_ROOT = os.path.abspath(os.path.dirname(__file__))
__version__ = 1.25

from sys import stdout, stderr
import logging

from automathemely.autoth_tools.utils import get_local, notify

# Create user config dir
if not os.path.isdir(get_local()):
    os.makedirs(get_local())


# Custom Handler to pass logs as notifications
class NotifyHandler(logging.StreamHandler):
    def emit(self, record):
        message = self.format(record)
        notify(message)


default_simple_format = '%(levelname)s: %(message)s'
timed_simple_format = '(%(asctime)s) %(levelname)s: %(message)s'

# Setup logging levels/handlers
main_file_handler = logging.FileHandler(get_local('automathemely.log'), mode='w')
updsun_file_handler = logging.FileHandler(get_local('.updsuntimes.log'), mode='w')
scheduler_file_handler = logging.FileHandler(get_local('.autothscheduler.log'), mode='w')
info_or_lower_handler = logging.StreamHandler(stdout)
info_or_lower_handler.setLevel(logging.DEBUG)
info_or_lower_handler.addFilter(lambda log: log.levelno <= logging.INFO)
warning_or_higher_handler = logging.StreamHandler(stderr)
warning_or_higher_handler.setLevel(logging.WARNING)
# This will be added in run.py if notifications are enabled
notifier_handler = NotifyHandler()
notifier_handler.setLevel(logging.INFO)

# Setup root logger
logging.basicConfig(
    # filename=get_local('automathemely.log'),
    # filemode='w',
    level=logging.DEBUG,
    handlers=(main_file_handler,
              info_or_lower_handler,
              warning_or_higher_handler,
              # notifier_handler
              ),
    # format='%(levelname)s (%(name)s - %(funcname)s): %(message)s'
    format=default_simple_format
)
