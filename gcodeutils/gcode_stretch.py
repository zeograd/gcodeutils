import argparse
import logging
import sys

from gcodeutils.filter.relative_extrusion import GCodeToRelativeExtrusionFilter
from gcodeutils.gcoder import GCode
from gcodeutils.stretch.stretch import Slic3rStretchFilter, CuraStretchFilter

__author__ = 'olivier'


def is_cura_gcode(gcode):  # pylint: disable=redefined-outer-name
    """Detect cura generated gcode by looking for the profile string"""
    for layer in gcode.all_layers:
        for opcode in layer:
            if 'CURA_PROFILE_STRING' in opcode.raw:
                return True
    return False


def main():
    """command line entry point"""
    parser = argparse.ArgumentParser(description='Modify GCode program to account for stretch and improve hole size')

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='Program filename to be modified. Defaults to standard input.')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='Modified program. Defaults to standard output.')

    parser.add_argument('--cross_limit_distance_over_edge_width', type=float, default=5.0,
                        help='Distance after and before a point where moves are considered to determine the local '
                             'normal. Defaults to %(default)s. Set too low or too high, it might cause points no to be '
                             'moved in the right direction.')
    parser.add_argument('--stretch_from_distance_over_edge_width', type=float, default=2.0,
                        help='Distance after and before a point where moves are considered to determine the local '
                             'normal. Defaults to %(default)s. Set too low or too high, it might cause points no to be '
                             'moved in the right direction.')

    parser.add_argument('--loop_stretch_over_edge_width', type=float, default=0.11,
                        help='Stretching strength for "loop" (extra shells), defaults to %(default)s')
    parser.add_argument('--edge_inside_stretch_over_edge_width', type=float, default=0.32,
                        help='Stretching strength for "inner perimeter", defaults to %(default)s')
    parser.add_argument('--edge_outside_stretch_over_edge_width', type=float, default=0.1,
                        help='Stretching strength for "outer perimeter", defaults to %(default)s')

    parser.add_argument('--stretch_strength', type=float, default=1.0,
                        help='Stretching stretch factor. This is the first setting you\'ll want to change to '
                             'modify the hole size')

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
    gcode = GCode(args.infile.readlines())  # pylint: disable=redefined-outer-name

    # First convert to relative extrusion
    GCodeToRelativeExtrusionFilter().filter(gcode)

    # Then perform the stretching
    if is_cura_gcode(gcode):
        CuraStretchFilter(**vars(args)).filter(gcode)
    else:
        Slic3rStretchFilter(**vars(args)).filter(gcode)

    # write back modified gcode
    gcode.write(args.outfile)


if __name__ == "__main__":
    main()
