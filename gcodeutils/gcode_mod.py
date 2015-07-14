#!/usr/bin/env python
# encoding: utf-8
"""modify gcode program"""
from __future__ import print_function
from __future__ import division

import argparse
import logging
import sys
from gcodeutils.filter.relative_extrusion import GCodeToRelativeExtrusionFilter

from gcodeutils.filter.translate import GCodeXYTranslateFilter

__author__ = 'Olivier Jolly <olivier@pcedev.com>'

from gcoder import GCode  # pylint: disable=relative-import


def main():
    """command line entry point"""
    parser = argparse.ArgumentParser(description='Modify gcode program')
    parser.add_argument('-x', type=float, metavar='amount',
                        help='Move all gcode program by <amount> units in the X axis.')
    parser.add_argument('-y', type=float, metavar='amount',
                        help='Move all gcode program by <amount> units in the Y axis.')

    parser.add_argument('-e', action='count', default=0, help='Convert all extrusion to relative')

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

    if args.x is not None or args.y is not None:
        GCodeXYTranslateFilter(**vars(args)).filter(gcode)

    if args.e:
        GCodeToRelativeExtrusionFilter().filter(gcode)

    # write back modified gcode
    gcode.write(args.outfile)


if __name__ == "__main__":
    main()
