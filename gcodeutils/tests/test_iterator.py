from nose.tools import eq_

from gcodeutils.gcoder import GCode
from gcodeutils.stretch.stretch import LineIteratorForwardLegacy, StretchFilter

__author__ = 'olivier'

layer1 = ";" + StretchFilter.EXTRUSION_ON_MARKER + """
G1 X1
G1 X2
G1 X3
G1 X4
G1 X5
""" + ";" + StretchFilter.EXTRUSION_OFF_MARKER


def cmp_ite(iterator, oracle):
    for expected_x in oracle:
        eq_(expected_x, iterator.get_next().x)
    try:
        iterator.get_next()
        raise AssertionError("iterator should have stopped")
    except StopIteration:
        pass


def test_trivial_iteration():
    gcode = GCode(layer1.split("\n"))

    cmp_ite(LineIteratorForwardLegacy(0, gcode.all_layers[0]), xrange(1, 6))

    for start_index in xrange(1, 6):
        cmp_ite(LineIteratorForwardLegacy(start_index, gcode.all_layers[0]), xrange(start_index, 6))
