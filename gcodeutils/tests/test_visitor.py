#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the visit submodule
"""

from gcodeutils.tests import open_gcode_file

from gcodeutils.visit.iterator import GCodeIterator
import gcodeutils.visit.pause_at_layer as pal

from nose.tools import assert_equal

__author__ = "wireddown"


def test_pause_at_layer():
    original_gcode = open_gcode_file("arc_raw_1.gcode")
    paused_gcode = open_gcode_file("arc_raw_1.gcode")

    iterator = GCodeIterator(paused_gcode, digits_of_precision=3)
    pause_at_layer = pal.PauseAtLayer(pause_layer_list=[1])
    iterator.accept(pause_at_layer)

    result = original_gcode.diff(paused_gcode)
    expected_result = pal.PAUSE_COMMAND
    has_pause_command = True if expected_result in result else False
    message = "Expected '%s' in 'vs' part of diff message; whole message is '%s'" % (expected_result, result)
    assert_equal(has_pause_command, True, message)
