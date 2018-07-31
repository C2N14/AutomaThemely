#!/usr/bin/env python3
import gi

gi.require_version('Gtk', '3.0')
# noinspection PyPep8
from gi.repository import Gtk, Gio, Gdk
# noinspection PyPep8
from automathemely import get_resource, get_local, notify
# noinspection PyPep8
from automathemely.autoth_tools import extratools
# noinspection PyPep8
import os
# noinspection PyPep8
from pathlib import Path
# noinspection PyPep8
from glob import glob
# noinspection PyPep8
import json


def get_installed_themes():
    themes = []
    # All paths that I know of that can contain GTK themes
    gtk_paths = [
        '/usr/share/themes/',
        os.path.join(Path.home(), '.themes/'),
        os.path.join(Path.home(), '.local/share/themes/')
    ]
    for directory in gtk_paths:
        t = [d.replace(directory, '').replace('/', '') for d in glob('{}*/'.format(directory))]
        themes += t
    themes.sort()
    return themes


def read_dict(dic, keys):
    for k in keys:
        dic = dic[k]
    return dic


def write_dic(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def split_name_attr(obj_id):
    if '~' in obj_id:
        return obj_id.split('~')
    else:
        return obj_id, None


def try_or_default_type(val, try_type):
    try:
        return try_type(val)
    except ValueError:
        if try_type == str:
            return ''
        elif try_type == int:
            return 0
        elif try_type == float:
            return 0.0
        else:
            return None


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


# noinspection PyUnusedLocal
class App(Gtk.Application):

    def __init__(self, us_se):
        super().__init__(application_id="com.github.c2n14.automathemely",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.main_window = None
        self.us_se = us_se

    #       BASIC Gtk.Application FUNCTIONS
    # noinspection PyAttributeOutsideInit
    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.builder = Gtk.Builder()
        self.builder.add_from_file(get_resource('manager_gui.glade'))
        self.builder.set_application(self)
        self.builder.connect_signals(self)

        self.extras = dict()
        for k, v in self.us_se['extras'].items():
            if v['enabled']:
                get_default = False
            else:
                get_default = True
            out = extratools.get_extra_themes(k, get_default)
            self.extras[k] = out[0]

        self.system_themes = get_installed_themes()
        self.listen_changes = False
        self.saved_settings = False
        self.entries_error = list()
        self.changed = list()

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

        #   Override the quit menu
        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_confirm_exit)
        self.add_action(action)

    # noinspection PyAttributeOutsideInit
    def do_activate(self):
        #   Called on primary instance activation
        #   Kinda like do_startup but after the window is displayed
        if not self.main_window:
            self.main_window = self.builder.get_object('main_window')
            self.main_window.set_application(self)
            self.main_window.set_title('AutomaThemely Settings')
            self.main_window.set_icon_from_file(get_resource('automathemely.svg'))

            sub_w_list = ['confirm_dialog', 'error_dialog']
            self.sub_windows = dict()
            for w in sub_w_list:
                self.sub_windows[w] = self.builder.get_object(w)
                self.sub_windows[w].set_transient_for(self.main_window)

            self.set_all()
            self.listen_changes = True

        self.main_window.present()

    def do_shutdown(self):
        Gtk.Application.do_shutdown(self)

        #   Dump file
        if self.changed and self.saved_settings:
            with open(get_local('user_settings.json'), 'w') as file:
                json.dump(self.us_se, file, indent=4)
            exit_message = 'Successfully saved settings'
        else:
            exit_message = 'No changes were made'

        #   As it skips over argmanager, it needs to handle exit notifications by itself
        if self.us_se['misc']['notifications']:
            notify(exit_message)
        print(exit_message)

    #      CALLED ON PRIMARY ACTIVATION
    def set_all(self):
        for obj in self.builder.get_objects():
            obj_id = Gtk.Buildable.get_name(obj)
            if '___object_' not in obj_id:
                obj_type = obj.get_name()
                obj_name, obj_attr = split_name_attr(obj_id)

                #   These don't contain data
                if obj_type == 'GtkLabel':
                    if obj_name.startswith('row_label'):
                        # This could change to be more in line with the official GNOME style standards
                        obj.set_alignment(0, 0.5)

                elif obj_type == 'GtkLinkButton':
                    obj.set_label("HINT: You can get most of this info at https://ipinfo.io/json")

                #   These DO contain data
                elif obj_type in ['GtkEntry', 'GtkSpinButton', 'GtkSwitch', 'GtkComboBoxText']:
                    keys = obj_name.split('.')
                    val = read_dict(self.us_se, keys)

                    if obj_type == 'GtkEntry':
                        obj.set_text(try_or_default_type(val, str))

                    elif obj_type == 'GtkSpinButton':
                        obj.configure(Gtk.Adjustment(value=try_or_default_type(val, int), lower=-999, upper=999,
                                                     step_increment=1, page_increment=5, page_size=0), 1, 0)
                    elif obj_type == 'GtkSwitch':
                        if val:
                            obj.set_active(True)

                        if obj_attr and 'frame' in obj_attr:
                            self.on_frame_toggle(obj)

                    elif obj_type == 'GtkComboBoxText':
                        if 'extras' in obj_attr:
                            self.set_extra_box(obj)

                        elif 'gtk' in obj_attr:
                            if val in self.system_themes:
                                index = self.system_themes.index(val)
                            else:
                                index = -1
                            for i, val in enumerate(self.system_themes):
                                obj.insert(i, str(i), val)
                            obj.set_active_id(str(index))

    #   Needs to be separate so it can be called in on_enable_extra_mid_run
    def set_extra_box(self, box):
        box_id = Gtk.Buildable.get_name(box)
        box_name = box_id.split('~')[0]
        box_attr = box_id.split('~')[1]

        keys = box_name.split('.')
        val = read_dict(self.us_se, keys)

        extra_type = box_attr.split('-')[-1]
        theme_type = box_attr.split('-')[-2]

        if val in self.extras[extra_type][theme_type]:
            index = self.extras[extra_type][theme_type].index(val)
        else:
            index = -1

        for i, val in enumerate(self.extras[extra_type][theme_type]):
            box.insert(i, str(i), val)
        box.set_active_id(str(index))

    #       HANDLERS
    def on_frame_toggle(self, switch, *args):
        switch_id = Gtk.Buildable.get_name(switch).split('~')
        switch_name = switch_id[0]
        switch_attr = switch_id[1]
        frame_name = '{}_toggleframe'.format('_'.join(switch_name.split('.')[:-1]))
        frame = self.builder.get_object(frame_name)

        if 'inverse' in switch_attr:
            disable = True
        else:
            disable = False

        if switch.get_active():
            frame.set_sensitive(not disable)
        else:
            frame.set_sensitive(disable)

    def on_enable_extra_mid_run(self, switch, *args):
        if self.listen_changes and switch.get_active():
            switch_id = Gtk.Buildable.get_name(switch)
            switch_name = switch_id.split('~')[0]
            extra_type = switch_name.split('.')[-2]

            empty = False
            for t, val in self.extras[extra_type].items():
                if not val:
                    empty = True

            if empty:
                out, is_error = extratools.get_extra_themes(extra_type)
                if is_error:
                    switch.set_active(False)
                    self.on_frame_toggle(switch)
                    switch.set_sensitive(False)
                else:
                    self.extras[extra_type] = out

                    for obj in self.builder.get_objects():
                        obj_id = Gtk.Buildable.get_name(obj)
                        obj_type = obj.get_name()
                        if obj_id.startswith('extras.{}'.format(extra_type)) and obj_type == 'GtkComboBoxText':
                            self.set_extra_box(obj)

    #   Multipurpose handle referenced on on_save_settings
    def on_any_change(self, emitter, *args, output=False):
        if self.listen_changes:
            emitter_id = Gtk.Buildable.get_name(emitter)
            emitter_data = None
            if not (emitter_id in self.changed):
                self.changed.append(emitter_id)
            elif emitter_id in self.changed:
                emitter_type = emitter.get_name()
                if emitter_type == 'GtkComboBoxText':
                    emitter_data = emitter.get_active_text()
                elif emitter_type == 'GtkSwitch':
                    emitter_data = emitter.get_active()
                elif emitter_type == 'GtkSpinButton':
                    emitter_data = emitter.get_value_as_int()
                elif emitter_type == 'GtkEntry':
                    text = emitter.get_text()
                    if 'float' in emitter_id and isfloat(text):
                        emitter_data = float(text)
                    else:
                        emitter_data = text

                if output:
                    return emitter_data

                else:
                    emitter_name = split_name_attr(emitter_id)[0]

                    if emitter_data == read_dict(self.us_se, emitter_name.split('.')):
                        self.changed.remove(emitter_id)

    def on_float_entry_change(self, emitter, *args):
        text = emitter.get_text()
        emitter_id = Gtk.Buildable.get_name(emitter)
        if text.strip() == '' or not isfloat(text):
            emitter.set_icon_from_stock(0, 'gtk-dialog-error')
            emitter.set_icon_tooltip_text(0, 'Input should not be empty and contain only valid decimal (float) numbers')
            if emitter_id not in self.entries_error:
                self.entries_error.append(Gtk.Buildable.get_name(emitter))
        elif emitter.get_icon_stock(0) == 'gtk-dialog-error':
            emitter.set_icon_from_stock(0, None)
            self.entries_error.remove(emitter_id)

    def on_confirm_exit(self, *args):
        if self.changed:
            response = self.sub_windows['confirm_dialog'].run()
            #   This should be destroy() but for some reason it won't work again once it's called
            self.sub_windows['confirm_dialog'].hide()
            if response == Gtk.ResponseType.YES:
                self.quit()
            elif response == Gtk.ResponseType.NO:
                self.on_save_settings()
                return True
        else:
            self.quit()

    # noinspection PyAttributeOutsideInit
    def on_save_settings(self, *args):
        if self.entries_error:
            self.sub_windows['error_dialog'].run()
            #   This should also be destroy()
            self.sub_windows['error_dialog'].hide()
        else:
            for change in self.changed:
                change_name = split_name_attr(change)[0]
                change_obj = self.builder.get_object(change)
                write_dic(self.us_se, change_name.split('.'), self.on_any_change(change_obj, output=True))
            self.saved_settings = True
            self.quit()


def main(user_settings):
    app = App(user_settings)
    app.run()
