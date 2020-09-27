#!/usr/bin/env python3

from collections import Mapping
import json
from pathlib import Path

BOOL_DICT = {
    'true': True,
    't': True,
    '1': True,
    'false': False,
    'f': False,
    '0': False,
}


def merge(orig_dic, upd_dic):
    """Recursively updates a dictionary without deleting its unused keys"""
    for k, v in upd_dic.items():
        if isinstance(v, Mapping):
            merge(orig_dic.get(k, {}), v)
        else:
            orig_dic[k] = v


def to_bool(value):
    """Converts a possible string or int representation of a bool into a bool"""
    try:
        return BOOL_DICT[str(value).lower()]
    except KeyError as e:
        raise TypeError(f'Can\'t convert {value} to bool') from e


class SettingsDict(dict):
    "Specialized wrapper class for the dict that holds the user's settings"

    def __init__(self, user_file, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__settings_file = user_file

    def __getitem__(self, key, sep='.'):
        """Extends dict functionality to read keys recursivly delimited by a
        separator"""
        dic = super()
        for k in key.split(sep):
            dic = dic.__getitem__(k)
        return dic

    def __setitem__(self, key, value, sep='.'):
        """Extends dict functionality to write keys recursivly delimited by a
        separator, if the full path doesn't exist then it will make it\n
        It keeps the original type by raising a TypeError exception if a
        conversion can't be made\n
        This also has the nice side effect that when an immutable is set this
        way, a copy of it is made and saved internally so it isn't referenced"""

        keys = key.split(sep)
        dic = super()
        for k in keys[:-1]:
            dic = dic.setdefault(k, {})

        last_key = keys[-1]
        # if the value doesn't exist, don't care for it's type
        type_ = type(dic.get(last_key, value))
        # prevent chaging types
        if type_ == bool and not isinstance(value, bool):
            dic.__setitem__(last_key, to_bool(value))
        else:
            dic.__setitem__(last_key, type_(value))

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
        'desktop_environment': str('custom'),
        'themes': {
            'gnome': {
                'light': {
                    'gtk': str(),
                    'icons': str(),
                    'shell': str()
                },
                'dark': {
                    'gtk': str(),
                    'icons': str(),
                    'shell': str()
                }
            },
            'kde': {
                'light': {
                    'lookandfeel': str(),
                    'gtk': str()
                },
                'dark': {
                    'lookandfeel': str(),
                    'gtk': str()
                }
            },
            'xfce': {
                'light': {
                    'gtk': str(),
                    'icons': str()
                },
                'dark': {
                    'gtk': str(),
                    'icons': str()
                }
            },
            'cinnamon': {
                'light': {
                    'gtk': str(),
                    'desktop': str(),
                    'icons': str()
                },
                'dark': {
                    'gtk': str(),
                    'desktop': str(),
                    'icons': str()
                }
            }
        },
        'offset': {
            'sunrise': int(0),
            'sunset': int(0)
        },
        'location': {
            'auto_enabled': bool(True),
            'manual': {
                'city': str(),
                'region': str(),
                'latitude': float(0.0),
                'longitude': float(0.0),
                'time_zone': str()
            }
        },
        'misc': {
            'notifications': bool(True)
        },
        'extras': {
            'atom': {
                'enabled': bool(False),
                'themes': {
                    'light': {
                        'theme': str(),
                        'syntax': str()
                    },
                    'dark': {
                        'theme': str(),
                        'syntax': str()
                    }
                }
            },
            'vscode': {
                'enabled': bool(False),
                'themes': {
                    'light': str(),
                    'dark': str()
                },
                'custom_config_dir': str()
            },
            'scripts': {
                'sunrise': {
                    '1': str(),
                    '2': str(),
                    '3': str(),
                    '4': str(),
                    '5': str()
                },
                'sunset': {
                    '1': str(),
                    '2': str(),
                    '3': str(),
                    '4': str(),
                    '5': str()
                }
            }
        }
    }
)
# yapf: enable

setts.load()
