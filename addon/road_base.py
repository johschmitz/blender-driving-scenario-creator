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

from . modal_two_point_base import DSC_OT_two_point_base
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
                if idx in materials['road_mark']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'road_mark')
                elif idx in materials['grass']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'grass')
                else:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'road_asphalt')
            # Remove double vertices from road lanes and lane lines to simplify mesh
            helpers.remove_duplicate_vertices(context, obj)
            # Make it active for the user to see what he created last
            helpers.select_activate_object(context, obj)

            # Metadata
            obj['dsc_category'] = 'OpenDRIVE'
            obj['dsc_type'] = 'road'

            # Remember connecting points for road snapping
            obj['cp_start'] = self.point_start
            obj['cp_end'] = self.geometry.params['point_end']

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
            obj['lanes_right_road_mark_types'] = self.params['lanes_right_road_mark_types']
            obj['lane_center_road_mark_type'] = self.params['lane_center_road_mark_type']

            return obj

    def get_mesh_update_params(self, context, for_stencil):
        '''
            Calculate and return the vertices, edges, faces and parameters to create a road mesh.
        '''
        if self.snapped_start:
            # Constrain point end
            point_end = self.constrain_point_end(self.point_start, self.heading_start,
                self.point_selected_end)
        else:
            point_end = self.point_selected_end
        if self.point_start == point_end:
            if not for_stencil:
                self.report({'WARNING'}, 'Start and end point can not be the same!')
            valid = False
            return valid, None, None, None

        # Update based on selected points
        self.update_lane_params(context)
        self.geometry.update(self.point_start, self.heading_start, point_end, self.heading_end)

        # Get values in t and s direction where the faces of the road start and end
        strips = context.scene.road_properties.strips
        strips_t_values = self.get_strips_t_values(strips)
        strips_s_boundaries = self.get_strips_s_boundaries(context.scene.road_properties)
        road_sample_points = self.get_road_sample_points(strips, strips_t_values, strips_s_boundaries)
        vertices, edges, faces = self.get_road_vertices_edges_faces(strips, road_sample_points)
        materials = self.get_face_materials(strips, strips_s_boundaries)

        # Create blender mesh
        mesh = bpy.data.meshes.new('temp_road')
        if not for_stencil:
            mesh.from_pydata(vertices, edges, faces)
        else:
            mesh.from_pydata(vertices, edges, [])
        valid = True
        return valid, mesh, self.geometry.matrix_world, materials

    def constrain_point_end(self, point_start, heading_start, point_selected_end):
        '''
            Constrain the endpoint if necessary.
        '''
        raise NotImplementedError()

    def update_lane_params(self, context):
        road_properties = context.scene.road_properties
        self.params = {'lanes_right_num': road_properties.num_lanes_right,
                       'lanes_left_num': road_properties.num_lanes_left,
                       'lanes_left_widths': [],
                       'lanes_right_widths': [],
                       'lanes_left_types': [],
                       'lanes_right_types': [],
                       'lanes_left_road_mark_types': [],
                       'lanes_right_road_mark_types': [],
                       'lane_center_road_mark_type': [],}

    def get_width_road_left(self, strips):
        '''
            Return the width of the left road side calculated by suming up all
            lane widths.
        '''
        width_road_left = 0
        for idx, strip in enumerate(strips):
            if idx == 0:
                if strip.type == 'line':
                    if strip.type_road_mark != 'none':
                        # If first strip is a line we need to add half its width
                        width_road_left += strip.width/2
            if not strip.type == 'line':
                if strip.direction == 'left':
                    width_road_left += strip.width
                    self.params['lanes_left_widths'].insert(0,strip.width)
                    self.params['lanes_left_types'].insert(0,strip.type)
                else:
                    self.params['lanes_right_widths'].append(strip.width)
                    self.params['lanes_right_types'].append(strip.type)
            elif strip.direction == 'center':
                self.params['lane_center_road_mark_type'] = strip.type_road_mark
            else:
                if strip.direction == 'left':
                    self.params['lanes_left_road_mark_types'].insert(0,strip.type_road_mark)
                else:
                    self.params['lanes_right_road_mark_types'].append(strip.type_road_mark)
        return width_road_left

    def get_strips_t_values(self, strips):
        '''
            Return list of t values of strip borders.
        '''
        t = self.get_width_road_left(strips)
        t_values = [t,]
        for idx_strip, strip in enumerate(strips):
            if strip.type == 'line':
                # Add nothing for 'none' road marks
                if strip.type_road_mark != 'none':
                    t = t - strip.width
            else:
                # Check if lines exist to left and/or right
                width_both_lines_on_lane = 0
                if idx_strip >= 0:
                    if strips[idx_strip - 1].type == 'line':
                        if strips[idx_strip - 1].type_road_mark != 'none':
                            width_both_lines_on_lane += strips[idx_strip - 1].width/2
                if idx_strip < len(strips) - 1:
                    if strips[idx_strip + 1].type == 'line':
                        if strips[idx_strip + 1].type_road_mark != 'none':
                            width_both_lines_on_lane += strips[idx_strip + 1].width/2
                # Adjust lane mesh width to not overlap with lines
                t = t - strip.width + width_both_lines_on_lane
            t_values.append(t)
        return t_values

    def get_strips_s_boundaries(self, road_properties):
        '''
            Return list of tuples with a line toggle flag and a list with the
            start and stop values of the faces in each strip.
        '''
        # Calculate line parameters
        # TODO offset must be provided by predecessor road for each marking
        length = self.geometry.params['length']
        # TODO make hardcoded cut length configurable
        cut_length_lane = 100
        offset = 0.5
        if offset < road_properties.length_broken_line:
            offset_first = offset
            line_toggle_start = True
        else:
            offset_first = offset % road_properties.length_broken_line
            line_toggle_start = False
        s_values = []
        for strip in road_properties.strips:
            # Calculate broken line parameters
            if strip.type_road_mark == 'broken':
                num_faces_strip = ceil((length \
                    - (road_properties.length_broken_line - offset_first)) \
                    / road_properties.length_broken_line)
                # Add one extra step for the shorter first piece
                if offset_first > 0:
                    num_faces_strip += 1
                length_first = min(length,
                    road_properties.length_broken_line - offset_first)
                if num_faces_strip > 1:
                    length_last = length - length_first \
                        - (num_faces_strip-2) * road_properties.length_broken_line
                else:
                    length_last = length_first
            else:
                if not (strip.type == 'line' and strip.type_road_mark == 'none'):
                    # We need to subdivide long faces to avoid rendering issues
                    num_faces_strip = int(length // cut_length_lane)
                    if length % cut_length_lane > 0:
                        num_faces_strip += 1
                else:
                    num_faces_strip = 1

            # Go in s direction along strip and calculate the start and stop values
            s_values_strip = [0]
            for idx_face_strip in range(num_faces_strip):
                # Calculate end points of the faces
                # s_start = 0
                if idx_face_strip < num_faces_strip-1:
                    s_stop = (idx_face_strip + 1) * cut_length_lane
                else:
                    s_stop = length
                if strip.type_road_mark == 'broken':
                    if idx_face_strip == 0:
                        # First piece
                        s_stop = length_first
                    elif idx_face_strip > 0 and idx_face_strip + 1 == num_faces_strip:
                        # Last piece and more than one piece
                        # s_start = idx_face_strip * road_properties.length_broken_line - offset_first
                        s_stop = length_first + (idx_face_strip - 1) * road_properties.length_broken_line \
                            + length_last
                    else:
                        # Middle piece
                        # s_start = idx_face_strip * road_properties.length_broken_line - offset_first
                        s_stop = length_first + idx_face_strip * road_properties.length_broken_line
                s_values_strip.append(s_stop)
            s_values.append((line_toggle_start, s_values_strip))
        return s_values

    def get_road_sample_points(self, strips, strips_t_values, strips_s_boundaries):
        '''
            Adaptively sample road in s direction based on local curvature.
        '''
        length = self.geometry.params['length']
        s = 0
        idx_boundaries_strips = [0]*len(strips_s_boundaries)
        # Obtain first curvature value
        xyz_samples, c = self.geometry.sample_local(0, strips_t_values)
        # We need 2 vectors for each strip to later construct the faces with one
        # list per face on each side of each strip
        sample_points = [[[]] for _ in range(2 * len(strips_s_boundaries))]
        for idx_strip, strip in enumerate(strips):
            if not (strip.type == 'line' and strip.type_road_mark == 'none'):
                # Add points for s=0
                sample_points[2*idx_strip][0].append((0, strips_t_values[idx_strip], 0))
                sample_points[2*idx_strip+1][0].append((0, strips_t_values[idx_strip+1], 0))
        # Concatenate vertices until end of road
        while s < length:
            if self.geometry.params['curve'] == 'line':
                # Directly jump to the end of the road
                s = length
            # TODO: Make hardcoded sampling parameters configurable
            if c == 0:
                step = 5
            else:
                step = max(1, min(5, 0.1/abs(c)))
            s += step
            if s >= length:
                s = length

            # Sample next points along road geometry (all t values for current s value)
            xyz_samples, c = self.geometry.sample_local(s, strips_t_values)

            for idx_strip, strip in enumerate(strips):
                # Get the boundaries of road marking faces for current strip plus left and right
                idx_boundaries = [0,0,0]
                s_boundaries_next = [length,length,length]
                # Check if there is a strip left and/or right to take into account
                if idx_strip > 0:
                    idx_boundaries[0] = idx_boundaries_strips[idx_strip-1]
                    s_boundaries_next[0] = strips_s_boundaries[idx_strip-1][1][idx_boundaries[0]+1]
                idx_boundaries[1] = idx_boundaries_strips[idx_strip]
                s_boundaries_next[1] = strips_s_boundaries[idx_strip][1][idx_boundaries[1]+1]
                if idx_strip < len(strips)-1:
                    idx_boundaries[2] = idx_boundaries_strips[idx_strip+1]
                    s_boundaries_next[2] = strips_s_boundaries[idx_strip+1][1][idx_boundaries[2]+1]

                # Check if any face boundary is smaller than sample point
                smaller, idx_smaller = self.compare_boundaries_with_s(s, s_boundaries_next)
                if smaller:
                    # Find all boundaries in between
                    while smaller:
                        # Sample the geometry
                        t_values = [strips_t_values[idx_strip], strips_t_values[idx_strip+1]]
                        xyz_boundary, c = self.geometry.sample_local(
                            s_boundaries_next[idx_smaller], t_values)
                        if idx_smaller == 0:
                            # Append left extra point
                            sample_points[2*idx_strip][idx_boundaries[1]].append(xyz_boundary[0])
                        if idx_smaller == 1:
                            # Append left and right points
                            sample_points[2*idx_strip][idx_boundaries[1]].append(xyz_boundary[0])
                            sample_points[2*idx_strip+1][idx_boundaries[1]].append(xyz_boundary[1])
                            # Start a new list for next face
                            sample_points[2*idx_strip].append([xyz_boundary[0]])
                            sample_points[2*idx_strip+1].append([xyz_boundary[1]])
                        if idx_smaller == 2:
                            # Append right extra point
                            sample_points[2*idx_strip+1][idx_boundaries[1]].append(xyz_boundary[1])
                        # Get the next boundary (relative to this strip)
                        idx_boundaries[idx_smaller] += 1
                        idx_strip_relative = idx_strip + idx_smaller - 1
                        s_boundaries_next[idx_smaller] = \
                            strips_s_boundaries[idx_strip_relative][1][idx_boundaries[idx_smaller]+1]
                        # Check again
                        smaller, idx_smaller = self.compare_boundaries_with_s(s, s_boundaries_next)
                    # Write back indices to global array (only left strip to avoid cross interference!)
                    if idx_strip > 0:
                        idx_boundaries_strips[idx_strip-1] = idx_boundaries[0]

                # Now there is no boundary in between anymore so append the samples
                sample_points[2*idx_strip][idx_boundaries[1]].append(xyz_samples[idx_strip])
                sample_points[2*idx_strip+1][idx_boundaries[1]].append(xyz_samples[idx_strip+1])

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

    def get_road_vertices_edges_faces(self, strips, road_sample_points):
        '''
            Return blender compatible vertices, edges and faces concatenated and
            calculated from road sample points.
        '''
        vertices = []
        edges = []
        faces = []
        idx_vertex = 0
        for idx_strip, strip in enumerate(strips):
            if not (strip.type == 'line' and strip.type_road_mark == 'none'):
                for idx_face_strip in range(len(road_sample_points[2*idx_strip])):
                    samples_right = road_sample_points[2*idx_strip+1][idx_face_strip]
                    samples_left = road_sample_points[2*idx_strip][idx_face_strip]
                    num_vertices = len(samples_left) + len(samples_right)
                    vertices += samples_right + samples_left[::-1]
                    edges += [[idx_vertex+n, idx_vertex+n+1] for n in range(num_vertices-1)] \
                            + [[idx_vertex+num_vertices-1, idx_vertex]]
                    faces += [[idx_vertex+n for n in range(num_vertices)]]

                    idx_vertex += num_vertices

        return vertices, edges, faces

    def get_face_materials(self, strips, strips_s_boundaries):
        '''
            Return dictionary with index of faces for each material.
        '''
        materials = {'asphalt': [], 'road_mark': [], 'grass': []}
        idx_face = 0
        for idx_strip, strip in enumerate(strips):
            line_toggle = strips_s_boundaries[idx_strip][0]
            num_faces = int(len(strips_s_boundaries[idx_strip][1])-1)
            for idx in range(num_faces):
                # Determine material
                if strip.type_road_mark == 'broken':
                    if line_toggle:
                        materials['road_mark'].append(idx_face)
                        line_toggle = False
                    else:
                        materials['asphalt'].append(idx_face)
                        line_toggle = True
                elif strip.type_road_mark == 'solid':
                    materials['road_mark'].append(idx_face)
                elif strip.type == 'median':
                    materials['grass'].append(idx_face)
                elif strip.type == 'shoulder':
                    materials['grass'].append(idx_face)
                else:
                    # Do not add material for 'none' lines
                    if not (strip.type == 'line' and strip.type_road_mark == 'none'):
                        materials['asphalt'].append(idx_face)
                # Do not count 'none' road marks which create no faces
                if not (strip.type == 'line' and strip.type_road_mark == 'none'):
                    idx_face += 1
        return materials