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

from mathutils import Vector, Matrix


class DSC_geometry():

    def __init__(self) -> None:
        self.update(Vector((0.0,0.0,0.0)), 0, Vector((1.0,1.0,0.0)), 0)

    def sample_local(self, s, t):
        '''
            Return a list of samples x, y = f(s, t) and curvature c in local
            coordinates.
        '''
        raise NotImplementedError()

    def update(self, point_start, heading_start, point_end, heading_end):
        '''
            Update parameters of the geometry and local to global tranformation
            matrix.
        '''
        raise NotImplementedError()

    def update_local_to_global(self, point_start, heading_start):
        '''
            Calculate matrix for local to global transform of the geometry.
        '''
        mat_translation = Matrix.Translation(point_start)
        mat_rotation = Matrix.Rotation(heading_start, 4, 'Z')
        self.matrix_world = mat_translation @ mat_rotation