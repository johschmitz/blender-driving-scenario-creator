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

    object_type = 'road_straight'

    @classmethod
    def poll(cls, context):
        return True

    def create_object_xodr(self, context):
        '''
            Create a straight road object
        '''
        valid, mesh, params = self.get_mesh_and_params(for_stencil=False)
        if not valid:
            return None
        else:
            obj_id = helpers.get_new_id_opendrive(context)
            mesh.name = self.object_type + '_' + str(obj_id)
            obj = bpy.data.objects.new(mesh.name, mesh)
            obj.location = self.point_start
            helpers.link_object_opendrive(context, obj)

            # Paint some road markings
            helpers.assign_road_materials(obj)
            obj.data.polygons[0].material_index = helpers.get_material_index(obj, 'road_asphalt')
            obj.data.polygons[1].material_index = helpers.get_material_index(obj, 'road_surface_marking')

            helpers.select_activate_object(context, obj)

            # Remember connecting points for road snapping
            obj['cp_start'] = self.point_start
            obj['cp_end'] = params['point_end']

            # Set OpenDRIVE custom properties
            obj['id_xodr'] = obj_id
            obj['geometry'] = 'line'
            obj['geometry_s'] = 0
            obj['geometry_x'] = self.point_start.x
            obj['geometry_y'] = self.point_start.y
            obj['geometry_hdg_start'] = params['heading_start']
            obj['geometry_hdg_end'] = params['heading_start']
            obj['geometry_length'] = params['length']

            return obj

    def get_mesh_and_params(self, for_stencil):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        if self.snapped_start:
            # Constrain point end
            point_end = helpers.project_point_vector(self.point_selected_end,
                self.point_start, self.heading_start)
        else:
            point_end = self.point_selected_end
        if self.point_start == point_end:
            self.report({"WARNING"}, "Start and end point can not be the same!")
            valid = False
            return valid, None, {}
        vector_start_end = point_end - self.point_start
        heading = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        length = vector_start_end.length
        params = {'point_start': self.point_start,
                  'heading_start': heading,
                  'point_end': point_end,
                  'length': length }
        vertices = [(0.0, 4.0, 0.0),
                    (length, 4.0, 0.0),
                    (0.0, 0.0, 0.0),
                    (length, 0.0, 0.0),
                    (0.0, -4.0, 0.0),
                    (length, -4.0, 0.0),
                    ]
        edges = [[0, 2],[2, 3],[3, 1],[1, 0],
                 [2, 4],[4, 5],[5, 3], [3, 2]]
        if for_stencil:
            faces = []
        else:
            # Make sure we define faces counterclockwise for correct normals
            faces = [[0, 2, 3, 1],[2, 4, 5, 3]]
        # Create blender mesh
        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, edges, faces)
        # Rotate and translate mesh according to selected start point
        self.transform_mesh_wrt_start(mesh, self.point_start, heading, self.snapped_start)
        valid = True
        heading = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        return valid, mesh, params
