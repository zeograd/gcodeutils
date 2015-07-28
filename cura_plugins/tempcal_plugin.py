#Name: Temp tower
#Info: Update temperature continuously
#Depend: GCode
#Type: postprocess
#Param: start_temp(float:150) Temperature at bottom of calibration object
#Param: end_temp(float:240) Temperature at top of calibration object
#Param: min_z_change(float:3) Minimum Z for changing temperatures
#Param: steps(float:10) Number of steps

# hack for windows platform with a non system wide python so that you can
# just copy gcodeutils into the plugins directory instead of installing it
# no twinkles for you, ultimaker
import sys
sys.path.append('plugins')

from gcodeutils.gcode_tempcal import GCodeStepTempGradient
from gcodeutils.gcoder import GCode

with open(filename, 'r') as gcode_file:  # pylint: disable=undefined-variable
    gcode = GCode(gcode_file)  # pylint: disable=redefined-outer-name,invalid-name

with open(filename, 'w') as gcode_file:  # pylint: disable=undefined-variable
    GCodeStepTempGradient(gcode=gcode, start_temp=start_temp, end_temp=end_temp, min_z_change=min_z_change,
                          steps=steps).write(gcode_file)
