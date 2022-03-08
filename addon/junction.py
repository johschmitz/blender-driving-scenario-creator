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

from . modal_two_point_base import DSC_OT_two_point_base
from . import helpers


class DSC_OT_junction(DSC_OT_two_point_base):
    bl_idname = 'dsc.junction'
    bl_label = 'Junction'
    bl_description = 'Create a junction'
    bl_options = {'REGISTER', 'UNDO'}

    object_type = 'junction'
    snap_filter = 'OpenDRIVE'

    def create_object(self, context):
        '''
            Create a junction object
        '''
        valid, mesh, matrix_world, materials = self.get_mesh_update_params(context, for_stencil=False)
        if not valid:
            return None
        else:
            id_obj = helpers.get_new_id_opendrive(context)
            mesh.name = self.object_type + '_' + str(id_obj)
            obj = bpy.data.objects.new(mesh.name, mesh)
            obj.matrix_world = matrix_world
            helpers.link_object_opendrive(context, obj)

            helpers.assign_road_materials(obj)

            helpers.select_activate_object(context, obj)

            # Metadata
            obj['dsc_category'] = 'OpenDRIVE'
            obj['dsc_type'] = 'junction'

            # Remember connecting points for snapping
            obj['cp_left'] = obj.matrix_world @ obj.data.vertices[1].co
            obj['cp_down'] = obj.matrix_world @ obj.data.vertices[3].co
            obj['cp_right'] = obj.matrix_world @ obj.data.vertices[5].co
            obj['cp_up'] = obj.matrix_world @ obj.data.vertices[7].co

            # Set OpenDRIVE custom properties
            obj['id_xodr'] = id_obj
            obj['junction_type'] = 'default'
            obj['planView_geometry_x'] = self.params['point_start'].x
            obj['planView_geometry_y'] = self.params['point_start'].y
            obj['hdg_left'] = self.params['hdg_left']
            obj['hdg_down'] = self.params['hdg_down']
            obj['hdg_right'] = self.params['hdg_right']
            obj['hdg_up'] = self.params['hdg_up']
            obj['elevation_level'] = self.params['point_start'].z

            obj['incoming_roads'] = {}

            return obj

    def get_mesh_update_params(self, context, for_stencil):
        '''
            Calculate and return the vertices, edges and faces to create a road
            mesh and road parameters.
        '''
        if self.params_input['connected_start']:
            # Constrain point end
            point_end = helpers.project_point_vector(self.params_input['point_start'],
                self.params_input['heading_start'], self.params_input['point_end'])
        else:
            point_end = self.params_input['point_end']
        if self.params_input['point_start'] == point_end:
            if not for_stencil:
                self.report({'WARNING'}, 'Start and end point can not be the same!')
            valid = False
            return valid, None, None, None
        # Parameters
        vector_start_end = point_end - self.params_input['point_start']
        vector_1_0 = Vector((1.0, 0.0))
        heading = vector_start_end.to_2d().angle_signed(vector_1_0)
        vector_hdg_left = Vector((-1.0, 0.0))
        vector_hdg_down = Vector((0.0, -1.0))
        vector_hdg_right = Vector((1.0, 0.0))
        vector_hdg_up = Vector((0.0, 1.0))
        vector_hdg_left.rotate(Matrix.Rotation(heading, 2))
        vector_hdg_down.rotate(Matrix.Rotation(heading, 2))
        vector_hdg_right.rotate(Matrix.Rotation(heading, 2))
        vector_hdg_up.rotate(Matrix.Rotation(heading, 2))
        hdg_left = vector_hdg_left.angle_signed(vector_1_0)
        hdg_down = vector_hdg_down.angle_signed(vector_1_0)
        hdg_right = vector_hdg_right.angle_signed(vector_1_0)
        hdg_up = vector_hdg_up.angle_signed(vector_1_0)
        self.params = {'point_start': self.params_input['point_start'],
                       'hdg_left': hdg_left,
                       'hdg_down': hdg_down,
                       'hdg_right': hdg_right,
                       'hdg_up': hdg_up,
                      }
        # Mesh
        vertices = [(-4.00, 4.00, 0.0),
                    (-4.00, 0.0, 0.0),
                    (-4.00, -4.00, 0.0),
                    (0.0, -4.00, 0.0),
                    (4.00, -4.00, 0.0),
                    (4.00, 0.0, 0.0),
                    (4.00, 4.00, 0.0),
                    (0.0, 4.00, 0.0),
                    ]
        edges = [[0, 1],[1, 2],[2, 3],[3, 4],[4, 5],[5, 6],[6, 7],[7, 0]]
        if for_stencil:
            faces = []
        else:
            # Make sure we define faces counterclockwise for correct normals
            faces = [[0, 1, 2, 3, 4, 5, 6, 7]]
        # Shift origin to connection point
        if self.params_input['connected_start']:
            vertices[:] = [(v[0] + 4.00, v[1], v[2]) for v in vertices]
        mat_translation = Matrix.Translation(self.params_input['point_start'])
        mat_rotation = Matrix.Rotation(heading, 4, 'Z')
        matrix_world = mat_translation @ mat_rotation
        # Create blender mesh
        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, edges, faces)
        valid = True
        # TODO implement material dictionary for the faces
        materials = {}
        return valid, mesh, matrix_world, materials


