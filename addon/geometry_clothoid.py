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
from pyclothoids import Clothoid
from math import pi


class DSC_geometry_clothoid(DSC_geometry):

    def update(self, point_start, heading_start, point_end, heading_end):
        # Calculate transform between global and local coordinates
        self.update_local_to_global(point_start, heading_start)
        point_end_local = self.matrix_world.inverted() @ point_end
        heading_end_local = heading_end - heading_start

        # Calculate geometry
        self.geometry_base = Clothoid.G1Hermite(0, 0, 0,
            point_end_local.x, point_end_local.y, heading_end_local)

        # Remember geometry parameters
        self.params = {'curve': 'spiral',
                       'point_start': point_start,
                       'heading_start': heading_start,
                       'point_end': point_end,
                       'heading_end': heading_start + self.geometry_base.ThetaEnd,
                       'length': self.geometry_base.length,
                       'curvature_start': self.geometry_base.KappaStart,
                       'curvature_end': self.geometry_base.KappaEnd,
                       'angle_end': self.geometry_base.ThetaEnd,}

    def sample_local(self, s, t_vec):
        curvature = self.geometry_base.KappaStart + self.geometry_base.dk * s
        x_s_0 = self.geometry_base.X(s)
        y_s_0 = self.geometry_base.Y(s)
        hdg_t = self.geometry_base.Theta(s) + pi/2
        vector_hdg_t = Vector((1.0, 0.0))
        vector_hdg_t.rotate(Matrix.Rotation(hdg_t, 2))
        xyz = []
        for t in t_vec:
            xy_vec = Vector((x_s_0, y_s_0)) + t * vector_hdg_t
            xyz += [(xy_vec.x, xy_vec.y, 0)]
        return xyz, curvature
