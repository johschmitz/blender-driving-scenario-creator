# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from . geometry import DSC_geometry
from . import helpers

from mathutils import Vector, Matrix
from math import pi


class DSC_geometry_line(DSC_geometry):

    def __init__(self):
        super().__init__()

    def load_section_curve(self, section):
        # Not needed for line since we can directly sample
        pass

    def update_plan_view(self, params, geometry_solver='default'):

        # Local starting point is 0 vector so length becomes length of end point vector
        length = (self.point_end_local - self.point_start_local).to_2d().length

        # Remember geometry parameters
        self.sections[-1]['curve_type'] = 'line'
        self.sections[-1]['geometry_solver'] = 'default'
        self.sections[-1]['point_start'] = params['points'][-2]
        self.sections[-1]['heading_start'] = params['heading_start']
        self.sections[-1]['curvature_start'] = 0
        self.sections[-1]['point_end'] = params['points'][-1]
        self.sections[-1]['heading_end'] = params['heading_start']
        self.sections[-1]['curvature_end'] = 0
        self.sections[-1]['length'] = length
        self.sections[-1]['valid'] = True

    def sample_plan_view(self, s):
        idx_section, s_section = self.get_section_idx_and_s(s)
        x_s = s_section
        y_s = 0
        curvature = 0
        hdg = 0
        xyz_s_local = self.sections[idx_section]['matrix_local'] @ Vector((x_s, y_s, 0.0))
        return xyz_s_local[0], xyz_s_local[1], hdg, curvature