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
        super().__init__()

    def load_section_curve(self, section):
        heading_local = self.matrix_world.to_euler().z
        point_start_local = self.matrix_world.inverted() @ Vector(section['point_start'])
        point_end_local = self.matrix_world.inverted() @ Vector(section['point_end'])
        if section['geometry_solver'] == 'hermite' or section['geometry_solver'] == 'default':
            section_curve = Clothoid.G1Hermite(
                point_start_local.x, point_start_local.y, section['heading_start'] - heading_local,
                point_end_local.x, point_end_local.y, section['heading_end'] - heading_local)
        elif section['geometry_solver'] == 'forward':
            section_curve = Clothoid.Forward(
                point_start_local.x, point_start_local.y, section['heading_start'] - heading_local,
                section['curvature_start'], point_end_local.x, point_end_local.y)
        self.section_curves.append(section_curve)

    def update_plan_view(self, params, geometry_solver='default'):
        # Calculate geometry
        if geometry_solver == 'hermite' or geometry_solver == 'default':
            self.section_curves[-1] = Clothoid.G1Hermite(
                self.point_start_local.x, self.point_start_local.y, self.heading_start_local,
                self.point_end_local.x, self.point_end_local.y, self.heading_end_local)

            # When the heading of start and end point is colinear the curvature
            # can become very small and the length becomes huge (solution is a gigantic
            # circle). Therefore as a workaround we limit the length to 10 km.
            if self.section_curves[-1].length < 10000.0:
                self.sections[-1]['valid'] = True
            else:
                self.sections[-1]['valid'] = False
        elif geometry_solver == 'forward':
            if self.point_end_local == Vector((0.0, 0.0, 0.0)):
                # Handle edge case where points are identical
                self.sections[-1]['valid'] = False
            else:
                self.section_curves[-1] = Clothoid.Forward(
                    self.point_start_local.x, self.point_start_local.y, self.heading_start_local,
                    self.curvature_start_local, self.point_end_local.x, self.point_end_local.y)

                # When the heading of start and end point is colinear the curvature
                # can become very small and the length becomes huge (solution is a gigantic
                # circle). Therefore as a workaround we limit the length to 10 km.
                if self.section_curves[-1].length < 10000.0:
                    self.sections[-1]['valid'] = True
                else:
                    self.sections[-1]['valid'] = False

        # Remember geometry parameters, only update if valid solution is found
        if self.sections[-1]['valid']:
            self.sections[-1]['curve_type'] = 'spiral'
            self.sections[-1]['geometry_solver'] = geometry_solver
            self.sections[-1]['point_start'] = params['points'][-2]
            self.sections[-1]['heading_start'] = params['heading_start'] + self.heading_start_local
            self.sections[-1]['point_end'] = params['points'][-1]
            self.sections[-1]['heading_end'] = params['heading_start'] + self.section_curves[-1].ThetaEnd
            self.sections[-1]['length'] = self.section_curves[-1].length
            self.sections[-1]['curvature_start'] = self.section_curves[-1].KappaStart
            self.sections[-1]['curvature_end'] = self.section_curves[-1].KappaEnd
            self.sections[-1]['angle_end'] = self.section_curves[-1].ThetaEnd

    def sample_plan_view(self, s):
        idx_section, s_section = self.get_section_idx_and_s(s)
        x_s = self.section_curves[idx_section].X(s_section)
        y_s = self.section_curves[idx_section].Y(s_section)
        curvature = self.section_curves[idx_section].KappaStart + self.section_curves[idx_section].dk * s_section
        hdg = self.section_curves[idx_section].Theta(s_section)
        return x_s, y_s, hdg, curvature
