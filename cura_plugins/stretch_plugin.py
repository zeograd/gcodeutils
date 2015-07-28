#Name: Stretch
#Info: Alter toolpath to partially compensate hole size in the X/Y plane
#Depend: GCode
#Type: postprocess
#Param: stretch_strength(float:1.0) Stretch factor, higher value will give bigger holes

# hack for windows platform with a non system wide python so that you can
# just copy gcodeutils into the plugins directory instead of installing it
# no twinkles for you, ultimaker
import sys
sys.path.append('plugins')

from gcodeutils.filter.relative_extrusion import GCodeToRelativeExtrusionFilter
from gcodeutils.gcoder import GCode
from gcodeutils.stretch.stretch import CuraStretchFilter

with open(filename, 'r') as gcode_file:  # pylint: disable=undefined-variable
    gcode = GCode(gcode_file)  # pylint: disable=redefined-outer-name,invalid-name

GCodeToRelativeExtrusionFilter().filter(gcode)
CuraStretchFilter(stretch_strength=stretch_strength).filter(gcode)  # pylint: disable=undefined-variable

with open(filename, 'w') as gcode_file:  # pylint: disable=undefined-variable
    gcode.write(gcode_file)
