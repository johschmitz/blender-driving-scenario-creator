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

import bpy
from mathutils import Vector

params_input = {
    'points': [],
    'heading_start': 0.0,
    'heading_end': 0.0,
    'curvature_start': 0.0,
    'curvature_end': 0.0,
    'slope_start': 0.0,
    'slope_end': 0.0,
    'connected_start': False,
    'connected_end': False,
    'normal_start': Vector((0.0,0.0,1.0)),
    'design_speed': 130.0,
}

def get_heading_start(point_start, point_end):
    '''
        Calculate heading for line between two input points.
    '''
    vector_hdg = Vector((1.0, 0.0))
    vector_start_end = (point_end - point_start).to_2d()
    if vector_start_end.length == 0:
        return 0
    else:
        return vector_start_end.angle_signed(vector_hdg)