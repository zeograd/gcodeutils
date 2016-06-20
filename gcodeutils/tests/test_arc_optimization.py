# GCodeUtils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GCodeUtils.  If not, see <http://www.gnu.org/licenses/>.

import logging
import sys

from gcodeutils.filter.arc_optimizer import GCodeArcOptimizerFilter
from gcodeutils.tests import open_gcode_file, gcode_eq
from gcodeutils.gcoder import PyLine
from gcodeutils.gcoder import GCode

__author__ = 'Eyck Jentzsch <eyck@jepemuc.de>'

PyLine.EQ_EPSILON=1e-4 # write to disc truncates to 4 digits after comma so accuraccy needs to be adapted for testing


def test_arc_optimization_1():
    gcode = open_gcode_file('arc_raw_1.gcode')
    gcode_ref = open_gcode_file('arc_ref_1.gcode')
    logging.basicConfig(level=logging.DEBUG)
    GCodeArcOptimizerFilter().filter(gcode)
    gcode_eq(gcode_ref, gcode)


def test_arc_optimization_2():
    gcode = open_gcode_file('arc_raw_2.gcode')
    gcode_ref = open_gcode_file('arc_ref_2.gcode')
    logging.basicConfig(level=logging.DEBUG)
    GCodeArcOptimizerFilter().filter(gcode)
    gcode_eq(gcode_ref, gcode)


def test_arc_optimization_3():
    gcode = open_gcode_file('arc_raw_3.gcode')
    gcode_ref = open_gcode_file('arc_raw_3.gcode')
    logging.basicConfig(level=logging.DEBUG)
    GCodeArcOptimizerFilter().filter(gcode)
    gcode_eq(gcode_ref, gcode)


def test_arc_optimization_4():
    gcode = open_gcode_file('arc_raw_4.gcode')
    gcode_ref = open_gcode_file('arc_ref_4.gcode')
    logging.basicConfig(level=logging.DEBUG)
    GCodeArcOptimizerFilter().filter(gcode)
    gcode_eq(gcode_ref, gcode)


if __name__ == "__main__":
    test_arc_optimization_1()
    test_arc_optimization_2()
    test_arc_optimization_3()
    test_arc_optimization_4()
