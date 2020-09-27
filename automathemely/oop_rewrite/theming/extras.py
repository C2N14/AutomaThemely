#!/usr/bin/env python3

from pathlib import Path
from os import walk
import json
from subprocess import check_output
from . import Theming

# TODO: Figure this out
from ...autoth_tools.settsmanager import settings


class ExtraTheming(Theming):
    """Theming for external applications"""
    pass


class InvalidVscodeDirError(Exception):
    """Exception for an invalid VSCode config directory"""
    pass


class VscodeTheming(ExtraTheming):
    """Theming for Visual Studio Code"""

    # All possible paths that I know of that can contain VSCode extensions
    extension_paths = (
        '/snap/vscode/current/usr/share/code/resources/app/extensions',
        '/usr/share/code/resources/app/extensions',
        str(Path.home().joinpath('.vscode',
                                 'extensions')), '/usr/lib/extensions',
        '/opt/visual-studio-code/resources/app/extensions')

    def __init__(self):
        self.themes = {}

    def set_to(self,
               theme,
               custom_settings_path=settings.get_setting(
                   'extras.vscode.custom_config_dir')):
        target_dir = Path.home().joinpath('.config', 'Code', 'User')

        if custom_settings_path:
            target_dir = Path(custom_settings_path)

        if not target_dir.is_dir():
            raise InvalidVscodeDirError(str(target_dir))

        target_file = target_dir.joinpath('settings.json')

        # Sometimes the file is not present until the user changes a setting
        if target_file.is_file():
            with target_file.open() as f:
                data = json.load(f)
        else:
            data = dict()

        data['workbench.colorTheme'] = theme

        with target_file.open(mode='w') as f:
            json.dump(data, f, indent=4)

    def get_installed(self):
        self.themes['themes'] = []
        for dir in self.extension_paths:
            scan = next(walk(dir), None)
            if scan is not None:
                with Path(scan[1]).joinpath('package.json').open() as f:
                    data = json.load(f)
                    for i in data['contributes']['themes']:
                        if 'id' in i:
                            self.themes['themes'].append(i['id'])
                        elif 'label' in i:
                            self.themes['themes'].append(i['label'])

        self.themes['themes'].sort()

        return self.themes


class InvalidAtomConfigError(Exception):
    """Exception for an invalid Atom config file"""
    pass


class AtomTheming(ExtraTheming):
    """Theming for the Atom editor"""
    def __init__(self):
        self.themes = {}

    def set_to(self, themes):
        import sys
        import fileinput

        target_file = Path().home().joinpath('.atom', 'config.cson')
        if not target_file.is_file():
            raise InvalidAtomConfigError(str(target_file))

        lines_below_keyword = 0
        for line in fileinput.input(str(target_file), inplace=True):
            # First look for line with the keyword "themes", then write lines
            if line.strip().startswith('themes:'):
                sys.stdout.write(line)
                lines_below_keyword += 1

            elif 1 <= lines_below_keyword <= 2:
                # Make sure it has the same preceding spaces as the original
                pre_number = (len(line) - len(line.lstrip(' ')))
                print('{space}"{theme}"'.format(
                    space=' ' * pre_number,
                    theme=themes['general' if lines_below_keyword ==
                                 1 else 'syntax']))

                lines_below_keyword += 1

            else:
                sys.stdout.write(line)

    def get_installed(self):
        from subprocess import check_output

        out = check_output('apm list --themes --bare',
                           shell=True).decode('utf-8')
        packs = [val.split('@')[0] for i, val in enumerate(out.split('\n'))]

        self.themes['syntax'], self.themes['general'] = [], []
        for p in packs:
            self.themes['syntax' if 'syntax' in p else 'general'].append(p)

        return self.themes
