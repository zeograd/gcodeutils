# GCodeUtils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GCodeUtils.  If not, see <http://www.gnu.org/licenses/>.

#import logging
from math import sqrt
import cmath
from gcodeutils.filter.filter import GCodeFilter
from gcodeutils.gcoder import Line, move_gcodes, unsplit

__author__ = 'Eyck Jentzsch <eyck@jepemuc.de>'

MIN_SEGMENTS = 8
ALIGNMENT_ERROR = 0.001  # mm
EXTRUSION_ERROR = 0.15  # percent


class Point(object):
    """
    an object representing a 2-dimensional point
    """

    __slots__ = ('x', 'y')

    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __str__(self):
        return "Point(%f, %f)" % self.x, self.y

    def amplitude(self):
        return sqrt(self.x * self.x + self.y * self.y)

    def distance_to(self, other):
        xdiff = self.x - other.x
        xdiffsq = pow(xdiff, 2)
        ydiff = self.y - other.y
        ydiffsq = pow(ydiff, 2)
        return sqrt(xdiffsq + ydiffsq)


class Circle(object):
    """
    an object representing a cicle
    """

    __slots__ = ('radius', 'center', 'direction', 'start', 'end')

    def __init__(self, radius=0.0, center=Point(0, 0), direction=None, start=Point(0, 0), end=Point(0, 0)):
        self.radius = radius
        self.center = center
        self.direction = direction
        self.start = start
        self.end = end

    def __str__(self):
        return self.direction + "-Cicrle(r=%f, center=%s from %s to %s" % self.radius, self.center.__str__(), \
               self.start.__str__(), self.end.__str__()


class GCodeArcOptimizerFilter(GCodeFilter):
    """filter replacing subsequent G1 moves with G2/G3 (cirle c/cw if applicable"""

    queue = []
    valid_circle = False

    def opcode_filter(self, opcode):
        return opcode

    def get_circle_least_squares(self):
        count = len(self.queue)
        xbar = sum(i.current_x for i in self.queue) / count
        ybar = sum(i.current_y for i in self.queue) / count
        suu = 0
        suuu = 0
        suvv = 0
        suv = 0
        svv = 0
        svvv = 0
        svuu = 0
        for line in self.queue:
            pt = Point(line.current_x - xbar, line.current_y - ybar)
            suu += pt.x * pt.x
            suuu += pt.x * pt.x * pt.x
            suvv += pt.x * pt.y * pt.y
            suv += pt.x * pt.y
            svv += pt.y * pt.y
            svvv += pt.y * pt.y * pt.y
            svuu += pt.y * pt.x * pt.x
        v = (((svvv + svuu) / 2) - ((suv / 2) * ((suuu + suvv) / suu))) / (((-(suv * suv)) / suu) + svv)
        u = (((suuu + suvv) / 2) - (v * suv)) / suu
        # calculate direction
        center = Point(x=u + xbar, y=v + ybar)
        p0 = cmath.phase(complex(self.queue[0].current_x - center.x, self.queue[0].current_y - center.y))
        p1 = cmath.phase(complex(self.queue[1].current_x - center.x, self.queue[1].current_y - center.y))
        return Circle(radius=sqrt((u * u) + (v * v) + ((suu + svv) / count)),
                      center=center,
                      direction="CCW" if p0 < p1 else "CW",
                      start=Point(self.queue[0].current_x, self.queue[0].current_y),
                      end=Point(self.queue[-1].current_x, self.queue[-1].current_y))

    def get_circle_errors(self, circle):
        errors = []
        for line in self.queue:
            length = Point(circle.center.x - line.current_x, circle.center.y - line.current_y).amplitude()
            errors.append(abs(length - circle.radius))
        return errors

    def get_circle(self):
        circle = self.get_circle_least_squares()
        errors = self.get_circle_errors(circle)
        return any([error > ALIGNMENT_ERROR for error in errors]), circle

    def get_distances(self):
        extrusions = {
            'total': {
                'path': 0,
                'filament': 0,
            },
            'avg': {
                'path': 0,
                'filament': 0,
                'ratio': 0,
            },
            'filament': {},
            'path': {},
            'ratio': {}
        }
        prev = None
        for num, line in enumerate(self.queue):
            if prev is not None:
                path = round(Point(line.current_x, line.current_y).distance_to(
                    Point(prev.current_x, prev.current_y)), 7)
                extrusion = line.e if line.relative_e else (line.e - (0 if prev.e is None else prev.e))
                extrusions['total']['filament'] += extrusion
                extrusions['total']['path'] += path
                extrusions['filament'][num] = extrusion
                extrusions['path'][num] = path
                extrusions['ratio'][num] = extrusions['filament'][num] / path
            prev = line
        extrusions['avg']['filament'] = extrusions['total']['filament'] / len(self.queue)
        extrusions['avg']['path'] = extrusions['total']['path'] / len(self.queue)
        extrusions['avg']['ratio'] = extrusions['total']['filament'] / extrusions['total']['path']
        return extrusions

    def queue_valid(self):
        # check from 1 as idx 0 indicates the move to the start point
        all_e = False if self.queue[1].e is None else True
        all_f = False if self.queue[1].f is None else True
        cur_z = self.queue[1].current_z
        for line in self.queue[1:]:
            all_e &= line.f is None and line.e is not None
            all_f &= line.e is None and line.f is not None
            if cur_z != line.current_z:  # check is all in same layer
                return True, None
        if not (all_e or all_f):
            return True, None
        if all_e:
            extrusions = self.get_distances()
            valid = all(abs((curext / extrusions['avg']['ratio']) - 1) < EXTRUSION_ERROR for curext in
                        extrusions['ratio'].itervalues())
            if not valid:
                return True, None
        return self.get_circle()

    def to_gcode(self):
        first = self.queue[0]
        last = self.queue.pop()
        count = len(self.queue)
        error, circle = self.get_circle()
        extrusions = self.get_distances()
        op1 = Line()
        op1.command = "G3" if circle.direction == "CCW" else "G2"
        op1.x = round(circle.end.x, 3)
        op1.y = round(circle.end.y, 3)
        op1.i = round(circle.center.x - circle.start.x, 3)
        op1.j = round(circle.center.y - circle.start.y, 3)
        op1.e = extrusions['total']['filament']
        unsplit(op1)
        op1.raw += "; generated from %s segments" % (count-1)
        self.valid_circle = False
        return first, op1, last

    def opcode_filter(self, x):
        self.queue.append(x)
        count = len(self.queue)
        if count > MIN_SEGMENTS:
            if not self.queue[-1].command in move_gcodes:
                if self.valid_circle:
                    # the last element inserted invalidated the circle, so process & flush
                    result = self.to_gcode()
                else:
                    # flush the queue as we have a GCode resetting the processing
                    result = self.queue[:]
                self.queue = []
                return result
            else:
                error, circle = self.queue_valid()
                if error:
                    if self.valid_circle:
                        # the last element inserted invalidated the circle
                        first, circle_gcode, last = self.to_gcode()
                        # since last elem was a move keep it in the queue
                        self.queue = [last]
                        return [first, circle_gcode]
                    else:
                        return self.queue.pop(0)
                else:
                    self.valid_circle = True
                    return []
        else:
            if not self.queue[-1].command in move_gcodes:
                # flush the queue as we have a GCode resetting the processing
                result = self.queue[:]
                self.queue = []
                self.valid_circle = False
                return result
            else:
                return []
