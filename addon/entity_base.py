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

from math import atan2, cos, pi, sin

from . modal_two_point_base import DSC_OT_modal_two_point_base
from . entity import entity
from . import helpers
from .entity_connections import (
    ENTITY_CONNECTION_POINTS,
    get_connection_snap,
    get_entity_position_from_connection_anchor,
    record_entity_connection,
)


def _heading_after_pointer_rotation(start_heading, start_angle, current_angle):
    """Apply the wrapped mouse-angle delta to the entity's starting heading."""
    delta = (current_angle - start_angle + pi) % (2.0 * pi) - pi
    return start_heading + delta


def _quantize_rotation_delta(delta, step=pi / 12.0):
    """Round a relative heading change to the nearest angular step."""
    return round(delta / step) * step


def _trailer_rotation_uses_lane_snap(event):
    """Match entity placement: ALT and SHIFT both bypass lane snapping."""
    return not event.shift and not event.alt


def _lane_center_offsets(road_obj, s):
    """Return drivable lane-center lateral offsets for a road station."""
    total_length = road_obj['geometry_total_length']
    lane_offset = helpers.calculate_lane_offset(
        s, road_obj['lane_offset_coefficients'], total_length)
    candidates = []
    for side in ('left', 'right'):
        widths_start = road_obj[f'lanes_{side}_widths_start']
        widths_end = road_obj[f'lanes_{side}_widths_end']
        widths = helpers._interpolate_lane_widths(
            widths_start, widths_end, s, total_length)
        lane_types = road_obj[f'lanes_{side}_types']
        accumulated_width = 0.0
        for index, width in enumerate(widths):
            if index < len(lane_types) and helpers._is_drivable_lane_type(
                    lane_types[index]):
                sign = 1.0 if side == 'left' else -1.0
                candidates.append((
                    side, index,
                    lane_offset + sign * (accumulated_width + width / 2.0)))
            accumulated_width += width
    return candidates


def _trailer_road_lane(road_obj, hit_point):
    """Load a road and identify which drivable lane the pointer hit."""
    if (not road_obj.get('dsc_type', '').startswith('road_')
            or road_obj.get('dsc_type') == 'road_object'):
        return None
    from .modal_road_object_base import load_geometry

    geometry = load_geometry(
        road_obj['dsc_type'], road_obj['geometry'],
        road_obj['lane_offset_coefficients'])
    if geometry is None:
        return None
    _ref_point, _heading, station, lateral = \
        geometry.get_closest_ref_line_x_y_heading_s_t(hit_point)
    candidates = _lane_center_offsets(road_obj, station)
    if not candidates:
        return None
    side, lane_index, _offset = min(
        candidates, key=lambda candidate: abs(candidate[2] - lateral))
    return geometry, side, lane_index


def _trailer_lane_sample(road_obj, geometry, station, side, lane_index):
    """Sample one consistent lane center along its complete road geometry."""
    candidates = _lane_center_offsets(road_obj, station)
    lane = next((candidate for candidate in candidates
                 if candidate[0] == side and candidate[1] == lane_index), None)
    if lane is None:
        return None
    local_point = geometry.sample_cross_section(
        station, [lane[2]], False)[0][0]
    _x, _y, tangent, _curvature = geometry.sample_plan_view(station)
    if side == 'left':
        tangent += pi
    tangent_vector = geometry.matrix_world.to_3x3() @ Vector((
        cos(tangent), sin(tangent), 0.0))
    tangent = atan2(tangent_vector.y, tangent_vector.x)
    return geometry.matrix_world @ Vector(local_point), tangent


def _trailer_road_circle_intersections(road_obj, geometry, side, lane_index,
                                       pivot, radius):
    """Find lane-center points exactly one coupler offset from the hitch."""
    total_length = geometry.total_length
    step = max(0.25, total_length / 2000.0)
    station_count = max(1, int(total_length / step))
    stations = [total_length * i / station_count
                for i in range(station_count + 1)]

    def sample(station):
        result = _trailer_lane_sample(
            road_obj, geometry, station, side, lane_index)
        if result is None:
            return None
        point, tangent = result
        return point, (point.to_2d() - pivot.to_2d()).length - radius, tangent

    intersections = []
    previous_station = stations[0]
    previous = sample(previous_station)
    for station in stations[1:]:
        current = sample(station)
        if previous is None or current is None:
            previous_station, previous = station, current
            continue
        if previous[1] == 0.0:
            intersections.append((previous_station, previous[0], previous[2]))
        if previous[1] * current[1] < 0.0:
            low, high = previous_station, station
            low_value = previous[1]
            for _ in range(24):
                middle = (low + high) * 0.5
                middle_sample = sample(middle)
                if middle_sample is None:
                    break
                if low_value * middle_sample[1] <= 0.0:
                    high = middle
                else:
                    low = middle
                    low_value = middle_sample[1]
            root = sample((low + high) * 0.5)
            if root is not None:
                intersections.append(((low + high) * 0.5, root[0], root[2]))
        previous_station, previous = station, current

    # Deduplicate roots that happen to land on a sample boundary.
    unique = []
    for station, point, tangent in intersections:
        if not unique or abs(station - unique[-1][0]) > 1e-3:
            unique.append((station, point, tangent))
    return unique


def _choose_trailer_road_solution(intersections, pivot, reference_origin):
    """Choose the forward-facing circle intersection nearest the initial pose."""
    solutions = []
    for _station, origin, lane_heading in intersections:
        heading = atan2(pivot.y - origin.y, pivot.x - origin.x)
        direction = Vector((pivot.x - origin.x,
                            pivot.y - origin.y)).normalized()
        lane_direction = Vector((cos(lane_heading), sin(lane_heading)))
        alignment = direction.dot(lane_direction)
        distance = (origin - reference_origin).length
        solutions.append((alignment, distance, origin, heading))
    forward_solutions = [item for item in solutions if item[0] > 0.0]
    pool = forward_solutions or solutions
    if not pool:
        return None
    _alignment, _distance, origin, heading = max(
        pool, key=lambda item: (item[0], -item[1]))
    return origin.copy(), heading


class DSC_OT_entity(DSC_OT_modal_two_point_base):
    bl_idname = 'dsc.entity'
    bl_label = 'Scenario entity'
    bl_description = 'Place a scenario entity object'
    bl_options = {'REGISTER', 'UNDO'}

    params = {}

    # Do not snap to other xodr or xosc objects in scene
    # TODO snap to road contact points, requires a lot of work
    snap_filter = 'surface'

    def create_object_model(self, context):
        '''
            Create a model object instance
        '''
        get_wheel_configs = getattr(self, 'get_wheel_configs', None)
        get_face_materials = getattr(self, 'get_face_materials', None)
        setup_entity_object = getattr(self, 'setup_entity_object', None)
        get_additional_meshes = getattr(self, 'get_additional_meshes', None)
        self.entity = entity(context, self.entity_type, self.entity_subtype,
            self.get_vertices_edges_faces, get_wheel_configs=get_wheel_configs,
            get_face_materials=get_face_materials,
            setup_entity_object=setup_entity_object,
            get_additional_meshes=get_additional_meshes)

    def create_object_3d(self, context):
        '''
            Create a 3d car object
        '''
        return self.entity.create_object_3d(context, self.params_input)

    def update_params_get_mesh(self, context, wireframe=True):
        '''
            Calculate and return the vertices, edges and faces to create an entity mesh.
        '''
        valid, mesh, matrix_world, materials = \
            self.entity.update_params_get_mesh(context, self.params_input, wireframe)
        if not valid:
            self.report({'WARNING'}, 'No valid entity geometry solution found!')
        return valid, mesh, matrix_world, materials

    def _start_trailer_rotation(self, context, event):
        self.rotation_pivot = self.selected_point.copy()
        self.rotation_start_heading = self.placement_heading
        self.rotation_normal = self.params_input['normal_start'].copy()
        pointer = helpers.mouse_to_xy_parallel_plane(
            context, event, self.rotation_pivot.z)
        direction = pointer - self.rotation_pivot
        self.rotation_start_pointer_angle = (
            atan2(direction.y, direction.x)
            if direction.to_2d().length > 0.0001 else None)
        self.rotation_reference_origin = self.placement_position.copy()
        self.rotation_road_solution_key = None
        self.rotation_road_solution = None
        context.scene.cursor.location = self.placement_position.copy()
        context.workspace.status_text_set(
            'MOUSEMOVE: rotate trailer around coupler, '
            'hold SHIFT: free rotation, hold ALT: free rotation in 15° steps, '
            'LEFTMOUSE: confirm, RIGHTMOUSE/ESCAPE: exit'
        )
        self.state = 'ROTATE_TRAILER'

    def _update_trailer_rotation(self, context, event):
        if _trailer_rotation_uses_lane_snap(event):
            params_snap = helpers.mouse_to_road_surface_params(
                context, event, (self.stencil,))
            if params_snap['hit_type'] == 'road_surface':
                road_obj = bpy.data.objects.get(params_snap['id_obj'])
                lane_info = (_trailer_road_lane(road_obj, params_snap['point'])
                             if road_obj is not None else None)
                if lane_info is None:
                    return
                geometry, side, lane_index = lane_info
                solution_key = (road_obj.name, side, lane_index)
                if solution_key != self.rotation_road_solution_key:
                    intersections = _trailer_road_circle_intersections(
                        road_obj, geometry, side, lane_index,
                        self.rotation_pivot,
                        abs(ENTITY_CONNECTION_POINTS[
                            self.entity_subtype]['x']))
                    solution = _choose_trailer_road_solution(
                        intersections, self.rotation_pivot,
                        self.rotation_reference_origin)
                    if solution is None:
                        return
                    self.rotation_road_solution_key = solution_key
                    self.rotation_road_solution = solution
                origin, heading = self.rotation_road_solution
                if event.alt:
                    delta = heading - self.rotation_start_heading
                    heading = (self.rotation_start_heading
                               + _quantize_rotation_delta(delta))
                    origin = get_entity_position_from_connection_anchor(
                        self.rotation_pivot, heading, self.rotation_normal,
                        self.entity_subtype)
                self._apply_trailer_rotation_pose(
                    context, origin, heading)
                return

        pointer = helpers.mouse_to_xy_parallel_plane(
            context, event, self.rotation_pivot.z)
        direction = pointer - self.rotation_pivot
        if direction.to_2d().length <= 0.0001:
            return
        pointer_angle = atan2(direction.y, direction.x)
        if self.rotation_start_pointer_angle is None:
            self.rotation_start_pointer_angle = pointer_angle
            return
        heading = _heading_after_pointer_rotation(
            self.rotation_start_heading, self.rotation_start_pointer_angle,
            pointer_angle)
        if event.alt:
            heading = (self.rotation_start_heading
                       + _quantize_rotation_delta(
                           heading - self.rotation_start_heading))
        origin = get_entity_position_from_connection_anchor(
            self.rotation_pivot, heading, self.rotation_normal,
            self.entity_subtype)
        self._apply_trailer_rotation_pose(context, origin, heading)

    def _apply_trailer_rotation_pose(self, context, origin, heading):
        self.placement_heading = heading
        self.placement_position = origin.copy()
        self.selected_point = self.rotation_pivot.copy()

        vec_dir = Vector((1.0, 0.0, 0.0))
        vec_dir.rotate(Matrix.Rotation(heading, 4, 'Z'))
        self.params_input['point_start'] = self.placement_position.copy()
        self.params_input['point_end'] = self.placement_position + vec_dir
        self.params_input['point_end'].z = self.placement_position.z
        self.params_input['heading_override'] = self.placement_heading
        self.params_input['normal_start'] = self.rotation_normal.copy()
        # Keep the 3D cursor attached to the trailer origin; the pointer's
        # road/lane snap target only determines the rotation direction.
        context.scene.cursor.location = self.placement_position.copy()
        self.update_stencil(context, update_start=False)

    def modal(self, context, event):
        # Single-click placement flow matching the move operator UX.
        if self.state == 'INIT':
            context.workspace.status_text_set(
                'LEFTMOUSE: place entity, '
                'lane center/orientation and hitch-coupler snap, '
                'hold SHIFT: disable lane snapping, '
                'hold ALT: heading-only mode, '
                'ALT+MIDDLEMOUSE: move view center, '
                'RIGHTMOUSE/ESCAPE: exit'
            )
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.reset_params_input()
            self.reset_params_snap()
            self.snapped_to_object = False
            self.connection_target = None
            self.selected_elevation = 0
            self.placement_position = helpers.mouse_to_xy_parallel_plane(
                context, event, 0)
            self.placement_heading = 0
            # Initialise stencil with a valid heading so it renders immediately.
            vec_heading = Vector((1.0, 0.0, 0.0))
            self.params_input['point_start'] = self.placement_position.copy()
            self.params_input['point_end'] = self.placement_position + vec_heading
            self.params_input['heading_override'] = self.placement_heading
            self.params_input['normal_start'] = Vector((0.0, 0.0, 1.0))
            self.create_stencil(context)
            self.update_stencil(context, update_start=False)
            self.state = 'PLACE'

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L',
                          'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if self.state == 'ROTATE_TRAILER' and event.type == 'MOUSEMOVE':
            self._update_trailer_rotation(context, event)

        elif event.type == 'MOUSEMOVE':
            # Raycast to road surface
            params_snap = helpers.mouse_to_road_surface_params(
                context, event, (self.stencil,))
            if params_snap['hit_type'] is not None:
                self.params_snap = params_snap
                self.snapped_to_object = True
                self.selected_point = params_snap['point']
            else:
                self.reset_params_snap()
                self.snapped_to_object = False
                # In ALT heading mode project to the entity's height (like
                # the move operator) so heading direction stays sensible.
                z = (self.placement_position.z if event.alt
                     else self.selected_elevation)
                self.selected_point = helpers.mouse_to_xy_parallel_plane(
                    context, event, z)

            lane_heading = None
            self.connection_target = None

            # Lane-center snapping is enabled by default; SHIFT and ALT disable it.
            if (not event.shift and not event.alt
                    and self.params_snap['hit_type'] == 'road_surface'):
                road_obj = bpy.data.objects.get(self.params_snap['id_obj'])
                if road_obj is not None:
                    lc_point, lh = \
                        helpers.get_lane_center_from_road_surface_hit(
                            road_obj, self.selected_point)
                    if lc_point is not None:
                        self.selected_point = lc_point
                        lane_heading = lh

            if not event.alt:
                # Normal mode: entity follows mouse
                self.placement_position = self.selected_point.copy()
                self.selected_elevation = self.selected_point.z
                if lane_heading is not None:
                    self.placement_heading = lane_heading
            else:
                # ALT heading-only mode: position stays, heading follows
                # mouse – exactly like the move operator.
                if lane_heading is not None:
                    self.placement_heading = lane_heading
                else:
                    vec = self.selected_point - self.placement_position
                    if vec.to_2d().length > 0.0001:
                        self.placement_heading = atan2(vec.y, vec.x)

            # Compare the candidate vehicle's actual hitch/coupler position
            # with compatible anchors; the pointer can be elsewhere on the
            # body. If close, rigidly move the candidate anchor onto the target.
            candidate_normal = (
                self.params_snap['normal'].copy()
                if self.snapped_to_object
                else Vector((0.0, 0.0, 1.0)))
            connection_snap = None
            if not event.shift and not event.alt:
                connection_snap = get_connection_snap(
                    context, self.placement_position, self.placement_heading,
                    candidate_normal, self.entity_subtype)

            if connection_snap is not None:
                target_obj, anchor_world = connection_snap
                self.connection_target = target_obj
                target_normal = (target_obj.matrix_world.to_3x3()
                                 @ Vector((0.0, 0.0, 1.0))).normalized()
                self.placement_position = get_entity_position_from_connection_anchor(
                    anchor_world, self.placement_heading, target_normal,
                    self.entity_subtype)
                self.selected_point = anchor_world.copy()
                self.selected_elevation = self.placement_position.z
                candidate_normal = target_normal
            else:
                candidate_normal = (
                    self.params_snap['normal'].copy()
                    if self.snapped_to_object
                    else Vector((0.0, 0.0, 1.0)))

            context.scene.cursor.location = self.selected_point.copy()

            # Update params and refresh stencil
            vec_dir = Vector((1.0, 0.0, 0.0))
            vec_dir.rotate(Matrix.Rotation(self.placement_heading, 4, 'Z'))
            self.params_input['point_start'] = self.placement_position.copy()
            self.params_input['point_end'] = self.placement_position + vec_dir
            self.params_input['point_end'].z = self.placement_position.z
            self.params_input['heading_override'] = self.placement_heading
            self.params_input['normal_start'] = candidate_normal

            self.update_stencil(context, update_start=False)

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.placement_position is not None:
                if (self.state == 'PLACE'
                        and self.entity_subtype == 'semiTrailer'
                        and self.connection_target is not None):
                    self._start_trailer_rotation(context, event)
                    return {'RUNNING_MODAL'}

                obj = self.create_object_3d(context)
                if obj is not None:
                    record_entity_connection(obj, self.connection_target)
                    self.remove_stencil()
                    self.state = 'INIT'
            return {'RUNNING_MODAL'}

        elif event.type == 'RIGHTMOUSE':
            if event.value == 'RELEASE':
                self.clean_up(context)
                return {'FINISHED'}

        elif event.type == 'ESC':
            if event.value == 'RELEASE':
                self.clean_up(context)
                return {'FINISHED'}

        elif event.type == 'WHEELUPMOUSE':
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type == 'WHEELDOWNMOUSE':
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1,
                                use_cursor_init=True)
        elif event.type == 'MIDDLEMOUSE':
            if event.alt and event.value == 'RELEASE':
                bpy.ops.view3d.view_center_cursor()

        return {'RUNNING_MODAL'}
