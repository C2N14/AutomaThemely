import os
from pathlib import Path

_ROOT = os.path.abspath(os.path.dirname(__file__))
__version__ = 1.0


def get_resource(path=''):
    return os.path.join(_ROOT, 'lib', path)


def get_bin(path=''):
    return os.path.join(_ROOT, 'bin', path)


def get_local(path=''):
    return os.path.join(str(Path.home()), '.config/AutomaThemely', path)


def get_root(path=''):
    return os.path.join(_ROOT, path)
