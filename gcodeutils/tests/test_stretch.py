import logging

from gcodeutils.stretch.stretch import SkeinforgeStretchFilter, Slic3rStretchFilter, CuraStretchFilter
from gcodeutils.tests import open_gcode_file, gcode_eq

__author__ = 'olivier'


def test_skeinforge_formatted_stretch():
    gcode_oracle = open_gcode_file('skeinforge_model1_poststretch.gcode')
    gcode = open_gcode_file('skeinforge_model1_prestretch.gcode')

    SkeinforgeStretchFilter().filter(gcode)

    gcode_eq(gcode_oracle, gcode)


def test_square_stretch_skeinforge():
    simple_square_gcode = open_gcode_file('skeinforge_square.gcode')

    logging.basicConfig(level=logging.DEBUG)
    SkeinforgeStretchFilter().filter(simple_square_gcode)
    simple_square_gcode.write()


def test_square_stretch_slic3r():
    simple_square_gcode = open_gcode_file('slic3r_square.gcode')

    logging.basicConfig(level=logging.DEBUG)
    Slic3rStretchFilter().filter(simple_square_gcode)
    simple_square_gcode.write()


def test_square_stretch_cura():
    simple_square_gcode = open_gcode_file('cura_square.gcode')

    logging.basicConfig(level=logging.DEBUG)
    CuraStretchFilter().filter(simple_square_gcode)
    simple_square_gcode.write()
