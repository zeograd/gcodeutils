GCodeUtils
==========

GCodeUtils is a set of utilities to manipulate GCode programs.
It is targetting RepRap oriented GCode but isn't limited to RepRap.

Currently, it is composed of one calibration generation program, a basic gcode modifier (which translates code along
X/Y or convert extrusion distance to relative) and a stretcher to increase hole size of printed parts.

Installation
------------

GCodeUtils is installable from PyPI with a single pip command::

    pip install gcodeutils

Alternatively, GCodeUtils can be run directly from sources after a git pull::

    git clone https://github.com/zeograd/gcodeutils.git
    cd gcodeutils && python setup.py install

Once GCodeUtils is installed, the .py files located in the cura_plugins
subdirectory can be copied into the *plugins* directory of Cura to be callable
from within Cura itself.

Documentation
-------------

Latest documentation can be found online at this address: http://gcodeutils.readthedocs.org/en/latest/

Acknowledgement
---------------

GCode parsing is borrowed from GCoder as found in Printrun (https://github.com/kliment/Printrun)
