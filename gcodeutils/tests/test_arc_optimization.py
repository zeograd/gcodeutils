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
    gcode1 = open_gcode_file('arc_raw_1.gcode')
    gcode_ref1 = open_gcode_file('arc_raw_1-ref.gcode')

    logging.basicConfig(level=logging.DEBUG)
    GCodeArcOptimizerFilter().filter(gcode1)
    gcode_eq(gcode_ref1, gcode1)


def test_arc_optimization_2():
    gcode2 = open_gcode_file('arc_raw_2.gcode')
    gcode_ref2 = open_gcode_file('arc_raw_2-ref.gcode')

    logging.basicConfig(level=logging.DEBUG)
    GCodeArcOptimizerFilter().filter(gcode2)
    gcode_eq(gcode_ref2, gcode2)


if __name__ == "__main__":
    test_arc_optimization_1()
    test_arc_optimization_2()
