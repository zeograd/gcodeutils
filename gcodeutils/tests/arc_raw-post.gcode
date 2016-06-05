M107
M190 S125 ; set bed temperature
G28 ; home all axes
G1 Z5 F5000 ; lift nozzle
M109 S270 ; wait for extruder temp to be reached
M3001 ; Aktivate Z-Compensation
M3004 S0 ; + n-steps bed down // - n-steps bed up!
G90 ; use absolute coordinates
M82 ; use absolute distances for extrusion
G92 E0 ; start line
G1 F300 E-0.5
G1 X230 Y25 Z0.35 F5000
G1 F800 E8
G1 X20 E25 F1000
M201 X1000 Y1000 Z1000
M202 X3000 Y3000 Z1000
G21 ; set units to millimeters
G90 ; use absolute coordinates
M82 ; use absolute distances for extrusion
G92 E0
G1 E-1.00000 F600.00000
G92 E0
G1 Z0.350 F6000.000
G1 X20 Y20 Z0.0000 E0
G1 X80 Y20 Z0.0000 E60
G1 X80 Y60 Z0.0000 E100
G1 X20 Y60 Z0.0000 E160
G1 X20 Y20 Z0.0000 E200
G92 E0
; begin of test data to be converted into arc
M83
G0 X100.0000 Y20.0000 Z0  first layer
G1 X100.0000 Y60.0000 E1.111111
G3 X80.0000 Y80.0000 E0.8713 I-20.0000 J-0.0000; generated from 8 segments
G1 X20.0000 Y80.0000 E1.666667
G3 X0.0000 Y60.0000 E0.8713 I0.0000 J-20.0000; generated from 8 segments
G1 X0.0000 Y20.0000 E1.111111
G3 X20.0000 Y0.0000 E0.8713 I20.0000 J0.0000; generated from 8 segments
G1 X80.0000 Y0.0000 E1.666667
G3 X100.0000 Y20.0000 E0.8713 I-0.0000 J20.0000; generated from 8 segments
G0 Z1.0000 ; next layer
G2 X80.0000 Y0.0000 E0.8713 I-20.0000 J0.0000; generated from 8 segments
G1 X20.0000 Y0.0000 E1.666667
G2 X0.0000 Y20.0000 E0.8713 I0.0000 J20.0000; generated from 8 segments
G1 X0.0000 Y60.0000 E1.111111
G2 X20.0000 Y80.0000 E0.8713 I20.0000 J-0.0000; generated from 8 segments
G1 X80.0000 Y80.0000 E1.666667
G2 X100.0000 Y60.0000 E0.8713 I-0.0000 J-20.0000; generated from 8 segments
G1 X100.0000 Y20.0000 E1.1111
;G1 X0 Y0
G92 E0
M104 S0
M140 S0
G91
G1 E-5 F300
M400
M3079
M400
M84
M201 X1000 Y1000 Z1000
M202 X1000 Y1000 Z1000
