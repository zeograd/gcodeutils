module hollow_tower(towerHeight=100, towerWidth=20, wallWidth=0.3, baseHeight=0.3) {
    translate([0, 0, towerHeight/2]) difference() {
        cube([towerWidth, towerWidth, towerHeight], center=true);
        translate([0, 0, baseHeight]) 
            cube([towerWidth-2*wallWidth, towerWidth-2*wallWidth, towerHeight], center=true);
    }
}

hollow_tower();
