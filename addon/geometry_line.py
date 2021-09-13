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


class DSC_geometry_line(DSC_geometry):

    def update(self, point_start, heading_start, point_end, heading_end):
        # Note: For the line geometry heading_start and heading_end input is ignored
        # since the degrees of freedom are to low.
        # Hence, recalculate start heading
        heading_start_line = (point_end - point_start).to_2d().angle_signed(Vector((1.0, 0.0)))
        # Calculate transform between global and local coordinates
        self.update_local_to_global(point_start, heading_start_line)
        point_end_local = self.matrix_world.inverted() @ point_end
        # Local starting point is 0 vector so length becomes length of end point vector
        length = point_end_local.length

        # Remember geometry parameters
        self.params = {'curve': 'line',
                       'point_start': point_start,
                       'heading_start': heading_start_line,
                       'point_end': point_end,
                       'heading_end': heading_start_line,
                       'length': length,
                       'curvature_start': 0,
                       'curvature_end': 0,}

    def sample_local(self, s, t_vec):
        xyz = []
        for idx, t in enumerate(t_vec):
            xyz += [(s, t, 0)]
        return xyz, 0
