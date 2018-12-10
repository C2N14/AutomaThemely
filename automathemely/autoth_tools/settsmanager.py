#!/usr/bin/env python3
import gi

gi.require_version('Gtk', '3.0')
# noinspection PyPep8
from gi.repository import Gtk, Gio
# noinspection PyPep8
from automathemely import get_resource, get_local, notify
# noinspection PyPep8
from automathemely.autoth_tools import extratools, envspecific
# noinspection PyPep8
import json


def read_dict(dic, keys):
    for k in keys:
        dic = dic[k]
    return dic


def write_dic(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def split_id_delimiter(obj_id):
    obj_id = obj_id.lstrip('*')
    if '~' in obj_id:
        return obj_id.split('~')
    else:
        return obj_id, None


# Handle unexpected or invalid values in user_settings
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
        elif try_type == bool:
            return False
        else:
            return None


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


# noinspection PyUnusedLocal
def get_object_data(obj, *args):
    if isinstance(obj, Gtk.ComboBoxText):
        return obj.get_active_id()
    elif isinstance(obj, Gtk.Switch):
        return obj.get_active()
    elif isinstance(obj, Gtk.SpinButton):
        return obj.get_value_as_int()
    elif isinstance(obj, Gtk.Entry):
        text = obj.get_text()
        if obj.get_name() == 'float_only' and isfloat(text):
            return float(text)
        else:
            return text


def scan_combobox_descendants(obj, match):
    try:
        children = obj.get_children()
    except AttributeError:
        return
    else:
        if children:
            comboboxes = []
            for child in children:
                scan = scan_combobox_descendants(child, match)
                if scan:
                    comboboxes.extend(scan)
            return comboboxes
        elif isinstance(obj, Gtk.ComboBoxText) and match in Gtk.Buildable.get_name(obj):
            return [obj]


def display_row_separators(row, before):
    if before:
        row.set_header(Gtk.Separator())


########
# This is a kind of weird system, but bear with me...
#
# GTk.Buildable.get_name() gets what is displayed as WIDGET ID in Glade
# obj.get_name() gets what is displayed as WIDGET NAME in Glade
#
# In data containing widgets (ID starts with an *):

# The widget ID is used for widget OUTPUT, i.e. value or PATH it isrelated to in user_settings, if there is a
# delimiter (~) it will also indicate which part of the GUI it affects (its SUBORDINATE), like in enabler switches
#
# The widget NAME is used for special attributes dependant on the type of
# widget, such as if it is float only in entries or what it will be populated with in combo boxes
########

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

        # This does not get initialized until needed
        self.extras = dict()

        self.system_themes = envspecific.get_themes(self.us_se['desktop_environment'])

        self.listen_changes = False
        self.saved_settings = False
        self.entries_error = list()
        self.changed = list()

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

            self.setup_all()
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

    #      MISC
    # Called on primary activation
    def setup_all(self):
        for obj in self.builder.get_objects():
            try:
                obj_id = Gtk.Buildable.get_name(obj)
            except TypeError:
                continue

            # Filter out non-relevant objects
            if '___object_' not in obj_id:

                #   These don't contain data
                if isinstance(obj, Gtk.LinkButton):
                    obj.set_label("HINT: You can get most of this info at https://ipinfo.io/json")

                elif isinstance(obj, Gtk.ListBox):
                    obj.set_header_func(display_row_separators)

                #   These DO contain data
                elif obj_id.startswith('*'):
                    obj_path, obj_sub = split_id_delimiter(obj_id)
                    obj_attr = obj.get_name()
                    keys = obj_path.split('.')
                    val = read_dict(self.us_se, keys)

                    # Has to go before entry because a SpinButton is also an entry...
                    if isinstance(obj, Gtk.SpinButton):
                        obj.configure(Gtk.Adjustment(value=try_or_default_type(val, int), lower=-999, upper=999,
                                                     step_increment=1, page_increment=5, page_size=0), 1, 0)

                    elif isinstance(obj, Gtk.Entry):
                        obj.set_text(try_or_default_type(val, str))

                    elif isinstance(obj, Gtk.Switch):
                        if try_or_default_type(val, bool):
                            obj.set_active(True)
                        else:
                            obj.set_active(False)
                            if obj_sub:
                                self.on_container_toggle(obj)

                    # Most of this method has been moved to populate_themes_boxes
                    elif isinstance(obj, Gtk.ComboBoxText):
                        if obj_attr == 'desk_envs':
                            # Special try or default
                            if not try_or_default_type(val, str):
                                val = 'custom'
                            obj.set_active_id(try_or_default_type(val, str))

    def populate_themes_box(self, box):
        # If box has an active id it has already been populated
        if box.get_active_id():
            return

        box_id = Gtk.Buildable.get_name(box)
        box_path = split_id_delimiter(box_id)[0]
        box_attr = box.get_name()

        val = read_dict(self.us_se, box_path.split('.'))
        themes = []

        if box_id.startswith('*themes'):
            theme_type = box_attr.split('-')[2]

            if not self.system_themes or not theme_type in self.system_themes:
                box.set_sensitive(False)
                return
            else:
                themes = self.system_themes[theme_type]

        elif box_id.startswith('*extras'):
            box_split = box_attr.split('-')
            theme_type = box_split[1]
            extra_type = box_split[2]

            if not theme_type in self.extras[extra_type]:
                box.set_sensitive(False)
            else:
                themes = self.extras[extra_type][theme_type]

        for theme in themes:
            t_name = theme['name']
            if not 'id' in theme:
                t_id = theme['name']
            else:
                t_id = theme['id']
            box.append(t_id, t_name)
        box.set_active_id(try_or_default_type(val, str))

    #       HANDLERS
    # noinspection PyAttributeOutsideInit
    def on_update_deskenv(self, box, *args):
        box_val = box.get_active_id()

        self.system_themes = envspecific.get_themes(box_val)

        revealer = self.builder.get_object('deskenvs_revealer')
        notebooks = self.builder.get_object('deskenvs_box').get_children()

        if box_val == 'custom':
            revealer.set_reveal_child(False)
        else:
            # Populate boxes before displaying
            env_notebook = self.builder.get_object(box_val)
            env_boxes = scan_combobox_descendants(env_notebook, box_val)

            for env_box in env_boxes:
                self.populate_themes_box(env_box)

            revealer.set_reveal_child(True)

            for obj in notebooks:
                if Gtk.Buildable.get_name(obj) == box_val:
                    obj.set_visible(True)
                else:
                    obj.set_visible(False)

    def on_container_toggle(self, switch, *args):
        switch_id = Gtk.Buildable.get_name(switch)
        container = split_id_delimiter(switch_id)[1]
        switch_attr = switch.get_name()

        container_obj = self.builder.get_object(container)

        if switch_attr == 'inverse':
            disable = True
        else:
            disable = False

        if switch.get_active():
            container_obj.set_sensitive(not disable)
        else:
            container_obj.set_sensitive(disable)

    # To reduce start time (specially because some take a long time to setup, looking at you Atom ლ(ಠ益ಠლ)),
    # extras' boxes are populated only if they are enabled to begin with or if they are enabled while it is running
    def on_enable_extra(self, switch, *args):
        if switch.get_active():
            switch_id = Gtk.Buildable.get_name(switch)
            switch_path, container = split_id_delimiter(switch_id)
            extra_type = switch_path.split('.')[1]

            # This is the culprit
            self.extras[extra_type] = extratools.get_extra_themes(extra_type)

            if self.extras[extra_type]:
                extras_boxes = scan_combobox_descendants(self.builder.get_object(container), extra_type)
                for extra_box in extras_boxes:
                    self.populate_themes_box(extra_box)
            else:
                switch.set_active(False)
                switch.set_sensitive(False)
                return

    def on_any_change(self, emitter, *args):
        if self.listen_changes:
            emitter_path = split_id_delimiter(Gtk.Buildable.get_name(emitter))[0]
            if get_object_data(emitter) != read_dict(self.us_se, emitter_path.split('.')):
                if not (emitter in self.changed):
                    self.changed.append(emitter)
            else:
                if emitter in self.changed:
                    self.changed.remove(emitter)

    def on_float_entry_change(self, emitter, *args):
        text = emitter.get_text()
        if text.strip() == '' or not isfloat(text):
            emitter.set_icon_from_stock(0, 'gtk-dialog-error')
            emitter.set_icon_tooltip_text(0, 'Input should not be empty and contain only valid decimal (float) numbers')
            if emitter not in self.entries_error:
                self.entries_error.append(emitter)
        elif emitter.get_icon_stock(0) == 'gtk-dialog-error':
            emitter.set_icon_from_stock(0, None)
            if emitter in self.entries_error:
                self.entries_error.remove(emitter)

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
            for change_obj in self.changed:
                change_path = split_id_delimiter(Gtk.Buildable.get_name(change_obj))[0]
                write_dic(self.us_se, change_path.split('.'), get_object_data(change_obj))
            self.saved_settings = True
            self.quit()

    def tmp(self, obj, *args):
        print(obj.get_active_id())


def main(user_settings):
    app = App(user_settings)
    app.run()
