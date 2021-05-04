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


class DSC_OT_road_straight(DSC_OT_snap_draw, bpy.types.Operator):
    bl_idname = 'dsc.road_straight'
    bl_label = 'Straight'
    bl_description = 'Create a straight road'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def create_object_xodr(self, context, point_start, heading_start, snapped_start,
                           point_end, heading_end, snapped_end):
        '''
            Create a straight road object
        '''
        if point_end == point_start:
            self.report({"WARNING"}, "Impossible to create zero length road!")
            return
        obj_id = helpers.get_new_id_opendrive(context)
        mesh = bpy.data.meshes.new('road_straight_' + str(obj_id))
        obj = bpy.data.objects.new(mesh.name, mesh)
        helpers.link_object_opendrive(context, obj)

        vertices = [(0.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0),
                    (1.0, -4.0, 0.0),
                    (0.0, -4.0, 0.0),
                    (0.0, 4.0, 0.0),
                    (1.0, 4.0, 0.0)
                    ]
        edges = [[0, 1],[1, 2],[2, 3],[3, 4],
                    [0, 4,],[4, 5],[5, 1]]
        faces = [[0, 1, 2, 3],[0, 4, 5, 1]]
        mesh.from_pydata(vertices, edges, faces)

        helpers.select_activate_object(context, obj)

        # Rotate, translate, scale according to selected points
        self.transform_object_wrt_start(obj, point_start, heading_start)
        vector_obj = obj.data.vertices[1].co - obj.data.vertices[0].co
        self.transform_object_wrt_end(obj, vector_obj, point_end, snapped_start)

        # Remember connecting points for road snapping
        obj['cp_start'] = point_start
        obj['cp_end'] = point_end

        # Set OpenDRIVE custom properties
        obj['id_xodr'] = obj_id
        obj['t_road_planView_geometry'] = 'line'
        obj['t_road_planView_geometry_s'] = 0
        obj['t_road_planView_geometry_x'] = point_start.x
        obj['t_road_planView_geometry_y'] = point_start.y
        vector_start_end = point_end - point_start
        obj['t_road_planView_geometry_hdg'] = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        obj['t_road_planView_geometry_length'] = vector_start_end.length

        return obj

    def create_stencil(self, context, point_start, heading_start, snapped_start):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene, currently only support OBJECT mode.
        '''
        stencil = bpy.data.objects.get('dsc_stencil_object')
        if stencil is not None:
            if context.scene.objects.get('dsc_stencil_object') is None:
                context.scene.collection.objects.link(stencil)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new("dsc_stencil_object")
            vertices = [(0.0,   0.0, 0.0),
                        (0.01,  0.0, 0.0),
                        (0.01, -4.0, 0.0),
                        (0.0,  -4.0, 0.0),
                        (0.0,   4.0, 0.0),
                        (0.01,  4.0, 0.0)
                        ]
            edges = [[0, 1],[1, 2],[2, 3],[3, 4],
                     [0, 4,],[4, 5],[5, 1]]
            faces = []
            mesh.from_pydata(vertices, edges, faces)
            self.stencil = bpy.data.objects.new("dsc_stencil_object", mesh)
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
        # Make sure vectors are not 0 length to avoid division error
        if vector_selected.length > 0 and vector_obj.length > 0:

            # Apply transformation
            mat_scale = Matrix.Scale(vector_selected.length/vector_obj.length, 4, vector_obj)
            if snapped_start:
                obj.data.transform(mat_scale)
            else:
                if vector_selected.angle(vector_obj)-pi > 0:
                    # Avoid numerical issues due to vectors directly facing each other
                    mat_rotation = Matrix.Rotation(pi, 4, 'Z')
                else:
                    mat_rotation = vector_obj.rotation_difference(vector_selected).to_matrix().to_4x4()
                obj.data.transform(mat_rotation @ mat_scale)
            obj.data.update()

    def project_point_end(self, point_start, heading_start, point_selected):
        '''
            Project selected point to direction vector.
        '''
        vector_selected = point_selected - point_start
        if vector_selected.length > 0:
            vector_object = Vector((1.0, 0.0, 0.0))
            vector_object.rotate(Matrix.Rotation(heading_start, 4, 'Z'))
            return point_start + vector_selected.project(vector_object)
        else:
            return point_selected
