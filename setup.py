import os

from setuptools import setup

from automathemely import __version__ as version


def get_package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


with open('README.md') as fh:
    long_description = fh.read()

setup(
    name='AutomaThemely',
    version=version,
    description='Simple, set-and-forget python application for changing between GNOME themes according to light and '
                'dark hours',
    long_description=long_description,
    author='Adrian Salgado',
    author_email='adriansalmar@gmail.com',
    url='https://github.com/C2N14/AutomaThemely',
    license='GPLv3',
    packages=['automathemely', 'automathemely.bin', 'automathemely.autoth_tools'],
    python_requires='>=3.5',
    install_requires=['requests', 'astral', 'pytz', 'tzlocal', 'schedule'],
    include_package_data=True,
    package_data={
        'automathemely': get_package_files('automathemely/lib') + ['../automathemely/bin/systemd-trigger.sh']
                         + ['../automathemely/bin/kde-refresh-gtk2']},
    data_files=[
        ('share/icons/hicolor/scalable/apps', ['automathemely/lib/automathemely.svg']),
        ('share/applications', ['automathemely/lib/automathemely.desktop'])
    ],
    entry_points={
        'console_scripts': [
            'automathemely=automathemely.bin.run:main'
        ],
    },
)
