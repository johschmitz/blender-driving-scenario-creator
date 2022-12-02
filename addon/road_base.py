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

from . modal_two_point_base import DSC_OT_modal_two_point_base
from . road import road


class DSC_OT_road(DSC_OT_modal_two_point_base):
    bl_idname = 'dsc.road'
    bl_label = 'Road'
    bl_description = 'Create road mesh'
    bl_options = {'REGISTER', 'UNDO'}

    snap_filter = 'OpenDRIVE'

    geometry_solver: bpy.props.StringProperty(
        name='Geometry solver',
        description='Solver used to determine geometry parameters.',
        options={'HIDDEN'},
        default='default')

    def create_object_model(self, context):
        '''
            Create a model object instance
        '''
        self.road = road(context, self.object_type, self.geometry, self.geometry_solver)

    def create_object_3d(self, context):
        '''
            Create a 3d object from the model
        '''
        return self.road.create_object_3d(context, self.params_input)

    def update_params_get_mesh(self, context, wireframe=True):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        valid, mesh, self.geometry.matrix_world, materials = \
            self.road.update_params_get_mesh(context, self.params_input, wireframe)
        if not valid:
            self.report({'WARNING'}, 'No valid road geometry solution found!')
        return valid, mesh, self.geometry.matrix_world, materials