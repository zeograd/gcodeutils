#Name: Stretch
#Info: Alter toolpath to partially compensate hole size in the X/Y plane
#Depend: GCode
#Type: postprocess
#Param: stretch_strength(float:1.0) Stretch factor, higher value will give bigger holes

from gcodeutils.filter.relative_extrusion import GCodeToRelativeExtrusionFilter
from gcodeutils.gcoder import GCode
from gcodeutils.stretch.stretch import CuraStretchFilter

with open(filename, 'r') as gcode_file:  # pylint: disable=undefined-variable
    gcode = GCode(gcode_file)  # pylint: disable=redefined-outer-name,invalid-name

GCodeToRelativeExtrusionFilter().filter(gcode)
CuraStretchFilter(stretch_strength=stretch_strength).filter(gcode)  # pylint: disable=undefined-variable

with open(filename, 'w') as gcode_file:  # pylint: disable=undefined-variable
    gcode.write(gcode_file)
