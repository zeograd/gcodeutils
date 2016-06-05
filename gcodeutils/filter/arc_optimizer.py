#import logging
from math import sqrt
import cmath
from gcodeutils.filter.filter import GCodeFilter
from gcodeutils.gcoder import Line, move_gcodes, unsplit

__author__ = 'Eyck Jentzsch <eyck@jepemuc.de>'

MIN_SEGMENTS = 8
ALIGNMENT_ERROR = 0.001  # mm
EXTRUSION_ERROR = 0.15   # percent


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
        return "Point(" + self.x + "," + self.y + ")"

    def amplitude(self):
        return sqrt(self.x * self.x + self.y * self.y)

    def distanceTo(self, other):
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
        return self.direction+"-Cicrle(r=" + self.radius + ",center" + self.center + "from "+self.start+" to "+self.end+")"


class GCodeArcOptimizerFilter(GCodeFilter):
    """filter replacing subsequent G1 moves with G2/G3 (cirle c/cw if applicable"""

    queue = []
    valid_circle = False
    alignment_error = 0.0001
    last_circle = Circle()
    extrusion_error = 0.15
    pos_error = 0.1

    def __init__(self, x=None, y=None, **kwargs):
        self.translate_x = x or 0.
        self.translate_y = y or 0.
        self.first_move_after_home = False
        self.absolute_distance_mode = None  # None if when it is unknown

    def opcode_filter(self, opcode):
        return opcode

    def getCircleLeastSquares(self):
        N = len(self.queue)
        xbar = sum(i.x for i in self.queue) / N
        ybar = sum(i.y for i in self.queue) / N
        Suu = 0
        Suuu = 0
        Suvv = 0
        Suv = 0
        Svv = 0
        Svvv = 0
        Svuu = 0
        for line in self.queue:
            pt = Point(line.x - xbar, line.y - ybar)
            Suu += pt.x * pt.x
            Suuu += pt.x * pt.x * pt.x
            Suvv += pt.x * pt.y * pt.y
            Suv += pt.x * pt.y
            Svv += pt.y * pt.y
            Svvv += pt.y * pt.y * pt.y
            Svuu += pt.y * pt.x * pt.x
        v = (((Svvv + Svuu) / 2) - ((Suv / 2) * ((Suuu + Suvv) / Suu))) / (((-(Suv * Suv)) / Suu) + Svv)
        u = (((Suuu + Suvv) / 2) - (v * Suv)) / (Suu)
        # calculate direction
        center = Point(x=u + xbar, y=v + ybar)
        p0 = cmath.phase(complex(self.queue[0].x - center.x, self.queue[0].y - center.y))
        p1 = cmath.phase(complex(self.queue[1].x - center.x, self.queue[1].y - center.y))
        return Circle(radius=sqrt((u * u) + (v * v) + ((Suu + Svv) / N)),
                         center=center,
                         direction="CCW" if p0 < p1 else "CW",
                         start=Point(self.queue[0].x, self.queue[0].y),
                         end=Point(self.queue[-1].x, self.queue[-1].y))

    def getCircleErrors(self, circle):
        errors = []
        for line in self.queue:
            length = Point(circle.center.x - line.x, circle.center.y - line.y).amplitude()
            errors.append(abs(length - circle.radius))
        return errors

    def getCircle(self):
        circle = self.getCircleLeastSquares()
        errors = self.getCircleErrors(circle)
        return any([error > ALIGNMENT_ERROR for error in errors]), circle

    def getDistances(self):
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
        prev = None;
        for num, line in enumerate(self.queue):
            if prev is not None:
                path = round(Point(line.current_x, line.current_y).distanceTo(Point(prev.current_x, prev.current_y)), 7)
                filLength = 0 if prev.e is None else line.e if line.relative_e else (line.e - prev.e)
                extrusions['total']['filament'] += filLength
                extrusions['total']['path'] += path;
                extrusions['filament'][num] = filLength
                extrusions['path'][num] = path;
                extrusions['ratio'][num] = extrusions['filament'][num] / path
            prev = line
        extrusions['avg']['filament'] = extrusions['total']['filament'] / len(self.queue)
        extrusions['avg']['path'] = extrusions['total']['path'] / len(self.queue)
        extrusions['avg']['ratio'] = extrusions['total']['filament'] / extrusions['total']['path']
        return extrusions

    def queueValid(self):
        ## check from 1 as idx 0 indicates the move to the start point
        allE = False if self.queue[1].e is None else True
        allF = False if self.queue[1].f is None else True
        curZ = self.queue[1].current_z
        for line in self.queue[1:]:
            allE &= line.f is None and line.e is not None
            allF &= line.e is None and line.f is not None
            if curZ != line.current_z: # check is all in same layer
                return True, None
        if not (allE or allF):
            return True, None
        if allE:
            extrusions = self.getDistances()
            valid = all(abs((curext / extrusions['avg']['ratio']) - 1) < EXTRUSION_ERROR for curext in
                        extrusions['ratio'].itervalues())
            if not valid:
                return True, None
        return self.getCircle()

    def toGcode(self, last=None):
        first = self.queue[0]
        last = self.queue.pop()
        error, circle = self.getCircle()
        extrusions = self.getDistances()
        op1 = Line()
        op1.command = "G3" if circle.direction == "CCW" else "G2"
        op1.x = round(circle.end.x, 3)
        op1.y = round(circle.end.y, 3)
        op1.i = round(circle.center.x - circle.start.x, 3)
        op1.j = round(circle.center.y - circle.start.y, 3)
        op1.e = extrusions['total']['filament']
        unsplit(op1)
        self.valid_circle = False
        return first, op1, last

    def opcode_filter(self, opcode):
        self.queue.append(opcode)
        count = len(self.queue)
        if count > MIN_SEGMENTS:
            if not self.queue[-1].command in move_gcodes:
                if self.valid_circle:
                    # the last element inserted invalidated the circle, so process & flush
                    result = self.toGcode()
                else:
                    # flush the queue as we have a GCode resetting the processing
                    result = self.queue[:]
                self.queue = []
                return result
            else:
                error, circle = self.queueValid()
                if error:
                    if self.valid_circle:
                        # the last element inserted invalidated the circle
                        first, circleGcode, last = self.toGcode()
                        # since last elem was a move keep it in the queue
                        self.queue = [last]
                        return [first, circleGcode]
                    else:
                        return self.queue.pop(0)
                else:
                    self.valid_circle = True
                    return None
        else:
            if not self.queue[-1].command in move_gcodes:
                # flush the queue as we have a GCode resetting the processing
                result = self.queue[:]
                self.queue = []
                self.valid_circle = False
                return result
            else:
                return None
