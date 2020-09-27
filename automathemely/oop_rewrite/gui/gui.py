#!/usr/bin/env python3
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio

import bisect
import sys

from ..oop_rewrite.settings import setts as settings
from ..oop_rewrite.theming import desktop

BIGGEST_SPACE = 18
BIG_SPACE = 12
REGULAR_SPACE = 8
SMALL_SPACE = 6
CASED_NAMES = {
    'gtk': 'GTK',
    'icons': 'Icons',
    'desktop': 'Desktop',
    'lookandfeel': 'Look and Feel',
    'shell': 'Shell'
}
SETTINGS_GROUP = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.BOTH)


# used for faster searching, only in ordered lists
def binary_index(a, x):
    """Locate the first value equal to x using binary search"""
    if a is None:
        return -1
    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    return -1


# regular old list.index(), but handling the exception
def linear_index(a, x):
    """Locate the first value equal to x using linear search"""
    if a is None:
        return -1
    try:
        i = a.index(x)
    except ValueError:
        return -1
    return i


def get_cased(name):
    return CASED_NAMES.get(name, name)


def display_row_separators(row, before):
    row.set_activatable(False)
    row.set_selectable(False)

    if before:
        row.set_header(Gtk.Separator())


class SettingsWidget:
    # the path that the widget corresponds to in the settings
    path = None

    def get_data(self):
        raise NotImplementedError


class SettingsCombo(Gtk.ComboBoxText, SettingsWidget):
    def __init__(self,
                 path,
                 *args,
                 options_list=None,
                 with_ids=False,
                 **kwargs):
        super().__init__(*args, **kwargs)

        if options_list is not None:
            if with_ids:
                self.set_all_ids(options_list)
            else:
                self.set_all(options_list)

        SETTINGS_GROUP.add_widget(self)

        self.path = path

    def set_all(self, options_list):
        self.remove_all()
        for o in options_list:
            self.append_text(o)

    def set_all_ids(self, options_list):
        self.remove_all()
        for o_id, o in options_list:
            self.append(o_id, o)

    def get_data(self):
        # prioritizes the id to the string
        id_ = self.get_active_id()
        return id_ if id_ is not None else self.get_active_text()


class SettingsSpin(Gtk.SpinButton, SettingsWidget):
    def __init__(self, path, *args, **kwargs):
        super().__init__(*args,
                         digits=3,
                         numeric=True,
                         input_purpose=Gtk.InputPurpose.DIGITS,
                         update_policy=Gtk.SpinButtonUpdatePolicy.IF_VALID,
                         **kwargs)

        self.configure(
            Gtk.Adjustment(lower=-999,
                           upper=999,
                           step_increment=1,
                           page_increment=5,
                           page_size=0), 1, 0)

        SETTINGS_GROUP.add_widget(self)

        self.path = path

    def get_data(self):
        return self.get_value_as_int()


class SettingsSwitch(Gtk.Switch, SettingsWidget):
    # when the switch disables or enables a container these two must me set
    related_container = None
    invert_container = None

    def __init__(self,
                 path,
                 *args,
                 related_container=None,
                 invert_container=False,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.related_container = related_container
        self.invert_container = invert_container

        self.path = path

    def get_data(self):
        return self.get_active()


class SettingsEntry(Gtk.Entry, SettingsWidget):
    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, halign=Gtk.Align.START, **kwargs)

        self.path = path

    def get_data(self):
        purpose = self.get_input_purpose()
        string = self.get_text()
        if purpose == Gtk.InputPurpose.NUMBER:
            return float(string)
        elif purpose == Gtk.InputPurpose.DIGITS:
            return int(string)
        else:
            return string


class SettingsList(Gtk.ListBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         selection_mode=Gtk.SelectionMode.NONE,
                         **kwargs)

        self.set_header_func(display_row_separators)

    def add_labeled_row(self, label_string, widget):
        label = Gtk.Label(label_string,
                          halign=Gtk.Align.START,
                          valign=Gtk.Align.CENTER,
                          hexpand_set=True,
                          vexpand_set=True,
                          hexpand=True,
                          vexpand=True)

        grid = Gtk.Grid(column_spacing=BIG_SPACE,
                        margin_start=BIG_SPACE,
                        margin_end=BIG_SPACE,
                        margin_top=REGULAR_SPACE,
                        margin_bottom=REGULAR_SPACE,
                        hexpand_set=True,
                        vexpand_set=True,
                        hexpand=True,
                        vexpand=True)
        grid.attach(label, 0, 0, 1, 1)
        grid.attach(widget, 1, 0, 1, 1)

        row = Gtk.ListBoxRow()
        row.add(grid)

        self.add(row)


class EnvironmentNotebook(Gtk.Notebook):
    environment = None
    base_path = None
    main_window = None

    def __init__(self, base_path, environment_object, main_window, *args,
                 **kwargs):
        super().__init__(*args, tab_pos=Gtk.PositionType.LEFT, **kwargs)

        self.environment = environment_object
        self.base_path = base_path
        # since this class creates its own SettingsWidgets, it needs to know the
        # window it belongs to, to connect the signals appropiately
        self.main_window = main_window

    def populate(self):
        lists = [('light', SettingsList()), ('dark', SettingsList())]

        themes = self.environment.get_themes()
        for key, value in themes.items():

            name = get_cased(key)

            for l_type, l in lists:
                path = f'{self.base_path}.{l_type}.{key}'
                combo = SettingsCombo(path, options_list=value)
                # the active index is set here, not in the constructor since
                # set_all() erases the index
                combo.set_active(binary_index(value, settings[path]))
                combo.connect('changed', self.main_window._on_any_change)

                l.add_labeled_row(name, combo)

        for l_type, l in lists:
            self.append_page(l, Gtk.Label(l_type.capitalize()))


class TitleLabel(Gtk.Label):
    def __init__(self, string, *args, **kwargs):
        super().__init__(f'<b>{string}</b>',
                         *args,
                         halign=Gtk.Align.FILL,
                         use_markup=True,
                         **kwargs)


class TitleBox(Gtk.Box):
    def __init__(self, label_string, widget, *args, **kwargs):
        super().__init__(*args,
                         orientation=Gtk.Orientation.HORIZONTAL,
                         spacing=BIG_SPACE,
                         halign=Gtk.Align.FILL,
                         homogeneous=True,
                         **kwargs)

        widget.set_halign(Gtk.Align.START)
        self.add(
            Gtk.Label(f'<b>{label_string}</b>',
                      halign=Gtk.Align.END,
                      use_markup=True))
        self.add(widget)


class ExtraSwitch(SettingsSwitch):
    related_notebook = None

    def __init__(self, *args, related_notebook=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.related_notebook = related_notebook


class AppWindow(Gtk.ApplicationWindow):
    app = None
    themes_revealer = None
    themes_box = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # for ease of use, must set in kwargs!!!
        self.app = self.props.application

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                           spacing=BIGGEST_SPACE,
                           margin_start=BIGGEST_SPACE,
                           margin_end=BIGGEST_SPACE,
                           margin_top=BIGGEST_SPACE,
                           margin_bottom=BIGGEST_SPACE)

        self.themes_revealer = Gtk.Revealer()
        self.themes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                  spacing=SMALL_SPACE,
                                  margin_top=BIGGEST_SPACE)
        self.themes_box.add(TitleLabel('Themes'))
        self.themes_revealer.add(self.themes_box)

        environments = [('gnome', 'GNOME/GNOME-like'), ('kde', 'KDE'),
                        ('xfce', 'XFCE'), ('cinnamon', 'Cinnamon'),
                        ('custom', 'Other/Custom')]
        env_combo = SettingsCombo('desktop_environment',
                                  options_list=environments,
                                  with_ids=True)
        env_combo.connect('changed', self._on_environment_change)
        env_combo.connect('changed', self._on_any_change)
        env_combo.set_active(
            linear_index([e for e, _ in environments],
                         settings['desktop_environment']))

        # this container doesn't have the spacing because it is set on its box
        # child
        desk_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        desk_container.add(TitleBox('Desktop environment', env_combo))
        desk_container.add(self.themes_revealer)

        main_box.add(desk_container)

        times = ('sunrise', 'sunset')
        time_list = SettingsList()
        for t in times:
            time_spin = SettingsSpin(f'offset.{t}',
                                     value=settings[f'offset.{t}'])
            time_spin.connect('changed', self._on_any_change)
            time_list.add_labeled_row(t.capitalize(), time_spin)

        time_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                 spacing=SMALL_SPACE)
        time_container.add(TitleLabel('Time offset (in minutes)'))
        time_container.add(time_list)

        main_box.add(time_container)

        loc_list = SettingsList()
        locations = [('city', 'City'), ('region', 'Region'),
                     ('latitude', 'Latitude'), ('longitude', 'Longitude'),
                     ('time_zone', 'Time zone name')]
        for l, name in locations:
            loc_entry = SettingsEntry(f'location.manual.{l}',
                                      text=settings[f'location.manual.{l}'])
            if l in ('latitude', 'longitude'):
                loc_entry.set_input_purpose(Gtk.InputPurpose.DIGITS)

            loc_entry.connect('changed', self._on_any_change)
            loc_list.add_labeled_row(name, loc_entry)
        loc_switch = SettingsSwitch('location.auto_enabled',
                                    related_container=loc_list,
                                    invert_container=True)
        loc_switch.connect('notify::active', self._on_toggle_container)
        loc_switch.connect('notify::active', self._on_any_change)
        loc_switch.set_active(settings['location.auto_enabled'])

        loc_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                spacing=SMALL_SPACE)
        loc_container.add(TitleBox('Automatic location', loc_switch))
        loc_container.add(loc_list)
        loc_container.add(
            Gtk.LinkButton(
                'https://ipinfo.io/json',
                'HINT: You can get most of this info at https://ipinfo.io/json'
            ))

        main_box.add(loc_container)

        notif_switch = SettingsSwitch('misc.notifications')
        notif_box = TitleBox('Notifications', notif_switch)

        main_box.add(notif_box)

        extras_expander = Gtk.Expander(label='Extras')

        # TODO: Implement extras

        main_box.add(extras_expander)

        self.add(main_box)

    def _on_environment_change(self, combo):
        """Toggles the revealer and populates de notebooks as necessary"""
        selected = combo.get_active_id()
        if selected == 'custom':
            self.themes_revealer.set_reveal_child(False)
        else:
            env_factory = desktop.EnvironmentFactory()
            env_notebook = EnvironmentNotebook(f'themes.{selected}',
                                               env_factory.create(selected),
                                               self)
            env_notebook.populate()

            # the walrus operator would be real nice here...
            children = self.themes_box.get_children()
            if len(children) > 1:
                self.themes_box.remove(children[-1])

            self.themes_box.add(env_notebook)
            self.themes_box.show_all()
            self.themes_revealer.set_reveal_child(True)

    def _on_toggle_container(self, switch, _):
        # XOR of switch state and invert_container
        switch.related_container.set_sensitive(
            switch.invert_container != switch.get_active())

    def _on_toggle_extra(self, switch, _):
        if switch.get_active():
            switch.related_notebook.populate()

    def _on_any_change(self, widget, *_):
        if self.app.listen_to_changes:
            self.app.changes.append(widget)


class App(Gtk.Application):
    window = None
    changes = None
    listen_to_changes = False

    def __init__(self):
        super().__init__(application_id='com.github.tester',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.changes = []

    # def do_startup(self):
    #     super().do_startup()

    def do_activate(self):
        if not self.window:
            self.window = AppWindow(application=self)
            self.window.show_all()

            self.listen_to_changes = True

        self.window.present()


app = App()
app.run()
