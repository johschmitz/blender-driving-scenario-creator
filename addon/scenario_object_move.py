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
from math import atan2

from . import helpers


class DSC_OT_scenario_object_move(bpy.types.Operator):
    bl_idname = 'dsc.scenario_object_move'
    bl_label = 'Move scenario object'
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

    def _raycast_to_movable_object(self, context, event):
        dsc_hit, raycast_point, raycast_normal, obj = helpers.raycast_mouse_to_dsc_object(context, event)
        del raycast_point, raycast_normal
        if not dsc_hit:
            return None
        if obj.get('dsc_category') != 'OpenSCENARIO':
            return None
        if obj.get('dsc_type') not in {'entity', 'trajectory'}:
            return None
        return obj

    def _raycast_to_road_surface(self, context, event):
        restore_visibility = None
        if self.state == 'MOVE' and self.selected_obj is not None:
            restore_visibility = self.selected_obj.hide_get()
            self.selected_obj.hide_set(True)
        dsc_hit, raycast_point, raycast_normal, obj = helpers.raycast_mouse_to_dsc_object(context, event)
        if restore_visibility is not None:
            self.selected_obj.hide_set(restore_visibility)
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

    def _update_object_transform(self, context, event):
        point, normal, road_obj = self._raycast_to_road_surface(context, event)
        del normal

        # ALT heading mode should also work away from road surfaces.
        if point is None and event.alt and self.selected_obj_type == 'entity':
            point = helpers.mouse_to_xy_parallel_plane(context, event, self.selected_obj.location.z)
            road_obj = None
        if point is None:
            return

        target_point = point.copy()
        heading_lane = None
        if event.shift and road_obj is not None:
            lane_center_point, lane_heading = helpers.get_lane_center_from_road_surface_hit(road_obj, point)
            if lane_center_point is not None:
                target_point = lane_center_point
                heading_lane = lane_heading

        context.scene.cursor.location = target_point

        if not event.alt:
            delta = target_point - self.anchor_point
            self.selected_obj.location = self.initial_location + delta

        if event.alt:
            if heading_lane is not None:
                heading_target = heading_lane
            else:
                vec_to_target = target_point - self.initial_location
                if vec_to_target.to_2d().length > 0.0001:
                    heading_target = atan2(vec_to_target.y, vec_to_target.x)
                else:
                    heading_target = self.initial_rotation_euler.z
            self._apply_entity_heading(heading_target)
        elif self.selected_obj_type == 'entity':
            if heading_lane is not None:
                self._apply_entity_heading(heading_lane)

        if self.selected_obj_type == 'entity':
            helpers.clear_legacy_entity_transform_properties(self.selected_obj)

    def _start_move(self, context, event):
        self.selected_obj = self.hovered_obj
        self.selected_obj_type = self.selected_obj['dsc_type']
        self.initial_location = self.selected_obj.location.copy()
        self.initial_rotation_euler = self.selected_obj.rotation_euler.copy()
        self.initial_matrix = self.selected_obj.matrix_world.copy()

        point, normal, road_obj = self._raycast_to_road_surface(context, event)
        del normal, road_obj
        if point is None:
            self.anchor_point = self.initial_location.copy()
        else:
            self.anchor_point = point.copy()
        self.state = 'MOVE'
        helpers.select_activate_object(context, self.selected_obj)

    def modal(self, context, event):
        if self.state == 'INIT':
            context.workspace.status_text_set(
                'LEFTMOUSE: select object and place repeatedly, hold SHIFT: lane-center snap, '
                'hold ALT: heading-only mode, '
                'RIGHTMOUSE: cancel current move / exit from selection, ESC: exit, '
                'ALT+MIDDLEMOUSE: move view center'
            )
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.state = 'SELECT_OBJECT'

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            if self.state == 'SELECT_OBJECT':
                self.hovered_obj = self._raycast_to_movable_object(context, event)
            elif self.state == 'MOVE':
                self._update_object_transform(context, event)

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.state == 'SELECT_OBJECT':
                if self.hovered_obj is None:
                    self.report({'INFO'}, 'Select an OpenSCENARIO entity or trajectory.')
                    return {'RUNNING_MODAL'}
                self._start_move(context, event)
                return {'RUNNING_MODAL'}
            if self.state == 'MOVE':
                # Keep operator active for multi-object/multi-step placement.
                self.selected_obj = None
                self.selected_obj_type = None
                self.initial_rotation_euler = None
                self.initial_matrix = None
                bpy.ops.object.select_all(action='DESELECT')
                self.state = 'SELECT_OBJECT'
                return {'RUNNING_MODAL'}

        elif event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
            if self.state == 'MOVE' and self.selected_obj is not None and self.initial_matrix is not None:
                self.selected_obj.matrix_world = self.initial_matrix.copy()
                self.selected_obj = None
                self.selected_obj_type = None
                self.initial_rotation_euler = None
                self.initial_matrix = None
                bpy.ops.object.select_all(action='DESELECT')
                self.state = 'SELECT_OBJECT'
                return {'RUNNING_MODAL'}
            self.clean_up(context)
            return {'FINISHED'}

        elif event.type == 'ESC':
            if self.state == 'MOVE' and self.selected_obj is not None and self.initial_matrix is not None:
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
        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        context.workspace.status_text_set(None)
        bpy.context.window.cursor_modal_restore()
        self.state = 'INIT'
