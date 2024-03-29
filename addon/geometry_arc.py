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

from mathutils import Vector, Matrix
from math import cos, inf, sin, pi, degrees


class Arc():

    def __init__(self, point_end):
        valid, self.radius, self.angle, self.determinant = \
            self.get_radius_angle_det(Vector((0.0, 0.0, 0.0)), point_end)
        if valid:
            if self.determinant > 0:
                self.offset_angle = 0
                self.curvature = 1/self.radius
                self.offset_y = self.radius
                if self.angle < 0:
                    # Limit angle to 180 degrees
                    self.heading_end  = pi
                    self.angle = pi
                else:
                    self.heading_end  = self.angle
            else:
                self.offset_angle = pi
                self.curvature = -1/self.radius
                self.offset_y = -self.radius
                if self.angle > 0:
                    # Limit angle to 180 degrees
                    self.heading_end = pi
                    self.angle = -pi
                else:
                    self.heading_end = self.angle
            self.length = self.radius * abs(self.angle)
        else:
            self.radius = inf
            self.curvature = 0
            self.offset_y = self.radius
            self.angle = 0
            self.offset_angle = 0
            self.heading_end = 0
            self.length = point_end.length


    def get_radius_angle_det(self, point_start, point_end):
        '''
            Calculate center and radius of the arc that is defined by the
            starting point (predecessor connecting point), the start heading
            (heading of the connected road) and the end point. Also return
            determinant that tells us if point end is left or right of heading
            direction.
        '''
        # The center of the arc is the crossing point of line orthogonal to the
        # predecessor road in the connecting point and the perpendicular
        # bisector of the connection between start and end point.
        p = point_start.to_2d()
        a = Vector((0.0, 1.0))
        q = 0.5 * (point_start + point_end).to_2d()
        b_normal = (point_start - point_end)
        b = Vector((-b_normal[1], b_normal[0]))
        if a.orthogonal() @ b != 0:
            # See https://mathepedia.de/Schnittpunkt.html for crossing point equation
            center = 1 / (a @ b.orthogonal()) * ((q @ b.orthogonal()) * a - (p @ a.orthogonal()) * b)
            radius = (center - p).length
            # Calculate determinant to know where to start drawing the arc {0, pi}
            vec_hdg = Vector((1.0, 0.0, 0.0))
            determinant = Matrix([vec_hdg.to_2d(), (point_end - point_start).to_2d()]).transposed().determinant()
            angle = (point_end.to_2d() - center).angle_signed(point_start.to_2d() - center)
            return True, radius, angle, determinant
        else:
            return False, 0, 0, 0


class DSC_geometry_arc(DSC_geometry):

    def __init__(self):
        super().__init__()

    def load_section_curve(self, section):
        # Transform to section coordinates since we calculate the arc always from (0,0)
        point_end_section = section['matrix_local'].inverted() @ self.matrix_world.inverted() @ Vector(section['point_end'])
        self.section_curves.append(Arc(point_end_section))

    def update_plan_view(self, params, geometry_solver='default'):
        # Transform to section coordinates since we calculate the arc always from (0,0)
        point_end_section = self.sections[-1]['matrix_local'].inverted() \
            @ self.point_end_local
        # Constrain in section coordinate system and transform back to global
        if point_end_section.x < 0:
            point_end_section.x = 0
        # Transform back to global
        point_end_global = self.matrix_world \
            @ self.sections[-1]['matrix_local'] @ point_end_section

        # Create and calculate geometry
        self.section_curves[-1] = Arc(point_end_section)

        # Remember geometry parameters
        self.sections[-1]['curve_type'] = 'arc'
        self.sections[-1]['geometry_solver'] = 'default'
        self.sections[-1]['point_start'] = params['points'][-2]
        self.sections[-1]['heading_start'] = params['heading_start'] \
            + self.heading_start_local
        self.sections[-1]['point_end'] = point_end_global
        self.sections[-1]['heading_end'] = params['heading_start'] \
            + self.section_curves[-1].heading_end + self.heading_start_local
        self.sections[-1]['curvature_start'] = self.section_curves[-1].curvature
        self.sections[-1]['curvature_end'] = self.section_curves[-1].curvature
        self.sections[-1]['length'] = self.section_curves[-1].length

    def sample_plan_view(self, s):
        idx_section, s_section = self.get_section_idx_and_s(s)
        hdg_local = self.sections[idx_section]['heading_start'] \
                    - self.sections[0]['heading_start']
        if self.section_curves[idx_section].radius == inf:
            # Circle degenerates into a straight line
            x_s = s_section
            y_s = 0
            hdg = hdg_local
        else:
            # We have a circle
            angle_s = s_section / self.section_curves[idx_section].radius
            if self.section_curves[idx_section].determinant > 0:
                x_s = cos(angle_s + self.section_curves[idx_section].offset_angle - pi/2) \
                        * self.section_curves[idx_section].radius
                y_s = sin(angle_s + self.section_curves[idx_section].offset_angle - pi/2) \
                        * self.section_curves[idx_section].radius \
                        + self.section_curves[idx_section].offset_y
                hdg = hdg_local + angle_s
            else:
                x_s = cos(-angle_s + self.section_curves[idx_section].offset_angle - pi/2) \
                        * self.section_curves[idx_section].radius
                y_s = sin(-angle_s + self.section_curves[idx_section].offset_angle - pi/2) \
                        * self.section_curves[idx_section].radius \
                        + self.section_curves[idx_section].offset_y
                hdg = hdg_local - angle_s
        xyz_s_local = self.sections[idx_section]['matrix_local'] @ Vector((x_s, y_s, 0.0))
        curvature = self.section_curves[idx_section].curvature
        return xyz_s_local[0], xyz_s_local[1], hdg, curvature