import argparse
import configparser
import traceback
import sys
import tempfile
from typing import Dict, Any
from os import path, remove

from zulipterminal.core import Controller


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
                        default='default',
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
    if not realm_url.startswith('https://'):
        realm_url = 'https://' + realm_url
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
    settings = {'theme': 'default'}

    if 'zterm' in zuliprc:
        if 'theme' in zuliprc['zterm']:
            settings['theme'] = zuliprc['zterm']['theme']

    return settings


def main() -> None:
    """
    Launch Zulip Terminal.
    """

    args = parse_args()
    if args.config_file:
        zuliprc_path = args.config_file
    else:
        zuliprc_path = '~/zuliprc'

    zterm = parse_zuliprc(zuliprc_path)

    if args.profile:
        import cProfile
        prof = cProfile.Profile()
        prof.enable()

    try:
        Controller(zuliprc_path, zterm['theme']).main()
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
