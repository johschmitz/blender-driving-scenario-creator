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
from idprop.types import IDPropertyArray

from math import pi

from .operator_snap_draw import DSC_OT_snap_draw
from . import helpers


class DSC_OT_junction(DSC_OT_snap_draw, bpy.types.Operator):
    bl_idname = 'dsc.junction'
    bl_label = 'Junction'
    bl_description = 'Create a junction'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def create_object_xodr(self, context, point_start, point_end, snapped_start):
        '''
            Create a junction object
        '''
        if point_end == point_start:
            self.report({"WARNING"}, "First and second selection are equal, "
                "direction can not be determined!")
            return None
        obj_id = helpers.get_new_id_opendrive(context)
        mesh = bpy.data.meshes.new('junction_' + str(obj_id))
        obj = bpy.data.objects.new(mesh.name, mesh)
        helpers.link_object_opendrive(context, obj)

        vertices = [(0.0, -4.0, 0.0),
                    (-4.0, -4.0, 0.0),
                    (-4.0, 0.0, 0.0),
                    (-4.0, 4.0, 0.0),
                    (0.0, 4.0, 0.0),
                    (4.0, 4.0, 0.0),
                    (4.0, 0.0, 0.0),
                    (4.0, -4.0, 0.0),
                    ]
        edges = [[0, 1],[1, 2],[2, 3],[3, 4],[4, 5],[5, 6],[6, 7],[7, 0]]
        faces = [[0, 1, 2, 3, 4, 5, 6, 7]]
        mesh.from_pydata(vertices, edges, faces)
        if snapped_start:
            # Use start point instead of center point as origin
            matrix = Matrix.Translation((0.0, 4.0, 0.0))
            obj.data.transform(matrix)

        helpers.select_activate_object(context, obj)

        # Rotate, translate, according to selected points
        vector_start_end_xy = (point_end - point_start).to_2d()
        vector_obj = obj.data.vertices[4].co - obj.data.vertices[0].co
        heading_start = vector_start_end_xy.angle_signed(vector_obj.to_2d())
        self.transform_object_wrt_start(obj, point_start, heading_start)

        # Remember connecting points for snapping
        obj['cp_down'] = obj.location + obj.data.vertices[0].co
        obj['cp_left'] = obj.location + obj.data.vertices[2].co
        obj['cp_up'] = obj.location + obj.data.vertices[4].co
        obj['cp_right'] = obj.location + obj.data.vertices[6].co

        # Set OpenDRIVE custom properties
        obj['id_xodr'] = obj_id
        obj['t_junction_e_junction_type'] = 'default'
        obj['t_junction_planView_geometry_x'] = point_start.x
        obj['t_junction_planView_geometry_y'] = point_start.y
        vector_hdg_down = obj.data.vertices[0].co - obj.data.vertices[4].co
        vector_hdg_left = obj.data.vertices[2].co - obj.data.vertices[6].co
        vector_hdg_up = obj.data.vertices[4].co - obj.data.vertices[0].co
        vector_hdg_right = obj.data.vertices[6].co - obj.data.vertices[2].co
        vec_0_1 = Vector((1.0, 0.0))
        obj['hdg_down'] = vector_hdg_down.to_2d().angle_signed(vec_0_1)
        obj['hdg_left'] = vector_hdg_left.to_2d().angle_signed(vec_0_1)
        obj['hdg_up'] = vector_hdg_up.to_2d().angle_signed(vec_0_1)
        obj['hdg_right'] = vector_hdg_right.to_2d().angle_signed(vec_0_1)

        obj['incoming_roads'] = {'cp_down': None, 'cp_left': None, 'cp_up': None, 'cp_right': None}

        return obj

    def create_stencil(self, context, point_start, heading_start, snapped_start):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene currently only support OBJECT mode.
        '''
        stencil = bpy.data.objects.get('dsc_stencil_object')
        if stencil is not None:
            if context.scene.objects.get('dsc_stencil_object') is None:
                context.scene.collection.objects.link(stencil)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new("dsc_stencil_object")
            vertices = [(0.0, 0.0, 0.0),
                        (8.0, 0.0, 0.0),
                        (-4.0, -4.0, 0.0),
                        (-4.0, 4.0, 0.0),
                        (4.0, 4.0, 0.0),
                        (4.0, -4.0, 0.0),
                        ]
            edges = [[0, 1],[2, 3],[3, 4],[4, 5],[5, 2]]
            faces = []
            mesh.from_pydata(vertices, edges, faces)
            self.stencil = bpy.data.objects.new("dsc_stencil_object", mesh)
            if snapped_start:
                # Use start point instead of center point as origin
                matrix = Matrix.Translation((4.0, 0.0, 0.0))
                self.stencil.data.transform(matrix)
            self.transform_object_wrt_start(self.stencil, point_start, heading_start)
            # Link
            context.scene.collection.objects.link(self.stencil)
            self.stencil.use_fake_user = True
            self.stencil.data.use_fake_user = True
        # Make stencil active object
        helpers.select_activate_object(context, self.stencil)

    def transform_object_wrt_end(self, obj, vector_obj, point_end, snapped_start):
        '''
            Transform object according to selected end point (keep start point fixed).
        '''
        vector_selected = point_end - obj.location
        # Make sure vectors are not 0 lenght to avoid division error
        if vector_selected.length > 0 and vector_obj.length > 0:
            # Apply transformation
            if snapped_start:
                return
            else:
                if vector_selected.angle(vector_obj)-pi > 0:
                    # Avoid numerical issues due to vectors directly facing each other
                    mat_rotation = Matrix.Rotation(pi, 4, 'Z')
                else:
                    mat_rotation = vector_obj.rotation_difference(vector_selected).to_matrix().to_4x4()
                obj.data.transform(mat_rotation)
                obj.data.update()
