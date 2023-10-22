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

from . import helpers
from . junction import junction


class DSC_OT_junction_generic(bpy.types.Operator):
    bl_idname = 'dsc.junction_generic'
    bl_label = 'Generic junction'
    bl_description = 'Create a generic junction'
    bl_options = {'REGISTER', 'UNDO'}

    snap_filter = 'OpenDRIVE'

    params_snap = {}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        # Display help text
        if self.state == 'INIT':
            context.workspace.status_text_set(
                'LEFTMOUSE: select road ends of incoming roads, '
                'RIGHTMOUSE: go back one step, '
                'ALT+MIDDLEMOUSE: move view center, '
                'SPACE/RETURN: finish, '
                'ESCAPE: cancel and exit.'
            )
            # Set custom cursor
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.reset_state(context)
            self.state = 'SELECT_INCOMING'
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update on move
        if event.type == 'MOUSEMOVE':
            # Snap to existing objects if any, otherwise xy plane
            self.params_snap = helpers.mouse_to_road_joint_params(
                context, event, road_type='road')
            if self.params_snap['hit_type'] != None:
                context.scene.cursor.location = self.params_snap['point']
            else:
                selected_point_new = helpers.mouse_to_xy_parallel_plane(context, event, 0.0)
                context.scene.cursor.location = selected_point_new
        # Select start and end
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_INCOMING':
                    if self.params_snap['hit_type'] != None:
                        contact_point_vec = self.params_snap['point'].copy()
                        # Calculate width of junction joints based on road direction
                        if self.params_snap['point_type'].startswith('cp_end'):
                            joint_widths_left = self.params_snap['lane_widths_left']
                            joint_widths_right = self.params_snap['lane_widths_right']
                            joint_lane_types_left = self.params_snap['lane_types_left']
                            joint_lane_types_right = self.params_snap['lane_types_right']
                        else:
                            # Switch direction if road points away from junction joint
                            joint_widths_left = self.params_snap['lane_widths_right']
                            joint_widths_right = self.params_snap['lane_widths_left']
                            joint_lane_types_left = self.params_snap['lane_types_right']
                            joint_lane_types_right = self.params_snap['lane_types_left']
                        joint_added = self.junction.add_joint_incoming(self.params_snap['id_obj'],
                            self.params_snap['point_type'], contact_point_vec,
                            self.params_snap['heading'], self.params_snap['curvature'], self.params_snap['slope'],
                            joint_widths_left, joint_widths_right, joint_lane_types_left, joint_lane_types_right)
                        if joint_added:
                            self.junction.update_stencil()
                        else:
                            self.report({'WARNING'}, 'Road with ID ' + str(self.params_snap['id_obj']) + \
                                ' already connected to this junction')
                    return {'RUNNING_MODAL'}
        elif event.type in {'RET'} or event.type in {'SPACE'}:
            if self.state == 'SELECT_INCOMING':
                # Create the final object
                self.junction.create_object_3d()
                self.clean_up(context)
                return {'FINISHED'}
        # Cancel step by step
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_INCOMING':
                    # One step back
                    if self.junction.has_joints():
                        self.junction.remove_last_joint()
                        self.junction.update_stencil()
                        return {'RUNNING_MODAL'}
                    else:
                        # Exit
                        self.clean_up(context)
                        self.state = 'INIT'
                        return {'FINISHED'}
        # Exit immediately
        elif event.type == 'ESC':
            if event.value == 'RELEASE':
                self.clean_up(context)
                return {'FINISHED'}
        # Zoom
        elif event.type == 'WHEELUPMOUSE':
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type == 'WHEELDOWNMOUSE':
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        elif event.type == 'MIDDLEMOUSE':
            if event.alt:
                if event.value == 'RELEASE':
                    bpy.ops.view3d.view_center_cursor()

        # Catch everything else arriving here
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # For operator state machine
        # possible states: {'INIT','SELECT_INCOMING'}
        self.state = 'INIT'
        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def reset_state(self, context):
        self.params_snap = {}
        self.junction = junction(context)

    def clean_up(self, context):
        # Make sure stencil is removed
        self.junction.remove_stencil()
        # Remove header text with 'None'
        context.workspace.status_text_set(None)
        # Set custom cursor
        bpy.context.window.cursor_modal_restore()
        # Make sure to exit edit mode
        if bpy.context.active_object:
            if bpy.context.active_object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
        self.state = 'INIT'
