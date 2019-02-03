#!/usr/bin/env python3
import json
import os
from pathlib import Path
from subprocess import check_output, CalledProcessError

import logging
logger = logging.getLogger(__name__)


#   For getting vscode themes
def scan_vscode_extensions(path):
    t_list = []
    try:
        for k in next(os.walk(path))[1]:
            with Path(path).joinpath(k, 'package.json').open() as f:
                data = json.load(f)
                if 'themes' in data['contributes']:
                    for i in data['contributes']['themes']:
                        if 'id' in i:
                            t_list.append(i['id'])
                        elif 'label' in i:
                            t_list.append(i['label'])
    except StopIteration:
        pass

    list.sort(t_list)
    themes = []
    for name in t_list:
        themes.append((name,))
    return themes


# Should be delayed and avoided as much as possible...
def get_installed_extra_themes(extra):
    if extra == 'atom':
        try:
            atom_packs = check_output('apm list --themes --bare', shell=True).decode('utf-8')
        except CalledProcessError:
            return

        atom_packs = atom_packs.split('\n')
        for i, v in enumerate(atom_packs):
            atom_packs[i] = v.split('@')[0]
        atom_packs = list(filter(None, atom_packs))
        list.sort(atom_packs)
        themes = []
        syntaxes = []
        for v in atom_packs:
            if 'syntax' in v:
                syntaxes.append((v,))
            else:
                themes.append((v,))
        return {'themes': themes, 'syntaxes': syntaxes}

    if extra == 'vscode':

        # All possible paths that I know of that can contain VSCode extensions
        vscode_extensions_paths = ['/snap/vscode/current/usr/share/code/resources/app/extensions',
                                   '/usr/share/code/resources/app/extensions',
                                   str(Path.home().joinpath('.vscode', 'extensions'))]
        vscode_themes = []
        for p in vscode_extensions_paths:
            vscode_themes += scan_vscode_extensions(p)

        if not vscode_themes:
            return

        else:
            return {'themes': vscode_themes}


def set_extra_theme(us_se, extra, theme_type):
    import fileinput
    import sys
    if extra == 'atom':

        target_file = Path.home().joinpath('.atom', 'config.cson')
        if not target_file.is_file():
            logger.error('Atom config file not found')
            return

        lines_below_keyword = 0
        for line in fileinput.input(str(target_file), inplace=True):
            # First look for line with the keyword "themes", then write lines
            if line.strip().startswith('themes:'):
                sys.stdout.write(line)
                lines_below_keyword += 1

            elif lines_below_keyword == 1:
                # Make sure it has the same spaces as the original file
                preceding_spaces = ' ' * (len(line) - len(line.lstrip(' ')))
                print(preceding_spaces + '"' + us_se['extras']['atom']['themes'][theme_type]['theme'] + '"')
                lines_below_keyword += 1

            elif lines_below_keyword == 2:
                # Make sure it has the same spaces as the original file
                preceding_spaces = ' ' * (len(line) - len(line.lstrip(' ')))
                print(preceding_spaces + '"' + us_se['extras']['atom']['themes'][theme_type]['syntax'] + '"')
                lines_below_keyword += 1

            else:
                sys.stdout.write(line)

    elif extra == 'vscode':
        target_file = Path.home().joinpath('.config', 'Code', 'User', 'settings.json')
        if not target_file.parent.is_dir():
            logger.error('VSCode config directory not found')
            return

        # Sometimes the settings file is not present until the user changes a setting
        if target_file.is_file():
            with target_file.open() as f:
                p = json.load(f)
        else:
            p = dict()

        p['workbench.colorTheme'] = us_se['extras']['vscode']['themes'][theme_type]

        with target_file.open(mode='w') as f:
            json.dump(p, f, indent=4)


def run_scripts(scripts, notifications_enabled):
    from automathemely import notifier_handler
    from subprocess import run

    # Temporarily remove notifier handler to not spam user of failed scripts
    logging.getLogger().removeHandler(notifier_handler)

    error_message = None
    for n, script in scripts.items():
        if not script:
            continue
        elif not Path(script).is_file():
            logger.error('Script file {} not found'.format(n))
            error_message = 'One or more of the script files was/were not found'
        else:
            try:
                run([script], check=True)
            except Exception as e:
                logger.exception('Error while running {}'.format(script), exc_info=e)
                error_message = 'One or more of the script files failed to run'

    # Add it back
    if notifications_enabled:
        logging.getLogger().addHandler(notifier_handler)

    if error_message:
        logger.warning(error_message)
