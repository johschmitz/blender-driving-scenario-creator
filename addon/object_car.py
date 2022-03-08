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

from .modal_two_point_base import DSC_OT_two_point_base
from . import helpers


class DSC_OT_object_car(DSC_OT_two_point_base):
    bl_idname = 'dsc.object_car'
    bl_label = 'Car'
    bl_description = 'Place a car object'
    bl_options = {'REGISTER', 'UNDO'}

    object_type = 'car'

    params = {}

    # Do not snap to other xodr or xosc objects in scene
    # TODO snap to road contact points, requires a lot of work
    snap_filter = 'surface'

    def create_object(self, context):
        '''
            Create a car object
        '''
        valid, mesh, matrix_world, materials = self.get_mesh_update_params(context, for_stencil=False)
        if not valid:
            return None
        else:
            id_obj = helpers.get_new_id_openscenario(context)
            obj_name = str(id_obj) + '_' + context.scene.object_properties.name
            mesh.name = obj_name
            obj = bpy.data.objects.new(mesh.name, mesh)
            obj.matrix_world = matrix_world
            helpers.link_object_openscenario(context, obj, subcategory='dynamic_objects')

            helpers.select_activate_object(context, obj)

            # Assign materials
            color = context.scene.object_properties.color
            helpers.assign_object_materials(obj, color)
            for idx in range(len(obj.data.polygons)):
                obj.data.polygons[idx].material_index = \
                    helpers.get_material_index(obj, helpers.get_paint_material_name(color))

            # Metadata
            obj['dsc_category'] = 'OpenSCENARIO'
            obj['dsc_type'] = 'car'

            # Set OpenSCENARIO custom properties
            obj['position'] = self.params['point_start']
            obj['hdg'] = self.params['heading_start']
            obj['speed_initial'] = context.scene.object_properties.speed_initial

        return obj

    def get_mesh_update_params(self, context, for_stencil):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        if self.params_input['point_start'] == self.params_input['point_end']:
            if not for_stencil:
                self.report({'WARNING'}, 'Start and end point can not be the same!')
            valid = False
            return valid, None, {}
        vector_start_end = self.params_input['point_end'] - self.params_input['point_start']
        heading = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        self.params = {'point_start': self.params_input['point_start'],
                  'heading_start': heading,
                  'point_end': self.params_input['point_end']}
        vertices, edges, faces = self.get_vertices_edges_faces()
        mat_translation = Matrix.Translation(self.params_input['point_start'])
        mat_rotation = Matrix.Rotation(heading, 4, 'Z')
        matrix_world = mat_translation @ mat_rotation
        # Create blender mesh
        if for_stencil:
            faces = []
        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, edges, faces)
        valid = True
        materials = {}
        return valid, mesh, matrix_world, materials

    def get_vertices_edges_faces(self):
        vertices = [(-2.2, -1.0, 0.0),
                    ( 2.2, -1.0, 0.0),
                    ( 2.2, -1.0, 0.5),
                    ( 1.9, -1.0, 0.8),
                    ( 1.1, -1.0, 0.85),
                    ( 0.1, -1.0, 1.6),
                    (-1.6, -1.0, 1.58),
                    (-2.2, -1.0, 0.9),
                    (-2.2, 1.0, 0.0),
                    ( 2.2, 1.0, 0.0),
                    ( 2.2, 1.0, 0.5),
                    ( 1.9, 1.0, 0.8),
                    ( 1.1, 1.0, 0.85),
                    ( 0.1, 1.0, 1.6),
                    (-1.6, 1.0, 1.58),
                    (-2.2, 1.0, 0.9),
                   ]
        edges = [[0, 1],[1, 2],[2, 3],[3, 4],[4 ,5],[5 ,6],[6 ,7],[7, 0],
                 [15 ,14],[14 ,13],[13 ,12],[12 ,11],[11 ,10],[10 ,9], [9 ,8], [8, 15],
                 [0, 8], [7 ,15], [6 ,14], [5 ,13], [4 ,12], [3 ,11], [2 ,10], [1 ,9],
                ]
        faces = [[0, 1, 2, 3, 4, 5, 6, 7, 0],[15, 14, 13, 12, 11, 10, 9, 8, 15],
                    [0, 7, 15, 8], [7, 6, 14, 15], [6, 5, 13, 14], [5, 4, 12, 13],
                    [4, 3, 11, 12], [3, 2, 10, 11], [2, 1, 9, 10], [8, 9, 1, 0]
                ]
        return vertices, edges, faces