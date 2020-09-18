#!/usr/bin/env python3

from collections import Mapping
import json
from pathlib import Path


def merge(orig_dic, upd_dic):
    """Recursively updates a dictionary without deleting its unused keys"""
    for k, v in upd_dic.items():
        if isinstance(v, Mapping):
            merge(orig_dic.get(k, {}), v)
        else:
            orig_dic[k] = v


class SettingsDict(dict):
    "Specialized wrapper class for the dict that holds the user's settings"

    # important to set user_file!!!
    def __init__(self, user_file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__settings_file = user_file

    def __getitem__(self, key, sep='.'):
        """Extends dict functionality to read keys recursivly delimited by a
        separator"""
        dic = super()
        for k in key.split(sep):
            # print(dic)
            dic = dic.__getitem__(k)
        return dic

    def __setitem__(self, key, value, sep='.'):
        """Extends dict functionality to write keys recursivly delimited by a
        separator, if the full path doesn't exist then it will make it"""
        keys = key.split(sep)
        dic = super()
        for k in keys[:-1]:
            dic = dic.setdefault(k, {})
        dic.__setitem__(keys[-1], value)

    def __str__(self):
        """Pretty printing using json.dumps"""
        return json.dumps(dict(self), indent=4)

    def load(self, file=None, merge_dict=True):
        if file is None:
            file = self.__settings_file

        with open(file, 'r') as f:
            if merge_dict:
                merge(self, json.load(f))
            else:
                self.update(json.load(f))

    def dump(self, file=None):
        if file is None:
            file = self.__settings_file

        with open(file, 'w') as f:
            json.dump(dict(self), f, indent=4)


# created with its default parameters
# yapf: disable
setts = SettingsDict(
    user_file=str(Path().home().joinpath('settings.json')), # for testing
    **{
        'desktop_environment': 'custom',
        'themes': {
            'gnome': {
                'light': {
                    'gtk': '',
                    'icons': '',
                    'shell': ''
                },
                'dark': {
                    'gtk': '',
                    'icons': '',
                    'shell': ''
                }
            },
            'kde': {
                'light': {
                    'lookandfeel': '',
                    'gtk': ''
                },
                'dark': {
                    'lookandfeel': '',
                    'gtk': ''
                }
            },
            'xfce': {
                'light': {
                    'gtk': '',
                    'icons': ''
                },
                'dark': {
                    'gtk': '',
                    'icons': ''
                }
            },
            'cinnamon': {
                'light': {
                    'gtk': '',
                    'desktop': '',
                    'icons': ''
                },
                'dark': {
                    'gtk': '',
                    'desktop': '',
                    'icons': ''
                }
            }
        },
        'offset': {
            'sunrise': 0,
            'sunset': 0
        },
        'location': {
            'auto_enabled': True,
            'manual': {
                'city': '',
                'region': '',
                'latitude': 0.0,
                'longitude': 0.0,
                'time_zone': ''
            }
        },
        'misc': {
            'notifications': True
        },
        'extras': {
            'atom': {
                'enabled': False,
                'themes': {
                    'light': {
                        'theme': '',
                        'syntax': ''
                    },
                    'dark': {
                        'theme': '',
                        'syntax': ''
                    }
                }
            },
            'vscode': {
                'enabled': False,
                'themes': {
                    'light': '',
                    'dark': ''
                },
                'custom_config_dir': ''
            },
            'scripts': {
                'sunrise': {
                    '1': '',
                    '2': '',
                    '3': '',
                    '4': '',
                    '5': ''
                },
                'sunset': {
                    '1': '',
                    '2': '',
                    '3': '',
                    '4': '',
                    '5': ''
                }
            }
        }
    }
)
# yapf: enable

setts.load()
