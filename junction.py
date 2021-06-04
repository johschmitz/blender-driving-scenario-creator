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

    object_type = 'junction'

    @classmethod
    def poll(cls, context):
        return True

    def create_object_xodr(self, context):
        '''
            Create a junction object
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

            helpers.assign_road_materials(obj)

            helpers.select_activate_object(context, obj)

            # Remember connecting points for snapping
            obj['cp_left'] = obj.location + obj.data.vertices[1].co
            obj['cp_down'] = obj.location + obj.data.vertices[3].co
            obj['cp_right'] = obj.location + obj.data.vertices[5].co
            obj['cp_up'] = obj.location + obj.data.vertices[7].co

            # Set OpenDRIVE custom properties
            obj['id_xodr'] = obj_id
            obj['junction_type'] = 'default'
            obj['planView_geometry_x'] = self.point_start.x
            obj['planView_geometry_y'] = self.point_start.y
            obj['hdg_down'] = params['hdg_down']
            obj['hdg_left'] = params['hdg_left']
            obj['hdg_up'] = params['hdg_up']
            obj['hdg_right'] = params['hdg_right']

            obj['incoming_roads'] = {'cp_down': None, 'cp_left': None, 'cp_up': None, 'cp_right': None}

            return obj

    def get_mesh_and_params(self, for_stencil):
        '''
            Calculate and return the vertices, edges and faces to create a road
            mesh and road parameters.
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
        # Parameters
        vector_start_end = point_end - self.point_start
        heading = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        vector_hdg_left = Vector((-1.0, 0.0))
        vector_hdg_down = Vector((0.0, -1.0))
        vector_hdg_right = Vector((1.0, 0.0))
        vector_hdg_up = Vector((0.0, 1.0))
        hdg_left = vector_hdg_left.to_2d().angle_signed(vector_start_end.to_2d())
        hdg_down = vector_hdg_down.to_2d().angle_signed(vector_start_end.to_2d())
        hdg_right = vector_hdg_right.to_2d().angle_signed(vector_start_end.to_2d())
        hdg_up = vector_hdg_up.to_2d().angle_signed(vector_start_end.to_2d())
        params = {'point_start': self.point_start,
                  'heading_start': heading,
                  'point_end': point_end,
                  'hdg_left': hdg_left,
                  'hdg_down': hdg_down,
                  'hdg_right': hdg_right,
                  'hdg_up': hdg_up,
                  }
        # Mesh
        vertices = [(-4.0, 4.0, 0.0),
                    (-4.0, 0.0, 0.0),
                    (-4.0, -4.0, 0.0),
                    (0.0, -4.0, 0.0),
                    (4.0, -4.0, 0.0),
                    (4.0, 0.0, 0.0),
                    (4.0, 4.0, 0.0),
                    (0.0, 4.0, 0.0),
                    ]
        edges = [[0, 1],[1, 2],[2, 3],[3, 4],[4, 5],[5, 6],[6, 7],[7, 0]]
        if for_stencil:
            faces = []
        else:
            # Make sure we define faces counterclockwise for correct normals
            faces = [[0, 1, 2, 3, 4, 5, 6, 7]]
        # Shift origin to connection point
        if self.snapped_start:
            vertices[:] = [(v[0] + 4.0, v[1], v[2]) for v in vertices]
        # Create blender mesh
        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, edges, faces)
        # Rotate and translate mesh according to selected start point
        self.transform_mesh_wrt_start(mesh, self.point_start, heading, self.snapped_start)

        valid = True
        return valid, mesh, params


