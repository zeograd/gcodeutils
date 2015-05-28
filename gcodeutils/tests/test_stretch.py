from gcodeutils.stretch.stretch import SkeinforgeStretchFilter
from gcodeutils.tests import open_gcode_file, gcode_eq

__author__ = 'olivier'


def test_skeinforge_formatted_stretch():
    gcode_oracle = open_gcode_file('skeinforge_model1_poststretch.gcode')
    gcode = open_gcode_file('skeinforge_model1_prestretch.gcode')

    SkeinforgeStretchFilter().filter(gcode)

    gcode_eq(gcode_oracle, gcode)
