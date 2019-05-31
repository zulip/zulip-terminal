import argparse
import configparser
import traceback
import sys
import logging
import requests
from typing import Dict, Any, List, Optional, Tuple
from os import path, remove

from urwid import set_encoding

from zulipterminal.core import Controller
from zulipterminal.model import ServerConnectionFailure
from zulipterminal.config.themes import (
    THEMES, all_themes, complete_and_incomplete_themes
)
from zulipterminal.version import ZT_VERSION

LOG_FILENAME = 'zulip-terminal-tracebacks.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


def in_color(color: str, text: str) -> str:
    color_for_str = {
        'red': '1',
        'green': '2',
        'yellow': '3',
        'blue': '4',
        'purple': '5',
        'cyan': '6',
    }
    # We can use 3 instead of 9 if high-contrast is eg. less compatible?
    return "\033[9{}m{}\033[0m".format(color_for_str[color], text)


def parse_args(argv: List[str]) -> argparse.Namespace:
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

    parser.add_argument('-v',
                        '--version',
                        action='store_true',
                        default=False,
                        help='Print zulip-terminal version and exit')

    return parser.parse_args(argv)


def get_api_key(realm_url: str) -> Tuple[requests.Response, str]:
    from getpass import getpass

    email = input(in_color('blue', "Email: "))
    password = getpass(in_color('blue', "Password: "))
    response = requests.post(
        url=realm_url + '/api/v1/fetch_api_key',
        data={
            'username': email,
            'password': password,
        }
    )
    return response, email


def fetch_zuliprc(zuliprc_path: str) -> None:
    realm_url = input(in_color('red', "zuliprc file was not found at " +
                                      zuliprc_path) +
                      "\nPlease enter your credentials to login into your"
                      " Zulip organization."
                      "\n" +
                      "\nNOTE: The " + in_color('blue', "Zulip URL") +
                      " is where you would go in a "
                      "web browser to log in to Zulip." +
                      "\nIt often looks like one of the following:" +
                      in_color('green', "\n   your-org.zulipchat.com") +
                      " (Zulip-hosted servers)" +
                      in_color('green', "\n   zulip.your-org.com") +
                      " (self-hosted servers)" +
                      in_color('green', "\n   chat.zulip.org") +
                      " (the Zulip community server)"
                      "\n" +
                      in_color('blue', "Zulip URL: "))
    if realm_url.startswith("localhost"):
        realm_url = "http://" + realm_url
    elif not realm_url.startswith("http"):
        realm_url = "https://" + realm_url
    # Remove trailing "/"s from realm_url to simplify the below logic
    # for adding "/api"
    realm_url = realm_url.rstrip("/")
    res, email = get_api_key(realm_url)

    while res.status_code != 200:
        print(in_color('red', "\nUsername or Password Incorrect!\n"))
        res, email = get_api_key(realm_url)

    with open(zuliprc_path, 'w') as f:
        f.write('[api]' +
                '\nemail=' + email +
                '\nkey=' + str(res.json()['api_key']) +
                '\nsite=' + realm_url)
    print('Generated API key saved at ' + zuliprc_path)


def parse_zuliprc(zuliprc_str: str) -> Dict[str, Any]:
    zuliprc_path = path.expanduser(zuliprc_str)
    while not path.exists(zuliprc_path):
        try:
            fetch_zuliprc(zuliprc_path)
        # Invalid user inputs (e.g. pressing arrow keys) may cause ValueError
        except (OSError, ValueError):
            # Remove zuliprc file if created.
            if path.exists(zuliprc_path):
                remove(zuliprc_path)
            print(in_color('red',
                           "\nInvalid Credentials, Please try again!\n"))
        except EOFError:
            # Assume that the user pressed Ctrl+D and continue the loop
            print("\n")

    zuliprc = configparser.ConfigParser()

    try:
        res = zuliprc.read(zuliprc_path)
        if len(res) == 0:
            print(in_color('red',
                           "\nZuliprc file could not be accessed at " +
                           zuliprc_path + "\n"))
            sys.exit(1)
    except configparser.MissingSectionHeaderError:
        print(in_color('red',
                       "\nFailed to parse zuliprc file at " +
                       zuliprc_path + "\n"))
        sys.exit(1)

    # default settings
    NO_CONFIG = 'with no config'
    settings = {
        'theme': ('default', NO_CONFIG),
        'autohide': ('no_autohide', NO_CONFIG),
    }

    if 'zterm' in zuliprc:
        config = zuliprc['zterm']
        ZULIPRC_CONFIG = 'in zuliprc file'
        if 'theme' in config:
            settings['theme'] = (config['theme'], ZULIPRC_CONFIG)
        if 'autohide' in config:
            settings['autohide'] = (config['autohide'], ZULIPRC_CONFIG)

    return settings


def main(options: Optional[List[str]]=None) -> None:
    """
    Launch Zulip Terminal.
    """

    argv = options if options is not None else sys.argv[1:]
    args = parse_args(argv)

    set_encoding('utf-8')

    if args.profile:
        import cProfile
        prof = cProfile.Profile()
        prof.enable()

    if args.version:
        print('Zulip Terminal ' + ZT_VERSION)
        sys.exit(0)

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
        available_themes = all_themes()
        if theme_to_use[0] not in available_themes:
            print("Invalid theme '{}' was specified {}."
                  .format(*theme_to_use))
            print("The following themes are available:")
            for theme in available_themes:
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
        complete, incomplete = complete_and_incomplete_themes()
        if theme_to_use[0] in incomplete:
            print(in_color('yellow',
                           "   WARNING: Incomplete theme; "
                           "results may vary!\n"
                           "      (you could try: {})".
                           format(", ".join(complete))))
        print("   autohide setting '{}' specified {}."
              .format(*zterm['autohide']))
        Controller(zuliprc_path,
                   THEMES[theme_to_use[0]],
                   autohide_setting).main()
    except ServerConnectionFailure as e:
        print(in_color('red',
                       "\nError connecting to Zulip server: {}.".format(e)))
        # Acts as separator between logs
        logging.info("\n\n" + str(e) + "\n\n")
        logging.exception(e)
        sys.exit(1)
    except Exception as e:
        logging.info("\n\n" + str(e) + "\n\n")
        logging.exception(e)
        if args.debug:
            sys.stdout.flush()
            traceback.print_exc(file=sys.stderr)
            run_debugger = input("Run Debugger? (y/n): ")
            if run_debugger in ["y", "Y", "yes"]:
                # Open PUDB Debuuger
                import pudb
                pudb.post_mortem()

        if hasattr(e, 'extra_info'):
            print("\n" + in_color("red", e.extra_info),    # type: ignore
                  file=sys.stderr)

        print(in_color("red", "\nZulip Terminal has crashed!"
                       "\nPlease refer to " + LOG_FILENAME + " for full log of"
                       " the error."), file=sys.stderr)
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
