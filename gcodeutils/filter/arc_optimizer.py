# coding=utf-8
# GCodeUtils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GCodeUtils.  If not, see <http://www.gnu.org/licenses/>.

import logging
from math import sqrt, sin
import cmath
from gcodeutils.filter.filter import GCodeFilter
from gcodeutils.gcoder import Line, move_gcodes, unsplit

__author__ = 'Eyck Jentzsch <eyck@jepemuc.de>'

# constraints for the detection algorithm
MIN_SEGMENTS = 8              # number is segments forming an arc
MAX_RADIUS = 200              # mm, maximum radius of the detectable circle
ALIGNMENT_ERROR = 0.015       # 15 µm, max. offset a point might be off of the resulting circle
PHASE_ERROR = 5*cmath.pi/180  # 5° in radian, max deviation of the angle steps forming a circle
EXTRUSION_ERROR = 0.15        # 15%, maximum deviation of the extrusion for the segments
EPSILON = 0.000001            # epsilon for zero comapriosn of float. everything less than will be treated as zero

EXTRUSION_CORRECTION_LIMIT=0.01 # 1%, if the length of all segments deviates more than this from the legnth of the arc
                                # a correction gcode is generated in absolute coordinate mode

logger = logging.getLogger('arc_optimizer')

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
        return "Point(%.3f, %.3f)" % (self.x, self.y)

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
    an object representing a cicle arc
    """

    __slots__ = ('radius', 'center', 'direction', 'start', 'end')

    def __init__(self, radius=0.0, center=Point(0, 0), direction=0.0, start=Point(0, 0), end=Point(0, 0)):
        self.radius = radius
        self.center = center
        self.direction = direction
        self.start = start
        self.end = end

    def __str__(self):
        circle_str="Arc(r=%.5f, center=%s from %s to %s" % (self.radius, str(self.center), str(self.start), str(self.end))
        return "CCW-" + circle_str if self.direction > 0.0 else "CW-" + circle_str


class GCodeArcOptimizerFilter(GCodeFilter):
    """filter replacing subsequent G1 moves with G2/G3 (cirle c/cw if applicable"""

    queue = []
    valid_circle = False

    def __init__(self):
        self.queue = []

    @staticmethod
    def phase_diff(phase1, phase2):
        """
        calculate the difference between to angles (in radian) starting a the positive x-axis

        asumption: we have MIN_SEGMENTS segments per cicle so the angle cannot be larget than 2*PI/MIN_SEGMENTS
        if angle is positive: diff=2*PI+p1-p2 if  p1<0 & p2>0 else p1-p2
        if angle is negative: diff=     p1-p2-2*PI if  p2<0 && p1>0 else p1-p2

        :param phase1: angle 1
        :param phase2: angle 2
        :return: the difference
        """
        diff = phase1 - phase2
        if diff < -cmath.pi:
            diff += 2 * cmath.pi
        elif diff > cmath.pi:
            diff -= 2 * cmath.pi
        return diff

    def opcode_filter(self, opcode):
        """
        default implementation of the opcode filter
        :param opcode: the gcode of the current line
        :return: the modified opcode
        """
        return opcode

    def parse_gcode(self, gcode, opcode_filter):
        for layer in gcode.all_layers:
            self.parse_layer(layer, opcode_filter)
        if len(self.queue) > 0:
            layer += self.queue

    def get_circle_least_squares(self):
        """
        get cicle based on least-square error method
        :return: the estimated cicle
        """
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
        if suu < EPSILON or svv < EPSILON:
            return None
        v = (((svvv + svuu) / 2) - ((suv / 2) * ((suuu + suvv) / suu))) / (((-(suv * suv)) / suu) + svv)
        u = (((suuu + suvv) / 2) - (v * suv)) / suu
        # calculate direction
        center = Point(x=u + xbar, y=v + ybar)
        p0 = complex(self.queue[0].current_x - center.x, self.queue[0].current_y - center.y)
        p1 = complex(self.queue[2].current_x - center.x, self.queue[2].current_y - center.y)
        return Circle(radius=sqrt((u * u) + (v * v) + ((suu + svv) / count)),
                      center=center,
                      direction=GCodeArcOptimizerFilter.phase_diff(cmath.phase(p1), cmath.phase(p0)),
                      start=Point(self.queue[0].current_x, self.queue[0].current_y),
                      end=Point(self.queue[-1].current_x, self.queue[-1].current_y))

    def get_circle_radius_errors(self, circle):
        """
        calculate the errors between the radius of the estimated circle and the distance of points on the circle to
        the center point
        :param circle: the estimated circle
        :return: list of error values
        """
        errors = []
        for line in self.queue:
            length = Point(circle.center.x - line.current_x, circle.center.y - line.current_y).amplitude()
            errors.append(abs(length - circle.radius))
        return errors

    def get_phase_diffs(self, circle):
        """
        get the angle between successive points
        :param circle:
        :return:
        """
        center = circle.center
        phases = [cmath.phase(complex(line.current_x - center.x, line.current_y - center.y)) for line in self.queue]
        phase_diffs = [GCodeArcOptimizerFilter.phase_diff(phases[idx], phases[idx - 1]) for idx in
                       range(1, len(phases))]
        return phase_diffs

    def get_circle_angle_errors(self, circle):
        """
        calculate the angle errors between 3 consecutive points on the circle

        :param circle: the estimated circle
        :return: the list of angle errors
        """
        phase_diffs = self.get_phase_diffs(circle)
        phase_diff_avg = sum(phase_diffs) / len(phase_diffs)
        phase_errors = [phase_diff - phase_diff_avg for phase_diff in phase_diffs]
        return phase_errors

    def get_circle(self):
        """
        check if we have a valid circle. There are three criterias
        - all points have to be on the cicle arc (with max ALIGNMENT_ERROR variation)
        - all points are equidistant to each other (the angle between them is of same size with max PHASE_ERROR
          variation)
        :return: a tuple consisting of the bool indication an erroneous circle and the estimated circle
        """
        circle = self.get_circle_least_squares()
        if circle is None or circle.radius>MAX_RADIUS:
            return True, circle
        radius_err = self.get_circle_radius_errors(circle)
        if any([error > ALIGNMENT_ERROR for error in radius_err]):
            return True, circle
        angle_err = self.get_circle_angle_errors(circle)
        return any([error > PHASE_ERROR for error in angle_err]), circle

    def get_distances(self):
        """
        calculate extrusion and distances allong a path and its ratios
        :return: a map containing the values
        """
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
                if path < EPSILON:
                    extrusions['ratio'][num] = 0
                else:
                    extrusions['ratio'][num] = extrusions['filament'][num] / path
            prev = line
        extrusions['avg']['filament'] = extrusions['total']['filament'] / len(self.queue)
        extrusions['avg']['path'] = extrusions['total']['path'] / len(self.queue)
        extrusions['avg']['ratio'] = extrusions['total']['filament'] / extrusions['total']['path']
        return extrusions

    def queue_valid(self):
        """
        check if entries in the queue constitute a valid circle
        :return: a tuple consisting of the bool indication an erroneous circle and the estimated circle
        """
        # check from 1 as idx 0 indicates the move to the start point
        all_e = False if self.queue[1].e is None else True
        cur_f = self.queue[1].current_f
        cur_z = self.queue[1].current_z
        valid_e = all([line.e is not None for line in self.queue[1:]]) if all_e else \
            not any([line.e is not None for line in self.queue[1:]])
        valid_f = all([line.current_f == cur_f for line in self.queue[1:]])
        valid_z = all([line.current_z == cur_z for line in self.queue[1:]])
        if not (valid_e and valid_f and valid_z):
            return True, None
        if all_e:
            extrusions = self.get_distances()
            if extrusions['avg']['ratio'] < EPSILON:
                return True, None
            valid = all(abs((curext / extrusions['avg']['ratio']) - 1) < EXTRUSION_ERROR for curext in
                        extrusions['ratio'].values())
            if not valid:
                return True, None
        return self.get_circle()

    def to_gcode(self):
        """
        translate a sequence of segments into a circular gcode command
        :return: the gcode command
        """
        result=[self.queue[0]]
        last = self.queue.pop()
        count = len(self.queue)
        end_point = self.queue[-1]
        error, circle = self.get_circle()
        extrusions = self.get_distances()
        op1 = Line()
        result.append(op1)
        op1.command = "G3" if circle.direction >0 else "G2" # G2 is CW, G3 CCW
        op1.x = round(circle.end.x, 3)
        op1.y = round(circle.end.y, 3)
        op1.i = round(circle.center.x - circle.start.x, 3)
        op1.j = round(circle.center.y - circle.start.y, 3)
        if end_point.relative_e:
            # calculate extrusion correction
            # arc length   b = r·alpha (alpha in radian)
            # chord length s = 2·r·sin(alpha/2)
            # resulting arc extrusion is s0*b/s
            op1.e = sum([ s0*(circle.radius*alpha)/(2*circle.radius*sin(alpha/2))
                  for s0, alpha in zip(extrusions['filament'].values(), self.get_phase_diffs(circle))])
            op1.relative_e = True
        else:
            # absolute mode: fall-back to the original length
            phase_diffs=self.get_phase_diffs(circle)
            arc_lens=[ alpha*circle.radius for alpha in phase_diffs]
            arc_extrusion_length=sum(arc_lens)*extrusions['avg']['ratio']
            op1.e=self.queue[0].current_e+arc_extrusion_length
            op1.relative_e=False
            rel = arc_extrusion_length/extrusions['total']['filament']
            if (rel - 1) > EXTRUSION_CORRECTION_LIMIT:
                op2= Line()
                op2.command="G92"
                op2.e = op2.current_e = end_point.current_e
                unsplit(op2)
                op2.raw += "; generated as arc to path relation is %f" % rel
                result.append(op2)
        op1.f = end_point.current_f
        unsplit(op1)
        op1.raw += "; generated from %s segments" % (count - 1)
        self.valid_circle = False
        result.append(last)
        logger.info(" generated arc from %s segments" % (count - 1))
        logger.debug("arc is "+str(circle))
        return result

    def opcode_filter(self, opcode):
        """
        scan the sequence of opcodes for valid cirle arcs
        :param opcode: the opcode
        :return: the resulting opcode or a list of resulting opcodes
        """
        if opcode.command is None and len(self.queue) > 0:
            opcode.current_x  =self.queue[-1].current_x
            opcode.current_y = self.queue[-1].current_y
            opcode.current_z = self.queue[-1].current_z
            opcode.current_e = self.queue[-1].current_e
            opcode.current_f = self.queue[-1].current_f
        self.queue.append(opcode)
        count = len(self.queue)
        if count > MIN_SEGMENTS:
            if not self.queue[-1].command in move_gcodes:
                if self.valid_circle:
                    # the last element inserted invalidated the circle, so process & flush
                    result = self.to_gcode()
                else:
                    # flush the queue as we have a GCode resetting the processing
                    result = self.queue
                self.queue = []
                return result
            else:
                error, circle = self.queue_valid()
                if error:
                    if self.valid_circle:
                        # the last element inserted invalidated the circle
                        result = self.to_gcode()
                        # since last elem was a move keep it in the queue
                        self.queue = [result.pop()]
                        return result
                    else:
                        return self.queue.pop(0)
                else:
                    self.valid_circle = True
                    return []
        else:
            if self.queue[-1].command in move_gcodes or self.queue[-1].command is None:
                return []
            else:
                # flush the queue as we have a GCode resetting the processing
                result = self.queue
                self.queue = []
                self.valid_circle = False
                return result
