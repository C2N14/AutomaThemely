#!/usr/bin/env python3

from os import walk


class DirectoryFilter:
    """Used for looking for valid themes in the specified directories"""
    def __init__(self, filtering_func, dirs, hardcoded=None):
        self.filtering_func = filtering_func
        self.dirs = dirs
        self.__hardcoded = {} if hardcoded is None else hardcoded

        self.__matches = {}

    def __getitem__(self, name: str) -> list:
        return self.__matches[name]

    def __walk_filter_dirs(self):
        for directory in self.dirs:
            scan = next(walk(directory), None)
            if scan is not None:
                self.__matches[scan[0]] = []
                # append to return_dirs if filtering function returns true
                [
                    self.__matches[scan[0]].append(subdir)
                    for subdir in scan[1]
                    if self.filtering_func(scan[0], subdir)
                ]

        self.__matches.update(self.__hardcoded)

    def __sort_dirs(self):
        for subdir in self.__matches:
            self.__matches[subdir].sort()

    # TODO: Does this need to be a public method calling a private one???
    def refresh_dirs(self):
        self.__walk_filter_dirs()
        self.__sort_dirs()

    def get_all(self, return_parents=False) -> list:
        if return_parents:
            # return self.__matches.items()
            return list(self.__matches.items())
        else:
            return sorted(set().union(*self.__matches.values()))
