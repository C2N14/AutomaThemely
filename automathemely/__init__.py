import os
from pathlib import Path
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify, GLib


_ROOT = os.path.abspath(os.path.dirname(__file__))
__version__ = 1.1


def get_resource(path=''):
    return os.path.join(_ROOT, 'lib', path)


def get_bin(path=''):
    return os.path.join(_ROOT, 'bin', path)


def get_local(path=''):
    return os.path.join(str(Path.home()), '.config/AutomaThemely', path)


def get_root(path=''):
    return os.path.join(_ROOT, path)


def notify(message):
    if not Notify.is_initted():
        Notify.init('AutomaThemely')
    n = Notify.Notification.new('AutomaThemely', message, get_resource('automathemely.svg'))
    try:  # I don't even know... https://bugzilla.redhat.com/show_bug.cgi?id=1582833
        n.show()
    except GLib.GError as e:
        if str(e) != 'g-dbus-error-quark: Unexpected reply type (16)':
            raise e
