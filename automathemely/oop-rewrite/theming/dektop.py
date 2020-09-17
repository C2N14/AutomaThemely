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

        setattr(gsettings, "gtk-theme", theme)
        # gsettings["gtk-theme"] = theme

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
        setattr(gsettings, 'icon-theme', theme)
        # gsettings['icon-theme'] = theme

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
                                      hardcoded={'default': 'default'})

        # This is WAY out of my level, I'll just let the professionals handle this one...
        import gtweak

        from gtweak.gshellwrapper import GnomeShellFactory
        from gtweak.defs import GSETTINGS_SCHEMA_DIR, LOCALE_DIR
        # This could probably be implemented in house but since we're already
        # importing from gtweak I guess it'll stay this way for now

        gtweak.GSETTINGS_SCHEMA_DIR = GSETTINGS_SCHEMA_DIR
        gtweak.LOCALE_DIR = LOCALE_DIR
        self.shell = GnomeShellFactory().get_shell()
        self.shell_theme_name = 'user-theme@gnome-shell-extensions.gcampax.github.com'
        self.shell_theme_schema = 'org.gnome.shell.extensions.user-theme'
        self.shell_theme_schema_dir = Path(
            # PATH_CONSTANTS['shell-user-extensions']).joinpath(
            'wee woo wee woo').joinpath(self.shell_theme_name, 'schemas')

        if self.shell is None:
            raise ShellNotRunning('GNOME Shell is not running')
        pass

    def set_to(self, theme):
        from gtweak.gsettings import GSettingsSetting

        shell_extensions = self.shell.list_extensions()

        if not self.shell_theme_name in shell_extensions or shell_extensions[
                self.shell_theme_name]['state'] != 1:
            raise ShellExtensionNotValid(
                'GNOME Shell extension not enabled or could not be reached')

        # If shell user-theme was installed locally e. g. through
        # extensions.gnome.org
        if Path(self.shell_theme_schema_dir).is_dir():
            user_shell_settings = GSettingsSetting(
                self.shell_theme_schema,
                schema_dir=str(self.shell_theme_schema_dir))

        # If it was installed as a system extension
        else:
            user_shell_settings = GSettingsSetting(self.shell_theme_schema)

        # To set the default theme you have to input an empty string, but since
        # that won't work with the Setting Manager's ComboBoxes we set it by
        # this placeholder name
        if theme == 'default':
            theme = ''

        # Set the GNOME Shell theme
        user_shell_settings.set_string('name', theme)

    def valid_themes_filter(self, dir, theme):
        return Path(dir).joinpath(
            theme, 'gnome-shell', 'gnome-shell.css').is_file() and \
                theme.lower() != 'default'


# -----------------------
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


# -----------------------
class CinnamonDesktopTheming(DesktopTheming):
    """Theming for Cinnamon Desktop"""
    def __init__(self):
        self.themes = DirectoryFilter(self.valid_themes_filter,
                                      PATH_CONSTANTS['general-themes'],
                                      hardcoded={'default': 'cinnamon'})

    def set_to(self, theme):
        from gi.repository import Gio
        cinnamon_settings = Gio.Settings.new('org.cinnamon.theme')
        setattr(cinnamon_settings, 'name', theme)
        # cinnamon_settings['name'] = theme

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
            self.theming_objects[key].set_to(theme)

    def get_themes(self):
        themes = {}
        for key, theming_object in self.theming_objects.items():
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

        super().__init__()


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
