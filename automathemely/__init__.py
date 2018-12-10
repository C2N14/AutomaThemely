import os
from pathlib import Path

_ROOT = os.path.abspath(os.path.dirname(__file__))
__version__ = 1.25


def get_resource(path=''):
    return os.path.join(_ROOT, 'lib', path)


def get_bin(path=''):
    return os.path.join(_ROOT, 'bin', path)


def get_local(path=''):
    return os.path.join(str(Path.home()), '.config/AutomaThemely', path)


def get_root(path=''):
    return os.path.join(_ROOT, path)


def notify(message):
    import gi
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify, GLib

    if not Notify.is_initted():
        Notify.init('AutomaThemely')

    n = Notify.Notification.new('AutomaThemely', message, get_resource('automathemely.svg'))
    try:  # I don't even know... https://bugzilla.redhat.com/show_bug.cgi?id=1582833
        n.show()
    except GLib.GError as e:
        if str(e) != 'g-dbus-error-quark: Unexpected reply type (16)' \
                and str(e) != 'g-dbus-error-quark: GDBus.Error:org.freedesktop.DBus.Error.NoReply: Message recipient ' \
                              'disconnected from message bus without replying (4)':
            raise e


def pgrep(process_name, use_full=False):
    import subprocess
    command = ['pgrep']
    if use_full:
        command.append('-f')
    command.append(process_name)
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    if p.wait() == 0:  # I. e. if return code == 0
        return True
    else:
        return False


def verify_gnome_session(wait=False):
    import time
    while True:
        if pgrep('gnome-session'):
            if not wait:
                return True
            break
        else:
            if not wait:
                return False
            time.sleep(1)
