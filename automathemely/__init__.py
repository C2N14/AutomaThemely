import logging
from pathlib import Path
from sys import stdout, stderr
from automathemely.autoth_tools.utils import get_local, notify

_ROOT = str(Path(__file__).resolve().parent)
__version__ = "1.3.0-dev"


# Move/rename older local config directory name to the new lowercase one
if Path.home().joinpath('.config', 'AutomaThemely').is_dir():
    import shutil
    shutil.move(str(Path.home().joinpath('.config', 'AutomaThemely')), get_local())

# Create user config dir if it doesn't exist already
Path(get_local()).mkdir(parents=True, exist_ok=True)


# Custom Handler to pass logs as notifications
class NotifyHandler(logging.StreamHandler):
    def emit(self, record):
        message = self.format(record)
        notify(message)


# noinspection SpellCheckingInspection
default_simple_format = '%(levelname)s: %(message)s'
# noinspection SpellCheckingInspection
timed_details_format = '(%(asctime)s) (%(filename)s:%(funcName)s:%(lineno)s) %(levelname)s: %(message)s'

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
# TODO: Figure out a better way to handle notifications that is as flexible as this that doesn't spam the user in case
# one of the imported libraries malfunctions and decides to also use this root logger
notifier_handler = NotifyHandler()
notifier_handler.setLevel(logging.INFO)

# Setup root logger
# noinspection SpellCheckingInspection
logging.basicConfig(
    # filename=get_local('automathemely.log'),
    # filemode='w',
    # level=logging.DEBUG,
    level=logging.DEBUG,
    handlers=(main_file_handler,
              info_or_lower_handler,
              warning_or_higher_handler,
              # notifier_handler
              ),
    # format='%(levelname)s (%(name)s - %(funcname)s): %(message)s'
    format=default_simple_format
)
