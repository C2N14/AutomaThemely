#!/usr/bin/env python3

import gi
# gi.require_version('Gtk', '3.0')

from pathlib import Path

# TODO: Figure this out
from ..utils import DirectoryFilter
from . import Theming

# ===============================
HOME = Path.home()
PATH_CONSTANTS = {
    'general-themes': ( \
        '/usr/share/themes/', \
        str(HOME.joinpath('.local/share/themes/')), \
        str(HOME.joinpath('.themes/')) \
    ),
    'icons-themes': ( \
        '/usr/share/icons/', \
        str(HOME.joinpath('.local/share/icons/')), \
        str(HOME.joinpath('.icons/')) \
    ),
    'lookandfeel-themes': ( \
        '/usr/share/plasma/look-and-feel/', \
        str(HOME.joinpath('.local/share/plasma/look-and-feel/')) \
    ),
    'shell-user-extensions': \
        str(HOME.joinpath('.local/share/gnome-shell/extensions/')),
    'kde-gtk-config': {
        'gtk3': str(HOME.joinpath('.config/gtk-3.0/settings.ini')),
        'gtk2': str(HOME.joinpath('.gtkrc-2.0'))
    },
}

# ===============================


class DesktopTheming(Theming):
    """Generic desktop theming"""
    def valid_themes_filter(self, dir, theme):
        raise NotImplementedError

    def get_installed(self):
        if self.themes is None:
            raise NotImplementedError

        self.themes.refresh_dirs()
        return self.themes.get_all()


# -----------------------
class GtkTheming(DesktopTheming):
    """Generic theming for GTK"""
    def __init__(self):
        self.gsettings_string = 'org.gnome.desktop.interface'
        self.themes = DirectoryFilter(self.valid_themes_filter,
                                      PATH_CONSTANTS['general-themes'])

    def set_to(self, theme):
        from gi.repository import Gio

        gsettings = Gio.Settings.new(self.gsettings_string)
        gsettings["gtk-theme"] = theme  # type: ignore

    def valid_themes_filter(self, dir, theme):
        return Path(dir).joinpath(theme).glob('gtk-3.*/gtk.css') and \
            theme.lower() != 'default'


# exactly the same
class GnomelikeGtkTheming(GtkTheming):
    """Theming for GNOME-like GTK"""
    pass


# slight difference
class CinnamonGtkTheming(GtkTheming):
    """Theming for Cinnamon GTK"""
    def __init__(self):
        super().__init__()

        self.gsettings_string = 'org.cinnamon.desktop.interface'


# way different
class XfceGtkTheming(GtkTheming):
    """Theming for XFCE GTK"""
    def set_to(self, theme):

        # not sure if you need to do this, but we'll do it anyway
        super().set_to(theme)

        from subprocess import run
        run([
            'xfconf-query', '-c', 'xsettings', '-p', '/Net/ThemeName', '-s',
            theme
        ])


class KdeGtkTheming(GtkTheming):
    """Theming for KDE GTK"""
    def set_to(self, theme):
        super().set_to(theme)

        # Extra code for KDE
        #TODO: Fill this


# -----------------------
class GtkIconsTheming(DesktopTheming):
    """Generic theming for GTK Icons"""
    def __init__(self):
        self.gsettings_string = 'org.gnome.desktop.interface'
        self.themes = DirectoryFilter(self.valid_themes_filter,
                                      PATH_CONSTANTS['icons-themes'])

    def set_to(self, theme):
        from gi.repository import Gio

        gsettings = Gio.Settings.new(self.gsettings_string)
        gsettings['icon-theme'] = theme  # type: ignore

    def valid_themes_filter(self, dir, theme):
        return Path(dir).joinpath(theme, 'index.theme') and \
            theme.lower() != 'default'


class GnomelikeGtkIconsTheming(GtkIconsTheming):
    """Theming for GNOME-like GTK Icons"""
    pass


class CinnamonGtkIconsTheming(GtkIconsTheming):
    """Theming for Cinnamon GTK Icons"""
    def __init__(self):
        super().__init__()

        self.gsettings_string = 'org.cinnamon.desktop.interface'


class XfceGtkIconsTheming(GtkIconsTheming):
    """Theming for XFCE GTK Icons"""
    def set_to(self, theme):
        super().set_to(theme)

        from subprocess import run

        run([
            'xfconf-query', '-c', 'xsettings', '-p', '/Net/IconThemeName',
            '-s', theme
        ])


# -----------------------
class ShellNotRunning(Exception):
    """Exception for when the GNOME Shell is not running"""
    pass


class ShellExtensionNotValid(Exception):
    """Exception for when the shell extension cannot be reached, either because
    it is not enabled or because it is in an invalid state"""
    pass


class GnomeShellTheming(DesktopTheming):
    """Theming for GNOME Shell"""
    def __init__(self):

        self.themes = DirectoryFilter(self.valid_themes_filter,
                                      PATH_CONSTANTS['general-themes'],
                                      hardcoded={'default': ['Default']})

        # This is WAY out of my level, I'll just let the professionals handle this one...
        import gtweak

        from gtweak.gshellwrapper import GnomeShellFactory
        from gtweak.defs import GSETTINGS_SCHEMA_DIR, LOCALE_DIR
        # This could probably be implemented in house but since we're already
        # importing from gtweak I guess it'll stay this way for now

        gtweak.GSETTINGS_SCHEMA_DIR = GSETTINGS_SCHEMA_DIR
        gtweak.LOCALE_DIR = LOCALE_DIR
        self.shell = GnomeShellFactory().get_shell()
        self.shell_ext_name = 'user-theme@gnome-shell-extensions.gcampax.github.com'
        self.shell_ext_schema = 'org.gnome.shell.extensions.user-theme'
        self.shell_ext_schema_dir = Path(
            PATH_CONSTANTS['shell-user-extensions']).joinpath(
                self.shell_ext_name, 'schemas')

        if self.shell is None:
            raise ShellNotRunning('GNOME Shell is not running')
        pass

    def set_to(self, theme):
        from gtweak.gsettings import GSettingsSetting

        shell_extensions = self.shell.list_extensions()

        if not self.shell_ext_name in shell_extensions or shell_extensions[
                self.shell_ext_name]['state'] != 1:
            raise ShellExtensionNotValid(
                'GNOME Shell extension not enabled or could not be reached')

        # If shell user-theme was installed locally e. g. through
        # extensions.gnome.org
        if Path(self.shell_ext_schema_dir).is_dir():
            user_shell_settings = GSettingsSetting(
                self.shell_ext_schema,
                schema_dir=str(self.shell_ext_schema_dir))

        # If it was installed as a system extension
        else:
            user_shell_settings = GSettingsSetting(self.shell_ext_schema)

        # Set the GNOME Shell theme
        # To set the default theme you have to input an empty string, but since
        # that won't work with the Setting Manager's ComboBoxes we set it by
        # this placeholder name
        user_shell_settings.set_string('name',
                                       '' if theme == 'default' else theme)

    def valid_themes_filter(self, dir, theme):
        return Path(dir).joinpath(
            theme, 'gnome-shell', 'gnome-shell.css').is_file() and \
                theme.lower() != 'default'


# -----------------------
# another messy class...
class LookAndFeelTheming(DesktopTheming):
    """Theming for KDE Look-and-Feel"""
    def __init__(self):
        self.themes = DirectoryFilter(self.valid_themes_filter,
                                      PATH_CONSTANTS['lookandfeel-themes'])

    def set_to(self, theme):
        from subprocess import run

        run(['lookandfeeltool', '-a', '{}'.format(theme)], check=True)

    def valid_themes_filter(self, dir, theme):
        return Path(dir).joinpath(theme, 'metadata.desktop').is_file() or \
               Path(dir).joinpath(theme, 'metadata.json').is_file()

    def get_installed(self):
        import configparser, json

        real_themes = []

        # prioritize .desktop  over .json just like systemsettings
        self.themes.refresh_dirs()
        # this is pretty much the only place where return_parents is used
        for parent, theme_dir in self.themes.get_all(return_parents=True):
            target_dir = Path(parent).joinpath(theme_dir)
            if target_dir.joinpath('metadata.desktop').is_file():
                metadata = configparser.ConfigParser(strict=False)
                metadata.read(str(target_dir.joinpath('metadata.desktop')))
                real_themes.append(metadata['Desktop Entry']['Name'])

            # has to be JSON because it was already filtered before
            else:
                with target_dir.joinpath('metadata.json').open() as f:
                    real_themes.append(json.load(f)['KPlugin']['Name'])

        return real_themes


# -----------------------
class CinnamonDesktopTheming(DesktopTheming):
    """Theming for Cinnamon Desktop"""
    def __init__(self):
        self.themes = DirectoryFilter(self.valid_themes_filter,
                                      PATH_CONSTANTS['general-themes'],
                                      hardcoded={'default': ['Cinnamon']})

    def set_to(self, theme):
        from gi.repository import Gio

        cinnamon_settings = Gio.Settings.new('org.cinnamon.theme')
        cinnamon_settings['name'] = theme  # type: ignore

    def valid_themes_filter(self, dir, theme):
        return Path(dir).joinpath(theme, 'cinnamon').is_dir()


# ==================================================


class InvalidThemingError(NotImplementedError):
    """Exception for when an invalid theming is passed to the environment"""
    pass


class Environment:
    """Environment SUPER base class"""
    theming_classes = None

    def __init__(self):
        if self.theming_classes is None:
            raise NotImplementedError

        # initialize all the objects
        self.theming_objects = {}
        for key, theming_class in self.theming_classes.items():
            self.theming_objects[key] = theming_class()

    def set_themes(self, themes):
        for key, theme in themes.items():
            if key not in self.theming_objects:
                raise InvalidThemingError(key)

            # TODO: Maybe log this somewhere?
            if self.theming_objects[key] is not None:
                self.theming_objects[key].set_to(theme)

    def get_themes(self):
        themes = {}
        for key, theming_object in self.theming_objects.items():
            if theming_object is None:
                themes[key] = None
            else:
                themes[key] = theming_object.get_installed()

        return themes


class GnomelikeEnvironment(Environment):
    """"GNOME-like Environment class"""
    def __init__(self):
        self.theming_classes = {
            'gtk': GnomelikeGtkTheming,
            'icons': GnomelikeGtkIconsTheming,
            'shell': GnomeShellTheming
        }

        try:
            super().__init__()
        except ModuleNotFoundError as e:
            if str(e) == 'No module named \'gtweak\'':
                self.theming_objects['shell'] = None
            else:
                raise ModuleNotFoundError(e)


class KdeEnvironment(Environment):
    """"KDE Environment class"""
    def __init__(self):
        self.theming_classes = {
            'lookandfeel': LookAndFeelTheming,
            'gtk': KdeGtkTheming,
        }

        super().__init__()


class XfceEnvironment(Environment):
    """"XFCE Environment class"""
    def __init__(self):
        self.theming_classes = {
            'gtk': XfceGtkTheming,
            'icons': XfceGtkIconsTheming
        }

        super().__init__()


class CinnamonEnvironment(Environment):
    """"Cinnamon Environment class"""
    def __init__(self):
        self.theming_classes = {
            'gtk': CinnamonGtkTheming,
            'icons': CinnamonGtkIconsTheming,
            'desktop': CinnamonDesktopTheming
        }

        super().__init__()


class InvalidEnvironmentError(InvalidThemingError):
    """Exception for when an invalid environment is passed to the environment
    factory"""
    pass


class EnvironmentFactory:
    """Environment Factory class"""
    # all the supported desktop environments
    environment_classes = {
        'gnome': GnomelikeEnvironment,
        'kde': KdeEnvironment,
        'xfce': XfceEnvironment,
        'cinnamon': CinnamonEnvironment
    }

    def create(self, environment):
        if environment not in self.environment_classes:
            raise InvalidEnvironmentError(environment)
        return self.environment_classes[environment]()
