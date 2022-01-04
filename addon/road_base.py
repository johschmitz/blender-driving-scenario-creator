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

from . modal_two_point_base import DSC_OT_two_point_base
from . road_properties import get_num_split_lanes_left
from . import helpers

from math import ceil


class DSC_OT_road(DSC_OT_two_point_base):
    bl_idname = 'dsc.road'
    bl_label = 'Road'
    bl_description = 'Create road mesh'
    bl_options = {'REGISTER', 'UNDO'}

    snap_filter = 'OpenDRIVE'

    geometry = None
    params = {}

    width_road_left = 0

    geometry_solver: bpy.props.StringProperty(
        name='Geometry solver',
        description='Solver used to determine geometry parameters.',
        options={'HIDDEN'},
        default='default')

    def create_object(self, context):
        '''
            Create the Blender road object
        '''
        valid, mesh_road, matrix_world, materials = self.get_mesh_update_params(context, for_stencil=False)
        if not valid:
            return None
        else:
            # Create road object
            obj_id = helpers.get_new_id_opendrive(context)
            mesh_road.name = self.object_type + '_' + str(obj_id)
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
            obj['dsc_type'] = 'road'

            # Number lanes which split to the right at road end
            obj['num_split_lanes_left'] = self.params['num_split_lanes_left']
            # Remember connecting points for road snapping
            obj['cp_start'] = self.geometry.params['point_start']
            obj['cp_end_l'], obj['cp_end_r']= self.get_cps_end()

            # Set OpenDRIVE custom properties
            obj['id_xodr'] = obj_id

            obj['geometry'] = self.geometry.params

            obj['lanes_left_num'] = self.params['lanes_left_num']
            obj['lanes_right_num'] = self.params['lanes_right_num']
            obj['lanes_left_types'] = self.params['lanes_left_types']
            obj['lanes_right_types'] = self.params['lanes_right_types']
            obj['lanes_left_widths'] = self.params['lanes_left_widths']
            obj['lanes_right_widths'] = self.params['lanes_right_widths']
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

    def get_mesh_update_params(self, context, for_stencil):
        '''
            Calculate and return the vertices, edges, faces and parameters to create a road mesh.
        '''
        # Update based on selected points
        self.update_lane_params(context)
        self.geometry.update(self.params_input, self.geometry_solver)
        if self.geometry.params['valid'] == False:
            self.report({'WARNING'}, 'No valid road geometry solution found!')
        # Get values in t and s direction where the faces of the road start and end
        strips = context.scene.road_properties.strips
        length_broken_line = context.scene.road_properties.length_broken_line
        width_line_standard = context.scene.road_properties.width_line_standard
        width_line_bold = context.scene.road_properties.width_line_bold
        self.set_lane_params(strips, width_line_standard, width_line_bold)
        # TODO: Possible optimization is to recalculate t values only when a cross section update occurs
        strips_t_values = self.get_strips_t_values(strips, width_line_standard, width_line_bold)
        strips_s_boundaries = self.get_strips_s_boundaries(strips, length_broken_line)
        road_sample_points = self.get_road_sample_points(strips, strips_t_values, strips_s_boundaries)
        vertices, edges, faces = self.get_road_vertices_edges_faces(road_sample_points)
        materials = self.get_face_materials(strips, strips_s_boundaries)

        # Create blender mesh
        mesh = bpy.data.meshes.new('temp_road')
        if not for_stencil:
            mesh.from_pydata(vertices, edges, faces)
        else:
            mesh.from_pydata(vertices, edges, [])
        valid = True
        return valid, mesh, self.geometry.matrix_world, materials

    def update_lane_params(self, context):
        road_properties = context.scene.road_properties
        num_split_lanes_left = get_num_split_lanes_left(road_properties)
        self.params = {'lanes_left_num': road_properties.num_lanes_left,
                       'lanes_right_num': road_properties.num_lanes_right,
                       'lanes_left_widths': [],
                       'lanes_right_widths': [],
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
                       'num_split_lanes_left': num_split_lanes_left}

    def get_cps_end(self):
        '''
            Return the two connection points for a split road. Return identical points
            in case of no split.
        '''
        num_split_lanes_left = self.params['num_split_lanes_left']
        t_cp_split = self.num_split_lanes_left_to_t(num_split_lanes_left)
        # Calculate connection points
        num_lanes = self.params['lanes_left_num'] + self.params['lanes_right_num']
        if num_split_lanes_left == 0 or num_split_lanes_left == num_lanes:
            # No split
            return self.geometry.params['point_end'], self.geometry.params['point_end']
        else:
            # Split
            cp_split = self.geometry.matrix_world @ Vector(self.geometry.sample_cross_section(
                self.geometry.params['length'], [t_cp_split])[0][0])
            # Check which part of the split contains the center lane, that part
            # gets the contact point on the center lane
            if t_cp_split < 0:
                return self.geometry.params['point_end'], cp_split
            else:
                return cp_split, self.geometry.params['point_end']

    def num_split_lanes_left_to_t(self, num_split_lanes_left):
        '''
            Convert number of lanes to the t coordinate of the left lane border.
            Return 0 if there is no split.
        '''
        t_cp_split = 0
        # Check if there really is a split
        if num_split_lanes_left < (self.params['lanes_left_num'] + self.params['lanes_left_num']):
            # Calculate lane idx from the number of lanes that split
            if self.params['lanes_left_num'] > 0:
                lane_id_split = num_split_lanes_left - self.params['lanes_left_num']
            else:
                lane_id_split = num_split_lanes_left - 1
            # Calculate t coordinate of split connection point
            if lane_id_split < 0:
                for idx in range(abs(lane_id_split)):
                    t_cp_split += self.params['lanes_left_widths'][idx]
            else:
                for idx in range(lane_id_split):
                    t_cp_split -= self.params['lanes_right_widths'][idx]
        return t_cp_split

    def map_road_mark_weight_to_width(self, road_mark_weight, width_line_standard, width_line_bold):
        '''
            Map a road mark weight (standard/bold) to the specified width.
        '''
        mapping_road_mark_weight = {
            'standard' : width_line_standard,
            'bold' : width_line_bold,
        }
        width = mapping_road_mark_weight[road_mark_weight]
        return width

    def get_width_road_left(self, strips, width_line_standard, width_line_bold):
        '''
            Return the width of the left road side calculated by suming up all
            lane widths.
        '''
        width_road_left = 0
        for idx, strip in enumerate(strips):
            if idx == 0:
                if strip.type == 'line':
                    if strip.road_mark_type != 'none':
                        # If first strip is a line we need to add half its width
                        width_line = self.map_road_mark_weight_to_width(strip.road_mark_weight,
                            width_line_standard, width_line_bold)
                        if strip.road_mark_type == 'solid_solid' or \
                            strip.road_mark_type == 'solid_broken' or \
                            strip.road_mark_type == 'broken_solid':
                                width_road_left += width_line * 3.0 / 2.0
                        else:
                            width_road_left += width_line / 2.0
            # Stop when reaching the right side
            if strip.direction == 'right':
                break
            if strip.type != 'line':
                if strip.direction == 'left':
                    width_road_left += strip.width
        return width_road_left

    def set_lane_params(self, strips, width_line_standard, width_line_bold):
        '''
            Set the lane parameters dictionary for later export.
        '''
        for idx, strip in enumerate(strips):
            if strip.type != 'line':
                if strip.direction == 'left':
                    self.params['lanes_left_widths'].insert(0, strip.width)
                    self.params['lanes_left_types'].insert(0, strip.type)
                else:
                    self.params['lanes_right_widths'].append(strip.width)
                    self.params['lanes_right_types'].append(strip.type)
            elif strip.direction == 'center':
                self.params['lane_center_road_mark_type'] = strip.road_mark_type
                self.params['lane_center_road_mark_weight'] = strip.road_mark_weight
                self.params['lane_center_road_mark_color'] = strip.road_mark_color
            else:
                if strip.direction == 'left':
                    self.params['lanes_left_road_mark_types'].insert(0, strip.road_mark_type)
                    self.params['lanes_left_road_mark_weights'].insert(0, strip.road_mark_weight)
                    self.params['lanes_left_road_mark_colors'].insert(0, strip.road_mark_color)
                else:
                    self.params['lanes_right_road_mark_types'].append(strip.road_mark_type)
                    self.params['lanes_right_road_mark_weights'].append(strip.road_mark_weight)
                    self.params['lanes_right_road_mark_colors'].append(strip.road_mark_color)

    def get_strips_t_values(self, strips, width_line_standard, width_line_bold):
        '''
            Return list of t values of strip borders.
        '''
        t = self.get_width_road_left(strips, width_line_standard, width_line_bold)
        t_values = [t, ]
        for idx_strip, strip in enumerate(strips):
            if strip.type == 'line':
                # Add nothing for 'none' road marks
                if strip.road_mark_type != 'none':
                    width_line = self.map_road_mark_weight_to_width(strip.road_mark_weight,
                        width_line_standard, width_line_bold)
                    if strip.road_mark_type == 'solid_solid' or \
                            strip.road_mark_type == 'solid_broken' or \
                            strip.road_mark_type == 'broken_solid':
                        t = t - 3 * width_line
                        t_values.append(t + width_line * 2)
                        t_values.append(t + width_line)
                    else:
                        t = t - width_line
            else:
                # Check if lines exist to left and/or right
                width_both_lines_on_lane = 0
                if idx_strip >= 0:
                    if strips[idx_strip - 1].type == 'line':
                        if strips[idx_strip - 1].road_mark_type != 'none':
                            width_line = self.map_road_mark_weight_to_width(
                                strips[idx_strip - 1].road_mark_weight, width_line_standard, width_line_bold)
                            if strips[idx_strip - 1].road_mark_type == 'solid_solid' or \
                                    strips[idx_strip - 1].road_mark_type == 'solid_broken' or \
                                    strips[idx_strip - 1].road_mark_type == 'broken_solid':
                                width_both_lines_on_lane += width_line * 3.0 / 2.0
                            else:
                                width_both_lines_on_lane += width_line / 2.0
                if idx_strip < len(strips) - 1:
                    if strips[idx_strip + 1].type == 'line':
                        if strips[idx_strip + 1].road_mark_type != 'none':
                            width_line = self.map_road_mark_weight_to_width(
                                strips[idx_strip + 1].road_mark_weight, width_line_standard, width_line_bold)
                            if strips[idx_strip + 1].road_mark_type == 'solid_solid' or \
                                    strips[idx_strip + 1].road_mark_type == 'solid_broken' or \
                                    strips[idx_strip + 1].road_mark_type == 'broken_solid':
                                width_both_lines_on_lane += width_line * 3.0 / 2.0
                            else:
                                width_both_lines_on_lane += width_line / 2.0
                # Adjust lane mesh width to not overlap with lines
                t = t - strip.width + width_both_lines_on_lane
            t_values.append(t)
        return t_values

    def get_strips_s_boundaries(self, strips, length_broken_line):
        '''
            Return list of tuples with a line toggle flag and a list with the
            start and stop values of the faces in each strip.
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
        for strip in strips:
            # Calculate broken line parameters
            if strip.road_mark_type == 'broken':
                num_faces_strip = ceil((length \
                                        - (length_broken_line - offset_first)) \
                                       / length_broken_line)
                # Add one extra step for the shorter first piece
                if offset_first > 0:
                    num_faces_strip += 1
                length_first = min(length, length_broken_line - offset_first)
                if num_faces_strip > 1:
                    length_last = length - length_first - (num_faces_strip - 2) * length_broken_line
                else:
                    length_last = length_first
            else:
                num_faces_strip = 1

            # Go in s direction along strip and calculate the start and stop values
            s_values_strip = [0]
            for idx_face_strip in range(num_faces_strip):
                # Calculate end points of the faces
                s_stop = length
                if strip.road_mark_type == 'broken':
                    if idx_face_strip == 0:
                        # First piece
                        s_stop = length_first
                    elif idx_face_strip > 0 and idx_face_strip + 1 == num_faces_strip:
                        # Last piece and more than one piece
                        s_stop = length_first + (idx_face_strip - 1) * length_broken_line \
                                 + length_last
                    else:
                        # Middle piece
                        s_stop = length_first + idx_face_strip * length_broken_line
                s_values_strip.append(s_stop)
            if strip.road_mark_type == 'solid_solid':
                s_values.append((line_toggle_start, s_values_strip))
                s_values.append((line_toggle_start, s_values_strip))
            s_values.append((line_toggle_start, s_values_strip))
        return s_values

    def get_road_sample_points(self, strips, strips_t_values, strips_s_boundaries):
        '''
            Adaptively sample road in s direction based on local curvature.
        '''
        length = self.geometry.params['length']
        s = 0
        # Obtain first curvature value
        xyz_samples, curvature_abs = self.geometry.sample_cross_section(0, strips_t_values)
        # We need 2 vectors for each strip to later construct the faces with one
        # list per face on each side of each strip
        sample_points = [[[]] for _ in range(2 * (len(strips_t_values) - 1))]
        t_offset = 0
        for idx_strip, strip in enumerate(strips):
            index = idx_strip + t_offset
            if strip.type == 'line' and strip.road_mark_type == 'none':
                continue
            if strip.road_mark_type == 'solid_solid':
                lane_num = 3
                for i in range(lane_num):
                    step_index = index + i
                    sample_points[2 * step_index][0].append((0, strips_t_values[step_index], 0))
                    sample_points[2 * step_index + 1][0].append((0, strips_t_values[step_index + 1], 0))
                t_offset = t_offset + lane_num - 1
                continue
            sample_points[2 * index][0].append((0, strips_t_values[index], 0))
            sample_points[2 * index + 1][0].append((0, strips_t_values[index + 1], 0))
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
                if idx_strip < len(strips) - 1:
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

    def get_road_mark_material(self, color):
        '''
            Return material name for road mark color.
        '''
        mapping_color_material = {
            'white': 'road_mark_white',
            'yellow': 'road_mark_yellow',
        }
        return mapping_color_material[color]

    def get_face_materials(self, strips, strips_s_boundaries):
        '''
            Return dictionary with index of faces for each material.
        '''
        materials = {'asphalt': [], 'road_mark_white': [], 'road_mark_yellow': [], 'grass': []}
        idx_face = 0
        offset = 0
        for idx_strip, strip in enumerate(strips):
            line_toggle = strips_s_boundaries[idx_strip + offset][0]
            num_faces = int(len(strips_s_boundaries[idx_strip + offset][1]) - 1)
            if strip.type == 'line' and strip.road_mark_type != 'none':
                material = self.get_road_mark_material(strip.road_mark_color)
            elif strip.type == 'median':
                material = 'grass'
            else:
                material = 'asphalt'
            for idx in range(num_faces):
                # Determine material
                if strip.road_mark_type == 'broken':
                    if line_toggle:
                        materials[material].append(idx_face)
                        line_toggle = False
                    else:
                        materials['asphalt'].append(idx_face)
                        line_toggle = True
                elif strip.road_mark_type == 'solid_solid':
                    materials[material].append(idx_face)
                    materials['asphalt'].append(idx_face + 1)
                    materials[material].append(idx_face + 2)
                    idx_face = idx_face + 2
                    offset += 2
                elif strip.type == 'median':
                    materials['grass'].append(idx_face)
                elif strip.type == 'shoulder':
                    materials['grass'].append(idx_face)
                else:
                    # Do not add material for 'none' lines
                    if not (strip.type == 'line' and strip.road_mark_type == 'none'):
                        materials[material].append(idx_face)
                # Do not count 'none' road marks which create no faces
                if not (strip.type == 'line' and strip.road_mark_type == 'none'):
                    idx_face += 1
        return materials

