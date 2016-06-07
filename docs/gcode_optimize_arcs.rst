gcode_optimize_arcs
---------

**gcode_optimize_arcs** modifies an existing GCode program to translate all moves along a circular are into G2/G3
commands.

Use case
........

As it stands now, its can be used to post-process gcode generated from STL. As STL does not have means to describe arcs
the resulting gcode does not contain arcs. Especially if there are small thru-holes with a high segmentation to be
printed it might kill the print as many small movements happen a the same place.

Usage
.....

Call **gcode_optimize_arcs** with the GCode either in plain text (or piped) or by giving its filename.

**gcode_optimize_arcs** attempts to handle relative and absolute moves as well as position setting (G92) but you better
double check the generated GCode until more feedback have been factored into polishing the translation algorithm.
Moreover there is currently no extrusion correction so you better us a high segmentation. In OpenSCAD this is
controlled by $fn so a good starting point (for small radius) is $fn=64;

::

    usage: gcode_optimize_arcs [-h] [--inplace] [--verbose] [--quiet]
                     [infile] [outfile]

    Modify GCode program to account arcs and replace the G1 with G2/G3

    positional arguments:
      infile         Program filename to be modified. Defaults to standard input.
      outfile        Modified program. Defaults to standard output.

    optional arguments:
      -h, --help     show this help message and exit
      --inplace      modify the code in-place, usefull if gcode_optimize_arcs is used as post processor in Slic3r
      --verbose, -v  Verbose mode
      --quiet, -q    Quiet mode

.. _inner-working:

Inner working
=============

Arcs are detected using a moving window over the gcode commands. The minimum size of the window is 9 so that at least 8
segments are needed to constitute an arc. The validity is checked using the following criterias:
* all segments are printed using the same speed (F parameter in gcode)
* if segments extrude they have to have the same ration between extrusion (E param) and the length of th epath
* the endpoints of the segments need to be equidistant on the arc
