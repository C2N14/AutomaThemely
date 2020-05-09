#!/usr/bin/env python3
import gi

gi.require_version('Gtk', '3.0')

# noinspection PyPep8
from gi.repository import Gtk, Gio
# noinspection PyPep8
from automathemely.autoth_tools.utils import get_resource, get_local, read_dict, write_dic
# noinspection PyPep8
from automathemely.autoth_tools import extratools, envspecific
# noinspection PyPep8
import json

# noinspection PyPep8
import logging
logger = logging.getLogger(__name__)


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
        return obj.get_active_id() if obj.get_active_id() != 'none' else ''
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


def scan_comboboxtext_descendants(obj, match):
    try:
        children = obj.get_children()
    except AttributeError:
        return
    else:
        if children:
            comboboxtexts = []
            for child in children:
                scan = scan_comboboxtext_descendants(child, match)
                if scan:
                    comboboxtexts.extend(scan)
            return comboboxtexts
        elif isinstance(obj, Gtk.ComboBoxText) and match in Gtk.Buildable.get_name(obj):
            return [obj]


def display_row_separators(row, before):
    # This was added in GTK 3.14, but since it really doesn't make much of a difference and is purely aesthetic, and
    # prevents it from running on GTK 3.10 lets just set this when it is possible but not enforce it
    # noinspection PyBroadException
    try:
        row.set_activatable(False)
        row.set_selectable(False)
    except:
        pass

    if before:
        row.set_header(Gtk.Separator())


def get_last_visible_row(max_number_of_rows, listbox_id, builder):
    for i in range(max_number_of_rows, 1, -1):
        entry = builder.get_object('{}.{}'.format(listbox_id, str(i)))
        row = entry.get_parent().get_parent()

        if row.get_visible():
            return i

    return 1


########
# This is a kind of weird system, but bear with me...
#
# GTk.Buildable.get_name() gets what is displayed as WIDGET ID in Glade
# obj.get_name() gets what is displayed as WIDGET NAME in Glade
#
# In data containing widgets (ID starts with an *):

# The widget ID is used for widget OUTPUT, i.e. value or PATH it is related to in user_settings, if there is a
# delimiter (~) it will also indicate which part of the GUI it affects (its SUBORDINATE), like in enabler Switches
#
# The widget NAME is used for special attributes dependant on the type of
# widget, such as if it is float only in Entries or what it will be populated with in ComboBoxTexts
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

        self.system_themes = envspecific.get_installed_themes(self.us_se['desktop_environment'])

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

        logger.info(exit_message)

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
                        if val is None and keys[-1] == "background":
                            # try to load current background from system settings
                            if self.system_themes and "background" in self.system_themes:
                                val = self.system_themes["background"]

                        obj.set_text(try_or_default_type(val, str))

                    elif isinstance(obj, Gtk.Switch):
                        if try_or_default_type(val, bool):
                            obj.set_active(True)
                        else:
                            obj.set_active(False)
                            if obj_sub:
                                self.on_container_toggle(obj)

                    # Most of this method has been moved to populate_themes_cboxts
                    elif isinstance(obj, Gtk.ComboBoxText):
                        if obj_attr == 'desk_envs':
                            # Special try or default
                            if not try_or_default_type(val, str):
                                val = 'custom'
                            obj.set_active_id(try_or_default_type(val, str))

        # Hardcoded setup scripts listboxes after their entries have already been setup
        scripts_listboxes = ['scripts_sunrise_listbox', 'scripts_sunset_listbox']
        for listbox in scripts_listboxes:
            listbox_type = listbox.split('_')[1]

            for i in range(5, 1, -1):
                entry = self.builder.get_object('*extras.scripts.{}.{}'.format(listbox_type, str(i)))
                entry_text = entry.get_text()

                if entry_text:
                    break
                else:
                    listbox_row = entry.get_parent().get_parent()
                    listbox_row.set_visible(False)

        # Artificially call function when pages are switched to enable or disable addrow_button according to row limit
        self.on_change_scripts_page()

    def populate_themes_cboxt(self, cboxt):
        # If ComboBoxText has an active id it has already been populated
        if cboxt.get_active_id():
            return

        cboxt_id = Gtk.Buildable.get_name(cboxt)
        cboxt_path = split_id_delimiter(cboxt_id)[0]
        cboxt_attr = cboxt.get_name()

        val = read_dict(self.us_se, cboxt_path.split('.'))
        themes = []

        if cboxt_id.startswith('*themes'):
            theme_type = cboxt_attr.split('-')[2]

            if not self.system_themes or theme_type not in self.system_themes:
                tmp = cboxt.get_children()
                cboxt.set_sensitive(False)
                return
            else:
                themes = self.system_themes[theme_type]

        elif cboxt_id.startswith('*extras'):
            cboxt_split = cboxt_attr.split('-')
            theme_type = cboxt_split[1]
            extra_type = cboxt_split[2]

            if theme_type not in self.extras[extra_type]:
                cboxt.set_sensitive(False)
            else:
                themes = self.extras[extra_type][theme_type]

        for theme in themes:
            t_id = theme[0]
            if len(theme) > 1:
                t_name = theme[1]
            else:
                t_name = t_id[0].upper() + t_id[1:]
            cboxt.append(t_id, t_name)

        active_id = try_or_default_type(val, str)
        if active_id:
            cboxt.set_active_id(active_id)
        else:
            # So it doesn't continue populating repeated options on non-set CBoxTs
            cboxt.set_active_id('none')

    #       HANDLERS
    # noinspection PyAttributeOutsideInit
    def on_update_deskenv(self, cboxt, *args):
        cboxt_val = cboxt.get_active_id()

        self.system_themes = envspecific.get_installed_themes(cboxt_val)

        revealer = self.builder.get_object('deskenvs_revealer')
        notebooks = self.builder.get_object('deskenvs_box').get_children()

        if cboxt_val == 'custom':
            revealer.set_reveal_child(False)
        else:
            # Populate CBoxTs before displaying
            env_notebook = self.builder.get_object(cboxt_val)
            env_cboxts = scan_comboboxtext_descendants(env_notebook, cboxt_val)

            for env_box in env_cboxts:
                self.populate_themes_cboxt(env_box)

            revealer.set_reveal_child(True)

            for obj in notebooks:
                if Gtk.Buildable.get_name(obj) == cboxt_val:
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
    # extras' CBoxTs are populated only if they are enabled to begin with or if they are enabled while it is running
    def on_enable_extra(self, switch, *args):
        if switch.get_active():
            switch_id = Gtk.Buildable.get_name(switch)
            switch_path, container = split_id_delimiter(switch_id)
            extra_type = switch_path.split('.')[1]

            # This is the culprit
            self.extras[extra_type] = extratools.get_installed_extra_themes(extra_type)

            if self.extras[extra_type]:
                extras_cboxts = scan_comboboxtext_descendants(self.builder.get_object(container), extra_type)
                for extra_cboxt in extras_cboxts:
                    self.populate_themes_cboxt(extra_cboxt)
            else:
                switch.set_active(False)
                switch.set_sensitive(False)
                return

    # These three functions related to scripts are kinda not great, and will probably change a lot in future revisions
    # because they were mostly an afterthought
    def on_remove_scripts_row(self, button, *args):
        button_id = Gtk.Buildable.get_name(button)
        sub_entry = split_id_delimiter(button_id)[1]
        listbox_type = sub_entry.split('.')[2]
        row_number = int(sub_entry.split('.')[-1])

        max_number_of_rows = 5
        last_row = get_last_visible_row(max_number_of_rows, '*extras.scripts.{}'.format(listbox_type), self.builder)

        if row_number == last_row:
            entry = self.builder.get_object('*extras.scripts.{}.{}'.format(listbox_type, str(row_number)))
            entry.set_text('')

            if row_number > 1:
                row = entry.get_parent().get_parent()
                row.set_visible(False)

        else:
            for i in range(row_number, last_row):
                origin_entry = self.builder.get_object('*extras.scripts.{}.{}'.format(listbox_type, str(i + 1)))
                origin_row = origin_entry.get_parent().get_parent()
                destination_entry = self.builder.get_object('*extras.scripts.{}.{}'.format(listbox_type, str(i)))

                destination_entry.set_text(origin_entry.get_text())

                if i + 1 == last_row:
                    origin_entry.set_text('')
                    origin_row.set_visible(False)

        add_button = self.builder.get_object('rowadd_button')
        add_button.set_sensitive(True)

    def on_bg_choose_file(self, button, *args):
        button_id = Gtk.Buildable.get_name(button)
        sub_entry = split_id_delimiter(button_id)[1]
        open_dialog = Gtk.FileChooserDialog("Pick a background", None,
                                            Gtk.FileChooserAction.OPEN,
                                           (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                            Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT))
        # extract current text in textbox
        entry = self.builder.get_object(sub_entry)
        cur_filename = entry.get_text()
        # set it as the default chosen file in dialog
        open_dialog.set_file(Gio.File.new_for_path(cur_filename))
        
        open_dialog.set_local_only(True)
        open_dialog.set_modal(True)
        open_dialog.connect("response", self.open_response_cb, sub_entry)
        open_dialog.show()

    def open_response_cb(self, dialog, response_id, data):
        entry = self.builder.get_object(data)

        # chosen file
        if response_id == Gtk.ResponseType.ACCEPT:
            entry.set_text(dialog.get_filename())

        # clears it
        elif response_id == Gtk.ResponseType.CANCEL:
            entry.set_text("")

        dialog.destroy()

    def on_add_scripts_row(self, button, *args):
        active_listbox_page = self.builder.get_object('scripts_notebook').get_current_page()

        if active_listbox_page == 0:
            listbox_type = 'sunrise'
        else:
            listbox_type = 'sunset'

        max_number_of_rows = 5
        last_row = get_last_visible_row(max_number_of_rows, '*extras.scripts.{}'.format(listbox_type), self.builder)

        next_row = self.builder.get_object('*extras.scripts.{}.{}'.format(listbox_type, str(last_row + 1))) \
            .get_parent().get_parent()

        next_row.set_visible(True)

        if last_row + 1 == max_number_of_rows:
            button.set_sensitive(False)

    def on_change_scripts_page(self, notebook=None, *args):
        if notebook:
            active_listbox_page = notebook.get_current_page()

            # Get the opposite tab, because signal is emitted before switching
            if active_listbox_page == 0:
                listbox_type = 'sunset'
            else:
                listbox_type = 'sunrise'

        # If called from setup the statement above does not hold
        else:
            listbox_type = 'sunrise'

        max_number_of_rows = 5
        last_row = get_last_visible_row(max_number_of_rows, '*extras.scripts.{}'.format(listbox_type), self.builder)

        add_button = self.builder.get_object('rowadd_button')
        if last_row == max_number_of_rows:
            add_button.set_sensitive(False)
        else:
            add_button.set_sensitive(True)

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
        if not text.strip() or not isfloat(text):
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


def main(user_settings):
    app = App(user_settings)
    app.run()
