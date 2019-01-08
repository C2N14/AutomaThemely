
![AutomaThemely icon](automathemely/lib/automathemely_large.svg)

# AutomaThemely

Simple, set-and-forget python application for changing between desktop themes according to light and dark hours

![AutomaThemly Screenshot](https://user-images.githubusercontent.com/29585778/50742182-de28f880-11c4-11e9-8039-4bfd20426a21.png)


## Current supported desktop environments

Right now, these desktop environments are supported natively:

* GNOME and other GNOME based or similar such as Unity
* KDE Plasma
* XFCE
* Cinnamon

Additionally, wether your DE is listed above or not, you can also create and add your own scripts.

Thus you can add support it even if not listed above (although if you'd like to see it integrated in a later version you can always make a suggestion by [oppening an issue](https://github.com/C2N14/AutomaThemely/issues)).

## Getting Started

### Prerequisites

* Python 3.5+
* GTK 3.10+
* pip3 (will be installed if package with dependencies is installed, otherwise it must be manually installed. More details below)

### Installing

#### Releases

Go to [releases](https://github.com/C2N14/AutomaThemely/releases) and download whichever package suits your needs

Because of the several python versions different distros have, and the current state and limitations of the packager used, here are my recommendations for the following distros:

| Distro | Recommendation |
| --- | --- |
| Ubuntu 16.04 | Manually install all the python dependencies with pip3 and install the python 3.5 no dependencies package |
| Ubuntu 18.04 | Just install the regular python 3.6 package and all the dependencies should be available |
| Other distros | Check your python version, and if it is equal or above 3.5 but not listed in the releases page you can try [packaging it yourself](https://github.com/C2N14/AutomaThemely/wiki/Packaging-it-yourself)

#### Packages

Some distros, however, may have their own maintainers:

| Distro | Package name/Link |
| --- | --- |
| Arch Linux | [`automathemely`](https://aur.archlinux.org/packages/automathemely/)

### Running

Once installed, either run the settings manager by clicking normally on the icon or through the terminal and configure as needed:

```bash
automathemely --manage
```

Or you can run once without any parameters to generate a settings file and manually edit the file in `/home/USER/.config/automathemely`

You can also tweak any setting you want with the help of `--list` and `--setting`:

```bash
# To show all the available options
automathemely --list
# For example:
automathemely --setting desktop_environment=gnome
automathemely --setting themes.gnome.light.gtk=Adwaita
```

Finally, you can either log out and back in or start the scheduler manually:

```bash
# (Re)start the scheduler
automathemely --restart
```

And that's it!


In the case of it failing to do its job (please report on [issues](https://github.com/C2N14/AutomaThemely/issues)) you can always try to restart the scheduler or run it manually to try to fix it by running `automathemely` or right clicking the icon and selecting "Run AutomaThemely"

## Notes

* This program assumes that a day in your location has both sunrise and sunset in the same 0 to 24 hr day span, and if you decide to set a custom time offset make sure both of these events still occur within this span
* This program requires an active internet connection **ONLY** if you set *Auto Location* on (it uses your ip to determine your geolocation), otherwise you can manually set your location and you won't need it.
* Currently to switch GNOME Shell themes, GNOME Tweaks and the GNOME User Themes extension have to be installed and enabled
* Tested with (Ku/Xu/U)buntu 18.04 & Ubuntu 16.04
* Yeah, yeah, I know that icon is an eyesore but I'm no designer so it'll have to do until a better one is made ¯\\\_(ツ)_/¯
* **For more detailed info, refer to the [FAQ](https://github.com/C2N14/AutomaThemely/wiki/FAQ)**

## License

This project is licensed under the GPLv3 License - see [LICENSE](LICENSE) for details
