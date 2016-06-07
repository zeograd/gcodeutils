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
ALIGNMENT_ERROR = 0.01  # mm
PHASE_ERROR = 0.02      # radian
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

    def get_circle_radius_errors(self, circle):
        errors = []
        for line in self.queue:
            length = Point(circle.center.x - line.current_x, circle.center.y - line.current_y).amplitude()
            errors.append(abs(length - circle.radius))
        return errors

    def phase_diff(self, phase1, phase2):
        """
        # asumption: we have MIN_SEGMENTS segments per cicle so the angle cannot be larget than 2*PI/MIN_SEGMENTS
        # boundary condition is
        # if angle is positive: diff=2*PI+p1-p2 if  p1<0 & p2>0 else p1-p2
        # if angle is negative: diff=     p1-p2-2*PI if  p2<0 && p1>0 else p1-p2
        # absulute value:
        # diff=abs(phase1-phase2)
        # return min(diff, 2*cmath.pi-diff )
        """
        diff = phase1 - phase2
        if diff < -cmath.pi:
            diff += 2 * cmath.pi
        elif diff > cmath.pi:
            diff -= 2 * cmath.pi
        return diff

    def get_circle_angle_errors(self, circle):
        center=circle.center
        phases = [cmath.phase(complex(line.current_x - center.x, line.current_y - center.y)) for line in self.queue]
        phase_diffs=[self.phase_diff(phases[idx],phases[idx-1]) for idx in range(1,len(phases)-1)]
        phase_diff_avg = sum(phase_diffs) / len(phase_diffs)
        phase_errors=[phase_diff - phase_diff_avg for phase_diff in phase_diffs]
        return phase_errors

    def get_circle(self):
        circle = self.get_circle_least_squares()
        radius_err = self.get_circle_radius_errors(circle)
        if any([error > ALIGNMENT_ERROR for error in radius_err]):
            return True, circle
        angle_err = self.get_circle_angle_errors(circle)
        return any([error > PHASE_ERROR for error in angle_err]), circle

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
                extrusion = line.e if line.relative_e else (line.current_e - prev.current_e)
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
        cur_f = self.queue[1].current_f
        cur_z = self.queue[1].current_z
        valid_e =  all([line.e is not None for line in self.queue[1:]]) if all_e else \
            not any([line.e is not None for line in self.queue[1:]])
        valid_f = all([line.current_f == cur_f for line in self.queue[1:]])
        valid_z = all([line.current_z == cur_z for line in self.queue[1:]])
        if not (valid_e and valid_f and valid_z):
            return True, None
        if all_e:
            extrusions = self.get_distances()
            if extrusions['avg']['ratio']==0:
                raise ArithmeticError
            valid = all(abs((curext / extrusions['avg']['ratio']) - 1) < EXTRUSION_ERROR for curext in
                        extrusions['ratio'].itervalues())
            if not valid:
                return True, None
        return self.get_circle()

    def to_gcode(self):
        first = self.queue[0]
        last = self.queue.pop()
        count = len(self.queue)
        end_point=self.queue[-1]
        error, circle = self.get_circle()
        extrusions = self.get_distances()
        op1 = Line()
        op1.command = "G3" if circle.direction == "CCW" else "G2"
        op1.x = round(circle.end.x, 3)
        op1.y = round(circle.end.y, 3)
        op1.i = round(circle.center.x - circle.start.x, 3)
        op1.j = round(circle.center.y - circle.start.y, 3)
        op1.e = extrusions['total']['filament'] if end_point.relative_e else end_point.e
        op1.f = end_point.current_f
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
