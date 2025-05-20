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
from . road import road
from . geometry_clothoid_triple import DSC_geometry_clothoid_triple

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
            # Convert the ngons to tris and quads to get a defined surface for elevated roads
            helpers.triangulate_quad_mesh(obj)

            self.create_connecting_roads(context, obj['id_odr'])

            return obj

    def create_connecting_roads(self, context, id_junction):
        '''
            Create all six connecting roads for a 4-way junction.
        '''
        # TODO: Get the widths from the selected road cross section
        width_lane_incoming = 3.5
        road_contact_point = 'end'
        helpers.set_connecting_road_properties(context, 'right', road_contact_point, width_lane_incoming, width_lane_incoming)
        road_type = 'junction_connecting_road'
        geometry = DSC_geometry_clothoid_triple()
        geometry_solver = 'hermite'
        connecting_road = road(context, road_type, geometry, geometry_solver)

        for idx_joint_i, joint_i in enumerate(self.junction.joints):
            for idx_joint_j, joint_j in enumerate(self.junction.joints):
                if idx_joint_j != idx_joint_i:
                    t_contact_point_start = 0
                    for idx_lane_i in range(len(joint_i.lane_widths_right)):
                        t_contact_point_end = 0
                        for idx_lane_j in range(len(joint_j.lane_widths_left[::-1])):
                            if (    joint_i.lane_types_right[idx_lane_i] == 'driving'
                                and joint_j.lane_types_left[::-1][idx_lane_j] == 'driving'
                            ):
                                # Calculate contact point
                                vec_hdg_start = Vector((1.0, 0.0, 0.0))
                                vec_hdg_start.rotate(Matrix.Rotation(joint_i.heading + pi/2, 4, 'Z'))
                                vec_hdg_end = Vector((1.0, 0.0, 0.0))
                                vec_hdg_end.rotate(Matrix.Rotation(joint_j.heading + pi/2, 4, 'Z'))
                                lane_contact_points_start = Vector(joint_i.contact_point_vec) + t_contact_point_start * vec_hdg_start
                                lane_contact_points_end = Vector(joint_j.contact_point_vec) + t_contact_point_end * vec_hdg_end

                                params_input = {
                                    'points': [lane_contact_points_start, lane_contact_points_end],
                                    'heading_start': joint_i.heading,
                                    'heading_end': joint_j.heading - pi,
                                    'curvature_start': 0,
                                    'curvature_end': 0,
                                    'slope_start': joint_i.slope,
                                    'slope_end': joint_j.slope,
                                    'connected_start': True,
                                    'connected_end': True,
                                    'normal_start': Vector((0.0,0.0,1.0)),
                                    'design_speed': 100.0,
                                }
                                obj = connecting_road.create_object_3d(context, params_input)
                                id_lane_i = -idx_lane_i - 1
                                id_lane_j = idx_lane_j + 1
                                helpers.create_object_xodr_links(obj, 'start',
                                    'junction_joint_open', id_junction, joint_i.id_joint, id_lane_i)
                                helpers.create_object_xodr_links(obj, 'end',
                                    'junction_joint_open', id_junction, joint_j.id_joint, id_lane_j)

                            # Update contact point t values
                            t_contact_point_end += joint_j.lane_widths_left[::-1][idx_lane_j]
                        t_contact_point_start -= joint_i.lane_widths_right[idx_lane_i]

    def update_params_get_mesh(self, context, wireframe):
        '''
            Calculate and return the vertices, edges and faces to create a road
            mesh and road parameters.
        '''
        if self.params_input['connected_start']:
            # Constrain point end
            point_end = helpers.project_point_vector_2d(self.params_input['point_start'],
                self.params_input['heading_start'], self.params_input['point_end'])
        else:
            point_end = self.params_input['point_end']
        if self.params_input['point_start'] == point_end:
            if not wireframe:
                self.report({'WARNING'}, 'Start and end point can not be the same!')
            valid = False
            return valid, None, None, None
        # Parameters
        lanes = context.scene.dsc_properties.road_properties.lanes
        lane_widths_left, lane_widths_right, types_left, types_right = self.get_lanes_left_right(lanes)
        width_right = sum(lane_widths_right)
        width_left = sum(lane_widths_left)
        vector_start_end = (point_end - self.params_input['point_start']).normalized()
        vector_1_0 = Vector((1.0, 0.0))
        heading = vector_start_end.to_2d().angle_signed(vector_1_0)
        offset_a = (width_left + width_right)/2
        offset_b = (width_left - width_right)/2
        vector_left = Vector((-1.5*offset_a, -offset_b, 0.0))
        vector_down = Vector((offset_b, -1.5*offset_a, 0.0))
        vector_right = Vector((1.5*offset_a, offset_b, 0.0))
        vector_up = Vector((-offset_b, 1.5*offset_a, 0.0))
        if self.params_input['connected_start']:
            vector_left += Vector((1.5*offset_a, offset_b, 0.0))
            vector_down += Vector((1.5*offset_a, offset_b, 0.0))
            vector_right += Vector((1.5*offset_a, offset_b, 0.0))
            vector_up += Vector((1.5*offset_a, offset_b, 0.0))
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
        self.params = {'lane_widths_left': lane_widths_left,
                       'lane_widths_right': lane_widths_right,
                       'types_left': types_left,
                       'types_right': types_right,
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
            self.params['hdg_left'], 0, 0, self.params['lane_widths_left'], self.params['lane_widths_right'],
            self.params['types_left'], self.params['types_right'])
        self.junction.add_joint_open(self.params['cp_down'],
            self.params['hdg_down'], 0, 0, self.params['lane_widths_left'], self.params['lane_widths_right'],
            self.params['types_left'], self.params['types_right'])
        self.junction.add_joint_open(self.params['cp_right'],
            self.params['hdg_right'], 0, 0, self.params['lane_widths_left'], self.params['lane_widths_right'],
            self.params['types_left'], self.params['types_right'])
        self.junction.add_joint_open(self.params['cp_up'],
            self.params['hdg_up'], 0, 0, self.params['lane_widths_left'], self.params['lane_widths_right'],
            self.params['types_left'], self.params['types_right'])

        valid, mesh, matrix_world = self.junction.get_mesh(wireframe=True)
        # TODO implement material dictionary for the faces
        materials = {}

        return valid, mesh, matrix_world, materials

    def get_lanes_left_right(self, lanes):
        '''
            Return the width of the left and right road sides calculated by
            summing up all lane widths.
        '''
        widths_left = []
        widths_right = []
        types_left = []
        types_right = []
        for idx, lane in enumerate(lanes):
            if lane.side == 'left':
                widths_left.append(lane.width_start)
                types_left.append(lane.type)
            if lane.side == 'right':
                widths_right.append(lane.width_start)
                types_right.append(lane.type)
        return widths_left, widths_right, types_left, types_right