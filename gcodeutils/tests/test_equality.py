from nose.tools import assert_not_equal

from gcodeutils.tests import open_gcode_file, gcode_eq

__author__ = 'olivier'


def test_identity_equality():
    gcode_eq(open_gcode_file('simple1.gcode'), open_gcode_file('simple1.gcode'))


def test_trivial_difference():
    assert_not_equal(open_gcode_file('simple1.gcode'), open_gcode_file('simple2.gcode'))


def test_ignore_non_command():
    gcode_eq(open_gcode_file('empty_for_good.gcode'), open_gcode_file('empty_skeinforge_format.gcode'))


def test_precision():
    """makes sure that gcode are equals if the numeric values are similar enough
    and different is the numeric values are far enough"""
    gcode_eq(open_gcode_file('simple1.gcode'), open_gcode_file('simple1_equivalent.gcode'))
    assert_not_equal(open_gcode_file('simple1.gcode'), open_gcode_file('simple1_slightly_different.gcode'))
