#!/usr/bin/env python3
import json
from pprint import pprint

from automathemely.autoth_tools import utils


class UserSettings:
    default_settings_dictionary = dict()
    user_settings_dictionary = dict()

    def __init__(self):
        with open(utils.get_resource('default_user_settings.json'), 'r') as f:
            self.default_settings_dictionary = json.load(f)
            self.user_settings_dictionary = self.default_settings_dictionary.copy(
            )

    def load(self,
             file_path=utils.get_local('user_settings.json'),
             merge=True):
        with open(file_path, 'r') as f:
            # Catch bad JSON file
            try:
                settings = json.load(f)
            except json.decoder.JSONDecodeError:
                settings = dict()

        self.user_settings_dictionary = settings
        if merge:
            self.merge_with_default()

    def dump(self, file_path=utils.get_local('user_settings.json')):
        with open(file_path, 'w') as f:
            json.dump(self.user_settings_dictionary, f, indent=4)

    def merge_with_default(self):
        self.user_settings_dictionary = utils.merge_dict(
            self.default_settings_dictionary, self.user_settings_dictionary)

    def get_setting(self, path, pop=False):
        keys_list = [s.strip() for s in path.split('.')]
        print(keys_list)
        return utils.read_dict(self.user_settings_dictionary, keys_list)

    def set_setting(self, path, value):
        keys_list = [s.strip() for s in path.split('.')]
        utils.write_dic(self.user_settings_dictionary, keys_list, value)

    def get_dictionary(self):
        return self.user_settings_dictionary.copy()

    def set_dictionary(self, dictionary):
        self.user_settings_dictionary = utils.merge_dict(
            self.default_settings_dictionary, dictionary)

    def DEV_print(self, dict_type):
        if dict_type == 'default':
            pprint(self.default_settings_dictionary, indent=4)

        elif dict_type == 'user':
            pprint(self.user_settings_dictionary, indent=4)


def main():
    settings = UserSettings()
    settings.load()

    print(settings.get_setting('version.other'))

    settings.DEV_print('user')
