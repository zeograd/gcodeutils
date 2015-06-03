gcode_mod
---------

**gcode_mod** modifies an existing GCode program to translate all moves along X and Y by some amount.

It is meant to expose X/Y translation filters which will later be used in more advanced calibration programs.

Use case
........

As it stands now, its only use is for reprinting at another place a part for which you only have the GCode program.
If you have the original stl, slicer program and settings and want to print at another location on your bed, you
better generate a new GCode program.

Usage
.....

Call **gcode_mod** with the amount of move in X and Y and the GCode either in plain text (or piped) or by giving
its filename.
**gcode_mod** attempts to handle relative and absolute moves as well as position setting (G92) but you better
double check the generated GCode until more feedback have been factored into polishing the translation algorithm.

::

    usage: gcode_mod [-h] [-x amount] [-y amount] [--verbose] [--quiet]
                     [infile] [outfile]

    Modify gcode program

    positional arguments:
      infile         Program filename to be modified. Defaults to standard input.
      outfile        Modified program. Defaults to standard output.

    optional arguments:
      -h, --help     show this help message and exit
      -x amount      Move all gcode program by <amount> units in the X axis.
      -y amount      Move all gcode program by <amount> units in the Y axis.
      --verbose, -v  Verbose mode
      --quiet, -q    Quiet mode

