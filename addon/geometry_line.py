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
from mathutils.geometry import distance_point_to_plane
from math import pi


class DSC_geometry_line(DSC_geometry):

    def update_plan_view(self, params, geometry_solver):
        if params['connected_start']:
            heading_start_line = params['heading_start']
            point_end = helpers.project_point_vector(params['point_start'].to_2d(),
                heading_start_line, params['point_end'].to_2d())
            # Add height back to end point
            point_end = point_end.to_3d()
            point_end.z = params['point_end'].z
            # Avoid negative heading
            vector_hdg = Vector((1.0, 0.0, 0.0))
            vector_hdg.rotate(Matrix.Rotation(heading_start_line, 3, 'Z'))
            distance = distance_point_to_plane(point_end, params['point_start'], vector_hdg)
            if distance < 0.0:
                point_end = params['point_start']
                valid = False
            else:
                valid = True
        else:
            point_end = params['point_end']
            # Note: For the line geometry heading_start and heading_end input is ignored
            # since the degrees of freedom are to low.
            # Hence, recalculate start heading
            heading_start_line = (point_end.to_2d() - \
                params['point_start'].to_2d()).angle_signed(Vector((1.0, 0.0)))
            valid = True

        # Calculate transform between global and local coordinates
        self.update_local_to_global(params['point_start'], heading_start_line,
            point_end, heading_start_line,)
        # Local starting point is 0 vector so length becomes length of end point vector
        length = self.point_end_local.to_2d().length

        # Remember geometry parameters
        self.params['curve'] = 'line'
        self.params['point_start'] = params['point_start']
        self.params['heading_start'] = heading_start_line
        self.params['curvature_start'] = 0
        self.params['point_end'] = point_end
        self.params['heading_end'] = heading_start_line
        self.params['curvature_end'] = 0
        self.params['length'] = length
        self.params['valid'] = valid

    def sample_plan_view(self, s):
        x_s = s
        y_s = 0
        curvature = 0
        hdg_t = pi/2
        return x_s, y_s, curvature, hdg_t