import argparse
import logging
import sys

from gcodeutils.gcoder import GCode
from gcodeutils.stretch.stretch import Slic3rStretchFilter

__author__ = 'olivier'


def main():
    """command line entry point"""
    parser = argparse.ArgumentParser(description='Modify GCode program to account for stretch and improve hole size')

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='Program filename to be modified. Defaults to standard input.')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='Modified program. Defaults to standard output.')

    parser.add_argument('--verbose', '-v', action='count', default=1,
                        help='Verbose mode')
    parser.add_argument('--quiet', '-q', action='count', default=0, help='Quiet mode')

    args = parser.parse_args()

    # count verbose and quiet flags to determine logging level
    args.verbose -= args.quiet

    if args.verbose > 1:
        logging.root.setLevel(logging.DEBUG)
    elif args.verbose > 0:
        logging.root.setLevel(logging.INFO)

    logging.basicConfig(format="%(levelname)s:%(message)s")

    # read original GCode
    gcode = GCode(args.infile.readlines())

    Slic3rStretchFilter(**vars(args)).filter(gcode)

    # write back modified gcode
    gcode.write(args.outfile)


if __name__ == "__main__":
    main()
