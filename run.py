#!/usr/bin/env python3
import argparse
import sys

from zulipterminal.core import ZulipController


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

    args = parser.parse_args()
    return args


def main():
    """
    Launch Zulip Terminal.
    """
    args = parse_args()
    if args.debug:
        save_stdout()
    try:
        ZulipController(args.config_file, args.theme).main()
    except Exception:
        # A unexpected exception occurred, open the debugger in debug mode
        if args.debug:
            import pudb
            pudb.post_mortem()
    finally:
        if args.debug:
            restore_stdout()

        print("\nThanks for using the Zulip-Terminal interface.\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
