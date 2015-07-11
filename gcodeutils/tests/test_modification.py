from gcodeutils.filter.relative_extrusion import GCodeToRelativeExtrusionFilter
from gcodeutils.gcode_mod import GCodeXYTranslateFilter
from gcodeutils.tests import open_gcode_file, gcode_eq

__author__ = 'olivier'


def test_nop_move():
    gcode = open_gcode_file('simple1.gcode')
    gcode_oracle = open_gcode_file('simple1.gcode')

    GCodeXYTranslateFilter(x=0, y=0).filter(gcode)

    gcode_eq(gcode_oracle, gcode)


def test_trivial_move():
    gcode = open_gcode_file('simple1.gcode')
    gcode_oracle = open_gcode_file('simple2.gcode')

    GCodeXYTranslateFilter(x=1, y=2).filter(gcode)

    gcode_eq(gcode_oracle, gcode)


def test_nop_relative_extrusion():
    gcode = open_gcode_file('simple1.gcode')
    gcode_oracle = open_gcode_file('simple1.gcode')

    GCodeToRelativeExtrusionFilter().filter(gcode)

    gcode_eq(gcode_oracle, gcode)


def test_trivial_relative_extrusion():
    gcode = open_gcode_file('simple3.gcode')
    gcode_oracle = open_gcode_file('simple3-relative.gcode')

    GCodeToRelativeExtrusionFilter().filter(gcode)

    gcode_eq(gcode_oracle, gcode)
