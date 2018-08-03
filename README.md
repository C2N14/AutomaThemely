
![AutomaThemely icon](automathemely/lib/automathemely_large.svg)

# AutomaThemely

Simple, set-and-forget python application for changing between GNOME themes according to light and dark hours

## Getting Started

### Prerequisites

* Obviously having the GNOME desktop environment
* Python 3.5+
* GTK 3.0+
* pip3 (will be installed if package with dependencies is installed, otherwise it must be manually installed)

### Installing

You can go to [releases](https://github.com/C2N14/AutomaThemely/releases) and download whichever package suits your needs

Because of the several python versions different distros have, here are my recommendations for the following distros:

| Distro | Recommendation |
| --- | --- |
| Ubuntu 16.04 | Manually install all the python dependencies with pip3 and install the python 3.5 no dependencies package |
| Ubuntu 18.04 | Just install the regular python 3.6 package and all the dependencies should be available |
| Other distros | Check your python version, and if it is equal or above 3.5 but not listed in the releases page you can try [packaging it yourself](https://github.com/C2N14/AutomaThemely/wiki/Packaging-it-yourself)

### Running

Once installed, run once to generate a settings file

```bash
automathemely
```

And then run again with `-m` or `--manage` use the settings manager (requires GTK 3.0+)

```bash
automathemely --manage
```

Or manually set the settings with `-s` or `--setting` if you somehow don't have GTK in your system

```bash
# To show all the available options
automathemely --list
# For example:
automathemely --setting themes.light=Adwaita
```

Or you can even manually edit the configuration file in `/home/user/.config/AutomaThemely`

Finally, you can either restart your computer or run the following to make sure it runs at the right hours and also start the scheduler so it starts working

```bash
# Update sunrise and sunset times
automathemely --update
# Start the scheduler
automathemely --restart
```

And that's it!

### Running it manually

In the case of it failing to do its job (please report to [issues](https://github.com/C2N14/AutomaThemely/issues)) you can always try to restart the scheduler or run it manually to try to fix it by running `automathemely` or by the icon on the application tray

## Notes

* This program assumes that a day in your location has both sunrise and sunset in the same 0 to 24 hr day span, and if you decide to set a custom time offset make sure both of these events still occur within this span
* Although it is specifically made for GNOME, it should be compatible with Unity and other GNOME based environments.
* This program requires an active internet connection **ONLY** if you set *Auto Location* on (it uses your ip to determine your geolocation), otherwise you can manually set your location and you won't need it.
* Tested with Ubuntu 18.04 & Ubuntu 16.04
* Yeah, yeah, I know that icon is an eyesore but I'm no designer so it'll have to do until a better one is made ¯\\\_(ツ)_/¯

## License

This project is licensed under the GPLv3 License - see [LICENSE](LICENSE) for details
