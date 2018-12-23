import argparse
import configparser
import traceback
import sys
import tempfile
from typing import Dict, Any
from os import path, remove

from zulipterminal.core import Controller
from zulipterminal.config.themes import THEMES


def parse_args() -> argparse.Namespace:
    description = '''
        Starts Zulip-Terminal.
        '''
    formatter_class = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=formatter_class)

    parser.add_argument('--config-file', '-c',
                        action='store',
                        help='config file downloaded from your zulip\
                             organization.(e.g. ~/zuliprc)')
    parser.add_argument('--theme', '-t',
                        help='choose color theme. (e.g. blue, light)')
    # debug mode
    parser.add_argument("-d",
                        "--debug",
                        action="store_true",
                        help="Start zulip terminal in debug mode.")

    parser.add_argument('--profile', dest='profile',
                        action="store_true",
                        default=False, help='Profile runtime.')

    args = parser.parse_args()
    return args


def get_api_key(realm_url: str) -> Any:
    from getpass import getpass
    import requests

    email = input("\033[94mEmail:\033[0m ")
    password = getpass("\033[94mPassword:\033[0m ")
    response = requests.post(
        url=realm_url + '/api/v1/fetch_api_key',
        data={
            'username': email,
            'password': password,
        }
    )
    return response, email


def fetch_zuliprc(zuliprc_path: str) -> None:
    realm_url = input("\033[91mzuliprc file was not found"
                      " at " + zuliprc_path + "\033[0m"
                      "\nPlease enter your credentials to login into your"
                      " Zulip organization."
                      "\n\033[94mZulip-Realm URL:\033[0m ")
    if realm_url.startswith("localhost"):
        realm_url = "http://" + realm_url
    elif not realm_url.startswith("http"):
        realm_url = "https://" + realm_url
    # Remove trailing "/"s from realm_url to simplify the below logic
    # for adding "/api"
    realm_url = realm_url.rstrip("/")
    res, email = get_api_key(realm_url)

    while res.status_code != 200:
        print("\n\033[91mUsername or Password Incorrect!\033[0m\n")
        res = get_api_key(realm_url)

    with open(zuliprc_path, 'w') as f:
        f.write('[api]' +
                '\nemail=' + email +
                '\nkey=' + str(res.json()['api_key']) +
                '\nsite=' + realm_url)
    print('Generated API key saved at ' + zuliprc_path)


def parse_zuliprc(zuliprc_str: str) -> Dict[str, Any]:
    zuliprc_path = path.expanduser(zuliprc_str)
    if not path.exists(zuliprc_path):
        try:
            fetch_zuliprc(zuliprc_path)
        except Exception:
            print('\n\033[91mInvalid Credentials, Please try again!\033[0m\n')
            # Remove zuliprc file if created.
            if path.exists(zuliprc_path):
                remove(zuliprc_path)
            parse_zuliprc(zuliprc_str)

    zuliprc = configparser.ConfigParser()
    zuliprc.read(zuliprc_path)

    # default settings
    NO_CONFIG = 'with no config'
    settings = {
        'theme': ('default', NO_CONFIG),
        'autohide': ('autohide', NO_CONFIG),
    }

    if 'zterm' in zuliprc:
        config = zuliprc['zterm']
        ZULIPRC_CONFIG = 'in zuliprc file'
        if 'theme' in config:
            settings['theme'] = (config['theme'], ZULIPRC_CONFIG)
        if 'autohide' in config:
            settings['autohide'] = (config['autohide'], ZULIPRC_CONFIG)

    return settings


def main() -> None:
    """
    Launch Zulip Terminal.
    """

    args = parse_args()

    if args.profile:
        import cProfile
        prof = cProfile.Profile()
        prof.enable()

    if args.config_file:
        zuliprc_path = args.config_file
    else:
        zuliprc_path = '~/zuliprc'

    try:
        zterm = parse_zuliprc(zuliprc_path)

        if args.theme:
            theme_to_use = (args.theme, 'on command line')
        else:
            theme_to_use = zterm['theme']
        valid_themes = THEMES.keys()
        if theme_to_use[0] not in valid_themes:
            print("Invalid theme '{}' was specified {}."
                  .format(*theme_to_use))
            print("The following themes are available:")
            for theme in valid_themes:
                print("  ", theme)
            print("Specify theme in zuliprc file or override "
                  "using -t/--theme options on command line.")
            sys.exit(1)

        valid_autohide_settings = {'autohide', 'no_autohide'}
        if zterm['autohide'][0] not in valid_autohide_settings:
            print("Invalid autohide setting '{}' was specified {}."
                  .format(*zterm['autohide']))
            print("The following options are available:")
            for option in valid_autohide_settings:
                print("  ", option)
            print("Specify the autohide option in zuliprc file.")
            sys.exit(1)
        autohide_setting = (zterm['autohide'][0] == 'autohide')

        print("Loading with:")
        print("   theme '{}' specified {}.".format(*theme_to_use))
        print("   autohide setting '{}' specified {}."
              .format(*zterm['autohide']))
        Controller(zuliprc_path,
                   THEMES[theme_to_use[0]],
                   autohide_setting).main()
    except Exception as e:
        if args.debug:
            # A unexpected exception occurred, open the debugger in debug mode
            import pudb
            pudb.post_mortem()

        sys.stdout.flush()
        traceback.print_exc(file=sys.stderr)
        print("Zulip Terminal has crashed!", file=sys.stderr)
        print("You can ask for help at:", file=sys.stderr)
        print("https://chat.zulip.org/#narrow/stream/206-zulip-terminal",
              file=sys.stderr)
        print("\nThanks for using the Zulip-Terminal interface.\n")
        sys.stderr.flush()

    finally:
        if args.profile:
            prof.disable()
            prof.dump_stats("/tmp/profile.data")
            print("Profile data saved to /tmp/profile.data")
            print("You can visualize it using e.g."
                  "`snakeviz /tmp/profile.data`")

        sys.exit(1)


if __name__ == '__main__':
    main()
