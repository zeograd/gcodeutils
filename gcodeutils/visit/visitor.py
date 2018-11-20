#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""A base visitor for use with GCodeIterator objects
"""

__author__ = "wireddown"


class GCodeVisitor(object):
    """The base class for visiting GCoder objects
    """

    def will_visit_layer(self, layer_as_pyline_list, gcode_iterator_info):
        """Called before iteration begins on a layer
        """
        pass

    def visit_line(self, pyline, gcode_iterator_info):
        """Called when iteration occurs on a line
        """
        pass

    def did_visit_layer(self, layer_as_pyline_list, gcode_iterator_info):
        """Called after iteration completes on a layer
        """
        pass
