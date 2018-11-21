#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""A visitor that pauses the print at a layer
"""

from gcodeutils.visit.visitor import GCodeVisitor

__author__ = "wireddown"

PAUSE_COMMAND = "M226"


class PauseAtLayer(GCodeVisitor):
    """This class inserts a pause command at the start of each layer specified
    """

    def __init__(self, pause_layer_list):
        self.__pause_layer_list = pause_layer_list

    def did_visit_layer(self, layer_as_pyline_list, gcode_iterator_info):
        """Inserts a pause command if the layer matches the list
        """
        is_printed = gcode_iterator_info.is_printed
        is_pause_layer = gcode_iterator_info.layer_number in self.__pause_layer_list
        should_pause = is_printed and is_pause_layer
        if should_pause:
            gcode = gcode_iterator_info.gcode
            layer_index = gcode_iterator_info.layer_index
            commands_to_prepend = [PAUSE_COMMAND]
            gcode.prepend_to_layer(commands_to_prepend, layer_index)
