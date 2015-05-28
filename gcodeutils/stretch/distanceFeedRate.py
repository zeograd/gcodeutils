import cStringIO

import re

__author__ = 'olivier'


class DistanceFeedRate:
    """A class to limit the z feed rate and round values."""

    DECIMAL_PLACES_CARRIED_REGEXP = re.compile('^\(<decimalPlacesCarried> (\d+)')

    def __init__(self):
        self.decimalPlacesCarried = 4
        self.decimal_formatter = "{.4f}"
        self.output = cStringIO.StringIO()
        self.print_iter = 0

    def add_line(self, line):
        """Add a line of text and a newline to the output."""
        if len(line) > 0:
            self.output.write(line + '\n')

        if not line.startswith('(') and self.print_iter < 10:
            print("adding {}".format(line))
            self.print_iter += 1

    def get_linear_gcode_movement(self, point, z):
        """Get a linear gcode movement."""
        return 'G1 X%s Y%s Z%s' % (self.get_rounded(point.real), self.get_rounded(point.imag), self.get_rounded(z))

    def get_linear_gcode_movement_with_feedrate(self, feed_rate_minute, point, z):
        """Get a z limited gcode movement."""
        linear_gcode_movement = self.get_linear_gcode_movement(point, z)
        if feed_rate_minute is None:
            return linear_gcode_movement
        return linear_gcode_movement + ' F' + self.get_rounded(feed_rate_minute)

    def search_decimal_places_carried(self, raw_line):
        """Search for skeinforge specific decimalPlaceCarried setting to store it."""
        match = self.DECIMAL_PLACES_CARRIED_REGEXP.match(raw_line)

        if match:
            self.decimalPlacesCarried = int(match.group(1))
            self.decimal_formatter = "{{:.{}f}}".format(self.decimalPlacesCarried)

    def get_rounded(self, number):
        """Get number rounded to the number of carried decimal places as a string."""
        return self.decimal_formatter.format(number)
