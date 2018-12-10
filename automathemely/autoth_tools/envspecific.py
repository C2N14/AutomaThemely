# from automathemely import get_resource

#   Old code to get GNOME GTK Themes

# def get_installed_themes():
#     themes = []
#     # All paths that I know of that can contain GTK themes
#     gtk_paths = [
#         '/usr/share/themes/',
#         os.path.join(str(Path.home()), '.themes/'),
#         os.path.join(str(Path.home()), '.local/share/themes/')
#     ]
#     for directory in gtk_paths:
#         t = [d.replace(directory, '').replace('/', '') for d in glob('{}*/'.format(directory))]
#         themes += t
#     themes.sort()
#     return themes


# TODO: Find out how to get these such as the function above
def get_themes(desk_env):
    if desk_env == 'gnome':
        # return a dictionary with: {'gtk': [], 'icons': [], 'shell': []} or None
        pass

    elif desk_env == 'kde':
        # return a dictionary with: {'plasma': [], 'icons': []} or None
        pass

    elif desk_env == 'xfce':
        # return a dictionary with: {'gtk': [], 'icons': []} or None
        pass

    elif desk_env == 'cinnamon':
        # return a dictionary with: {'gtk': [], 'desktop': [], 'icons': []} or None
        pass

    elif desk_env == 'custom':
        return

    else:
        raise Exception('Invalid Desktop Environment "{}"'.format(desk_env))


# TODO: Find out how to set these such as how it currently works in run.py
def set_theme(desk_env, t_type, theme):
    if desk_env == 'gnome':
        if t_type == 'gtk':
            pass

        elif t_type == 'icons':
            pass

        elif t_type == 'shell':
            pass

    elif desk_env == 'kde':
        if t_type == 'plasma':
            pass

        elif t_type == 'icons':
            pass

    elif desk_env == 'xfce':
        if t_type == 'gtk':
            pass

        elif t_type == 'icons':
            pass

    else:
        raise Exception('Invalid Desktop Environment "{}"'.format(desk_env))
