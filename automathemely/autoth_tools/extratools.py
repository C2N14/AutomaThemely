#!/usr/bin/env python3
import json
import os
from pathlib import Path
from subprocess import check_output, CalledProcessError


#   For getting vscode themes
def scan_vscode_extensions(path):
    th = []
    try:
        for k in next(os.walk(path))[1]:
            if 'theme' in k:
                with open(os.path.join(path, k, 'package.json')) as f:
                    data = json.load(f)
                    if 'themes' in data['contributes']:
                        for i in data['contributes']['themes']:
                            if 'id' in i:
                                th.append(i['id'])
                            elif 'label' in i:
                                th.append(i['label'])
    except StopIteration:
        pass
    return th


def get_extra_themes(extra, placeholder=False):
    if extra == 'atom':
        default = dict(themes=[], syntaxes=[])
        if placeholder:
            return default, True
        try:
            atom_packs = check_output('apm list --themes --bare', shell=True).decode('utf-8')
        except CalledProcessError:
            return default, True

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
        return {'themes': sorted(atom_themes), 'syntaxes': sorted(atom_syntaxes)}, False

    if extra == 'vscode':
        default = dict(themes=[])
        if placeholder:
            return default, True

        #   All possible paths that I know of that can contain VSCode extensions
        vscode_extensions_paths = ['/snap/vscode/current/usr/share/code/resources/app/extensions',
                                   '/usr/share/code/resources/app/extensions',
                                   os.path.join(Path.home(), '.vscode/extensions')]
        vscode_themes = []
        for p in vscode_extensions_paths:
            vscode_themes += scan_vscode_extensions(p)

        if not vscode_themes:
            return default, True

        else:
            return {'themes': sorted(vscode_themes)}, False


def set_extra_theme(us_se, extra, theme_type):
    import getpass
    username = getpass.getuser()
    if extra == 'atom':
        import shutil

        target_file = '/home/{}/.atom/config.cson'.format(username)
        if not os.path.isfile(target_file):
            return True

        i = 0
        with open(target_file) as fileIn, open(
                target_file + '.tmp'.format(username), 'w') as fileOut:
            # First look for line with "themes", then go from bottom to top writing lines
            for item in fileIn:
                if i == 1:
                    # Make sure it has the same spaces as the original file
                    item = ' ' * (len(item) - len(item.lstrip(' '))) + '"' \
                           + us_se['extras']['atom']['themes'][theme_type]['syntax'] + '"'
                    i -= 1
                if i == 2:
                    # Make sure it has the same spaces as the original file
                    item = ' ' * (len(item) - len(item.lstrip(' '))) + '"' \
                           + us_se['extras']['atom']['themes'][theme_type]['theme'] + '"'
                    i -= 1
                if item.strip().startswith('themes:'):
                    i = 2

                fileOut.write(item)

        shutil.move(target_file + '.tmp', target_file)

    elif extra == 'vscode':
        target_file = '/home/{}/.config/Code/User/settings.json'.format(username)
        if not os.path.isfile(target_file):
            return True

        with open(target_file) as f:
            p = json.load(f)

        p['workbench.colorTheme'] = us_se['extras']['vscode']['themes'][theme_type]

        with open(target_file, 'w') as f:
            json.dump(p, f, indent=4)
