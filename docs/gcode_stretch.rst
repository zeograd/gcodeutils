gcode_stretch
*************

**gcode_stretch** modifies existing GCode program to change the size of "printed" holes.

It is a port of skeinforge stretch module, made to work with other modern libre slicers.

.. warning::
    This filter isn't extensively tested yet. Please apply an appropriate amount of scepticism and report both
    failures and successes.

Use case
========

When designing technical 3D parts for printing, you often need to make sure that the hole made in your part will
accomodate another part of a known size. Typically, you want to be able to fit a M8 screw or rod.

Due to several reasons, the printed part may end up with a smaller size than expected.

.. note::
    To achieve the right round hole size, when using OpenSCAD, you should use `polyholes <http://hydraraptor.blogspot.fr/2011/02/polyholes.html>`_.

If you have no way to improve the original design to increase the hole size (not having access to the source files,
not having round holes or just feeling very lazy), **gcode_stretch** can help increase it.

Usage
=====

The GCode to modify must be prepared so that **gcode_stretch** knows about the theorical edge width and loop types.
This step is specific to each slicer.

Preparation of Slic3r GCode
---------------------------

Upstream slic3r doesn't provide any distinction of external and internal perimeters in its GCode.
Since the 2 July 2015, slic3r doesn't generate usable comments to distinguish properly all loops type.

There is an open ticket regarding this GCode verbosity. If a solution is found, regular slic3r versions will be compatible
with **gcode_stretch**.

Once done, you need to set 2 settings to produce compatible GCode :

* "External perimeters first" (in *Print Settings* > *Layers and perimeters* > *Advanced*)
* "Verbose G-code" (in *Print Settings* > *Output options* > *Output file*)

At this point, you can generate GCode and apply **gcode_stretch** manually or you should be able to use **gcode_stretch** as
post processing script (settable in *Print Settings* > *Output options* > *Post-processing scripts*, but untested).

Preparation of Cura GCode
-------------------------

Cura generates usable GCode for stretching by default.

You can either manually postprocess generated GCode or copy the gcode_stretch.py file to your Cura plugins
directory to enable stretching from within Cura itself.

Command line
------------

GCode can be provided in standard input and will be output in standard output by default. You can set the GCode
filename on command line and set the output filename too.

If you need to change the sizing, you're advised to play with the stretch_strength parameter first (it defaults to 1,
increase it to increase hole size [1.1, 1.2, ...], decrease it to decrease hole size [0.9, 0.8, ...]) . Changing other
parameters imply knowledge of the inner working.

::

    usage: gcode_stretch [-h]
                         [--cross_limit_distance_over_edge_width CROSS_LIMIT_DISTANCE_OVER_EDGE_WIDTH]
                         [--stretch_from_distance_over_edge_width STRETCH_FROM_DISTANCE_OVER_EDGE_WIDTH]
                         [--loop_stretch_over_edge_width LOOP_STRETCH_OVER_EDGE_WIDTH]
                         [--edge_inside_stretch_over_edge_width EDGE_INSIDE_STRETCH_OVER_EDGE_WIDTH]
                         [--edge_outside_stretch_over_edge_width EDGE_OUTSIDE_STRETCH_OVER_EDGE_WIDTH]
                         [--stretch_strength STRETCH_STRENGTH] [--verbose]
                         [--quiet]
                         [infile] [outfile]

    Modify GCode program to account for stretch and improve hole size

    positional arguments:
      infile                Program filename to be modified. Defaults to standard
                            input.
      outfile               Modified program. Defaults to standard output.

    optional arguments:
      -h, --help            show this help message and exit
      --cross_limit_distance_over_edge_width CROSS_LIMIT_DISTANCE_OVER_EDGE_WIDTH
                            Distance after and before a point where moves are
                            considered to determine the local normal. Defaults to
                            5.0. Set too low or too high, it might cause points no
                            to be moved in the right direction.
      --stretch_from_distance_over_edge_width STRETCH_FROM_DISTANCE_OVER_EDGE_WIDTH
                            Distance after and before a point where moves are
                            considered to determine the local normal. Defaults to
                            2.0. Set too low or too high, it might cause points no
                            to be moved in the right direction.
      --loop_stretch_over_edge_width LOOP_STRETCH_OVER_EDGE_WIDTH
                            Stretching strength for "loop" (extra shells),
                            defaults to 0.11
      --edge_inside_stretch_over_edge_width EDGE_INSIDE_STRETCH_OVER_EDGE_WIDTH
                            Stretching strength for "inner perimeter", defaults to
                            0.32
      --edge_outside_stretch_over_edge_width EDGE_OUTSIDE_STRETCH_OVER_EDGE_WIDTH
                            Stretching strength for "outer perimeter", defaults to
                            0.1
      --stretch_strength STRETCH_STRENGTH
                            Stretching stretch factor. This is the first setting
                            you'll want to change to modify the hole size
      --verbose, -v         Verbose mode
      --quiet, -q           Quiet mode



.. _inner-working:

Inner working
=============

This filter uses metadata provided by the slicer to determine the type of path to which a point belong.
Only points being part of the visible shell are affected (infill, skirt, brim and so on aren't related to hole sizes).

When a loop is flagged in the GCode (external perimeter being the outer shell, external perimeter being the inner
shell or internal perimeter), all points in this loop are considered for streching.

For each point, the normal vector is estimated by looking at the next and previous points of this loop. Once the normal
vector is found, the point is moved away proportionally to the edge width, normal strength and loop type stretching
strength.
Extrusion is also adapted (quite empirically at this moment) to limit overextrusion in the shell / infill boundary.