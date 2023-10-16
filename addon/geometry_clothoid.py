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

from mathutils import Vector
from pyclothoids import Clothoid
from math import pi


class DSC_geometry_clothoid(DSC_geometry):

    def __init__(self):
        super().__init__(curve_type='clothoid')

    def update_plan_view(self, params, geometry_solver='default'):
        # Calculate geometry
        if geometry_solver == 'hermite' or geometry_solver == 'default':
            self.sections[-1]['curve'] = Clothoid.G1Hermite(
                self.point_start_local.x, self.point_start_local.y, self.heading_start_local,
                self.point_end_local.x, self.point_end_local.y, self.heading_end_local)

            # When the heading of start and end point is colinear the curvature
            # can become very small and the length becomes huge (solution is a gigantic
            # circle). Therefore as a workaround we limit the length to 10 km.
            if self.sections[-1]['curve'].length < 10000.0:
                self.sections[-1]['params']['valid'] = True
            else:
                self.sections[-1]['params']['valid'] = False
        elif geometry_solver == 'forward':
            if self.point_end_local == Vector((0.0, 0.0, 0.0)):
                # Handle edge case where points are identical
                self.sections[-1]['curve'].length = 0.0
                self.sections[-1]['curve'].KappaStart = 0.0
                self.sections[-1]['curve'].KappaEnd = 0.0
                self.sections[-1]['curve'].ThetaEnd = 0.0
                self.sections[-1]['params']['valid'] = False
            else:
                self.sections[-1]['curve'] = Clothoid.Forward(
                    self.point_start_local.x, self.point_start_local.y, self.heading_start_local,
                    self.curvature_start_local, self.point_end_local.x, self.point_end_local.y)
                # When the heading of start and end point is colinear the curvature
                # can become very small and the length becomes huge (solution is a gigantic
                # circle). Therefore as a workaround we limit the length to 10 km.
                if self.sections[-1]['curve'].length < 10000.0:
                    self.sections[-1]['params']['valid'] = True
                else:
                    self.sections[-1]['params']['valid'] = False

        # Remember geometry parameters, only update if valid solution is found
        if self.sections[-1]['params']['valid']:
            self.sections[-1]['params']['curve_type'] = 'spiral'
            self.sections[-1]['params']['point_start'] = params['points'][-2]
            self.sections[-1]['params']['heading_start'] = params['heading_start'] + self.heading_start_local
            self.sections[-1]['params']['point_end'] = params['points'][-1]
            self.sections[-1]['params']['heading_end'] = params['heading_start'] + self.sections[-1]['curve'].ThetaEnd
            self.sections[-1]['params']['length'] = self.sections[-1]['curve'].length
            self.sections[-1]['params']['curvature_start'] = self.sections[-1]['curve'].KappaStart
            self.sections[-1]['params']['curvature_end'] = self.sections[-1]['curve'].KappaEnd
            self.sections[-1]['params']['angle_end'] = self.sections[-1]['curve'].ThetaEnd

    def sample_plan_view(self, s):
        idx_section, s_section = self.get_section_idx_and_s(s)
        x_s = self.sections[idx_section]['curve'].X(s_section)
        y_s = self.sections[idx_section]['curve'].Y(s_section)
        curvature = self.sections[idx_section]['curve'].KappaStart + self.sections[idx_section]['curve'].dk * s_section
        hdg_t = self.sections[idx_section]['curve'].Theta(s_section) + pi/2
        return x_s, y_s, curvature, hdg_t
