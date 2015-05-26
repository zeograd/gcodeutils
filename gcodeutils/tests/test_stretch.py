import StringIO
from nose.tools import eq_

import os

from gcodeutils.stretch.stretch import getCraftedText
from gcodeutils.tests import open_gcode_file

__author__ = 'olivier'


def test_skeinforge_formatted_stretch():
    gcode_oracle = open_gcode_file('skeinforge_model1_poststretch.gcode')

    gcode = getCraftedText(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skeinforge_model1_prestretch.gcode'), None)

    gcode_oracle_str = StringIO.StringIO()
    gcode_oracle.write(gcode_oracle_str)

    eq_(gcode_oracle_str.getvalue(), gcode)
