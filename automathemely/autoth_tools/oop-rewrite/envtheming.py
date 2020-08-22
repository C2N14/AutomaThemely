#!/usr/bin/env python3

# TODO: Uncomment this
# import gi

from pathlib import Path


# Theming SUPER base class
class Theming:
    def set_to(self, theme):
        raise NotImplementedError

    def get_installed(self):
        raise NotImplementedError


# Generic desktop theming
class DesktopTheming(Theming):
    pass


# -----------------------
# GTK Theming
class GtkTheming(DesktopTheming):
    def __init__(self):
        self.gsettings_string = 'org.gnome.desktop.interface'

    def set_to(self, theme):
        # TODO: Uncomment this
        # from gi.repository import Gio

        # gsettings = Gio.Settings.new(self.gsettings_string)

        # gsettings['gtk-theme'] = theme
        pass

    # def get_installed(self):
    #     pass


# exactly the same
class GnomelikeGtkTheming(GtkTheming):
    pass


# slight difference
class CinnamonGtkTheming(GtkTheming):
    def __init__(self):
        super().__init__()

        self.gsettings_string = 'org.cinnamon.desktop.interface'


# way different
class XfceGtkTheming(GtkTheming):
    def set_to(self, theme):

        # not sure if you need to do this, but we'll do it anyway
        super().set_to(theme)

        from subprocess import run
        run([
            'xfconf-query', '-c', 'xsettings', '-p', '/Net/ThemeName', '-s',
            theme
        ])


class KdeGtkTheming(GtkTheming):
    def set_to(self, theme):
        super().set_to(theme)

        # Extra code for KDE
        #TODO: Fill this


# -----------------------
# GTK Icons Theming
class GtkIconsTheming(DesktopTheming):
    def __init__(self):
        self.gsettings_string = 'org.gnome.desktop.interface'

    def set_to(self, theme):
        # TODO: Uncomment this
        # from gi.repository import Gio

        # gsettings = Gio.Settings.new(self.gsettings_string)
        # gsettings['icon-theme'] = theme
        pass


class GnomelikeGtkIconsTheming(GtkIconsTheming):
    pass


class CinnamonGtkIconsTheming(GtkIconsTheming):
    def __init__(self):
        super().__init__()

        self.gsettings_string = 'org.cinnamon.desktop.interface'


class XfceGtkIconsTheming(GtkIconsTheming):
    def set_to(self, theme):
        super().set_to(theme)

        from subprocess import run, CalledProcessError

        run([
            'xfconf-query', '-c', 'xsettings', '-p', '/Net/IconThemeName',
            '-s', theme
        ])


# -----------------------
# GNOME Shell Theming
class ShellNotRunning(Exception):
    """Ëxception for when the GNOME Shell is not running"""
    pass


class ShellExtensionNotValid(Exception):
    """Exception for when the shell extension cannot be reached, either because
    it is not enabled or because it is in an invalid state"""
    pass


class GnomeShellTheming(DesktopTheming):
    def __init__(self):
        # This is WAY out of my level, I'll just let the professionals handle this one...
        # import gtweak

        # from gtweak.gshellwrapper import GnomeShellFactory
        # from gtweak.defs import GSETTINGS_SCHEMA_DIR, LOCALE_DIR
        # # This could probably be implemented in house but since we're already importing from gtweak I guess it'll stay
        # # this way for now

        # gtweak.GSETTINGS_SCHEMA_DIR = GSETTINGS_SCHEMA_DIR
        # gtweak.LOCALE_DIR = LOCALE_DIR
        # self.shell = GnomeShellFactory().get_shell()
        # self.shell_theme_name = 'user-theme@gnome-shell-extensions.gcampax.github.com'
        # self.shell_theme_schema = 'org.gnome.shell.extensions.user-theme'
        # self.shell_theme_schema_dir = Path(
        #     # PATH_CONSTANTS['shell-user-extensions']).joinpath(
        #     'wee woo wee woo').joinpath(self.shell_theme_name, 'schemas')

        # if self.shell is None:
        #     raise ShellNotRunning('GNOME Shell is not running')
        pass

    def set_to(self, theme):
        # from gtweak.gsettings import GSettingsSetting

        # shell_extensions = self.shell.list_extensions()

        # if not self.shell_theme_name in shell_extensions or shell_extensions[
        #         self.shell_theme_name]['state'] != 1:
        #     raise ShellExtensionNotValid(
        #         'GNOME Shell extension not enabled or could not be reached')

        # # If shell user-theme was installed locally e. g. through extensions.gnome.org
        # if Path(self.shell_theme_schema_dir).is_dir():
        #     user_shell_settings = GSettingsSetting(
        #         self.shell_theme_schema,
        #         schema_dir=str(self.shell_theme_schema_dir))

        # # If it was installed as a system extension
        # else:
        #     user_shell_settings = GSettingsSetting(self.shell_theme_schema)

        # # To set the default theme you have to input an empty string, but since that won't work with the
        # # Setting Manager's ComboBoxes we set it by this placeholder name
        # if theme == 'default':
        #     theme = ''

        # # Set the GNOME Shell theme
        # user_shell_settings.set_string('name', theme)
        pass


# -----------------------
# KDE Look and Feel Theming
class LookAndFeelTheming(DesktopTheming):
    def set_to(self, theme):
        # from subprocess import run

        # run(['lookandfeeltool', '-a', '{}'.format(theme)], check=True)
        pass


# -----------------------
# Cinnamon Desktop Theming
class CinnamonDesktopTheming(DesktopTheming):
    def set_to(self, theme):
        # from gi.repository import Gio
        # cinnamon_settings = Gio.Settings.new('org.cinnamon.theme')
        # cinnamon_settings['name'] = theme
        pass


# ==================================================


class InvalidThemingError(NotImplementedError):
    """Exception for when an invalid theming is passed to the environment"""
    pass


# Environment SUPER base class
class Environment:
    theming_classes = {}

    def __init__(self):
        if not self.theming_classes:
            raise NotImplementedError

        # initialize all the objects
        self.theming_objects = {}
        for key, theming_class in self.theming_classes.items():
            self.theming_objects[key] = theming_class()

    def set_themes(self, themes):
        for key, theme in themes.items():
            if key not in self.theming_objects:
                raise InvalidThemingError(key, )
            self.theming_objects[key].set_to(theme)

    def get_themes(self):
        themes = {}
        for key, theming_object in self.theming_objects.items():
            if key not in themes:
                raise InvalidThemingError(key)
            themes[key] = theming_object.get_installed()

        return themes


class GnomelikeEnvironment(Environment):
    def __init__(self):
        self.theming_classes = {
            'gtk': GnomelikeGtkTheming,
            'icons': GnomelikeGtkIconsTheming,
            'shell': GnomeShellTheming
        }

        super().__init__()


class KdeEnvironment(Environment):
    def __init__(self):
        self.theming_classes = {
            'lookandfeel': LookAndFeelTheming,
            'gtk': KdeGtkTheming,
        }

        super().__init__()


class XfceEnvironment(Environment):
    def __init__(self):
        self.theming_classes = {
            'gtk': XfceGtkTheming,
            'icons': XfceGtkIconsTheming
        }

        super().__init__()


class CinnamonEnvironment(Environment):
    def __init__(self):
        self.theming_classes = {
            'gtk': CinnamonGtkTheming,
            'icons': CinnamonGtkIconsTheming,
            'desktop': CinnamonDesktopTheming
        }

        super().__init__()


class InvalidEnvironmentError(NotImplementedError):
    """Exception for when an invalid environment is passed to the environment
    factory"""
    pass


class EnvironmentFactory:
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
