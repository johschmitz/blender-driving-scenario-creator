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

from .operator_snap_draw import DSC_OT_snap_draw
from . import helpers


class DSC_OT_object_car(DSC_OT_snap_draw):
    bl_idname = "dsc.object_car"
    bl_label = "Car"
    bl_description = "Place a car object"
    bl_options = {'REGISTER', 'UNDO'}

    object_type = 'car'

    def __init__(self):
        self.object_snapping = False

    def create_object(self, context):
        '''
            Create a car object
        '''
        valid, mesh, materials, params = self.get_mesh_and_params(context, for_stencil=False)
        if not valid:
            return None
        else:
            obj_id = helpers.get_new_id_openscenario(context)
            obj_name = str(obj_id) + '_' + context.scene.object_properties.name
            mesh.name = obj_name
            obj = bpy.data.objects.new(mesh.name, mesh)
            self.transform_object_wrt_start(obj, params['point_start'], params['heading_start'])
            helpers.link_object_openscenario(context, obj)

            helpers.select_activate_object(context, obj)

            # Assign materials
            color = context.scene.object_properties.color
            helpers.assign_object_materials(obj, color)
            for idx in range(len(obj.data.polygons)):
                obj.data.polygons[idx].material_index = \
                    helpers.get_material_index(obj, helpers.get_paint_material_name(color))

            # Remember connecting points for snapping
            obj['cp_down'] = obj.location + obj.data.vertices[0].co
            obj['cp_left'] = obj.location + obj.data.vertices[2].co
            obj['cp_up'] = obj.location + obj.data.vertices[4].co
            obj['cp_right'] = obj.location + obj.data.vertices[6].co

            # Set OpenSCENARIO custom properties
            obj['type'] = 'car'
            obj['id_xosc'] = obj_id
            obj['x'] = params['point_start'].x
            obj['y'] = params['point_start'].y
            obj['z'] = params['point_start'].z
            obj['hdg'] = params['heading_start']
            obj['speed_initial'] = context.scene.object_properties.speed_initial

        return obj

    def get_mesh_and_params(self, context, for_stencil):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        if self.point_start == self.point_selected_end:
            self.report({"WARNING"}, "Start and end point can not be the same!")
            valid = False
            return valid, None, {}
        vector_start_end = self.point_selected_end - self.point_start
        heading = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        params = {'point_start': self.point_start,
                  'heading_start': heading,
                  'point_end': self.point_selected_end}
        vertices, edges, faces = self.get_vertices_edges_faces()
        # Create blender mesh
        if for_stencil:
            faces = []
        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, edges, faces)
        valid = True
        materials = {}
        return valid, mesh, materials, params

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