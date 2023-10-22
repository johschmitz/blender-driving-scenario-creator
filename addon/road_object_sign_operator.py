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
from mathutils import Vector, Matrix

from math import pi

from . modal_road_object_base import DSC_OT_modal_road_object_base
from . road_object_sign import road_object_sign


class DSC_OT_road_object_sign(DSC_OT_modal_road_object_base):
    bl_idname = 'dsc.road_object_sign'
    bl_label = 'Sign'
    bl_description = 'Place a sign object'
    bl_options = {'REGISTER', 'UNDO'}

    params = {}

    # Do not snap to other xodr or xosc objects in scene
    # TODO snap to road contact points, requires a lot of work
    snap_filter = 'surface'

    road_object_type = 'sign'

    def create_object_model(self, context):
        '''
            Create a model object instance
        '''
        self.road_object = road_object_sign(context, self.road_object_type)

    def create_object_3d(self, context):
        '''
            Create a 3d road object
        '''
        return self.road_object.create_object_3d(context, self.params_input, self.id_road)

    def update_params_get_mesh(self, context, wireframe=True):
        '''
            Calculate and return the vertices, edges and faces to create a road object mesh.
        '''
        valid, mesh, matrix_world, materials = \
            self.road_object.update_params_get_mesh(context, self.params_input, wireframe)
        if not valid:
            self.report({'WARNING'}, 'No valid road object geometry solution found!')
        return valid, mesh, matrix_world, materials
