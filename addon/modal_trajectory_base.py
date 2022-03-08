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

from . import helpers


class DSC_OT_trajectory_base(bpy.types.Operator):
    bl_idname = 'dsc.trajectory_base'
    bl_label = 'DSC trajectory operator'
    bl_options = {'REGISTER', 'UNDO'}

    snap_filter = 'OpenSCENARIO'
    trajectory = None
    trajectory_points = []
    trajectory_owner_name = None
    point_start = None

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def make_trajectory_final(self, context):
        id_obj = helpers.get_new_id_openscenario(context)
        obj_name = 'trajectory' + '_' + str(id_obj)
        self.trajectory.name = obj_name
        self.set_xosc_properties()

    def set_xosc_properties(self):
        '''
            Set the custom OpenSCENARIO properties.
        '''
        raise NotImplementedError()

    def create_trajectory_temp(self, context, point_start):
        '''
            Create Blender object for the trajectory.
        '''
        raise NotImplementedError()

    def remove_trajectory_temp(self, context):
        '''
            Remove the trajectory Blender object.
        '''
        if self.trajectory is not None:
            bpy.data.objects.remove(self.trajectory, do_unlink=True)

    def update_trajectory(self, context):
        '''
            Update trajectory based on available points.
        '''
        raise NotImplementedError()

    def modal(self, context, event):
        # Display help text
        if self.state == 'INIT':
            context.workspace.status_text_set('Select object then place points. '
                'Press RIGHTMOUSE to go back. Press RETURN to finish, ESCAPE to exit.')
            # Set custom cursor
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.state = 'SELECT_OBJECT'
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update on move
        if event.type == 'MOUSEMOVE':
            # Snap to existing objects if any, otherwise xy plane
            if self.state == 'SELECT_OBJECT':
                # Start of trajectory should be an OpenSCENARIO object
                self.snapped, self.params_snap = helpers.mouse_to_object_params(
                    context, event, filter=self.snap_filter)
            else:
                # For remaining trajectory points use any surface point
                self.snapped, self.params_snap = helpers.mouse_to_object_params(
                    context, event, filter='surface')
            if self.snapped:
                self.selected_point = self.params_snap['point']
            else:
                self.selected_point = helpers.mouse_to_xy_parallel_plane(context, event, 0)
            # Move point up about height of rear axle
            self.selected_point.z += 0.3
            context.scene.cursor.location = self.selected_point
            # CTRL activates grid snapping if not snapped to object
            if event.ctrl and not self.snapped:
                bpy.ops.view3d.snap_cursor_to_grid()
                self.selected_point = context.scene.cursor.location
        # Select object and trajectory points
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_OBJECT':
                    if self.snapped:
                        self.point_start = self.selected_point
                        self.trajectory_points.append(self.selected_point.copy())
                        self.create_trajectory_temp(context)
                        self.trajectory_owner_name = self.params_snap['id_obj']
                        helpers.select_activate_object(context, self.trajectory)
                        self.state = 'SELECT_POINT'
                        return {'RUNNING_MODAL'}
                    else:
                        self.report({'INFO'}, "Select dynamic OpenSCENARIO object.")
                if self.state == 'SELECT_POINT':
                    self.trajectory_points.append(self.selected_point.copy())
                    self.update_trajectory(context)
                    return {'RUNNING_MODAL'}
        elif event.type in {'RET'}:
            if self.state == 'SELECT_POINT':
                self.make_trajectory_final(context)
                self.clean_up(context)
                return {'FINISHED'}
        # Cancel step by step
        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}:
            # Back to beginning
            if self.state == 'SELECT_POINT':
                if len(self.trajectory_points) > 0:
                    self.trajectory_points.pop()
                if len(self.trajectory_points) == 0:
                    self.remove_trajectory_temp(context)
                    self.state = 'SELECT_OBJECT'
                else:
                    self.update_trajectory(context)
                return {'RUNNING_MODAL'}
            # Exit
            if self.state == 'SELECT_OBJECT':
                self.clean_up(context)
                return {'FINISHED'}
        # Elevation adjustment from current point of view
        elif event.type == 'E':
            if event.value == 'PRESS':
                if self.adjust_elevation == 'DISABLED':
                    self.adjust_elevation = 'GENERIC'
            elif event.value == 'RELEASE':
                self.adjust_elevation = 'DISABLED'
        # Toggle side view for elevation adjustment
        elif event.type == 'S':
            if event.value == 'PRESS':
                if self.adjust_elevation == 'DISABLED':
                    # Remember previous view
                    self.view_memory.remember_view(context)
                    # Look at current object from the side, perpendicular to z-axis
                    view3d = context.space_data
                    bpy.ops.view3d.view_axis(type='LEFT', align_active=False, relative=False)
                    self.adjust_elevation = 'SIDEVIEW'
            elif event.value == 'RELEASE':
                if self.adjust_elevation == 'SIDEVIEW':
                    # Restore previous view
                    self.view_memory.restore_view(context)
                self.adjust_elevation = 'DISABLED'
        # Exit immediately
        elif event.type in {'ESC'}:
            self.remove_trajectory_temp(context)
            self.clean_up(context)
            return {'FINISHED'}
        # Zoom
        elif event.type in {'WHEELUPMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type in {'WHEELDOWNMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        elif event.type in {'MIDDLEMOUSE'}:
            if event.alt:
                bpy.ops.view3d.view_center_cursor()

        # Catch everything else arriving here
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # For operator state machine
        # possible states: {'INIT','SELECT_OBJECT', 'SELECT_POINT'}
        self.state = 'INIT'
        self.trajectory_points.clear()
        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        # Remove header text with 'None'
        context.workspace.status_text_set(None)
        # Set custom cursor
        bpy.context.window.cursor_modal_restore()
        # Make sure to exit edit mode
        if bpy.context.active_object:
            if bpy.context.active_object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
        self.state = 'INIT'
