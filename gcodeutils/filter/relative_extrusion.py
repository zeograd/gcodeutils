from decimal import Decimal

from gcodeutils.filter.filter import GCodeFilter
from gcodeutils.gcoder import GCODE_SET_POSITION_COMMAND, GCODE_RELATIVE_POSITIONING_COMMAND, move_gcodes, split, Line, \
    GCODE_ABSOLUTE_EXTRUSION_COMMAND, \
    GCODE_RELATIVE_EXTRUSION_COMMAND, raw_to_line, unsplit

__author__ = 'olivier'


class GCodeToRelativeExtrusionFilter(GCodeFilter):
    def __init__(self):
        self.relative_extrusion = False
        self.current_extrusion_distance = Decimal()

    def opcode_filter(self, opcode):
        if opcode.command == GCODE_RELATIVE_EXTRUSION_COMMAND:
            self.relative_extrusion = True
            return

        if opcode.command == GCODE_ABSOLUTE_EXTRUSION_COMMAND:
            self.relative_extrusion = False
            return raw_to_line(GCODE_RELATIVE_EXTRUSION_COMMAND)

        if opcode.command == GCODE_SET_POSITION_COMMAND:

            # when setting position, if E is set, use it, but if there is parameter, consider E=0
            if opcode.e is not None:
                self.current_extrusion_distance = Decimal(opcode.e)
            elif opcode.x is None and opcode.y is None and opcode.z is None:
                self.current_extrusion_distance = Decimal()

            return

        if opcode.command in move_gcodes and not self.relative_extrusion and opcode.e is not None:
            # we're extruding while in absolute extrusion mode, reduce by the amount extruded so far
            # and keep track of the current e for later reuse
            opcode.e, self.current_extrusion_distance = (
            opcode.e - float(self.current_extrusion_distance), Decimal(opcode.e))
            opcode.relative_e=True
            unsplit(opcode)
            return opcode
