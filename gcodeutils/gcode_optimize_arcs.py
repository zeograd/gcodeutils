import argparse
import logging
import sys

from gcodeutils.filter.relative_extrusion import GCodeToRelativeExtrusionFilter
from gcodeutils.gcoder import GCode
from gcodeutils.filter.arc_optimizer import GCodeArcOptimizerFilter

__author__ = 'Eyck Jentzsch <eyck@jepemuc.de>'


def main():
    """command line entry point"""
    parser = argparse.ArgumentParser(description='Modify GCode program to account arcs and replace the G1 with G2/G3')

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='Program filename to be modified. Defaults to standard input.')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='Modified program. Defaults to standard output.')
    parser.add_argument('--inplace', action='store_true', help='Modify file inplace')

    parser.add_argument('--verbose', '-v', action='count', default=1, help='Verbose mode')
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
    gcode = GCode(args.infile.readlines())  # pylint: disable=redefined-outer-name

    # First convert to relative extrusion
    # GCodeToRelativeExtrusionFilter().filter(gcode)

    # Then perform the stretching
    GCodeArcOptimizerFilter().filter(gcode)

    # write back modified gcode
    gcode.write(args.outfile if args.inplace is True else args.outfile)


if __name__ == "__main__":
    main()
