import cStringIO
import math
import re

__author__ = 'olivier'


def getTagBracketedLine(tagName, value):
    'Get line with a begin tag, value and end tag.'
    return '(<%s> %s </%s>)' % (tagName, value, tagName)


def getTagBracketedProcedure(procedure):
    'Get line with a begin procedure tag, procedure and end procedure tag.'
    return getTagBracketedLine('procedureName', procedure)


def addLinesToCString(cString, lines):
    'Add lines which have something to cStringIO.'
    for line in lines:
        if line != '':
            cString.write(line + '\n')


def getRoundedToPlaces(decimalPlaces, number):
    'Get number rounded to a number of decimal places.'
    decimalPlacesRounded = max(1, int(round(decimalPlaces)))
    return round(number, decimalPlacesRounded)


def getRoundedToPlacesString(decimalPlaces, number):
    'Get number rounded to a number of decimal places as a string, without exponential formatting.'
    roundedToPlaces = getRoundedToPlaces(decimalPlaces, number)
    roundedToPlacesString = str(roundedToPlaces)
    if 'e' in roundedToPlacesString:
        return ('%.15f' % roundedToPlaces).rstrip('0')
    return roundedToPlacesString


def getFourSignificantFigures(number):
    'Get number rounded to four significant figures as a string.'
    if number == None:
        return None
    absoluteNumber = abs(number)
    if absoluteNumber >= 100.0:
        return getRoundedToPlacesString(2, number)
    if absoluteNumber < 0.000000001:
        return getRoundedToPlacesString(13, number)
    return getRoundedToPlacesString(3 - math.floor(math.log10(absoluteNumber)), number)


class DistanceFeedRate:
    'A class to limit the z feed rate and round values.'

    DECIMAL_PLACES_CARRIED_REGEXP = re.compile('^\(<decimalPlacesCarried> (\d+)')


    def __init__(self):
        'Initialize.'
        self.isAlteration = False
        self.decimalPlacesCarried = 3
        self.output = cStringIO.StringIO()

    def addFlowRateLine(self, flowRate):
        'Add a flow rate line.'
        self.output.write('M108 S%s\n' % getFourSignificantFigures(flowRate))

    def addGcodeFromFeedRateThreadZ(self, feedRateMinute, thread, travelFeedRateMinute, z):
        'Add a thread to the output.'
        if len(thread) > 0:
            self.addGcodeMovementZWithFeedRate(travelFeedRateMinute, thread[0], z)
        else:
            print('zero length vertex positions array which was skipped over, this should never happen.')
        if len(thread) < 2:
            print('thread of only one point in addGcodeFromFeedRateThreadZ in gcodec, this should never happen.')
            print(thread)
            return
        self.output.write('M101\n')  # Turn extruder on.
        for point in thread[1:]:
            self.addGcodeMovementZWithFeedRate(feedRateMinute, point, z)
        self.output.write('M103\n')  # Turn extruder off.

    # def addGcodeFromLoop(self, loop, z):
    # 	'Add the gcode loop.'
    # 	euclidean.addNestedRingBeginning(self, loop, z)
    # 	self.addPerimeterBlock(loop, z)
    # 	self.addLine('(</boundaryPerimeter>)')
    # 	self.addLine('(</nestedRing>)')

    def addGcodeFromThreadZ(self, thread, z):
        'Add a thread to the output.'
        if len(thread) > 0:
            self.addGcodeMovementZ(thread[0], z)
        else:
            print('zero length vertex positions array which was skipped over, this should never happen.')
        if len(thread) < 2:
            print('thread of only one point in addGcodeFromThreadZ in gcodec, this should never happen.')
            print(thread)
            return
        self.output.write('M101\n')  # Turn extruder on.
        for point in thread[1:]:
            self.addGcodeMovementZ(point, z)
        self.output.write('M103\n')  # Turn extruder off.

    def addGcodeMovementZ(self, point, z):
        'Add a movement to the output.'
        self.output.write(self.getLinearGcodeMovement(point, z) + '\n')

    def addGcodeMovementZWithFeedRate(self, feedRateMinute, point, z):
        'Add a movement to the output.'
        self.output.write(self.getLinearGcodeMovementWithFeedRate(feedRateMinute, point, z) + '\n')

    def addGcodeMovementZWithFeedRateVector3(self, feedRateMinute, vector3):
        'Add a movement to the output by Vector3.'
        xRounded = self.getRounded(vector3.x)
        yRounded = self.getRounded(vector3.y)
        self.output.write(
            'G1 X%s Y%s Z%s F%s\n' % (xRounded, yRounded, self.getRounded(vector3.z), self.getRounded(feedRateMinute)))

    def addLine(self, line):
        'Add a line of text and a newline to the output.'
        if len(line) > 0:
            self.output.write(line + '\n')

    def addLines(self, lines):
        'Add lines of text to the output.'
        addLinesToCString(self.output, lines)

    def addTagBracketedLine(self, tagName, value):
        'Add a begin tag, value and end tag.'
        self.addLine(getTagBracketedLine(tagName, value))

    def addTagRoundedLine(self, tagName, value):
        'Add a begin tag, rounded value and end tag.'
        self.addLine('(<%s> %s </%s>)' % (tagName, self.getRounded(value), tagName))

    def addTagBracketedProcedure(self, procedure):
        'Add a begin procedure tag, procedure and end procedure tag.'
        self.addLine(getTagBracketedProcedure(procedure))

    def getBoundaryLine(self, location):
        'Get boundary gcode line.'
        return '(<boundaryPoint> X%s Y%s Z%s </boundaryPoint>)' % (
            self.getRounded(location.x), self.getRounded(location.y), self.getRounded(location.z))

    def getFirstWordMovement(self, firstWord, location):
        'Get the start of the arc line.'
        return '%s X%s Y%s Z%s' % (
            firstWord, self.getRounded(location.x), self.getRounded(location.y), self.getRounded(location.z))

    def getInfillBoundaryLine(self, location):
        'Get infill boundary gcode line.'
        return '(<infillPoint> X%s Y%s Z%s </infillPoint>)' % (
            self.getRounded(location.x), self.getRounded(location.y), self.getRounded(location.z))

    def getIsAlteration(self, line):
        'Determine if it is an alteration.'
        if self.isAlteration:
            self.addLineCheckAlteration(line)
            return True
        return False

    def getLinearGcodeMovement(self, point, z):
        'Get a linear gcode movement.'
        return 'G1 X%s Y%s Z%s' % (self.getRounded(point.real), self.getRounded(point.imag), self.getRounded(z))

    def getLinearGcodeMovementWithFeedRate(self, feedRateMinute, point, z):
        'Get a z limited gcode movement.'
        linearGcodeMovement = self.getLinearGcodeMovement(point, z)
        if feedRateMinute == None:
            return linearGcodeMovement
        return linearGcodeMovement + ' F' + self.getRounded(feedRateMinute)

    def parseSplitLine(self, raw_line):
        '''Search for skeinforge specific decimalPlaceCarried setting to store it.'''
        match = self.DECIMAL_PLACES_CARRIED_REGEXP.match(raw_line)

        if match:
            self.decimalPlacesCarried = int(match.group(1))


    def getRounded(self, number):
        'Get number rounded to the number of carried decimal places as a string.'
        return getRoundedToPlacesString(self.decimalPlacesCarried, number)
