# GCodeUtils is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GCodeUtils.  If not, see <http://www.gnu.org/licenses/>.

import logging

from gcodeutils.filter.arc_optimizer import GCodeArcOptimizerFilter
from gcodeutils.tests import open_gcode_file, gcode_eq
from gcodeutils.gcoder import PyLine

__author__ = 'Eyck Jentzsch <eyck@jepemuc.de>'

PyLine.EQ_EPSILON=1e-4 # write to disc truncates to 4 digits after comma so accuraccy needs to be adapted for testing

def test_arc_optimization():
    gcode = open_gcode_file('arc_raw.gcode')
    gcode_oracle = open_gcode_file('arc_raw-post.gcode')

    logging.basicConfig(level=logging.DEBUG)
    GCodeArcOptimizerFilter().filter(gcode)
    gcode_eq(gcode_oracle, gcode)

if __name__ == "__main__":
    test_arc_optimization()
