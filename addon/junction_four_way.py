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
from . junction import junction
from . import helpers


class DSC_OT_junction_four_way(DSC_OT_modal_two_point_base):
    bl_idname = 'dsc.junction_four_way'
    bl_label = '4-way junction'
    bl_description = 'Create a junction'
    bl_options = {'REGISTER', 'UNDO'}

    object_type = 'junction_area'
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
        self.junction = junction(context)

    def create_object_3d(self, context):
        '''
            Create a 3d junction object
        '''
        valid, mesh, matrix_world, materials = self.update_params_get_mesh(context, wireframe=False)
        if not valid:
            return None
        else:
            obj = self.junction.create_object_3d()

            return obj

    def update_params_get_mesh(self, context, wireframe):
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
            if not wireframe:
                self.report({'WARNING'}, 'Start and end point can not be the same!')
            valid = False
            return valid, None, None, None
        # Parameters
        lanes = context.scene.road_properties.lanes
        width_left, width_right = self.get_width_left_right(lanes)
        vector_start_end = point_end - self.params_input['point_start']
        vector_1_0 = Vector((1.0, 0.0))
        heading = vector_start_end.to_2d().angle_signed(vector_1_0)
        vector_left = Vector((-1.5*width_left, 0.0, 0.0))
        vector_down = Vector((0.0, -1.5*width_right, 0.0))
        vector_right = Vector((1.5*width_right, 0.0, 0.0))
        vector_up = Vector((0.0, 1.5*width_left, 0.0))
        if self.params_input['connected_start']:
            vector_left += Vector((1.5*width_left, 0.0, 0.0))
            vector_down += Vector((1.5*width_left, 0.0, 0.0))
            vector_right += Vector((1.5*width_left, 0.0, 0.0))
            vector_up += Vector((1.5*width_left, 0.0, 0.0))
        vector_left.rotate(Matrix.Rotation(heading, 3, 'Z'))
        vector_down.rotate(Matrix.Rotation(heading, 3, 'Z'))
        vector_right.rotate(Matrix.Rotation(heading, 3, 'Z'))
        vector_up.rotate(Matrix.Rotation(heading, 3, 'Z'))
        vector_left += self.params_input['point_start']
        vector_down += self.params_input['point_start']
        vector_right += self.params_input['point_start']
        vector_up += self.params_input['point_start']
        vector_hdg_left = Vector((1.0, 0.0))
        vector_hdg_down = Vector((0.0, 1.0))
        vector_hdg_right = Vector((-1.0, 0.0))
        vector_hdg_up = Vector((0.0, -1.0))
        vector_hdg_left.rotate(Matrix.Rotation(heading, 2))
        vector_hdg_down.rotate(Matrix.Rotation(heading, 2))
        vector_hdg_right.rotate(Matrix.Rotation(heading, 2))
        vector_hdg_up.rotate(Matrix.Rotation(heading, 2))
        hdg_left = vector_hdg_left.angle_signed(vector_1_0)
        hdg_down = vector_hdg_down.angle_signed(vector_1_0)
        hdg_right = vector_hdg_right.angle_signed(vector_1_0)
        hdg_up = vector_hdg_up.angle_signed(vector_1_0)
        self.params = {'width_left': width_left,
                       'width_right': width_right,
                       'cp_left': vector_left,
                       'cp_down': vector_down,
                       'cp_right': vector_right,
                       'cp_up': vector_up,
                       'hdg_left': hdg_left,
                       'hdg_down': hdg_down,
                       'hdg_right': hdg_right,
                       'hdg_up': hdg_up,
                      }

        # Remove the 4 joints from the last update
        # TODO implement modification of joints
        self.junction.remove_last_joint()
        self.junction.remove_last_joint()
        self.junction.remove_last_joint()
        self.junction.remove_last_joint()

        # Add 4 new joints, 1 for each direction
        self.junction.add_joint_open(self.params['cp_left'],
            self.params['hdg_left'], 0, self.params['width_left'], self.params['width_right'])
        self.junction.add_joint_open(self.params['cp_down'],
            self.params['hdg_down'], 0, self.params['width_left'], self.params['width_right'])
        self.junction.add_joint_open(self.params['cp_right'],
            self.params['hdg_right'], 0, self.params['width_left'], self.params['width_right'])
        self.junction.add_joint_open(self.params['cp_up'],
            self.params['hdg_up'], 0, self.params['width_left'], self.params['width_right'])

        valid, mesh, matrix_world = self.junction.get_mesh(wireframe=True)
        # TODO implement material dictionary for the faces
        materials = {}

        return valid, mesh, matrix_world, materials

    def get_width_left_right(self, lanes):
        '''
            Return the width of the left and right road sides calculated by
            suming up all lane widths.
        '''
        width_road_left = 0
        width_road_right = 0
        for idx, lane in enumerate(lanes):
            if idx == 0:
                if lane.road_mark_type != 'none':
                    # If first lane has a line we need to add half its width
                    width_line = lane.road_mark_width
                    if lane.road_mark_type == 'solid_solid' or \
                        lane.road_mark_type == 'solid_broken' or \
                        lane.road_mark_type == 'broken_solid':
                            width_road_left += width_line * 3.0 / 2.0
                    else:
                        width_road_left += width_line / 2.0
            if idx == len(lanes):
                if lane.road_mark_type != 'none':
                    # If last lane has a line we need to add half its width
                    width_line = lane.road_mark_width
                    if lane.road_mark_type == 'solid_solid' or \
                        lane.road_mark_type == 'solid_broken' or \
                        lane.road_mark_type == 'broken_solid':
                            width_road_right += width_line * 3.0 / 2.0
                    else:
                        width_road_right += width_line / 2.0
            # Sum up both sides separately
            if lane.side == 'left':
                width_road_left += lane.width
            if lane.side == 'right':
                width_road_right += lane.width
        return width_road_left, width_road_right