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

from mathutils import Matrix, Vector
from math import atan2

from . import helpers
from .entity_base import (
    _choose_trailer_road_solution,
    _heading_after_pointer_rotation,
    _quantize_rotation_delta,
    _trailer_road_circle_intersections,
    _trailer_road_lane,
    _trailer_rotation_uses_lane_snap,
)
from .entity_connections import (
    ENTITY_CONNECTION_POINTS,
    clear_entity_connection,
    get_entity_position_from_connection_anchor,
    get_connection_snap,
    record_entity_connection,
)


def _fallback_move_point(context, event, selected_elevation):
    """Project normal off-road movement at the latest snapped elevation."""
    return helpers.mouse_to_xy_parallel_plane(context, event, selected_elevation)


def _heading_only_target(context, event, current_location, current_heading):
    """Get an off-road heading target without road or lane snapping."""
    point = helpers.mouse_to_xy_parallel_plane(
        context, event, current_location.z)
    direction = point - current_location
    heading = (atan2(direction.y, direction.x)
               if direction.to_2d().length > 0.0001
               else current_heading)
    return point, heading


def _entity_transform_matrix(location, heading, normal, scale):
    """Match entity placement's translation, surface alignment, and heading."""
    normal_rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(
        normal.normalized())
    heading_rotation = Matrix.Rotation(heading, 4, 'Z').to_3x3()
    rotation = normal_rotation.to_matrix() @ heading_rotation
    return Matrix.LocRotScale(location, rotation.to_quaternion(), scale)


def _set_cursor_to_object_origin(context, obj):
    """Keep Blender's 3D cursor on the moved scenario object's world origin."""
    context.scene.cursor.location = obj.matrix_world.translation.copy()


def _move_entity_origin(initial_location, anchor_point, target_point):
    """Move the entity root by the pointer delta from its initial origin."""
    return initial_location + target_point - anchor_point


def _should_rotate_connected_trailer(obj_type, obj, connection_target):
    """Only a semitrailer snapped to a heavy truck enters pivot rotation."""
    return (
        obj_type == 'entity'
        and obj is not None
        and obj.get('entity_subtype') == 'semiTrailer'
        and connection_target is not None
        and connection_target.get('entity_subtype') == 'heavyTruck'
    )


class DSC_OT_scenario_entity_move(bpy.types.Operator):
    bl_idname = 'dsc.scenario_entity_move'
    bl_label = 'Move scenario entity or trajectory'
    bl_description = 'Move an existing scenario entity or trajectory with road and lane snapping'
    bl_options = {'REGISTER', 'UNDO'}

    selected_obj = None
    selected_obj_type = None
    hovered_obj = None
    state = 'INIT'

    initial_location = Vector((0.0, 0.0, 0.0))
    initial_rotation_euler = None
    initial_matrix = None
    anchor_point = Vector((0.0, 0.0, 0.0))

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def _raycast_to_movable_target(self, context, event):
        dsc_hit, _raycast_point, _raycast_normal, obj = \
            helpers.raycast_mouse_to_dsc_object(context, event)
        if not dsc_hit:
            return None
        if obj.get('dsc_category') != 'OpenSCENARIO':
            return None
        # Wheels and coupling hardware are child objects; move their entity
        # root just as placement creates and exports the entity root.
        if obj.parent is not None and obj.parent.get('dsc_type') == 'entity':
            obj = obj.parent
        if obj.get('dsc_type') not in {'entity', 'trajectory'}:
            return None
        return obj

    def _raycast_to_road_surface(self, context, event):
        exclude_objects = (
            (self.selected_obj,)
            if self.state in {'MOVE', 'ROTATE_TRAILER'}
            and self.selected_obj is not None else ())
        dsc_hit, raycast_point, raycast_normal, obj = \
            helpers.raycast_mouse_to_dsc_object_excluding(
                context, event, exclude_objects)
        if not dsc_hit:
            return None, None, None
        if obj.get('dsc_category') != 'OpenDRIVE':
            return None, None, None
        return raycast_point, raycast_normal, obj

    def _apply_entity_heading(self, heading):
        self.selected_obj.rotation_mode = 'XYZ'
        self.selected_obj.rotation_euler = (
            self.initial_rotation_euler.x,
            self.initial_rotation_euler.y,
            heading,
        )

    def _set_entity_transform(self, location, heading, normal=None):
        """Apply placement-equivalent location, heading, and road normal."""
        if normal is None:
            normal = self.initial_matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))
        self.selected_obj.matrix_world = _entity_transform_matrix(
            location, heading, normal, self.initial_matrix.to_scale())

    def _update_transform(self, context, event):
        if event.alt:
            # ALT is a pure in-place heading adjustment: do not raycast roads,
            # find lane centers, or inherit a surface normal from the pointer.
            current_location, current_heading = \
                helpers.get_object_world_position_heading(self.selected_obj)
            target_point, heading_target = _heading_only_target(
                context, event, current_location, current_heading)
            if self.selected_obj_type == 'entity':
                current_normal = (self.selected_obj.matrix_world.to_3x3()
                                  @ Vector((0.0, 0.0, 1.0))).normalized()
                self._set_entity_transform(
                    current_location, heading_target, current_normal)
            else:
                self._apply_entity_heading(heading_target)
            context.scene.cursor.location = target_point.copy()
            self.transform_changed = True
            self.pending_connection_target = None
            self.pending_connection_anchor = None
            return

        point, normal, road_obj = self._raycast_to_road_surface(context, event)

        # Match entity placement: when the pointer is not over a road, project
        # onto a horizontal plane and keep the elevation from the drag anchor.
        # This is needed in normal mode too so vehicles can leave the road.
        if point is None:
            point = _fallback_move_point(
                context, event, self.selected_elevation)
            normal = Vector((0.0, 0.0, 1.0))
            road_obj = None

        target_point = point.copy()
        heading_lane = None
        if not event.shift and not event.alt and road_obj is not None:
            lane_center_point, lane_heading = helpers.get_lane_center_from_road_surface_hit(road_obj, point)
            if lane_center_point is not None:
                target_point = lane_center_point
                heading_lane = lane_heading

        if not event.alt:
            # Like placement, retain the latest road/lane elevation when the
            # cursor subsequently leaves the road surface.
            self.selected_elevation = target_point.z

        # In move mode, just as in placement, the 3D cursor marks the current
        # pointer target. The entity origin follows that target in normal mode.
        context.scene.cursor.location = target_point.copy()

        target_location = _move_entity_origin(
            self.initial_location, self.anchor_point, target_point)
        target_heading = helpers.get_object_world_position_heading(
            self.selected_obj)[1]
        if heading_lane is not None:
            target_heading = heading_lane

        connection_snap = None
        if self.selected_obj_type == 'entity':
            subtype = self.selected_obj.get('entity_subtype')
            if subtype in ENTITY_CONNECTION_POINTS:
                connection_snap = get_connection_snap(
                    context, target_location, target_heading, normal, subtype,
                    moving_obj=self.selected_obj)
        if connection_snap is not None:
            target_obj, target_anchor = connection_snap
            target_normal = (target_obj.matrix_world.to_3x3()
                             @ Vector((0.0, 0.0, 1.0))).normalized()
            local_anchor = ENTITY_CONNECTION_POINTS[
                self.selected_obj['entity_subtype']]
            anchor_offset = Vector((local_anchor['x'], 0.0,
                                    local_anchor['z']))
            normal_rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(
                target_normal).to_matrix().to_4x4()
            anchor_offset = (normal_rotation
                             @ Matrix.Rotation(target_heading, 4, 'Z')
                             @ anchor_offset.to_4d()).to_3d()
            target_location = target_anchor - anchor_offset
            normal = target_normal
            self.pending_connection_target = target_obj
            self.pending_connection_anchor = target_anchor.copy()
        else:
            self.pending_connection_target = None
            self.pending_connection_anchor = None

        if self.selected_obj_type == 'entity':
            self._set_entity_transform(target_location, target_heading, normal)
        else:
            self.selected_obj.location = target_location

        if self.selected_obj_type == 'entity':
            helpers.clear_legacy_entity_transform_properties(self.selected_obj)
        self.transform_changed = True

    def _start_trailer_rotation(self, context, event):
        self.rotation_pivot = self.pending_connection_anchor.copy()
        self.rotation_start_heading = helpers.get_object_world_position_heading(
            self.selected_obj)[1]
        self.rotation_normal = (self.pending_connection_target.matrix_world
                                .to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
        self.rotation_reference_origin = \
            self.selected_obj.matrix_world.translation.copy()
        self.rotation_road_solution_key = None
        self.rotation_road_solution = None
        pointer = helpers.mouse_to_xy_parallel_plane(
            context, event, self.rotation_pivot.z)
        direction = pointer - self.rotation_pivot
        self.rotation_start_pointer_angle = (
            atan2(direction.y, direction.x)
            if direction.to_2d().length > 0.0001 else None)
        context.scene.cursor.location = self.rotation_reference_origin.copy()
        context.workspace.status_text_set(
            'MOUSEMOVE: rotate trailer around coupler, '
            'hold SHIFT: free rotation, hold ALT: free rotation in 15° steps, '
            'LEFTMOUSE: confirm, RIGHTMOUSE/ESCAPE: cancel move'
        )
        self.state = 'ROTATE_TRAILER'

    def _update_trailer_rotation(self, context, event):
        if _trailer_rotation_uses_lane_snap(event):
            params_snap = helpers.mouse_to_road_surface_params(
                context, event, (self.selected_obj,))
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
                        abs(ENTITY_CONNECTION_POINTS['semiTrailer']['x']))
                    solution = _choose_trailer_road_solution(
                        intersections, self.rotation_pivot,
                        self.rotation_reference_origin)
                    if solution is None:
                        return
                    self.rotation_road_solution_key = solution_key
                    self.rotation_road_solution = solution
                origin, heading = self.rotation_road_solution
                self._set_entity_transform(
                    origin, heading, self.rotation_normal)
                context.scene.cursor.location = origin.copy()
                self.transform_changed = True
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
            self.rotation_start_heading,
            self.rotation_start_pointer_angle, pointer_angle)
        if event.alt:
            heading = (self.rotation_start_heading
                       + _quantize_rotation_delta(
                           heading - self.rotation_start_heading))
        origin = get_entity_position_from_connection_anchor(
            self.rotation_pivot, heading, self.rotation_normal, 'semiTrailer')
        self._set_entity_transform(origin, heading, self.rotation_normal)
        context.scene.cursor.location = origin.copy()
        self.transform_changed = True

    def _commit_connection(self):
        if (self.selected_obj_type != 'entity'
                or not getattr(self, 'transform_changed', False)):
            return
        clear_entity_connection(self.selected_obj)
        if self.pending_connection_target is not None:
            record_entity_connection(
                self.selected_obj, self.pending_connection_target)

    def _start_move(self, context, event):
        self.selected_obj = self.hovered_obj
        self.selected_obj_type = self.selected_obj['dsc_type']
        self.initial_location = self.selected_obj.location.copy()
        self.initial_rotation_euler = self.selected_obj.rotation_euler.copy()
        self.initial_matrix = self.selected_obj.matrix_world.copy()
        self.pending_connection_target = None
        self.pending_connection_anchor = None
        self.transform_changed = False

        # Match the placement operator's origin-at-pointer behavior: the
        # selected entity starts at the cursor, then its root follows the
        # cursor directly rather than preserving an arbitrary body click offset.
        self.anchor_point = self.initial_location.copy()
        self.selected_elevation = self.initial_location.z
        _set_cursor_to_object_origin(context, self.selected_obj)
        self.state = 'MOVE'
        helpers.select_activate_object(context, self.selected_obj)

    def modal(self, context, event):
        if self.state == 'INIT':
            context.workspace.status_text_set(
                'LEFTMOUSE: select entity or trajectory and move repeatedly, '
                'lane center/orientation and hitch-coupler snap, '
                'hold SHIFT: disable lane snapping, '
                'hold ALT: heading-only mode / trailer 15° rotation steps, '
                'RIGHTMOUSE: cancel current move / exit from selection, ESC: exit, '
                'ALT+MIDDLEMOUSE: move view center'
            )
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.state = 'SELECT_TARGET'

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            if self.state == 'SELECT_TARGET':
                self.hovered_obj = self._raycast_to_movable_target(context, event)
            elif self.state == 'MOVE':
                self._update_transform(context, event)
            elif self.state == 'ROTATE_TRAILER':
                self._update_trailer_rotation(context, event)

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.state == 'SELECT_TARGET':
                if self.hovered_obj is None:
                    self.report({'INFO'}, 'Select an OpenSCENARIO entity or trajectory.')
                    return {'RUNNING_MODAL'}
                self._start_move(context, event)
                return {'RUNNING_MODAL'}
            if self.state == 'MOVE':
                if _should_rotate_connected_trailer(
                    self.selected_obj_type, self.selected_obj,
                    self.pending_connection_target):
                    self._start_trailer_rotation(context, event)
                    return {'RUNNING_MODAL'}

                self._commit_connection()
                self.selected_obj = None
                self.selected_obj_type = None
                self.initial_rotation_euler = None
                self.initial_matrix = None
                bpy.ops.object.select_all(action='DESELECT')
                self.state = 'SELECT_TARGET'
                return {'RUNNING_MODAL'}
            if self.state == 'ROTATE_TRAILER':
                # Keep operator active for multi-step placement.
                self._commit_connection()
                self.selected_obj = None
                self.selected_obj_type = None
                self.initial_rotation_euler = None
                self.initial_matrix = None
                bpy.ops.object.select_all(action='DESELECT')
                self.state = 'SELECT_TARGET'
                return {'RUNNING_MODAL'}

        elif event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
            if (self.state in {'MOVE', 'ROTATE_TRAILER'}
                    and self.selected_obj is not None
                    and self.initial_matrix is not None):
                self.selected_obj.matrix_world = self.initial_matrix.copy()
                self.selected_obj = None
                self.selected_obj_type = None
                self.initial_rotation_euler = None
                self.initial_matrix = None
                self.pending_connection_target = None
                self.pending_connection_anchor = None
                bpy.ops.object.select_all(action='DESELECT')
                self.state = 'SELECT_TARGET'
                return {'RUNNING_MODAL'}
            self.clean_up(context)
            return {'FINISHED'}

        elif event.type == 'ESC':
            if (self.state in {'MOVE', 'ROTATE_TRAILER'}
                    and self.selected_obj is not None
                    and self.initial_matrix is not None):
                self.selected_obj.matrix_world = self.initial_matrix.copy()
            self.clean_up(context)
            return {'FINISHED'}

        elif event.type in {'WHEELUPMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type in {'WHEELDOWNMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        elif event.type in {'MIDDLEMOUSE'}:
            if event.alt and event.value == 'RELEASE':
                bpy.ops.view3d.view_center_cursor()

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        del event
        self.state = 'INIT'
        self.selected_obj = None
        self.hovered_obj = None
        self.selected_obj_type = None
        self.initial_rotation_euler = None
        self.initial_matrix = None
        self.pending_connection_target = None
        self.pending_connection_anchor = None
        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        context.workspace.status_text_set(None)
        bpy.context.window.cursor_modal_restore()
        self.state = 'INIT'
