GCodeUtils
==========

GCodeUtils is a set of utilities to manipulate GCode programs.
It is targetting RepRap oriented GCode but isn't limited to RepRap.

Currently, it is composed of one calibration generation program.

gcode_tempcal
-------------

gcode_tempcal modifies an existing gcode program to introduce temperature
gradient along the Z axis.

When finetuning the extrusion temperature for an unknown filament, it is possible
to perform an unattented calibration print where the temperature changes along
with Z. Once the print is finished, you can observe which height the print looks
better and determines the temperature at which this part was printed.

Usage
-----



Acknowledgement
---------------

GCode parsing is borrowed from GCoder as found in Printrun (https://github.com/kliment/Printrun)