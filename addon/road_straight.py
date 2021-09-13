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

import bmesh
from mathutils import Vector, Matrix

from math import pi, ceil

from . road_base import DSC_OT_road
from . geometry_line import DSC_geometry_line
from . import helpers


class DSC_OT_road_straight(DSC_OT_road):
    bl_idname = 'dsc.road_straight'
    bl_label = 'Straight'
    bl_description = 'Create a straight road'
    bl_options = {'REGISTER', 'UNDO'}

    object_type = 'road_straight'

    geometry = DSC_geometry_line()
    params = {}

    def constrain_point_end(self, point_start, heading_start, point_selected_end):
        '''
            Constrain the endpoint if necessary.
        '''
        point_end = helpers.project_point_vector(self.point_start, self.heading_start,
            self.point_selected_end)
        return point_end