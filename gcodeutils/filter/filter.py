__author__ = 'olivier'


class GCodeFilter(object):
    """abstract base filter class"""

    def opcode_filter(self, x):
        raise NotImplementedError

    def filter(self, gcode):
        self.parse_gcode(gcode, self.opcode_filter)

    def parse_gcode(self, gcode, opcode_filter):
        for layer in gcode.all_layers:
            self.parse_layer(layer, opcode_filter)

    def parse_layer(self, layer, opcode_filter):
        dirty_layer = False
        new_layer = []
        for opcode in layer:
            opcode_filter_result = opcode_filter(opcode)

            if opcode_filter_result is not None:
                dirty_layer = True
                try:
                    new_layer += opcode_filter_result
                except TypeError:
                    new_layer.append(opcode_filter_result)
            else:
                new_layer.append(opcode)

        if dirty_layer:
            layer[:] = new_layer
