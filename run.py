#!/usr/bin/env python3
import argparse
import sys

from core import ZulipController

def parse_args():
    description = '''
        Starts Zulip-Terminal.
        '''

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--config-file', '-c',
                        action='store',
                        help='config file downloaded from your zulip organization.(e.g. ~/zuliprc)')
    parser.add_argument('--theme','-t',
                        default='default',
                        help='choose color theme. (e.g. blue,light)')

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    try:
        ZulipController(args.config_file, args.theme).main()
    except KeyboardInterrupt:
        print("\nThanks for using the Zulip-Terminal interface.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
