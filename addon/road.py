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

from . import helpers

from math import ceil

class road:

    def __init__(self, context, road_type, geometry, geometry_solver):
        self.context = context
        self.road_type = road_type
        self.geometry = geometry
        self.geometry_solver = geometry_solver
        self.params = {}

    def create_object_3d(self, context, params_input):
        '''
            Create the 3d Blender road object
        '''
        if self.road_type == 'junction_connecting_road':
            wireframe = True
        else:
            wireframe = False
        valid, mesh_road, matrix_world, materials = self.update_params_get_mesh(context,
            params_input, wireframe=wireframe)
        if not valid:
            return None
        else:
            # Create road object
            id_obj = helpers.get_new_id_opendrive(context)
            mesh_road.name = self.road_type + '_' + str(id_obj)
            obj = bpy.data.objects.new(mesh_road.name, mesh_road)
            obj.matrix_world = matrix_world
            helpers.link_object_opendrive(context, obj)

            # Assign materials
            helpers.assign_road_materials(obj)
            for idx in range(len(obj.data.polygons)):
                if idx in materials['road_mark_white']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'road_mark_white')
                elif idx in materials['grass']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'grass')
                elif idx in materials['road_mark_yellow']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'road_mark_yellow')
                else:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'road_asphalt')
            # Remove double vertices from road lanes and lane lines to simplify mesh
            helpers.remove_duplicate_vertices(context, obj)
            # Make it active for the user to see what he created last
            helpers.select_activate_object(context, obj)

            # Convert the ngons to tris and quads to get a defined surface for elevated roads
            helpers.triangulate_quad_mesh(obj)

            # Metadata
            obj['dsc_category'] = 'OpenDRIVE'
            if self.road_type == 'junction_connecting_road':
                obj['dsc_type'] = 'junction_connecting_road'
            else:
                obj['dsc_type'] = 'road'

            # Number lanes which split to the left side at road end
            obj['road_split_lane_idx'] = self.params['road_split_lane_idx']

            # Remember connecting points for road snapping
            if self.params['road_split_type'] == 'start':
                obj['cp_start_l'], obj['cp_start_r'] = self.get_split_cps('start')
                obj['cp_end_l'], obj['cp_end_r']= self.geometry.params['point_end'], self.geometry.params['point_end']
            elif self.params['road_split_type'] == 'end':
                obj['cp_start_l'], obj['cp_start_r'] = self.geometry.params['point_start'], self.geometry.params['point_start']
                obj['cp_end_l'], obj['cp_end_r']= self.get_split_cps('end')
            else:
                obj['cp_start_l'], obj['cp_start_r'] = self.geometry.params['point_start'], self.geometry.params['point_start']
                obj['cp_end_l'], obj['cp_end_r']= self.geometry.params['point_end'], self.geometry.params['point_end']

            # A road split needs to create an OpenDRIVE direct junction
            obj['road_split_type'] = self.params['road_split_type']
            if self.params['road_split_type'] != 'none':
                direct_junction_id = helpers.get_new_id_opendrive(context)
                direct_junction_name = 'direct_junction' + '_' + str(direct_junction_id)
                obj_direct_junction = bpy.data.objects.new(direct_junction_name, None)
                obj_direct_junction.empty_display_type = 'PLAIN_AXES'
                if self.params['road_split_lane_idx'] > self.params['lanes_left_num']:
                    if self.params['road_split_type'] == 'start':
                        obj_direct_junction.location = obj['cp_start_r']
                    else:
                        obj_direct_junction.location = obj['cp_end_r']
                else:
                    if self.params['road_split_type'] == 'start':
                        obj_direct_junction.location = obj['cp_start_l']
                    else:
                        obj_direct_junction.location = obj['cp_end_l']
                # FIXME also add rotation based on road heading and slope
                helpers.link_object_opendrive(context, obj_direct_junction)
                obj_direct_junction['id_odr'] = direct_junction_id
                obj_direct_junction['dsc_category'] = 'OpenDRIVE'
                obj_direct_junction['dsc_type'] = 'junction_direct'
                if self.params['road_split_type'] == 'start':
                    obj['id_direct_junction_start'] = direct_junction_id
                else:
                    obj['id_direct_junction_end'] = direct_junction_id

            # Set OpenDRIVE custom properties
            obj['id_odr'] = id_obj

            obj['geometry'] = self.geometry.params

            obj['lanes_left_num'] = self.params['lanes_left_num']
            obj['lanes_right_num'] = self.params['lanes_right_num']
            obj['lanes_left_types'] = self.params['lanes_left_types']
            obj['lanes_right_types'] = self.params['lanes_right_types']
            obj['lanes_left_widths'] = self.params['lanes_left_widths']
            obj['lanes_left_widths_change'] = self.params['lanes_left_widths_change']
            obj['lanes_right_widths'] = self.params['lanes_right_widths']
            obj['lanes_right_widths_change'] = self.params['lanes_right_widths_change']
            obj['lanes_left_road_mark_types'] = self.params['lanes_left_road_mark_types']
            obj['lanes_left_road_mark_weights'] = self.params['lanes_left_road_mark_weights']
            obj['lanes_left_road_mark_colors'] = self.params['lanes_left_road_mark_colors']
            obj['lanes_right_road_mark_types'] = self.params['lanes_right_road_mark_types']
            obj['lanes_right_road_mark_weights'] = self.params['lanes_right_road_mark_weights']
            obj['lanes_right_road_mark_colors'] = self.params['lanes_right_road_mark_colors']
            obj['lane_center_road_mark_type'] = self.params['lane_center_road_mark_type']
            obj['lane_center_road_mark_weight'] = self.params['lane_center_road_mark_weight']
            obj['lane_center_road_mark_color'] = self.params['lane_center_road_mark_color']

            return obj

    def update_params_get_mesh(self, context, params_input, wireframe):
        '''
            Calculate and return the vertices, edges, faces and parameters to create a road mesh.
        '''
        # Update parameters based on selected points
        self.geometry.update(params_input, self.geometry_solver)
        if self.geometry.params['valid'] == False:
            valid = False
            return valid, None, None, []
        length_broken_line = context.scene.road_properties.length_broken_line
        self.set_lane_params(context.scene.road_properties)
        lanes = context.scene.road_properties.lanes
        # Get values in t and s direction where the faces of the road start and end
        strips_s_boundaries = self.get_strips_s_boundaries(lanes, length_broken_line)
        # Calculate meshes for Blender
        road_sample_points = self.get_road_sample_points(lanes, strips_s_boundaries)
        vertices, edges, faces = self.get_road_vertices_edges_faces(road_sample_points)
        materials = self.get_face_materials(lanes, strips_s_boundaries)

        if wireframe:
            # Transform start and end point to local coordinate system then add
            # a vertical edge down to the xy-plane to make elevation profile
            # more easily visible
            point_start = (self.geometry.params['point_start'])
            point_start_local = (0.0, 0.0, 0.0)
            point_start_bottom = (0.0, 0.0, -point_start.z)
            point_end = self.geometry.params['point_end']
            point_end_local = self.geometry.matrix_world.inverted() @ point_end
            point_end_local.z = point_end.z - point_start.z
            point_end_bottom = (point_end_local.x, point_end_local.y, -point_start.z)
            vertices += [point_start_local[:], point_start_bottom, point_end_local[:], point_end_bottom]
            edges += [[len(vertices)-1, len(vertices)-2], [len(vertices)-3, len(vertices)-4]]

        # Create blender mesh
        mesh = bpy.data.meshes.new('temp_road')
        if not wireframe:
            mesh.from_pydata(vertices, edges, faces)
        else:
            mesh.from_pydata(vertices, edges, [])
        valid = True
        return valid, mesh, self.geometry.matrix_world, materials

    def set_lane_params(self, road_properties):
        '''
            Set the lane parameters dictionary for later export.
        '''
        self.params = {'lanes_left_num': road_properties.num_lanes_left,
                       'lanes_right_num': road_properties.num_lanes_right,
                       'lanes_left_widths': [],
                       'lanes_left_widths_change': [],
                       'lanes_right_widths': [],
                       'lanes_right_widths_change': [],
                       'lanes_left_types': [],
                       'lanes_right_types': [],
                       'lanes_left_road_mark_types': [],
                       'lanes_left_road_mark_weights': [],
                       'lanes_left_road_mark_colors': [],
                       'lanes_right_road_mark_types': [],
                       'lanes_right_road_mark_weights': [],
                       'lanes_right_road_mark_colors': [],
                       'lane_center_road_mark_type': [],
                       'lane_center_road_mark_weight': [],
                       'lane_center_road_mark_color': [],
                       'road_split_type': road_properties.road_split_type,
                       'road_split_lane_idx': road_properties.road_split_lane_idx}
        for idx, lane in enumerate(road_properties.lanes):
            if lane.side == 'left':
                self.params['lanes_left_widths'].insert(0, lane.width)
                self.params['lanes_left_widths_change'].insert(0, lane.width_change)
                self.params['lanes_left_types'].insert(0, lane.type)
                self.params['lanes_left_road_mark_types'].insert(0, lane.road_mark_type)
                self.params['lanes_left_road_mark_weights'].insert(0, lane.road_mark_weight)
                self.params['lanes_left_road_mark_colors'].insert(0, lane.road_mark_color)
            elif lane.side == 'right':
                self.params['lanes_right_widths'].append(lane.width)
                self.params['lanes_right_widths_change'].append(lane.width_change)
                self.params['lanes_right_types'].append(lane.type)
                self.params['lanes_right_road_mark_types'].append(lane.road_mark_type)
                self.params['lanes_right_road_mark_weights'].append(lane.road_mark_weight)
                self.params['lanes_right_road_mark_colors'].append(lane.road_mark_color)
            else:
                # lane.side == 'center'
                self.params['lane_center_road_mark_type'] = lane.road_mark_type
                self.params['lane_center_road_mark_weight'] = lane.road_mark_weight
                self.params['lane_center_road_mark_color'] = lane.road_mark_color

    def get_split_cps(self, road_split_type):
        '''
            Return the two connection points for a split road.
        '''
        t_cp_split = self.road_split_lane_idx_to_t()
        if road_split_type == 'start':
            t = 0
            cp_base = self.geometry.params['point_start']
        else:
            t = self.geometry.params['length']
            cp_base = self.geometry.params['point_end']
        # Split
        cp_split = self.geometry.matrix_world @ Vector(self.geometry.sample_cross_section(
            t, [t_cp_split])[0][0])
        # Check which part of the split contains the center lane, that part
        # gets the contact point on the center lane
        if t_cp_split < 0:
            return cp_base, cp_split
        else:
            return cp_split, cp_base

    def road_split_lane_idx_to_t(self):
        '''
            Convert index of first splitting lane to t coordinate of left/right
            side of the split lane border. Return 0 if there is no split.
        '''
        t_cp_split = 0
        road_split_lane_idx = self.params['road_split_lane_idx']
        # Check if there really is a split
        if self.params['road_split_type'] != 'none':
            # Calculate lane ID from split index
            if self.params['lanes_left_num'] > 0:
                lane_id_split = -1 * (road_split_lane_idx - self.params['lanes_left_num'])
            else:
                lane_id_split = -1 * road_split_lane_idx
            # Calculate t coordinate of split connecting point
            for idx in range(abs(lane_id_split)):
                if lane_id_split > 0:
                    # Do not add lanes with 0 width
                    if not ((self.params['road_split_type'] == 'start' and
                                self.params['lanes_left_widths_change'][idx] == 'open') or
                            (self.params['road_split_type'] == 'end' and \
                                self.params['lanes_left_widths_change'][idx] == 'close')):
                        t_cp_split += self.params['lanes_left_widths'][idx]
                else:
                    # Do not add lanes with 0 width
                    if not ((self.params['road_split_type'] == 'start' and
                                self.params['lanes_right_widths_change'][idx] == 'open') or
                            (self.params['road_split_type'] == 'end' and \
                                self.params['lanes_right_widths_change'][idx] == 'close')):
                        t_cp_split -= self.params['lanes_right_widths'][idx]
        return t_cp_split

    def get_width_road_left(self, lanes):
        '''
            Return the width of the left road side calculated by suming up all
            lane widths.
        '''
        width_road_left = 0
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
            # Stop when reaching the right side
            if lane.side == 'right':
                break
            if lane.side == 'left':
                width_road_left += lane.width
        return width_road_left

    def get_strips_t_values(self, lanes, s):
        '''
            Return list of t values of strip borders.
        '''
        t = self.get_width_road_left(lanes)
        t_values = []
        # Make sure the road has a non-zero length
        if self.geometry.params['length'] == 0:
            return t_values
        # Build up t values lane by lane
        for idx_lane, lane in enumerate(lanes):
            s_norm = s / self.geometry.params['length']
            if lane.width_change == 'open':
                lane_width_s = (3.0 * s_norm**2 - 2.0 * s_norm**3) * lane.width
            elif lane.width_change == 'close':
                lane_width_s = (1.0 - 3.0 * s_norm**2 + 2.0 * s_norm**3) * lane.width
            else:
                lane_width_s = lane.width
            # Add lane width for right side of road BEFORE (in t-direction) road mark lines
            if lane.side == 'right':
                width_left_lines_on_lane = 0.0
                if lanes[idx_lane - 1].road_mark_type != 'none':
                    width_line = lanes[idx_lane - 1].road_mark_width
                    if lanes[idx_lane - 1].road_mark_type == 'solid_solid' or \
                            lanes[idx_lane - 1].road_mark_type == 'solid_broken' or \
                            lanes[idx_lane - 1].road_mark_type == 'broken_solid':
                        width_left_lines_on_lane = width_line * 3.0 / 2.0
                    else:
                        width_left_lines_on_lane = width_line / 2.0
                width_right_lines_on_lane = 0.0
                if lane.road_mark_type != 'none':
                    width_line = lane.road_mark_width
                    if lane.road_mark_type == 'solid_solid' or \
                            lane.road_mark_type == 'solid_broken' or \
                            lane.road_mark_type == 'broken_solid':
                        width_right_lines_on_lane = width_line * 3.0 / 2.0
                    else:
                        width_right_lines_on_lane = width_line / 2.0
                t -= lane_width_s - width_left_lines_on_lane - width_right_lines_on_lane
            # Add road mark lines
            if lane.road_mark_type != 'none':
                width_line = lane.road_mark_width
                if lane.road_mark_type == 'solid_solid' or \
                        lane.road_mark_type == 'solid_broken' or \
                        lane.road_mark_type == 'broken_solid':
                    t_values.append(t)
                    t_values.append(t -       width_line)
                    t_values.append(t - 2.0 * width_line)
                    t_values.append(t - 3.0 * width_line)
                    t = t - 3.0 * width_line
                else:
                    t_values.append(t)
                    t_values.append(t - width_line)
                    t -= width_line
            else:
                t_values.append(t)
            # Add lane width for left side of road AFTER (in t-direction) road mark lines
            if lane.side == 'left':
                width_left_lines_on_lane = 0
                if lane.road_mark_type != 'none':
                    width_line = lane.road_mark_width
                    if lane.road_mark_type == 'solid_solid' or \
                            lane.road_mark_type == 'solid_broken' or \
                            lane.road_mark_type == 'broken_solid':
                        width_left_lines_on_lane = width_line * 3.0 / 2.0
                    else:
                        width_left_lines_on_lane = width_line / 2.0
                width_right_lines_on_lane = 0
                if lanes[idx_lane + 1].road_mark_type != 'none':
                    width_line = lanes[idx_lane + 1].road_mark_width
                    if lanes[idx_lane + 1].road_mark_type == 'solid_solid' or \
                            lanes[idx_lane + 1].road_mark_type == 'solid_broken' or \
                            lanes[idx_lane + 1].road_mark_type == 'broken_solid':
                        width_right_lines_on_lane = width_line * 3.0 / 2.0
                    else:
                        width_right_lines_on_lane = width_line / 2.0
                t -= lane_width_s - width_left_lines_on_lane - width_right_lines_on_lane
        return t_values

    def get_strips_s_boundaries(self, lanes, length_broken_line):
        '''
            Return list of tuples with a line marking toggle flag and a list
            with the start and stop values of the faces in each strip.
        '''
        # Calculate line parameters
        # TODO offset must be provided by predecessor road for each marking
        length = self.geometry.params['length']
        offset = 0.5
        if offset < length_broken_line:
            offset_first = offset
            line_toggle_start = True
        else:
            offset_first = offset % length_broken_line
            line_toggle_start = False
        s_values = []
        for lane in lanes:
            # Calculate broken line parameters
            if lane.road_mark_type == 'broken':
                num_faces_strip_line = ceil((length \
                                        - (length_broken_line - offset_first)) \
                                       / length_broken_line)
                # Add one extra step for the shorter first piece
                if offset_first > 0:
                    num_faces_strip_line += 1
                length_first = min(length, length_broken_line - offset_first)
                if num_faces_strip_line > 1:
                    length_last = length - length_first - (num_faces_strip_line - 2) * length_broken_line
                else:
                    length_last = length_first
            else:
                num_faces_strip_line = 1

            # Go in s direction along lane and calculate the start and stop values
            # ASPHALT
            if lane.side == 'right':
                s_values.append((line_toggle_start, [0, length]))
            # ROAD MARK
            if lane.road_mark_type != 'none':
                s_values_strip = [0]
                for idx_face_strip in range(num_faces_strip_line):
                    # Calculate end points of the faces
                    s_stop = length
                    if lane.road_mark_type == 'broken':
                        if idx_face_strip == 0:
                            # First piece
                            s_stop = length_first
                        elif idx_face_strip > 0 and idx_face_strip + 1 == num_faces_strip_line:
                            # Last piece and more than one piece
                            s_stop = length_first + (idx_face_strip - 1) * length_broken_line \
                                    + length_last
                        else:
                            # Middle piece
                            s_stop = length_first + idx_face_strip * length_broken_line
                    s_values_strip.append(s_stop)
                if lane.road_mark_type == 'solid_solid':
                    s_values.append((line_toggle_start, s_values_strip))
                    s_values.append((line_toggle_start, s_values_strip))
                s_values.append((line_toggle_start, s_values_strip))
            # ASPHALT
            if lane.side == 'left':
                s_values.append((line_toggle_start, [0, length]))
        return s_values

    def get_road_sample_points(self, lanes, strips_s_boundaries):
        '''
            Adaptively sample road in s direction based on local curvature.
        '''
        length = self.geometry.params['length']
        s = 0
        strips_t_values = self.get_strips_t_values(lanes, s)
        # Obtain first curvature value
        xyz_samples, curvature_abs = self.geometry.sample_cross_section(0, strips_t_values)
        # We need 2 vectors for each strip to later construct the faces with one
        # list per face on each side of each strip
        sample_points = [[[]] for _ in range(2 * (len(strips_t_values) - 1))]
        t_offset = 0
        for idx_t in range(len(strips_t_values) - 1):
            sample_points[2 * idx_t][0].append((0, strips_t_values[idx_t], 0))
            sample_points[2 * idx_t + 1][0].append((0, strips_t_values[idx_t + 1], 0))
        # Concatenate vertices until end of road
        idx_boundaries_strips = [0] * len(strips_s_boundaries)
        while s < length:
            # TODO: Make hardcoded sampling parameters configurable
            if curvature_abs == 0:
                step = 5
            else:
                step = max(1, min(5, 0.1 / abs(curvature_abs)))
            s += step
            if s >= length:
                s = length

            # Sample next points along road geometry (all t values for current s value)
            strips_t_values = self.get_strips_t_values(lanes, s)
            xyz_samples, curvature_abs = self.geometry.sample_cross_section(s, strips_t_values)
            point_index = -2
            while point_index < len(sample_points) - 2:
                point_index = point_index + 2
                if not sample_points[point_index][0]:
                    continue
                idx_strip = point_index//2
                # Get the boundaries of road marking faces for current strip plus left and right
                idx_boundaries = [0, 0, 0]
                s_boundaries_next = [length, length, length]
                # Check if there is a strip left and/or right to take into account
                if idx_strip > 0:
                    idx_boundaries[0] = idx_boundaries_strips[idx_strip - 1]
                    s_boundaries_next[0] = strips_s_boundaries[idx_strip - 1][1][idx_boundaries[0] + 1]
                idx_boundaries[1] = idx_boundaries_strips[idx_strip]
                s_boundaries_next[1] = strips_s_boundaries[idx_strip][1][idx_boundaries[1] + 1]
                if idx_strip < len(strips_s_boundaries) - 1:
                    idx_boundaries[2] = idx_boundaries_strips[idx_strip + 1]
                    s_boundaries_next[2] = strips_s_boundaries[idx_strip + 1][1][idx_boundaries[2] + 1]

                # Check if any face boundary is smaller than sample point
                smaller, idx_smaller = self.compare_boundaries_with_s(s, s_boundaries_next)
                if smaller:
                    # Find all boundaries in between
                    while smaller:
                        # Sample the geometry
                        t_values = [strips_t_values[idx_strip], strips_t_values[idx_strip + 1]]
                        xyz_boundary, curvature_abs = self.geometry.sample_cross_section(
                            s_boundaries_next[idx_smaller], t_values)
                        if idx_smaller == 0:
                            # Append left extra point
                            sample_points[2 * idx_strip][idx_boundaries[1]].append(xyz_boundary[0])
                        if idx_smaller == 1:
                            # Append left and right points
                            sample_points[2 * idx_strip][idx_boundaries[1]].append(xyz_boundary[0])
                            sample_points[2 * idx_strip + 1][idx_boundaries[1]].append(xyz_boundary[1])
                            # Start a new list for next face
                            sample_points[2 * idx_strip].append([xyz_boundary[0]])
                            sample_points[2 * idx_strip + 1].append([xyz_boundary[1]])
                        if idx_smaller == 2:
                            # Append right extra point
                            sample_points[2 * idx_strip + 1][idx_boundaries[1]].append(xyz_boundary[1])
                        # Get the next boundary (relative to this strip)
                        idx_boundaries[idx_smaller] += 1
                        idx_strip_relative = idx_strip + idx_smaller - 1
                        s_boundaries_next[idx_smaller] = \
                            strips_s_boundaries[idx_strip_relative][1][idx_boundaries[idx_smaller] + 1]
                        # Check again
                        smaller, idx_smaller = self.compare_boundaries_with_s(s, s_boundaries_next)
                    # Write back indices to global array (only left strip to avoid cross interference!)
                    if idx_strip > 0:
                        idx_boundaries_strips[idx_strip - 1] = idx_boundaries[0]

                # Now there is no boundary in between anymore so append the samples
                sample_points[2 * idx_strip][idx_boundaries[1]].append(xyz_samples[idx_strip])
                sample_points[2 * idx_strip + 1][idx_boundaries[1]].append(xyz_samples[idx_strip + 1])
        return sample_points

    def compare_boundaries_with_s(self, s, s_boundaries_next):
        '''
            Return True if any boundary is smaller than s, also return the index
            to the boundary.
        '''
        smaller = False
        idx_sorted = sorted(range(len(s_boundaries_next)), key=s_boundaries_next.__getitem__)
        if s_boundaries_next[idx_sorted[0]] < s:
            smaller = True

        return smaller, idx_sorted[0]

    def get_road_vertices_edges_faces(self, road_sample_points):
        '''
           generate mesh from samplepoints
        '''
        vertices = []
        edges = []
        faces = []
        idx_vertex = 0
        point_index = 0
        while point_index < len(road_sample_points):
            for idx_face_strip in range(len(road_sample_points[point_index])):
                # ignore empty samplepoints, it may be none type line or any thing that doesn't need to build a mesh
                if not road_sample_points[point_index][0]:
                    continue
                samples_right = road_sample_points[point_index + 1][idx_face_strip]
                samples_left = road_sample_points[point_index][idx_face_strip]
                num_vertices = len(samples_left) + len(samples_right)
                vertices += samples_right + samples_left[::-1]
                edges += [[idx_vertex + n, idx_vertex + n + 1] for n in range(num_vertices - 1)] \
                         + [[idx_vertex + num_vertices - 1, idx_vertex]]
                faces += [[idx_vertex + n for n in range(num_vertices)]]
                idx_vertex += num_vertices
            point_index = point_index + 2
        return vertices, edges, faces

    def get_strip_to_lane_mapping(self, lanes):
        '''
            Return list of lane indices for strip indices.
        '''
        strip_to_lane = []
        strip_is_road_mark = []
        for idx_lane, lane in enumerate(lanes):
            if lane.side == 'left':
                if lane.road_mark_type != 'none':
                    if lane.road_mark_type == 'solid' or \
                        lane.road_mark_type == 'broken':
                        strip_to_lane.append(idx_lane)
                        strip_is_road_mark.append(True)
                    else:
                        # Double line
                        strip_to_lane.append(idx_lane)
                        strip_to_lane.append(idx_lane)
                        strip_to_lane.append(idx_lane)
                        strip_is_road_mark.append(True)
                        strip_is_road_mark.append(False)
                        strip_is_road_mark.append(True)
                strip_to_lane.append(idx_lane)
                strip_is_road_mark.append(False)
            elif lane.side == 'center':
                if lane.road_mark_type != 'none':
                    if lane.road_mark_type == 'solid' or \
                        lane.road_mark_type == 'broken':
                        strip_to_lane.append(idx_lane)
                        strip_is_road_mark.append(True)
                    else:
                        # Double line
                        strip_to_lane.append(idx_lane)
                        strip_to_lane.append(idx_lane)
                        strip_to_lane.append(idx_lane)
                        strip_is_road_mark.append(True)
                        strip_is_road_mark.append(False)
                        strip_is_road_mark.append(True)
            else:
                # lane.side == 'right'
                strip_to_lane.append(idx_lane)
                strip_is_road_mark.append(False)
                if lane.road_mark_type != 'none':
                    if lane.road_mark_type == 'solid' or \
                        lane.road_mark_type == 'broken':
                        strip_to_lane.append(idx_lane)
                        strip_is_road_mark.append(True)
                    else:
                        # Double line
                        strip_to_lane.append(idx_lane)
                        strip_to_lane.append(idx_lane)
                        strip_to_lane.append(idx_lane)
                        strip_is_road_mark.append(True)
                        strip_is_road_mark.append(False)
                        strip_is_road_mark.append(True)
        return strip_to_lane, strip_is_road_mark

    def get_road_mark_material(self, color):
        '''
            Return material name for road mark color.
        '''
        mapping_color_material = {
            'white': 'road_mark_white',
            'yellow': 'road_mark_yellow',
        }
        return mapping_color_material[color]

    def get_face_materials(self, lanes, strips_s_boundaries):
        '''
            Return dictionary with index of faces for each material.
        '''
        materials = {'asphalt': [], 'road_mark_white': [], 'road_mark_yellow': [], 'grass': []}
        idx_face = 0
        strip_to_lane, strip_is_road_mark = self.get_strip_to_lane_mapping(lanes)
        for idx_strip in range(len(strips_s_boundaries)):
            idx_lane = strip_to_lane[idx_strip]
            if strip_is_road_mark[idx_strip]:
                line_toggle = strips_s_boundaries[idx_strip][0]
                num_faces = int(len(strips_s_boundaries[idx_strip][1]) - 1)
                material = self.get_road_mark_material(lanes[idx_lane].road_mark_color)
                # Step through faces of a road mark strip
                for idx in range(num_faces):
                    # Determine material
                    if lanes[idx_lane].road_mark_type == 'solid':
                        materials[material].append(idx_face)
                        idx_face += 1
                    elif lanes[idx_lane].road_mark_type == 'broken':
                        if line_toggle:
                            materials[material].append(idx_face)
                            line_toggle = False
                        else:
                            materials['asphalt'].append(idx_face)
                            line_toggle = True
                        idx_face += 1
                    elif lanes[idx_lane].road_mark_type == 'solid_solid':
                        materials[material].append(idx_face)
                        idx_face += 1
            else:
                if lanes[idx_lane].type == 'median':
                    materials['grass'].append(idx_face)
                elif lanes[idx_lane].type == 'shoulder':
                    materials['grass'].append(idx_face)
                else:
                    materials['asphalt'].append(idx_face)
                idx_face += 1

        return materials
