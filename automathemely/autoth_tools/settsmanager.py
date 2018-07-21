#!/usr/bin/env python3
import gi

gi.require_version('Gtk', '3.0')
# noinspection PyPep8
from gi.repository import Gtk, Gdk
# noinspection PyPep8
from glob import glob
# noinspection PyPep8
from subprocess import check_output
# noinspection PyPep8
import collections
# noinspection PyPep8
from automathemely import get_resource
# noinspection PyPep8
from . import extratools
import os
from pathlib import Path


def get_installed_themes(dirs):
    themes = []
    for directory in dirs:
        t = [d.replace(directory, '').replace('/', '') for d in glob('{}*/'.format(directory))]
        themes += t
    themes.sort()
    return themes


def get_atom_themes():
    atom_packs = check_output('apm list --themes --bare', shell=True).decode('utf-8')
    atom_packs = atom_packs.split('\n')
    for i, v in enumerate(atom_packs):
        atom_packs[i] = v.split('@')[0]
    atom_packs = list(filter(None, atom_packs))
    atom_themes = []
    atom_syntaxes = []
    for v in atom_packs:
        if 'syntax' in v:
            atom_syntaxes.append(v)
        else:
            atom_themes.append(v)
    return {'themes': sorted(atom_themes), 'syntaxes': sorted(atom_syntaxes)}


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def common_plural(word):
    # noinspection SpellCheckingInspection
    consonants = 'bcdfghjklmnpqrstvwxyz'
    if word.endswith(('s', 'x', 'z', 'ch')):
        return word + 'es'
    elif word.endswith('y') and word[-2] in consonants:
        word[-1] = 'i'
        return word + 'es'
    elif word.endswith('o') and word[-2] in consonants:
        return word + 'es'
    elif word.endswith('f'):
        word = word.rstrip('f')
        return word + 'ves'
    elif word.endswith('fe'):
        word = word.rstrip('fe')
        return word + 'ves'
    else:
        return word + 's'


class DictTree(collections.UserDict):
    def __init__(self, data=None):
        super().__init__()
        if data is not None:
            self.data = data

    def __getitem__(self, key):
        node = self.data
        for k in key:
            node = node[k]
        return node

    def __setitem__(self, key, value):
        node = self.data
        for k in key[:-1]:
            node = node.setdefault(k, {})
        node[key[-1]] = value


class ProxyDict:
    def __init__(self, master, delayed_writeback=True, **_map):
        self.delayed_writeback = delayed_writeback
        self.master = master
        if delayed_writeback:
            self.front = collections.ChainMap({}, master)
        else:
            self.front = master
        self.map = _map

    def __getitem__(self, key):
        return self.front[self.map[key]]

    def __setitem__(self, key, value):
        self.front[self.map[key]] = value

    def keys(self):
        return self.map.keys()

    def values(self):
        return (self[k] for k in self.keys())

    def items(self):
        return ((k, self[k]) for k in self.keys())

    def __iter__(self):
        return iter(self.keys())

    def writeback(self):
        if self.delayed_writeback:
            self.master.update(self.front.maps[0])


# noinspection PyUnusedLocal
class GUI(object):

    def __init__(self, us_se, th, extras):
        css = b'''.frame-row{
                background-color: @base_color;
            }

            .no-bottom border{
                border-bottom: none;
            }'''
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.th = th
        self.extras = extras
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('manager_gui.glade'))
        self.builder.connect_signals(self)

        self.main_window = self.builder.get_object("main_window")
        self.main_window.set_title('AutomaThemely Settings')
        self.main_window.set_icon_from_file(get_resource('automathemely.svg'))
        self.confirm_dialog = self.builder.get_object('confirm_dialog')
        self.confirm_dialog.set_transient_for(self.main_window)
        self.error_dialog = self.builder.get_object('error_dialog')
        self.error_dialog.set_transient_for(self.main_window)

        self.fix_hint_link()
        self.fix_labels()

        self.us_se = us_se
        self.us_se_tree = DictTree(us_se)
        self.us_se_dict = ProxyDict(
            self.us_se_tree,
            light_theme_box=('themes', 'light'),
            dark_theme_box=('themes', 'dark'),
            sunrise_spin=('offset', 'sunrise'),
            sunset_spin=('offset', 'sunset'),
            autolocation_inverse_switch=('location', 'auto_enabled'),
            manual_city_entry=('location', 'manual', 'city'),
            manual_region_entry=('location', 'manual', 'region'),
            manual_latitude_entry_float=('location', 'manual', 'latitude'),
            manual_longitude_entry_float=('location', 'manual', 'longitude'),
            manual_timezone_entry=('location', 'manual', 'time_zone'),
            notification_switch=('misc', 'notifications'),
            # Extras
            autoatom_extra_switch=('extras', 'atom', 'enabled'),
            atom_light_theme_extra_box=('extras', 'atom', 'themes', 'light', 'theme'),
            atom_light_syntax_extra_box=('extras', 'atom', 'themes', 'light', 'syntax'),
            atom_dark_theme_extra_box=('extras', 'atom', 'themes', 'dark', 'theme'),
            atom_dark_syntax_extra_box=('extras', 'atom', 'themes', 'dark', 'syntax'),
            autovscode_extra_switch=('extras', 'vscode', 'enabled'),
            vscode_light_theme_extra_box=('extras', 'vscode', 'themes', 'light'),
            vscode_dark_theme_extra_box=('extras', 'vscode', 'themes', 'dark')
        )
        self.changed = []

        self.listen_changes = False
        self.entries_error = []
        self.set_all()

        self.main_window.show_all()

    #   Set GUI to match with the user's setting
    def set_all(self):
        for k in self.us_se_dict:
            v = self.us_se_dict[k]
            if k.endswith('entry'):
                self.builder.get_object(k).set_text(str(v))

            elif k.endswith('entry_float'):
                self.builder.get_object(k).set_text(str(v))

            elif k.endswith('spin'):
                self.builder.get_object(k).configure(
                    Gtk.Adjustment(value=v, lower=-999, upper=999, step_increment=1, page_increment=5, page_size=0), 1,
                    0)

            elif k.endswith('extra_box'):
                self.set_extra_box(k, v)

            elif k.endswith('box'):
                if v in self.th:
                    index = self.th.index(v)
                else:
                    index = -1
                box = self.builder.get_object(k)
                for i, val in enumerate(self.th):
                    box.insert(i, str(i), val)
                box.set_active_id(str(index))

            elif k.endswith('switch'):
                switch = self.builder.get_object(k)
                if self.us_se_dict[k]:
                    switch.set_active(True)
                    if k.startswith('auto'):
                        self.on_frame_toggle(switch)
                else:
                    switch.set_active(False)
                    if k.startswith('auto'):
                        self.on_frame_toggle(switch)
        #   Start listening for changes
        self.listen_changes = True

    #   Needs to be separate so it can be called in on_enable_extra_mid_run
    def set_extra_box(self, k, v):
        extra = k.split('_')[0]
        t = common_plural(k.split('_')[-3])
        if v in self.extras[extra][t]:
            index = self.extras[extra][t].index(v)
        else:
            index = -1

        box = self.builder.get_object(k)
        for i, val in enumerate(self.extras[extra][t]):
            box.insert(i, str(i), val)
        box.set_active_id(str(index))

    #   FIXES for stuff that couldn't be done in Glade
    def fix_hint_link(self):
        hint_link = self.builder.get_object('hint_link')
        hint_link.set_label("HINT: You can get most of this info at https://ipinfo.io/json")

    def fix_labels(self):
        i = 0
        while True:
            label = self.builder.get_object('row_label{}'.format(i + 1))
            if label:
                #   Label alignment could change in the future
                label.set_alignment(0, 0.5)
                i += 1
            else:
                break

    #   HANDLERS
    def on_frame_toggle(self, switch, state=None):
        frame_name = Gtk.Buildable.get_name(switch).replace('switch', 'toggle_frame')

        if 'inverse' in frame_name:
            active = True
        else:
            active = False

        if switch.get_active():
            self.builder.get_object(frame_name).set_sensitive(not active)
        else:
            self.builder.get_object(frame_name).set_sensitive(active)

    #   Multipurpose handle referenced on on_save_settings
    def on_any_change(self, emitter, state=None, output=False):
        emitter_name = Gtk.Buildable.get_name(emitter)
        if self.listen_changes:
            emitter_data = None
            if not (emitter_name in self.changed):
                self.changed.append(emitter_name)
            elif emitter_name in self.changed:
                if isinstance(emitter, gi.repository.Gtk.ComboBoxText):
                    emitter_data = emitter.get_active_text()
                elif isinstance(emitter, gi.repository.Gtk.Switch):
                    emitter_data = emitter.get_active()
                elif isinstance(emitter, gi.repository.Gtk.SpinButton):
                    emitter_data = emitter.get_value_as_int()
                elif isinstance(emitter, gi.repository.Gtk.Entry):
                    text = emitter.get_text()
                    if 'float' in emitter_name and isfloat(text):
                        emitter_data = float(text)
                    else:
                        emitter_data = text

                if output:
                    return emitter_data
                else:
                    if emitter_data == self.us_se_dict[emitter_name]:
                        self.changed.remove(emitter_name)

    #   This shouldn't be a separate function but if added to on_any_change it stops working reliably
    def on_float_entry_change(self, emitter):
        text = emitter.get_text()
        if text.strip() == '' or not isfloat(text):
            emitter.set_icon_from_stock(0, 'gtk-dialog-error')
            emitter.set_icon_tooltip_text(0, 'Input should not be empty and contain only valid decimal (float) numbers')
            if Gtk.Buildable.get_name(emitter) not in self.entries_error:
                self.entries_error.append(Gtk.Buildable.get_name(emitter))
        elif emitter.get_icon_stock(0) == 'gtk-dialog-error':
            emitter.set_icon_from_stock(0, None)
            self.entries_error.remove(Gtk.Buildable.get_name(emitter))

    def on_enable_extra_mid_run(self, switch, state=None):
        if self.listen_changes:
            extra = Gtk.Buildable.get_name(switch).split('_')[0].replace('auto', '', 1)
            if switch.get_active():
                empty = False
                for t, val in self.extras[extra].items():
                    if not val:
                        empty = True

                if empty:
                    th, is_error = extratools.get_extra_themes(extra)
                    if is_error:
                        switch.set_active(False)
                        self.on_frame_toggle(switch)
                        switch.set_sensitive(False)
                    else:
                        self.extras[extra] = th
                        for k in self.us_se_dict:
                            if k.startswith(extra):
                                v = self.us_se_dict[k]
                                self.set_extra_box(k, v)

    def on_confirm_exit(self, *args):
        if self.changed:
            response = self.confirm_dialog.run()
            #   This should be destroy() but for some reason it won't work again once it's called
            self.confirm_dialog.hide()
            if response == Gtk.ResponseType.YES:
                Gtk.main_quit(*args)
            elif response == Gtk.ResponseType.NO:
                self.on_save_settings()
                return True
        else:
            Gtk.main_quit(*args)

    def on_save_settings(self, *args):
        if self.entries_error:
            self.error_dialog.run()
            #   This should also be destroy()
            self.error_dialog.hide()
        else:
            for change in self.changed:
                self.us_se_dict[change] = self.on_any_change(self.builder.get_object(change), None, True)
            self.us_se_dict.writeback()
            Gtk.main_quit(*args)

    def return_settings(self):
        return self.us_se


def main(us_se):
    # All paths that I know of that can contain GTK themes
    gtk_paths = [
        '/usr/share/themes/',
        os.path.join(Path.home(), '.themes/'),
        os.path.join(Path.home(), '.local/share/themes/')
    ]
    th = get_installed_themes(gtk_paths)
    extras = dict()

    for k, v in us_se['extras'].items():
        default = True
        if v['enabled']:
            default = False
        out, is_error = extratools.get_extra_themes(k, default)
        extras.update({k: out})

    settings = GUI(us_se, th, extras).return_settings()
    Gtk.main()
    return settings
