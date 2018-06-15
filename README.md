
![](automathemely/lib/automathemely_large.svg)

# AutomaThemely

Simple, set-and-forget python application for changing between GNOME themes according to light and dark hours

## Getting Started

### Prerequisites

* Obviously having the GNOME desktop environment (or maybe not, see [notes](#notes) for more info)
* Python 3.5+
* Crontab
* GTK+ 3.0+ (optional, for the settings manager GUI)
* Pip3 (optional, for installation)

### Installing

You can go to [releases](https://github.com/C2N14/AutomaThemely/releases) and download whichever package suits your needs

Or install it through snapcraft (Not yet, TODO)

```
snap install automathemely --classic
```

Or even clone the project and install it yourself (icons and shortcuts will not be installed)

```
git clone https://github.com/C2N14/AutomaThemely.git
cd AutomaThemely
python3 setup.py install
```

### Running

Once installed, run once to generate a settings file

```
automathemely
```

And then run again with `-m` or `--manager` use the settings manager (requires GTK)

```
automathemely --manage
```

Or manually set the settings with `-s` or `--setting` if you somehow don't have GTK in your system

```
# To show all the available options
automathemely --list
# For example:
automathemely --setting themes.light=Adwaita
```

Or you can even manually edit the configuration file in `/home/user/.config/AutomaThemely`

Finally, update all the necessary crontabs to make sure it runs at the right hours

```
automathemely --update
```

And that's it! You don't have to worry about touching anything anymore.

## Notes

* Although it is specifically made for GNOME, it should be compatible with Unity, and other desktop environments could easily be implemented.
* This program requires an active internet connection **ONLY** if you set *Auto Location* on (it uses your ip to determine your geolocation), otherwise you can manually set your location and you won't need it.
* You should never really manually edit the version number on the configuration file because it will most likely be overwritten 
* Tested with Ubuntu 17.10 & Ubuntu 16.04
* Yeah, yeah, I know that icon is an eyesore but I'm no designer so it'll have to do until a better one is made ¯\\\_(ツ)_/¯

## License

This project is licensed under the GPLv3 License - see [LICENSE](LICENSE) for details
