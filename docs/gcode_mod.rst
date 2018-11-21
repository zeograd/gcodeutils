gcode_mod
---------

**gcode_mod** modifies an existing GCode program to translate all moves along X and Y by some amount,
or to convert all extrusion distance to relative, or to insert a pause command at a specific layer.

Use case
........

This program can be used to reprint a part at another place when you only have the GCode program.
If you have the original stl, slicer program, and settings and you want to print at another location
on your bed, you will get better results by generating a new GCode program.

This program can be used to convert absolute extrusion to relative extrusion so that further GCode
processing is eased. It is used for instance in **gcode_stretch** as a preprocessor before performing
toolpath changes required for stretching.

This program can also be used to insert a pause command when the GCode programs begins a new layer.

Usage
.....

Call **gcode_mod** with the GCode either in plain text (or piped) or by giving its filename.
Depending on the required modification, you have to pass at least one of (i) the -x and -y amount to
translate, (ii) -e to enable relative extrusion, or (iii) -p layer to pause.

**gcode_mod** attempts to handle relative and absolute moves as well as position setting (G92) but you better
double check the generated GCode until more feedback have been factored into polishing the translation algorithm.

::

    usage: gcode_mod [-h] [-x amount] [-y amount] [-e] [-p layer] [--verbose] [--quiet]
                     [infile] [outfile]

    Modify gcode program

    positional arguments:
      infile         Program filename to be modified. Defaults to standard input.
      outfile        Modified program. Defaults to standard output.

    optional arguments:
      -h, --help     show this help message and exit
      -x amount      Move all gcode program by <amount> units in the X axis.
      -y amount      Move all gcode program by <amount> units in the Y axis.
      -e             Convert all extrusion to relative
      -p layer       Pause the gcode program at layer <layer>.
      --verbose, -v  Verbose mode
      --quiet, -q    Quiet mode

