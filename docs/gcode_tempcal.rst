gcode_tempcal
-------------

**gcode_tempcal** modifies an existing gcode program to introduce temperature
gradient along the Z axis.

When finetuning the extrusion temperature for an unknown filament, it is possible
to perform an unattented calibration print where the temperature changes along
with Z. Once the print is finished, you can observe which height the print looks
better and determines the temperature at which this part was printed.

Use case
........

Finding out what is the ideal temperature to print with a new spool of filament can
be achieved using the technique described on this video : https://www.youtube.com/watch?v=FSOPsRiiOZk

Basically, you create a tower that you'll slice to print only the outer shell.

Then you update manually the gcode program to insert temperature decrase as you print and
you inspect the print quality to find out which temperature resulted in the best appearance.

**gcode_tempcal** comes with a suitable cuboid model and a script to perform this temperature
alteration in the gcode produced by your slicer to get you ready to print in a shorter time.

You may also want to use a tower with vertical holes like this one : http://www.thingiverse.com/thing:826019 so
that you'll both see perimeter appearance and bridge quality depending on the temperature.

Usage
.....

Follow the directions in the video https://www.youtube.com/watch?v=FSOPsRiiOZk except
that you can use the cuboid located at this location https://github.com/zeograd/gcodeutils/blob/master/models/temperature/temperature_hollow_tower.stl
which is already hollowed out (you may want to check that the slicer will generate at least
one outer shell for the thin walls. If not you can force the perimeter width or regenerate the
mode out of the self documented openSCAD model at the same location).

Once sliced, instead of manually editing the gcode program, use **gcode_tempcal** to insert
the temperature change instructions.

.. code:: bash

    $ gcode_tempcal 220 210 temperate_hollow_tower.gcode temperature_grad220-210.gcode -v
    [ ... heights snippet removed ...]
    INFO:temperature gradient from 220.0°C, altitude 0.30mm to 210.0°C, altitude 99.95mm
    DEBUG:target temp for layer #2 (height 0.30mm) is 220.0°C
    DEBUG:target temp for layer #34 (height 9.65mm) is 219.0°C
    DEBUG:target temp for layer #64 (height 18.65mm) is 218.0°C
    DEBUG:target temp for layer #94 (height 27.65mm) is 217.0°C
    DEBUG:target temp for layer #124 (height 36.65mm) is 216.0°C
    DEBUG:target temp for layer #154 (height 45.65mm) is 215.0°C
    DEBUG:target temp for layer #185 (height 54.95mm) is 214.0°C
    DEBUG:target temp for layer #215 (height 63.95mm) is 213.0°C
    DEBUG:target temp for layer #245 (height 72.95mm) is 212.0°C
    DEBUG:target temp for layer #275 (height 81.95mm) is 211.0°C
    DEBUG:target temp for layer #305 (height 90.95mm) is 210.0°C


::

    usage: gcode_tempcal [-h] [--min_z_change MIN_Z_CHANGE] [--continuous]
                         [--steps STEPS] [--verbose] [--quiet]
                         start_temp end_temp [infile] [outfile]

    Add temperature gradient to gcode program

    positional arguments:
      start_temp            Initial temperature (best set to the default slicing
                            temperature). For instance, for ABS you may want 240
                            and 200 for PLA.
      end_temp              End temperature for the gcode program. Usually lower
                            than the initial temperature. Make sure that your
                            material can be still be extruded at this temperature
                            to avoid clogging your extruder.
      infile                Program filename to be modified. Defaults to standard
                            input.
      outfile               Modified program with temperature gradient. Defaults
                            to standard output.

    optional arguments:
      -h, --help            show this help message and exit
      --min_z_change MIN_Z_CHANGE, -z MIN_Z_CHANGE
                            Minimum height above which temperature gradient is
                            created. If you have a special start sequence playing
                            with temperatures, you may want to raise this to avoid
                            overlapping of temperature. Defaults to 0.1mm which is
                            compatible with NopHead ooze free unattended start
                            sequence.
      --verbose, -v         Verbose mode. It notably outputs the mapping between
                            temperature and height if you have troubles figuring
                            it out.
      --quiet, -q           Quiet mode

    temperature control:
      --continuous, -c      Switch to a continuous gradient generation where
                            temperature is recomputed for every layer. You may
                            want this in the case of very precise and fast hotend.
                            Defaults to discrete temperature gradient divided in X
                            steps.
      --steps STEPS, -s STEPS
                            Number of steps used to create a discrete gradient
                            when using the default gradient generation model.
                            Defaults to 10 steps. This setting is not used when
                            using the continuous gradient generation model.

