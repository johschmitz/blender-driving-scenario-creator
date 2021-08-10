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

import bmesh
from mathutils import Vector, Matrix

from math import pi, ceil

from . operator_snap_draw import DSC_OT_snap_draw
from . road_properties import DSC_road_properties
from . import helpers


class DSC_OT_road_straight(DSC_OT_snap_draw):
    bl_idname = 'dsc.road_straight'
    bl_label = 'Straight'
    bl_description = 'Create a straight road'
    bl_options = {'REGISTER', 'UNDO'}

    object_type = 'road_straight'

    def create_object(self, context):
        '''
            Create a straight road object
        '''
        valid, mesh_road, materials, params = self.get_mesh_and_params(context, for_stencil=False)
        if not valid:
            return None
        else:
            # Create road object
            obj_id = helpers.get_new_id_opendrive(context)
            mesh_road.name = self.object_type + '_' + str(obj_id)
            obj = bpy.data.objects.new(mesh_road.name, mesh_road)
            self.transform_object_wrt_start(obj, params['point_start'], params['heading_start'])
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
            obj['lanes_left_num'] = params['lanes_left_num']
            obj['lanes_right_num'] = params['lanes_right_num']
            obj['lanes_left_types'] = params['lanes_left_types']
            obj['lanes_right_types'] = params['lanes_right_types']
            obj['lanes_left_widths'] = params['lanes_left_widths']
            obj['lanes_right_widths'] = params['lanes_right_widths']
            obj['lanes_left_road_mark_types'] = params['lanes_left_road_mark_types']
            obj['lanes_right_road_mark_types'] = params['lanes_right_road_mark_types']
            obj['lane_center_road_mark_type'] = params['lane_center_road_mark_type']

            return obj

    def get_mesh_and_params(self, context, for_stencil):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        road_properties = context.scene.road_properties
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
                  'length': length,
                  'lanes_right_num': road_properties.lanes_right_num,
                  'lanes_left_num': road_properties.lanes_left_num,
                  'lanes_left_widths': [],
                  'lanes_right_widths': [],
                  'lanes_left_types': [],
                  'lanes_right_types': [],
                  'lanes_left_road_mark_types': [],
                  'lanes_right_road_mark_types': [],
                 }
        # Calculate line parameters
        length_line = 3.0
        # TODO offset must be provided by predecessor road
        offset = 0.5
        if offset < length_line:
            offset_first = offset
            line_toggle_start = True
        else:
            offset_first = offset % length_line
            line_toggle_start = False
        # Initialize
        width_road_left = 0
        for idx, strip in enumerate(road_properties.strips):
            if idx == 0:
                if strip.type == 'line':
                    if strip.type_road_mark != 'none':
                        # If first strip is a line we need to add half its width
                        width_road_left += strip.width/2
            if not strip.type == 'line':
                if strip.direction == 'left':
                    width_road_left += strip.width
                    params['lanes_left_widths'].insert(0,strip.width)
                    params['lanes_left_types'].insert(0,strip.type)
                else:
                    params['lanes_right_widths'].append(strip.width)
                    params['lanes_right_types'].append(strip.type)
            elif strip.direction == 'center':
                params['lane_center_road_mark_type'] = strip.type_road_mark
            else:
                if strip.direction == 'left':
                    params['lanes_left_road_mark_types'].insert(0,strip.type_road_mark)
                else:
                    params['lanes_right_road_mark_types'].append(strip.type_road_mark)
        vertices = []
        edges = []
        faces = []
        t = width_road_left
        idx_vertex = 0
        idx_face = 0
        # Indices of faces for each material
        materials = {'asphalt': [], 'road_mark': [], 'grass': []}
        # Build up road in -t direction strip by strip
        for idx_strip, strip in enumerate(road_properties.strips):
            if strip.type == 'line':
                if strip.type_road_mark == 'none':
                    # Skip none lines completely
                    continue
            # Calculate t values for this strip
            t_start = t
            if strip.type == 'line':
                t_stop = t - strip.width
            else:
                # Check if lines     exist to left and/or right
                width_both_lines_on_lane = 0
                if idx_strip >= 0:
                    if road_properties.strips[idx_strip - 1].type == 'line':
                        if road_properties.strips[idx_strip - 1].type_road_mark != 'none':
                            width_both_lines_on_lane += road_properties.strips[idx_strip - 1].width/2
                if idx_strip < len(road_properties.strips) - 1:
                    if road_properties.strips[idx_strip + 1].type == 'line':
                        if road_properties.strips[idx_strip + 1].type_road_mark != 'none':
                            width_both_lines_on_lane += road_properties.strips[idx_strip + 1].width/2
                # Adjust lane mesh width do not overlap with lines
                t_stop = t - strip.width + width_both_lines_on_lane
            # Update t for next strip
            t = t_stop
            # Calculate broken line parameters
            if strip.type_road_mark == 'broken':
                line_toggle = line_toggle_start
                num_steps = ceil((length - (length_line - offset_first))/length_line)
                # Add one extra step for the shorter first piece
                if offset_first > 0:
                    num_steps += 1
                length_first = min(length, length_line - offset_first)
                if num_steps > 1:
                    length_last = length - length_first - (num_steps-2) * length_line
                else:
                    length_last = length_first
            else:
                num_steps = 1
            # Go in s direction along strip
            for idx_step in range(num_steps):
                start = 0
                stop = length
                if strip.type_road_mark == 'broken':
                    if idx_step == 0:
                        # First piece
                        stop = length_first
                    elif idx_step > 0 and idx_step + 1 == num_steps:
                        # Last piece and more than one piece
                        start = idx_step * length_line - offset_first
                        stop = length_first + (idx_step - 1) * length_line + length_last
                    else:
                        # Middle piece
                        start = idx_step * length_line - offset_first
                        stop = length_first + idx_step * length_line
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
                    materials['asphalt'].append(idx_face)
                # Lines are halfway on both touching lanes
                vertices += [(start, t_start, 0.0),
                             (stop, t_start, 0.0),
                             (start, t_stop, 0.0),
                             (stop, t_stop, 0.0)]
                edges += [[idx_vertex+2, idx_vertex+3], [idx_vertex+3, idx_vertex+1],
                          [idx_vertex+1, idx_vertex], [idx_vertex, idx_vertex+2]]
                if not for_stencil:
                    # Make sure we define faces counterclockwise for correct normals
                    faces += [[idx_vertex+2, idx_vertex+3, idx_vertex+1, idx_vertex]]
                idx_vertex +=4
                idx_face += 1

        # Create blender mesh
        mesh = bpy.data.meshes.new('temp_road')
        mesh.from_pydata(vertices, edges, faces)
        valid = True
        heading = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        return valid, mesh, materials, params
