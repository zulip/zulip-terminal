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
                        help='choose color theme. (e.g. light)')

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    try:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        ZulipController(args.config_file, args.theme).main()
=======
        ZulipController(args.config_file,args.theme).main()
>>>>>>> 01e2011... Add Light theme
=======
        ZulipController(args.config_file, args.theme).main()
>>>>>>> bebe8c1... Final Commit
=======
        ZulipController(args.config_file,args.theme).main()
>>>>>>> 01e2011... Add Light theme
=======
        ZulipController(args.config_file, args.theme).main()
>>>>>>> c3f004d... Update with a space
    except KeyboardInterrupt:
        print("\nThanks for using the Zulip-Terminal interface.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
