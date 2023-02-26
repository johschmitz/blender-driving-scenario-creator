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

from . modal_two_point_base import DSC_OT_modal_two_point_base
from . entity import entity


class DSC_OT_entity(DSC_OT_modal_two_point_base):
    bl_idname = 'dsc.entity'
    bl_label = 'Entity'
    bl_description = 'Place an entity object'
    bl_options = {'REGISTER', 'UNDO'}

    params = {}

    # Do not snap to other xodr or xosc objects in scene
    # TODO snap to road contact points, requires a lot of work
    snap_filter = 'surface'

    def create_object_model(self, context):
        '''
            Create a model object instance
        '''
        self.entity = entity(context, self.entity_type, self.entity_subtype,
            self.get_vertices_edges_faces)

    def create_object_3d(self, context):
        '''
            Create a 3d car object
        '''
        return self.entity.create_object_3d(context, self.params_input)

    def update_params_get_mesh(self, context, wireframe=True):
        '''
            Calculate and return the vertices, edges and faces to create an entity mesh.
        '''
        valid, mesh, matrix_world, materials = \
            self.entity.update_params_get_mesh(context, self.params_input, wireframe)
        if not valid:
            self.report({'WARNING'}, 'No valid entity geometry solution found!')
        return valid, mesh, matrix_world, materials
