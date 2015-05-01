#!/usr/bin/env python
# encoding: utf-8
"""Add temperature gradient to gcode program to create unattended temprature calibration program"""
from __future__ import print_function

import argparse
import logging
import sys

__author__ = 'Olivier Jolly <olivier@pcedev.com>'

from .gcoder import GCode


class GCodeTempGradient:
    """Alter gcode to inject temperature changes along Z"""
    MIN_Z_CHANGE_TEMP = 0.4

    ABSOLUTE_MIN_TEMPERATURE = 150
    ABSOLUTE_MAX_TEMPERATURE = 250

    def __init__(self, start_temp, end_temp, gcode):
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.gcode = gcode

        self.zmax = gcode.zmax
        self.zmin = None

        self.last_cooked_temperature = None


    def generate_temperature_gcode(self, temperature):
        """Return a gcode line for the given temperature, under condition that the temperature
        is between the security absolute temperature bounds and that the temperature rounded
        to the nearest 0.1°C is different from the previous one (to avoid spurious gcode generation
        in vase mode)"""
        if self.ABSOLUTE_MIN_TEMPERATURE <= temperature <= self.ABSOLUTE_MAX_TEMPERATURE:

            # round the tempeature to the nearest 0.1°C first
            cooked_temperature = "%.1f" % temperature

            # don't generate temperature change if same as last generation
            if cooked_temperature != self.last_cooked_temperature:
                self.last_cooked_temperature = cooked_temperature
                return "M104 S{}".format(cooked_temperature)

        return ""

    def write(self, output_file=sys.stdout):
        """Write the modified GCode"""

        # first, we parse the GCode program to determine the Z bounds
        for layer_idx, layer in enumerate(self.gcode.all_layers):

            # don't parse layer without any instruction
            if layer:
                current_z = layer[0].current_z

                if current_z is not None:
                    logging.debug("layer #%d altitude is %.2fmm", layer_idx, current_z)

                # Keep the lowest Z which is above the minimum height (used to keep the slicer first layers
                # temperature for adhesion)
                if self.zmin is None and current_z is not None and current_z > self.MIN_Z_CHANGE_TEMP:
                    self.zmin = current_z

        # Make sure that the sliced model is high enough to be usable
        if self.zmin is None:
            raise RuntimeError("Height is too small to create temperature gradient (no layer found ?)")

        logging.info(
            "temperature gradient from %.1f°C, altitude %.2fmm to %.1f°C, altitude %.2fmm ", self.start_temp, self.zmin,
            self.end_temp, self.zmax)

        if self.zmin >= self.zmax:
            raise RuntimeError("Height is too small to create temperature gradient (all operation are below {}mm ?)",
                               self.MIN_Z_CHANGE_TEMP)

        # precompute temperature change per Z unit
        delta_temp_per_z = (self.end_temp - self.start_temp) / (self.zmax - self.zmin)

        # spit back the original GCode with temperature GCode injected accordingly to their Z
        for layer_idx, layer in enumerate(self.gcode.all_layers):

            if layer:
                current_z = layer[0].current_z

                if current_z and self.zmin <= current_z <= self.zmax:
                    target_temp = self.start_temp + delta_temp_per_z * (current_z - self.zmin)
                    logging.debug("target temp for layer #%d is %.1f°C", layer_idx, target_temp)
                    print(self.generate_temperature_gcode(target_temp), file=output_file)

                for line in layer:
                    print(line.raw, file=output_file)


def main():
    """command line entry point"""
    parser = argparse.ArgumentParser(description='Add temperature gradient to gcode program')
    parser.add_argument('start_temp', type=int)
    parser.add_argument('end_temp', type=int)
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('--verbose', '-v', action='count', default=1)
    parser.add_argument('--quiet', '-q', action='count', default=0)

    args = parser.parse_args()

    # count verbose and quiet flags to determine logging level
    args.verbose -= args.quiet

    if args.verbose > 1:
        logging.root.setLevel(logging.DEBUG)
    elif args.verbose > 0:
        logging.root.setLevel(logging.INFO)

    logging.basicConfig(format="%(levelname)s:%(message)s")

    # read original GCode
    gcode = GCode(args.infile.readlines())

    # Alter and write back modified GCode
    temp_gradient = GCodeTempGradient(args.start_temp, args.end_temp, gcode)
    temp_gradient.write(args.outfile)


if __name__ == "__main__":
    main()
