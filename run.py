#!/usr/bin/env python3
import argparse
import configparser
import sys
from os import environ, path

from zulipterminal.core import Controller


def save_stdout():
    """Save shell screen."""
    sys.stdout.write("\033[?1049h\033[H")


def restore_stdout():
    """Restore saved shell screen."""
    sys.stdout.write("\033[?1049l")


def parse_args():
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


def parse_zuliprc(zuliprc_str):
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


def main():
    """
    Launch Zulip Terminal.
    """
    args = parse_args()
    if args.config_file:
        zuliprc_path = args.config_file
    else:
        zuliprc_path = '~/zuliprc'

    zterm = parse_zuliprc(zuliprc_path)

    if args.debug:
        save_stdout()
    if args.profile:
        import cProfile
        prof = cProfile.Profile()
        prof.enable()

    try:
        Controller(zuliprc_path, zterm['theme']).main()
    except Exception:
        # A unexpected exception occurred, open the debugger in debug mode
        if args.debug:
            import pudb
            pudb.post_mortem()
    finally:
        if args.debug:
            restore_stdout()

        if args.profile:
            prof.disable()
            prof.dump_stats("/tmp/profile.data")
            print("Profile data saved to /tmp/profile.data")
            print("You can visualize it using e.g."
                  "`snakeviz /tmp/profile.data`")

        print("\nThanks for using the Zulip-Terminal interface.\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
