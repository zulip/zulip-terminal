import argparse
import configparser
import traceback
import sys
from typing import Dict, Any
from os import path

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


def parse_zuliprc(zuliprc_str: str) -> Dict[str, Any]:
    zuliprc_path = path.expanduser(zuliprc_str)
    if not path.exists(zuliprc_path):
        sys.exit("Error: Cannot find {}".format(zuliprc_path))

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
