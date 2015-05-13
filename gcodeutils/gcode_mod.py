#!/usr/bin/env python
# encoding: utf-8
"""modify gcode program"""
from __future__ import print_function
from __future__ import division

import argparse
import logging
import sys

from gcodeutils.gcoder import move_gcodes, split, unsplit


__author__ = 'Olivier Jolly <olivier@pcedev.com>'

from gcoder import GCode  # pylint: disable=relative-import

gcode_absolute_positioning_command = 'G90'
gcode_relative_positioning_command = 'G91'
gcode_set_position_command = 'G92'


class GCodeFilter(object):
    opcode_filter = lambda self, x: None

    def filter(self, gcode):
        self.parse_gcode(gcode, self.opcode_filter)

    def parse_gcode(self, gcode, opcode_filter):
        for layer in gcode.all_layers:
            self.parse_layer(layer, opcode_filter)

    def parse_layer(self, layer, opcode_filter):
        dirty_layer = False
        new_layer = []
        for opcode in layer:
            opcode_filter_result = opcode_filter(opcode)

            if opcode_filter_result is not None:
                dirty_layer = True
                try:
                    new_layer += opcode_filter_result
                except TypeError:
                    new_layer.append(opcode_filter_result)
            else:
                new_layer.append(opcode)

        if dirty_layer:
            layer[:] = new_layer


class GCodeXYTranslateFilter(GCodeFilter):
    def __init__(self, x=None, y=None, **kwargs):
        self.translate_x = x or 0.
        self.translate_y = y or 0.

        self.first_move_after_home = False

        self.absolute_distance_mode = None  # None if when it is unknown

    def generate_translation(self):
        line = "G0 X%.4f Y%.4f" % (self.translate_x, self.translate_y)
        split(line)

    def opcode_filter(self, opcode):
        if opcode.command in move_gcodes:

            if self.absolute_distance_mode is None:
                logging.warn('Move detected without absolute or related mode selected first')
                return

            if not self.absolute_distance_mode:

                # we're in relative mode, if the first move after a homing, translate quickly
                if self.first_move_after_home:
                    self.first_move_after_home = False
                    return [self.generate_translation(), opcode]

                return

            # at this point, we're an absolute move, we have to "hard patch" coordinate
            if opcode.x is not None and self.translate_x:
                opcode.x += self.translate_x
                unsplit(opcode)

            if opcode.y is not None and self.translate_y:
                opcode.y += self.translate_y
                unsplit(opcode)

            return opcode

        if opcode.command == gcode_absolute_positioning_command:
            self.absolute_distance_mode = True
            return

        if opcode.command == gcode_relative_positioning_command:
            self.absolute_distance_mode = False
            return

        if opcode.command == gcode_set_position_command:
            if opcode.x is None and opcode.y is None and opcode.z is None:
                # no coordinate given is equivalent to all 0
                opcode.x = - self.translate_x
                opcode.y = - self.translate_y

                # now, there is a new reference point, that we translated so there's nothing left to do until
                # the end of the program
                self.translate_x = self.translate_y = 0

                unsplit(opcode)
                return opcode

            if opcode.x is not None:
                opcode.x -= self.translate_x
                self.translate_x = 0

            if opcode.y is not None:
                opcode.y -= self.translate_y
                self.translate_y = 0

            unsplit(opcode)
            return opcode


def main():
    """command line entry point"""
    parser = argparse.ArgumentParser(description='Modify gcode program')
    parser.add_argument('-x', type=float, metavar='amount',
                        help='Move all gcode program by <amount> units in the X axis.')
    parser.add_argument('-y', type=float, metavar='amount',
                        help='Move all gcode program by <amount> units in the Y axis.')

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

    # write back modified gcode
    gcode.write(args.outfile)


if __name__ == "__main__":
    main()
