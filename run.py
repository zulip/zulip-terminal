#!/usr/bin/env python3
import argparse
import sys

from display import ZulipController

def parse_args():
    description = '''
        Starts Zulip-Terminal.
        '''

    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--config-file', '-c',
                        action='store',
                        help='config file downloaded from your zulip organization.(e.g. ~/zuliprc)')

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    try:
        ZulipController(args.config_file).main()
    except KeyboardInterrupt:
        print("\nThanks for using the Zulip-Terminal interface.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
