#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""An iterator for GCoder objects that accepts a GCodeVisitor
"""

import logging

__author__ = "wireddown"

LOGGER_NAME = "iterator"
PRINTED_LAYER_KIND = "PRINTED"
PARSED_LAYER_KIND = "parsed"


class GCodeIteratorInformation(object):
    """This class is a simple POD that represents the state of the iterator
    """

    def __init__(self, gcode, layer_number, layer_index, line_number, is_printed):
        self.gcode = gcode
        self.layer_number = layer_number
        self.layer_index = layer_index
        self.line_number = line_number
        self.is_printed = is_printed


# Best write-up I could find
# https://guillaume.segu.in/blog/code/487/optimizing-memory-usage-in-python-a-case-study/
class GCodeIterator(object):
    """This class iterates over a GCoder object and accepts a GCodeVisitor
    """

    def __init__(self, gcode, digits_of_precision=2):
        self.__gcode = gcode
        self.__digits_of_precision = digits_of_precision
        self.__logger = logging.getLogger(LOGGER_NAME)
        self.__all_zs = sorted(
            [round(z, self.__digits_of_precision) for z in self.__gcode.all_zs]
        )
        self.__logger.debug("  all_zs: %s", self.__all_zs)
        self.__logger.debug("  %s layers: %s", PRINTED_LAYER_KIND, len(self.__all_zs))

    def accept(self, visitor):
        """Walk the GCode structure and visit each layer and each line
        """
        parsed_layer_number = 0
        parsed_line_number = 0

        for parsed_layer in self.__gcode.all_layers:
            layer_index = self.__gcode.all_layers.index(parsed_layer)
            try:
                layer_z = round(parsed_layer.z, self.__digits_of_precision)
                layer_number = self.__all_zs.index(layer_z)
                is_printed = True
            except:
                layer_number = parsed_layer_number
                is_printed = False

            layer_kind = PRINTED_LAYER_KIND if is_printed else PARSED_LAYER_KIND
            self.__logger.debug(
                "  visiting %-7s layer %+4s...", layer_kind, layer_number
            )
            info = GCodeIteratorInformation(
                self.__gcode, layer_number, layer_index, parsed_line_number, is_printed
            )
            visitor.will_visit_layer(parsed_layer, info)

            for line in parsed_layer:
                self.__logger.debug("    visiting line %s...", parsed_line_number)
                self.__logger.debug(line.raw)
                info = GCodeIteratorInformation(
                    self.__gcode, layer_number, layer_index, parsed_line_number, is_printed
                )
                visitor.visit_line(line, info)

                parsed_line_number += 1
                self.__logger.debug("    finished line")

            # "-1" because we haven't advanced to the next line /just/ yet
            info = GCodeIteratorInformation(
                self.__gcode, layer_number, layer_index, parsed_line_number - 1, is_printed
            )
            visitor.did_visit_layer(parsed_layer, info)

            parsed_layer_number += 1
            self.__logger.debug("  finished layer")
