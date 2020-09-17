#!/usr/bin/env python3


class Theming:
    """Theming SUPER base class"""

    themes = None

    def set_to(self, theme):
        raise NotImplementedError

    def get_installed(self):
        return NotImplementedError
