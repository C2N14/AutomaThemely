from pathlib import Path
import collections


#   PATH RELATED FUNCTIONS
def get_resource(path=''):
    from automathemely import _ROOT
    return str(Path(_ROOT).joinpath('lib', path))


def get_bin(path=''):
    from automathemely import _ROOT
    return str(Path(_ROOT).joinpath('bin', path))


def get_local(path=''):
    return str(Path.home().joinpath('.config', 'automathemely', path))


def get_root(path=''):
    from automathemely import _ROOT
    return str(Path(_ROOT).joinpath(path))


#   DICT RELATED FUNCTIONS
def read_dict(dic, keys):
    for k in keys:
        try:
            dic = dic[k]
        except KeyError:
            return
    return dic


def write_dic(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


#   MISC FUNCTIONS
def notify(message, title='AutomaThemely'):
    import gi
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify, GLib

    if not Notify.is_initted():
        Notify.init('AutomaThemely')

    n = Notify.Notification.new(title, message, get_resource('automathemely.svg'))
    try:  # I don't even know... https://bugzilla.redhat.com/show_bug.cgi?id=1582833
        n.show()
    except GLib.GError as e:
        if str(e) != 'g-dbus-error-quark: Unexpected reply type (16)' \
                and str(e) != 'g-dbus-error-quark: GDBus.Error:org.freedesktop.DBus.Error.NoReply: Message recipient ' \
                              'disconnected from message bus without replying (4)':
            raise e


def pgrep(process_names, use_full=False):
    from subprocess import run, DEVNULL
    command = ['pgrep']
    if use_full:
        command.append('-f')
    for p_name in process_names:
        p_command = command + [p_name]
        p = run(p_command, stdout=DEVNULL)
        if p.returncode == 0:
            return True


def verify_desktop_session(wait=False):
    import time
    while True:
        # noinspection SpellCheckingInspection
        if pgrep(['gnome-session', 'plasmashell', 'cinnamon-sessio', 'xfce4-session']):
            if not wait:
                return True
            break
        else:
            if not wait:
                return False
            time.sleep(1)
