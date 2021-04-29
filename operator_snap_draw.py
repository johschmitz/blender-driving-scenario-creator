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

class DSC_OT_snap_draw(bpy.types.Operator):
    bl_idname = 'dsc.snap_draw'
    bl_label = 'DSC snap draw operator'
    bl_options = {'INTERNAL'}

    def __init__(self):
        self.object_snapping = True

    @classmethod
    def poll(cls, context):
        return True

    def create_object_xodr(self, context, point_start, point_end, snapped_start):
        '''
            Create a junction object
        '''
        raise NotImplementedError()

    def create_stencil(self, context, point_start, heading_start, snapped_start):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene currently only support OBJECT mode.
        '''
        raise NotImplementedError()

    def remove_stencil(self):
        '''
            Unlink stencil, needs to be in OBJECT mode.
        '''
        stencil = bpy.data.objects.get('dsc_stencil_object')
        if stencil is not None:
            bpy.data.objects.remove(stencil, do_unlink=True)

    def update_stencil(self, point_end, snapped_start):
        '''
            Transform stencil object to follow the mouse pointer.
        '''
        vector_obj = self.stencil.data.vertices[1].co - self.stencil.data.vertices[0].co
        self.transform_object_wrt_end(self.stencil, vector_obj, point_end, snapped_start)

    def transform_object_wrt_start(self, obj, point_start, heading_start):
        '''
            Rotate and translate origin to start point and rotate to start heading.
        '''
        obj.location = point_start
        mat_rotation = Matrix.Rotation(heading_start, 4, 'Z')
        obj.data.transform(mat_rotation)
        obj.data.update()

    def transform_object_wrt_end(self, obj, vector_obj, point_end, snapped_start):
        '''
            Transform object according to selected end point (keep start point fixed).
        '''
        raise NotImplementedError()

    def project_point_end(self, point_start, heading_start, point_selected):
        '''
            Project selected point to direction vector.
        '''
        vector_selected = point_selected - point_start
        if vector_selected.length > 0:
            vector_object = Vector((1.0, 0.0, 0.0))
            vector_object.rotate(Matrix.Rotation(heading_start, 4, 'Z'))
            return point_start + vector_selected.project(vector_object)
        else:
            return point_selected

    def modal(self, context, event):
        # Display help text
        if self.state == 'INIT':
            context.workspace.status_text_set("Place object by clicking, hold CTRL to snap to grid, "
                "press ESCAPE, RIGHTMOUSE to exit.")
            # Set custom cursor
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            # Reset snapping
            self.snapped_start = False
            self.state = 'SELECT_START'
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update on move
        if event.type == 'MOUSEMOVE':
            # Snap to existing objects if any, otherwise xy plane
            self.hit, self.id_xodr_hit, self.cp_type, point_selected, heading_selected = \
                helpers.raycast_mouse_to_object_else_xy(context, event, self.object_snapping)
            context.scene.cursor.location = point_selected
            # CTRL activates grid snapping if not snapped to object
            if event.ctrl and not self.hit:
                bpy.ops.view3d.snap_cursor_to_grid()
                point_selected = context.scene.cursor.location
            # Process and remember points according to modal state machine
            if self.state == 'SELECT_START':
                self.point_selected_start = point_selected.copy()
                self.heading_selected_start = heading_selected
                # Make sure end point and heading is set even if mouse is not moved
                self.point_selected_end = point_selected
                self.heading_selected_end = heading_selected
            if self.state == 'SELECT_END':
                # For snapped case use projected end point
                if self.snapped_start:
                    point_selected = self.project_point_end(
                        self.point_selected_start, self.heading_selected_start, point_selected)
                    context.scene.cursor.location = point_selected
                    self.update_stencil(point_selected, self.snapped_start)
                else:
                    self.update_stencil(point_selected, self.snapped_start)
                self.point_selected_end = point_selected
                self.heading_selected_end = heading_selected
        # Select start and end
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_START':
                    self.snapped_start = self.hit
                    self.id_xodr_start = self.id_xodr_hit
                    self.cp_type_start = self.cp_type
                    # Create helper stencil mesh
                    self.create_stencil(context, context.scene.cursor.location,
                        self.heading_selected_start, self.snapped_start)
                    self.state = 'SELECT_END'
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_END':
                    snapped_end = self.hit
                    cp_type_end = self.cp_type
                    # Create the final object
                    obj = self.create_object_xodr(context, self.point_selected_start,
                        self.point_selected_end, self.snapped_start)
                    if self.snapped_start:
                        link_type = 'start'
                        helpers.create_object_xodr_links(context, obj, link_type, self.id_xodr_start, self.cp_type_start)
                    if snapped_end:
                        link_type = 'end'
                        helpers.create_object_xodr_links(context, obj, link_type, self.id_xodr_hit, cp_type_end)
                    # Remove stencil and go back to initial state to draw again
                    self.remove_stencil()
                    self.state = 'INIT'
                    return {'RUNNING_MODAL'}
        # Cancel step by step
        elif event.type in {'RIGHTMOUSE'} and event.value in {'RELEASE'}:
            # Back to beginning
            if self.state == 'SELECT_END':
                self.remove_stencil()
                self.state = 'INIT'
                return {'RUNNING_MODAL'}
            # Exit
            if self.state == 'SELECT_START':
                self.clean_up(context)
                return {'FINISHED'}
        # Exit immediately
        elif event.type in {'ESC'}:
            self.clean_up(context)
            return {'FINISHED'}
        # Zoom
        elif event.type in {'WHEELUPMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type in {'WHEELDOWNMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)

        # Catch everything else arriving here
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_loc_x = context.region.x
        self.value = event.mouse_x
        # For operator state machine
        # possible states: {'INIT','SELECT_START', 'SELECT_END'}
        self.state = 'INIT'

        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        # Make sure stencil is removed
        self.remove_stencil()
        # Remove header text with 'None'
        context.workspace.status_text_set(None)
        # Set custom cursor
        bpy.context.window.cursor_modal_restore()
        # Make sure to exit edit mode
        if bpy.context.active_object:
            if bpy.context.active_object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
        self.state = 'INIT'
