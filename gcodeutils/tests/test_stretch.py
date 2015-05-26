import StringIO

from nose.tools import eq_

import os

from gcodeutils.stretch.stretch import getCraftedTextFromText
from gcodeutils.tests import open_gcode_file

__author__ = 'olivier'


def test_skeinforge_formatted_stretch():
    gcode_oracle = open_gcode_file('skeinforge_model1_poststretch.gcode')

    gcode = getCraftedTextFromText(
        open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skeinforge_model1_prestretch.gcode')).read())

    gcode_oracle_str = StringIO.StringIO()
    gcode_oracle.write(gcode_oracle_str)

    eq_(gcode_oracle_str.getvalue(), gcode)
