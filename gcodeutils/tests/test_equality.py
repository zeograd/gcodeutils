from nose.tools import eq_, assert_not_equal

from gcodeutils.tests import open_gcode_file

__author__ = 'olivier'


def test_identity_equality():
    gcode1 = open_gcode_file('simple1.gcode')
    gcode2 = open_gcode_file('simple1.gcode')

    eq_(gcode1, gcode2)


def test_trivial_difference():
    assert_not_equal(open_gcode_file('simple1.gcode'), open_gcode_file('simple2.gcode'))

def test_ignore_non_command():
    eq_(open_gcode_file('empty_for_good.gcode'), open_gcode_file('empty_skeinforge_format.gcode'))