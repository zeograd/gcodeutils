"""
This page is in the table of contents.
Stretch is very important Skeinforge plugin that allows you to partially compensate for the fact that extruded holes are
smaller then they should be.  It stretches the threads to partially compensate for filament shrinkage when extruded.

The stretch manual page is at:
http://fabmetheus.crsndoo.com/wiki/index.php/Skeinforge_Stretch

Extruded holes are smaller than the model because while printing an arc the head is depositing filament on both sides
of the arc but in the inside of the arc you actually need less material then on the outside of the arc. You can read
more about this on the RepRap ArcCompensation page:
http://reprap.org/bin/view/Main/ArcCompensation

In general, stretch will widen holes and push corners out.  In practice the filament contraction will not be identical
to the algorithm, so even once the optimal parameters are determined, the stretch script will not be able to eliminate
the inaccuracies caused by contraction, but it should reduce them.

All the defaults assume that the thread sequence choice setting in fill is the edge being extruded first, then the
loops, then the infill.  If the thread sequence choice is different, the optimal thread parameters will also be
different.  In general, if the infill is extruded first, the infill would have to be stretched more so that even after
the filament shrinkage, it would still be long enough to connect to the loop or edge.

Holes should be made with the correct area for their radius.  In other words, for example if your modeling program
approximates a hole of radius one (area = pi) by making a square with the points at [(1,0), (0,1), (-1,0), (0,-1)]
(area = 2), the radius should be increased by sqrt(pi/2).  This can be done in fabmetheus xml by writing:
radiusAreal='True'

in the attributes of the object or any parent of that object.  In other modeling programs, you'll have to this manually
or make a script.  If area compensation is not done, then changing the stretch parameters to over compensate for too
small hole areas will lead to incorrect compensation in other shapes.

==Settings==
===Loop Stretch Over Perimeter Width===
Default is 0.1.

Defines the ratio of the maximum amount the loop aka inner shell threads will be stretched compared to the edge width,
in general this value should be the same as the 'Perimeter Outside Stretch Over Perimeter Width' setting.

===Path Stretch Over Perimeter Width===
Default is zero.

Defines the ratio of the maximum amount the threads which are not loops, like the infill threads, will be stretched
compared to the edge width.

===Perimeter===
====Perimeter Inside Stretch Over Perimeter Width====
Default is 0.32.

Defines the ratio of the maximum amount the inside edge thread will be stretched compared to the edge width, this is
the most important setting in stretch.  The higher the value the more it will stretch the edge and the wider holes will
be.  If the value is too small, the holes could be drilled out after fabrication, if the value is too high, the holes
would be too wide and the part would have to junked.

====Perimeter Outside Stretch Over Perimeter Width====
Default is 0.1.

Defines the ratio of the maximum amount the outside edge thread will be stretched compared to the edge width, in
general this value should be around a third of the 'Perimeter Inside Stretch Over Perimeter Width' setting.

===Stretch from Distance over Perimeter Width===
Default is two.

The stretch algorithm works by checking at each turning point on the extrusion path what the direction of the thread
is at a distance of 'Stretch from Distance over Perimeter Width' times the edge width, on both sides, and moves the
thread in the opposite direction.  So it takes the current turning-point, goes
"Stretch from Distance over Perimeter Width" * "Perimeter Width" ahead, reads the direction at that point.  Then it
goes the same distance in back in time, reads the direction at that other point.  It then moves the thread in the
opposite direction, away from the center of the arc formed by these 2 points+directions.

The magnitude of the stretch increases with:
the amount that the direction of the two threads is similar and
by the '..Stretch Over Perimeter Width' ratio.

==Examples==
The following examples stretch the file Screw Holder Bottom.stl.  The examples are run in a terminal in the folder
which contains Screw Holder Bottom.stl and stretch.py.

> python stretch.py
This brings up the stretch dialog.

> python stretch.py Screw Holder Bottom.stl
The stretch tool is parsing the file:
Screw Holder Bottom.stl
..
The stretch tool has created the file:
.. Screw Holder Bottom_stretch.gcode

"""

from __future__ import absolute_import
import base64
import logging
import zlib

import re

from gcodeutils.gcoder import split, Line, parse_coordinates, unsplit, linear_move_gcodes
from .vector3 import Vector3

__author__ = 'Enrique Perez (perez_enrique@yahoo.com)'
__date__ = '$Date: 2008/21/04 $'
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'


def get_location_from_line(old_location, line):
    """Get the location from a GCode line, carrying over existing location."""
    if old_location is None:
        old_location = Vector3()

    return Vector3(
        line.x if line.x is not None else old_location.x,
        line.y if line.y is not None else old_location.y,
        line.z if line.z is not None else old_location.z,
    )


def dot_product(lhs, rhs):
    """Get the dot product of a pair of complexes."""
    return lhs.real * rhs.real + lhs.imag * rhs.imag


class LineIteratorForwardLegacy(object):
    """Forward line iterator class."""

    logger = logging.getLogger('iterator')

    def __init__(self, line_index, lines):
        self.first_visited_index = None
        self.line_index = line_index
        self.first_visited_index = None
        self.lines = lines
        self.increment = 1
        self.stop_on_extrusion_off = True

        self.logger.debug("started iterator with line_index = %d", self.line_index)

    def index_setup(self):
        pass

    def reset_index_on_limit(self):
        """Get index just after the activate command."""
        self.logger.debug("reset index forward")
        for lineIndex in xrange(self.line_index - 1, 0, - 1):
            if StretchFilter.EXTRUSION_ON_MARKER in self.lines[lineIndex].raw:
                return lineIndex + 1
        print('This should never happen in stretch, no activate command was found for this thread.')
        raise StopIteration, "You've reached the end of the line."

    def index_in_valid_range(self):
        return 0 <= self.line_index < len(self.lines)

    def get_next(self):
        """Get next line going backward or raise exception."""

        self.index_setup()

        while self.index_in_valid_range():

            if self.line_index == self.first_visited_index:
                self.logger.debug("infinite looping detected")
                raise StopIteration, "You've reached the end of the line."
            if self.first_visited_index is None:
                self.first_visited_index = self.line_index

            line = self.lines[self.line_index]
            if StretchFilter.EXTRUSION_OFF_MARKER in line.raw and self.stop_on_extrusion_off:
                self.line_index = self.reset_index_on_limit()
                continue

            self.line_index += self.increment
            if line.command in linear_move_gcodes and (line.x is not None or line.y is not None):
                self.logger.debug("found (%d) %s %s", self.increment, line.x, line.y)
                return line

        self.logger.debug("no more point in loop")
        raise StopIteration, "You've reached the end of the line."


class LineIteratorBackwardLegacy(LineIteratorForwardLegacy):
    """Backward line iterator class."""

    def __init__(self, line_index, lines):
        super(LineIteratorBackwardLegacy, self).__init__(line_index, lines)
        self.increment = -1

    def index_setup(self):
        if self.line_index < 1:
            self.line_index = self.reset_index_on_limit()

    def reset_index_on_limit(self):
        """Get index two lines before the deactivate command."""

        self.logger.debug("reset index backward")

        for lineIndex in xrange(self.line_index + 1, len(self.lines)):
            if StretchFilter.EXTRUSION_OFF_MARKER in self.lines[lineIndex].raw:
                return lineIndex - 2
        print('This should never happen in stretch, no deactivate command was found for this thread.')
        raise StopIteration, "You've reached the end of the line."


class LineIteratorForward(LineIteratorForwardLegacy):
    def reset_index_on_limit(self):
        """Get index just after the activate command."""
        self.logger.debug("reset index forward (modern)")
        for lineIndex in xrange(self.line_index - 1, -1, - 1):
            if StretchFilter.LOOP_START_MARKER in self.lines[lineIndex].raw:
                return lineIndex + 1
        print('This should never happen in stretch, no activate command was found for this thread.')
        raise StopIteration, "You've reached the end of the line."


class CuraLineIteratorForward(LineIteratorForwardLegacy):
    def __init__(self, line_index, lines):
        super(CuraLineIteratorForward, self).__init__(line_index, lines)
        self.stop_on_extrusion_off = False

    def index_setup(self):
        if StretchFilter.LOOP_STOP_MARKER in self.lines[self.line_index].raw:
            self.line_index = self.reset_index_on_limit()

    def reset_index_on_limit(self):
        """Get index just after the activate command."""
        self.logger.debug("reset index forward (modern)")
        for lineIndex in xrange(self.line_index - 1, -1, - 1):
            if StretchFilter.LOOP_START_MARKER in self.lines[lineIndex].raw:
                return lineIndex
        print('This should never happen in stretch, no activate command was found for this thread.')
        raise StopIteration, "You've reached the end of the line."


class LineIteratorBackward(LineIteratorBackwardLegacy):
    def index_setup(self):
        if self.line_index < 0:
            self.line_index = self.reset_index_on_limit()
        elif StretchFilter.LOOP_START_MARKER in self.lines[self.line_index + 1].raw:  # if just before a loop start
            self.line_index = self.reset_index_on_limit()

    def reset_index_on_limit(self):
        """Get index two lines before the deactivate command."""

        self.logger.debug("reset index backward (modern)")

        for lineIndex in xrange(self.line_index + 1, len(self.lines)):
            if StretchFilter.EXTRUSION_OFF_MARKER in self.lines[lineIndex].raw:
                return lineIndex - 2
        print('This should never happen in stretch, no deactivate command was found for this thread.')
        raise StopIteration, "You've reached the end of the line."


class CuraLineIteratorBackward(LineIteratorBackwardLegacy):
    def __init__(self, line_index, lines):
        super(CuraLineIteratorBackward, self).__init__(line_index, lines)
        self.stop_on_extrusion_off = False

    def index_setup(self):
        if self.line_index < 0:
            self.line_index = self.reset_index_on_limit()
        elif StretchFilter.LOOP_START_MARKER in self.lines[self.line_index + 1].raw:  # if just before a loop start
            self.line_index = self.reset_index_on_limit()

    def reset_index_on_limit(self):
        """Get index two lines before the deactivate command."""

        self.logger.debug("reset index backward (modern)")

        for lineIndex in xrange(self.line_index + 1, len(self.lines)):
            if StretchFilter.LOOP_STOP_MARKER in self.lines[lineIndex].raw:
                return lineIndex - 1
        print('This should never happen in stretch, no deactivate command was found for this thread.')
        raise StopIteration, "You've reached the end of the line."


class StretchRepository:
    """A class to handle the stretch settings."""

    def __init__(self, cross_limit_distance_over_edge_width=5.0, loop_stretch_over_edge_width=0.11,
                 edge_inside_stretch_over_edge_width=0.32, edge_outside_stretch_over_edge_width=0.1,
                 stretch_from_distance_over_edge_width=2.0, stretch_strength=1.0, **kwargs):
        """Set the default settings."""

        # Cross Limit Distance Over Perimeter Width (ratio)
        self.crossLimitDistanceOverEdgeWidth = cross_limit_distance_over_edge_width

        self.loopStretchOverEdgeWidth = loop_stretch_over_edge_width * stretch_strength
        self.edgeInsideStretchOverEdgeWidth = edge_inside_stretch_over_edge_width * stretch_strength
        self.edgeOutsideStretchOverEdgeWidth = edge_outside_stretch_over_edge_width * stretch_strength

        # Stretch From Distance Over Perimeter Width (ratio)
        self.stretchFromDistanceOverEdgeWidth = stretch_from_distance_over_edge_width


class StretchFilter:
    """A class to stretch a skein of extrusions."""

    EXTRUSION_ON_MARKER = 'stretch-extrusion-on'
    EXTRUSION_OFF_MARKER = 'stretch-extrusion-off'
    LOOP_START_MARKER = 'stretch-loop-start'
    INNER_EDGE_START_MARKER = LOOP_START_MARKER + ' stretch-inner-edge-start'
    OUTER_EDGE_START_MARKER = LOOP_START_MARKER + ' stretch-outer-edge-start'
    LOOP_STOP_MARKER = 'stretch-loop-stop'

    def __init__(self, **kwargs):
        self.edgeWidth = 0.4
        self.extruderActive = False
        self.feedRateMinute = 959.0
        self.isLoop = False
        self.oldLocation = None
        self.gcode = None
        self.current_layer = None
        self.line_number_in_layer = 0
        self.stretchRepository = StretchRepository(**kwargs)

        self.thread_maximum_absolute_stretch = 0

        self.line_forward_iterator = LineIteratorForwardLegacy
        self.line_backward_iterator = LineIteratorBackwardLegacy

    def filter(self, gcode):
        """Parse gcode text and store the stretch gcode."""
        self.gcode = gcode

        self.setup_filter()

        for self.current_layer_index, current_layer in enumerate(self.gcode.all_layers):
            self.current_layer = current_layer[:]
            for self.line_number_in_layer, line in enumerate(self.current_layer):
                gcode_line = self.parse_line(line)
                parse_coordinates(gcode_line, split(gcode_line))
                self.gcode.all_layers[self.current_layer_index][self.line_number_in_layer] = gcode_line

    def get_cross_limited_stretch(self, crossLimitedStretch, crossLineIterator, locationComplex):
        """Get cross limited relative stretch for a location."""
        try:
            line = crossLineIterator.get_next()
        except StopIteration:
            return crossLimitedStretch
        pointComplex = get_location_from_line(self.oldLocation, line).dropAxis()
        pointMinusLocation = locationComplex - pointComplex
        pointMinusLocationLength = abs(pointMinusLocation)
        if pointMinusLocationLength <= self.crossLimitDistanceFraction:
            return crossLimitedStretch
        parallelNormal = pointMinusLocation / pointMinusLocationLength
        parallelStretch = dot_product(parallelNormal, crossLimitedStretch) * parallelNormal
        if pointMinusLocationLength > self.crossLimitDistance:
            return parallelStretch
        crossNormal = complex(parallelNormal.imag, - parallelNormal.real)
        crossStretch = dot_product(crossNormal, crossLimitedStretch) * crossNormal
        crossPortion = (self.crossLimitDistance - pointMinusLocationLength) / self.crossLimitDistanceRemainder
        return parallelStretch + crossStretch * crossPortion

    def get_relative_stretch(self, locationComplex, lineIterator):
        """Get relative stretch for a location."""
        lastLocationComplex = locationComplex
        oldTotalLength = 0.0
        pointComplex = locationComplex
        totalLength = 0.0
        while 1:
            try:
                line = lineIterator.get_next()
            except StopIteration:
                locationMinusPoint = locationComplex - pointComplex
                locationMinusPointLength = abs(locationMinusPoint)
                if locationMinusPointLength > 0.0:
                    return locationMinusPoint / locationMinusPointLength
                return complex()
            pointComplex = get_location_from_line(self.oldLocation, line).dropAxis()
            locationMinusPoint = lastLocationComplex - pointComplex
            locationMinusPointLength = abs(locationMinusPoint)
            totalLength += locationMinusPointLength

            logging.debug("total length: %d, stretchFromDistance: %f", totalLength, self.stretchFromDistance)

            if totalLength >= self.stretchFromDistance:
                distanceFromRatio = (self.stretchFromDistance - oldTotalLength) / locationMinusPointLength
                totalPoint = distanceFromRatio * pointComplex + (1.0 - distanceFromRatio) * lastLocationComplex
                locationMinusTotalPoint = locationComplex - totalPoint
                return locationMinusTotalPoint / self.stretchFromDistance
            lastLocationComplex = pointComplex
            oldTotalLength = totalLength

    def stretch_line(self, line):
        """Get stretched gcode line."""
        location = get_location_from_line(self.oldLocation, line)
        self.feedRateMinute = line.f or self.feedRateMinute
        self.oldLocation = location

        # if thread_maximum_absolute_stretch is set (ie within a loop) and we're extruding or after to do so,
        # adjust the point location to account for stretching
        if self.thread_maximum_absolute_stretch > 0.0:
            return self.get_stretched_line_from_index_location(self.line_number_in_layer - 1,
                                                               self.line_number_in_layer + 1,
                                                               location,
                                                               line)
        return line

    def get_stretched_line_from_index_location(self, indexPreviousStart, indexNextStart, location, original_line):
        """Get stretched gcode line from line index and location."""
        crossIteratorForward = self.line_forward_iterator(indexNextStart, self.current_layer)
        crossIteratorBackward = self.line_backward_iterator(indexPreviousStart, self.current_layer)
        iteratorForward = self.line_forward_iterator(indexNextStart, self.current_layer)
        iteratorBackward = self.line_backward_iterator(indexPreviousStart, self.current_layer)

        locationComplex = location.dropAxis()

        logging.debug("original point to stretch: %s", locationComplex)

        relativeStretch = self.get_relative_stretch(locationComplex, iteratorForward) \
                          + self.get_relative_stretch(locationComplex, iteratorBackward)
        relativeStretch *= 0.8
        relativeStretch = self.get_cross_limited_stretch(relativeStretch, crossIteratorForward, locationComplex)
        relativeStretch = self.get_cross_limited_stretch(relativeStretch, crossIteratorBackward, locationComplex)

        relativeStretchLength = abs(relativeStretch)

        if relativeStretchLength > 1.0:
            relativeStretch /= relativeStretchLength

        logging.debug("relativeStretchLength: %f", relativeStretchLength)

        absoluteStretch = relativeStretch * self.thread_maximum_absolute_stretch
        stretchedPoint = location.dropAxis() + absoluteStretch

        result = Line()
        result.command = original_line.command
        result.x = stretchedPoint.real
        result.y = stretchedPoint.imag
        result.z = original_line.z
        result.f = self.feedRateMinute

        # TODO improve new extrusion length computation. It's clearly a very rough estimate
        if original_line.e is not None:
            result.e = original_line.e * (1 - abs(absoluteStretch))

        unsplit(result)

        logging.debug("stretched point: %f %f", result.x, result.y)

        return result

    def is_just_before_extrusion(self):
        """Determine if activate command is before linear move command."""
        for line in self.current_layer[self.line_number_in_layer + 1:]:
            if line.command in linear_move_gcodes or self.EXTRUSION_OFF_MARKER in line.raw:
                return False
            if self.EXTRUSION_ON_MARKER in line.raw:
                return True
        return False

    def set_edge_width(self, edge_width):
        # In the original code, the edge width found in the GCode was only used to recompute the
        # stretchFromDistance.
        # It does seem like either a typo or a hack around a problem I've yet to bump into.
        # For now, I'll apply the edge width to recompute all distance related variables
        self.edgeWidth = edge_width
        self.crossLimitDistance = self.edgeWidth * self.stretchRepository.crossLimitDistanceOverEdgeWidth

        self.loopMaximumAbsoluteStretch = self.edgeWidth * self.stretchRepository.loopStretchOverEdgeWidth
        self.edgeInsideAbsoluteStretch = self.edgeWidth * self.stretchRepository.edgeInsideStretchOverEdgeWidth
        self.edgeOutsideAbsoluteStretch = self.edgeWidth * self.stretchRepository.edgeOutsideStretchOverEdgeWidth

        self.stretchFromDistance = self.stretchRepository.stretchFromDistanceOverEdgeWidth * self.edgeWidth
        self.thread_maximum_absolute_stretch = 0

        self.crossLimitDistanceFraction = self.crossLimitDistance / 3
        self.crossLimitDistanceRemainder = self.crossLimitDistance - self.crossLimitDistanceFraction

    def parse_line(self, line):
        """Parse a gcode line and add it to the stretch skein."""

        # check for loop markers
        if self.is_inner_edge_begin(line):
            self.isLoop = True
            self.thread_maximum_absolute_stretch = self.edgeInsideAbsoluteStretch
        elif self.is_outer_edge_begin(line):
            self.isLoop = True
            self.thread_maximum_absolute_stretch = self.edgeOutsideAbsoluteStretch
        elif self.is_loop_begin(line):
            self.isLoop = True
            self.thread_maximum_absolute_stretch = self.loopMaximumAbsoluteStretch
        elif self.is_loop_end(line):
            self.isLoop = False
            self.set_stretch_to_path()

        # handle move command if in loop
        if line.command in linear_move_gcodes and self.isLoop and (line.x is not None or line.y is not None):
            return self.stretch_line(line)

        return line

    def set_stretch_to_path(self):
        """Set the thread stretch to path stretch and is loop false."""
        self.isLoop = False
        self.thread_maximum_absolute_stretch = 0

    def is_loop_begin(self, line):
        return self.LOOP_START_MARKER in line.raw

    def is_loop_end(self, line):
        return self.LOOP_STOP_MARKER in line.raw

    def is_inner_edge_begin(self, line):
        return self.INNER_EDGE_START_MARKER in line.raw

    def is_outer_edge_begin(self, line):
        return self.OUTER_EDGE_START_MARKER in line.raw

    def setup_filter(self):
        raise NotImplementedError


class Slic3rStretchFilter(StretchFilter):
    UNKNOWN = 0
    EXTERNAL_PERIMETER = 1
    EXTRA_PERIMETER = 2

    EDGE_WIDTH_REGEXP = re.compile(r'; external perimeters extrusion width\s+=\s+([\.\d]+)mm')

    def __init__(self, **kwargs):
        StretchFilter.__init__(self, **kwargs)

        self.line_forward_iterator = LineIteratorForward
        self.line_backward_iterator = LineIteratorBackward

        self.next_external_perimeter_is_outer = None
        self.current_type_line = None

    def new_perimeter(self, line, external=False):

        if external:
            if self.next_external_perimeter_is_outer:
                logging.debug("found external perimeter outer")
                line.raw += " ; " + StretchFilter.OUTER_EDGE_START_MARKER
                self.next_external_perimeter_is_outer = False
            else:
                logging.debug("found external perimeter inner")
                line.raw += " ; " + StretchFilter.INNER_EDGE_START_MARKER

            if self.current_type_line != self.EXTERNAL_PERIMETER:
                logging.debug("found end of loop")
                line.raw += " ; " + StretchFilter.LOOP_STOP_MARKER

            self.current_type_line = self.EXTERNAL_PERIMETER

        else:
            logging.debug("found extra perimeter")
            line.raw += " ; " + StretchFilter.LOOP_START_MARKER

            if self.EXTERNAL_PERIMETER == self.current_type_line:
                logging.debug("found end of loop")
                line.raw += " ; " + StretchFilter.LOOP_STOP_MARKER

            self.current_type_line = self.EXTRA_PERIMETER

    def setup_filter(self):

        edge_width_found = False
        extruding = False

        for self.current_layer in self.gcode.all_layers:
            self.next_external_perimeter_is_outer = True
            self.current_type_line = self.UNKNOWN

            for line_idx, line in enumerate(self.current_layer):

                # checking extrusion
                if not extruding and line.command in linear_move_gcodes and line.e is not None:
                    extruding = True
                    line.raw += " ; " + StretchFilter.EXTRUSION_ON_MARKER
                elif extruding and line.command in linear_move_gcodes and line.e is None and self.current_type_line in (
                        self.EXTRA_PERIMETER, self.EXTERNAL_PERIMETER):
                    extruding = False
                    line.raw += " ; " + StretchFilter.EXTRUSION_OFF_MARKER

                # checking perimeter type
                if '; perimeter external' in line.raw:

                    if self.EXTERNAL_PERIMETER != self.current_type_line:
                        self.new_perimeter(line, True)

                elif '; perimeter' in line.raw:

                    if self.EXTRA_PERIMETER != self.current_type_line:
                        self.new_perimeter(line)

                elif '; move to first perimeter point' in line.raw:
                    # search if next perimeter is external or not
                    for loop_ahead_idx in xrange(line_idx + 1, len(self.current_layer)):
                        if '; perimeter external' in self.current_layer[loop_ahead_idx].raw:
                            self.new_perimeter(line, True)
                            break
                        elif '; perimeter' in self.current_layer[loop_ahead_idx].raw:
                            self.new_perimeter(line)
                            break

                elif 'unretract' not in line.raw:

                    if self.current_type_line in (self.EXTRA_PERIMETER, self.EXTERNAL_PERIMETER):
                        logging.debug("found end of loop")
                        line.raw += " ; " + StretchFilter.LOOP_STOP_MARKER

                    self.current_type_line = self.UNKNOWN

                # checking for edge width
                match = self.EDGE_WIDTH_REGEXP.match(line.raw)
                if match:
                    edge_width_found = True
                    self.set_edge_width(float(match.group(1)))

            if self.current_type_line != self.UNKNOWN:
                logging.warn("unfinished loop")

        if not edge_width_found:
            logging.warn("no edge width found in comments, picking a default value")
            self.set_edge_width(0.4)


class CuraStretchFilter(StretchFilter):
    UNKNOWN = 0
    EXTERNAL_PERIMETER = 1
    EXTRA_PERIMETER = 2

    CURA_PROFILE_REGEXP = re.compile(r';CURA_PROFILE_STRING:(.*)$')

    def __init__(self, **kwargs):
        StretchFilter.__init__(self, **kwargs)

        self.line_forward_iterator = CuraLineIteratorForward
        self.line_backward_iterator = CuraLineIteratorBackward

    def new_perimeter(self, line, external=False, outer=False):

        if external:
            if outer:
                logging.debug("found external perimeter outer")
                line.raw += " ; " + StretchFilter.OUTER_EDGE_START_MARKER
            else:
                logging.debug("found external perimeter inner")
                line.raw += " ; " + StretchFilter.INNER_EDGE_START_MARKER

            if self.current_type_line != self.UNKNOWN:
                logging.debug("found end of loop")
                line.raw += " ; " + StretchFilter.LOOP_STOP_MARKER

            self.current_type_line = self.EXTERNAL_PERIMETER

        else:
            logging.debug("found extra perimeter")
            line.raw += " ; " + StretchFilter.LOOP_START_MARKER

            if self.current_type_line != self.UNKNOWN:
                logging.debug("found end of loop")
                line.raw += " ; " + StretchFilter.LOOP_STOP_MARKER

            self.current_type_line = self.EXTRA_PERIMETER

    def setup_filter(self):

        edge_width_found = False
        extruding = False

        for self.current_layer in self.gcode.all_layers:
            self.current_type_line = self.UNKNOWN
            next_line_marker = None

            for line_idx, line in enumerate(self.current_layer):

                # checking extrusion
                if not extruding and line.command in linear_move_gcodes and line.e is not None:
                    extruding = True
                    line.raw += " ; " + StretchFilter.EXTRUSION_ON_MARKER
                elif extruding and line.command in linear_move_gcodes and line.e is None and self.current_type_line in (
                        self.EXTRA_PERIMETER, self.EXTERNAL_PERIMETER):
                    extruding = False
                    line.raw += " ; " + StretchFilter.EXTRUSION_OFF_MARKER

                if next_line_marker is not None:
                    self.new_perimeter(line, *next_line_marker)
                    next_line_marker = None

                # checking perimeter type
                if 'TYPE:WALL-OUTER' in line.raw:
                    self.stop_loop(line)
                    next_line_marker = (True, True)

                elif 'TYPE:WALL-INNER' in line.raw:
                    self.stop_loop(line)
                    next_line_marker = (True, False)

                elif 'TYPE:SKIN' in line.raw:
                    self.stop_loop(line)
                    next_line_marker = (False, False)

                elif 'TYPE:FILL' in line.raw:
                    self.stop_loop(line)

                # end loop if we reach the end of the current layer
                if line_idx == len(self.current_layer) - 1:
                    self.stop_loop(line)

                # checking for edge width
                match = self.CURA_PROFILE_REGEXP.match(line.raw)
                if match:
                    edge_width_found = self.parse_cura_profile(match.group(1))

        if not edge_width_found:
            logging.warn("no edge width found in comments, picking a default value")
            self.set_edge_width(0.4)

    def parse_cura_profile(self, cura_profile):
        profileOpts, alt = zlib.decompress(base64.b64decode(cura_profile)).split('\f', 1)
        for option in profileOpts.split('\b'):
            if len(option) > 0:
                key, value = option.split('=', 1)
                logging.debug("found cura option %s = %s", key, value)

                if key == 'nozzle_size':
                    self.set_edge_width(float(value))
                    return True

        return False

    def stop_loop(self, line):
        if self.current_type_line != self.UNKNOWN:
            logging.debug("found end of loop")
            line.raw += " ; " + StretchFilter.LOOP_STOP_MARKER
        self.current_type_line = self.UNKNOWN


class SkeinforgeStretchFilter(StretchFilter):
    EDGE_WIDTH_REGEXP = re.compile(r'\(<edgeWidth> ([\.\d]+)')

    def parse_initialisation_line(self, line):
        # self.distanceFeedRate.search_decimal_places_carried(line.raw)
        if line.raw == '(</extruderInitialization>)':
            return True
        match = self.EDGE_WIDTH_REGEXP.match(line.raw)
        if match:
            self.set_edge_width(float(match.group(1)))
        return False

    def setup_filter(self):
        for self.current_layer in self.gcode.all_layers:
            for line in self.current_layer:
                self.parse_initialisation_line(line)
                if line.command == 'M101':
                    line.raw += '; ' + self.EXTRUSION_ON_MARKER
                elif line.command == 'M103':
                    line.raw += '; ' + self.EXTRUSION_OFF_MARKER
                elif line.raw.startswith("(<loop>"):
                    line.raw += '; ' + self.LOOP_START_MARKER
                elif line.raw.startswith("(<edge>") and not line.raw.startswith("(<edge> outer"):
                    line.raw += '; ' + self.INNER_EDGE_START_MARKER
                elif line.raw.startswith("(<edge> outer"):
                    line.raw += '; ' + self.OUTER_EDGE_START_MARKER
                elif line.raw.startswith("(</edge>)") or line.raw.startswith("(</loop>)"):
                    line.raw += '; ' + self.LOOP_STOP_MARKER
