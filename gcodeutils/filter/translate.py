import logging

from gcodeutils.filter.filter import GCodeFilter
from gcodeutils.gcoder import move_gcodes, split, unsplit, GCODE_ABSOLUTE_POSITIONING_COMMAND, \
    GCODE_RELATIVE_POSITIONING_COMMAND, GCODE_SET_POSITION_COMMAND, Line, raw_to_line

__author__ = 'olivier'


class GCodeXYTranslateFilter(GCodeFilter):
    """filter translating moves in the X/Y plane"""

    def __init__(self, x=None, y=None, **kwargs):
        self.translate_x = x or 0.
        self.translate_y = y or 0.

        self.first_move_after_home = False

        self.absolute_distance_mode = None  # None if when it is unknown

    def generate_translation(self):
        return raw_to_line("G0 X%.4f Y%.4f" % (self.translate_x, self.translate_y))

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

        if opcode.command == GCODE_ABSOLUTE_POSITIONING_COMMAND:
            self.absolute_distance_mode = True
            return

        if opcode.command == GCODE_RELATIVE_POSITIONING_COMMAND:
            self.absolute_distance_mode = False
            return

        if opcode.command == GCODE_SET_POSITION_COMMAND:
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
