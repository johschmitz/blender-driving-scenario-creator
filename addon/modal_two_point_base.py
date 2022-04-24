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
from mathutils import Vector, Matrix, Euler

from math import pi

from . import helpers
from . import view_memory_helper


class DSC_OT_two_point_base(bpy.types.Operator):
    bl_idname = 'dsc.two_point_base'
    bl_label = 'DSC snap draw operator'
    bl_options = {'REGISTER', 'UNDO'}

    snap_filter = None

    # Elevation adjustment can be 'DISABLED', 'SIDEVIEW', 'GENERIC'
    adjust_elevation = 'DISABLED'

    stencil = None

    params_input = {}
    params_snap = {}

    view_memory = view_memory_helper.view_memory_helper()

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def reset_params(self):
        self.params_input = {
            'point_start': Vector((0.0,0.0,0.0)),
            'point_end': Vector((0.0,0.0,0.0)),
            'heading_start': 0,
            'heading_end': 0,
            'curvature_start': 0,
            'curvature_end': 0,
            'slope_start': 0,
            'slope_end': 0,
            'connected_start': False,
            'connected_end': False,
            'design_speed': 130.0,
        }
        self.params_snap = {
            'id_obj': None,
            'point': Vector((0.0,0.0,0.0)),
            'type': 'cp_none',
            'heading': 0,
            'curvature': 0,
            'slope': 0,
        }

    def create_object(self, context):
        '''
            Create a road object
        '''
        raise NotImplementedError()

    def create_stencil(self, context, point_start):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene currently only support OBJECT mode.
        '''
        stencil = bpy.data.objects.get('dsc_stencil')
        if stencil is not None:
            if context.scene.objects.get('dsc_stencil') is None:
                context.scene.collection.objects.link(stencil)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new('dsc_stencil')
            vertices, edges, faces = self.get_initial_vertices_edges_faces()
            mesh.from_pydata(vertices, edges, faces)
            # Rotate in start heading direction
            self.stencil = bpy.data.objects.new('dsc_stencil', mesh)
            self.stencil.location = point_start
            # Link
            context.scene.collection.objects.link(self.stencil)
            self.stencil.use_fake_user = True
            self.stencil.data.use_fake_user = True
        # Make stencil active object
        helpers.select_activate_object(context, self.stencil)

    def remove_stencil(self):
        '''
            Unlink stencil, needs to be in OBJECT mode.
        '''
        stencil = bpy.data.objects.get('dsc_stencil')
        if stencil is not None:
            bpy.data.objects.remove(stencil, do_unlink=True)
            self.stencil = None

    def update_stencil(self, context):
        '''
            Transform stencil object to follow the mouse pointer.
        '''
        if self.params_input['point_end'] == self.params_input['point_start']:
            # This can happen due to start point snapping -> ignore
            return
        # Try getting data for a new mesh
        valid, mesh, matrix_world, materials = self.get_mesh_update_params(context, for_stencil=True)
        # If we get a valid solution we can update the mesh, otherwise just return
        if valid:
            helpers.replace_mesh(self.stencil, mesh)
            # Set stencil global transform
            self.stencil.matrix_world = matrix_world

    def get_initial_vertices_edges_faces(self):
        '''
            Calculate and return the vertices, edges and faces to create the initial stencil mesh.
        '''
        vertices = [(0.0, 0.0, 0.0)]
        edges = []
        faces = []
        return vertices, edges, faces

    def get_mesh_update_params(self, context, for_stencil=True):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        raise NotImplementedError()

    def calculate_heading_end(self, point_start, heading_start, point_end):
        vector_hdg = Vector((1.0, 0.0))
        vector_hdg.rotate(Matrix.Rotation(heading_start, 2))
        vector_start_end = (point_end - point_start).to_2d()
        adjacent = vector_start_end.to_2d().project(vector_hdg)
        # TODO make the heading ratio adjustable
        heading_ratio = 0.75
        vector_end = vector_start_end - heading_ratio * adjacent
        if vector_end.length == 0:
            return 0
        else:
            return vector_end.angle_signed(Vector((1.0, 0.0)))

    def input_valid(self, for_stencil):
        '''
            Return False if start and end point are identical, otherwise True.
        '''
        if self.params_input['point_start'].to_2d() == self.params_input['point_end'].to_2d():
            if not for_stencil:
                self.report({'WARNING'}, 'Start and end point can not be the same!')
            return False
        elif (self.params_input['point_end'].to_2d()-self.params_input['point_start'].to_2d()).length > 10000:
            # Limit length of objects to 10km
            self.report({'WARNING'}, 'Start and end point can not be more than 10km apart!')
            return False
        else:
            return True

    def modal(self, context, event):
        # Display help text
        if self.state == 'INIT':
            context.workspace.status_text_set('Place object by clicking, hold CTRL to snap to grid, '
                                              'hold E to adjust elevation, '
                                              'hold S to toggle sideview and adjust elevation, '
                                              'press RIGHTMOUSE to cancel selection, press ESCAPE to exit.')
            # Set custom cursor
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.reset_params()
            self.snapped = False
            self.selected_elevation = 0
            self.selected_point = Vector((0.0,0.0,0.0))
            self.selected_heading = 0
            self.selected_curvature = 0
            self.selected_slope = 0
            self.state = 'SELECT_START'
            self.params_input['design_speed'] = context.scene.road_properties.design_speed
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update on move
        if event.type == 'MOUSEMOVE':
            if self.adjust_elevation != 'DISABLED':
                # Get the selected point
                self.selected_elevation = helpers.mouse_to_elevation(context, event,
                    self.selected_point)
                if self.state == 'SELECT_START':
                    self.selected_point = self.params_input['point_start']
                if self.state == 'SELECT_END':
                    self.selected_point = self.params_input['point_end']
                self.selected_point.z = self.selected_elevation
            else:
                # Snap to existing objects if any, otherwise xy plane
                self.snapped, self.params_snap = helpers.mouse_to_object_params(
                    context, event, filter=self.snap_filter)
                if self.snapped:
                    self.selected_point = self.params_snap['point']
                    self.selected_heading = self.params_snap['heading']
                    self.selected_curvature = self.params_snap['curvature']
                    self.selected_slope = self.params_snap['slope']
                else:
                    self.selected_point = helpers.mouse_to_xy_parallel_plane(context, event,
                        self.selected_elevation)
                    self.selected_heading = 0
                    self.selected_curvature = 0
                    self.selected_slope = 0
            context.scene.cursor.location = self.selected_point.copy()
            # CTRL activates grid snapping if not snapped to object
            if event.ctrl and not self.snapped:
                bpy.ops.view3d.snap_cursor_to_grid()
                self.selected_point = context.scene.cursor.location
            # Process and remember plan view (floor) points according to modal state machine
            if self.state == 'SELECT_START':
                self.params_input['point_start'] = self.selected_point.copy()
                self.params_input['heading_start'] = self.selected_heading
                if self.params_snap['type'] is not None:
                    if self.params_snap['type'] != 'surface':
                        self.params_input['connected_start'] = True
                else:
                    self.params_input['connected_start'] = False
                self.params_input['curvature_start'] = self.selected_curvature
                self.params_input['slope_start'] = self.selected_slope
            if self.state == 'SELECT_END':
                self.params_input['point_end'] = self.selected_point.copy()
                if self.params_snap['type'] is not None:
                    if self.params_snap['type'] != 'surface':
                        self.params_input['connected_end'] = True
                        self.params_input['heading_end'] = self.selected_heading + pi
                        self.params_input['curvature_end'] = self.selected_curvature
                        self.params_input['slope_end'] = self.selected_slope
                else:
                    self.params_input['connected_end'] = False
                    self.params_input['heading_end'] = self.calculate_heading_end(self.params_input['point_start'],
                        self.params_input['heading_start'], self.params_input['point_end'])
                if self.input_valid(for_stencil=True):
                    self.update_stencil(context)
        # Select start and end
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_START':
                    self.id_xodr_start = self.params_snap['id_obj']
                    self.id_connected_junction_start = self.params_snap['id_connected_junction']
                    self.cp_type_start = self.params_snap['type']
                    # Create helper stencil mesh
                    self.create_stencil(context, self.params_input['point_start'])
                    # Set elevation so that end point selection starts on the same level
                    self.selected_elevation = self.selected_point.z
                    self.state = 'SELECT_END'
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_END':
                    cp_type_end = self.params_snap['type']
                    # Create the final object
                    if self.input_valid(for_stencil=False):
                        obj = self.create_object(context)
                        if self.params_input['connected_start']:
                            link_type = 'start'
                            helpers.create_object_xodr_links(obj, link_type, self.cp_type_start,
                                self.id_xodr_start, self.id_connected_junction_start)
                        if self.params_input['connected_end']:
                            link_type = 'end'
                            helpers.create_object_xodr_links(obj, link_type, cp_type_end,
                                self.params_snap['id_obj'], self.params_snap['id_connected_junction'])
                        # Remove stencil and go back to initial state to draw again
                        self.remove_stencil()
                        self.state = 'INIT'
                    return {'RUNNING_MODAL'}
        # Cancel step by step
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'RELEASE':
                # Back to beginning
                if self.state == 'SELECT_END':
                    self.remove_stencil()
                    self.state = 'INIT'
                    return {'RUNNING_MODAL'}
                # Exit
                if self.state == 'SELECT_START':
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
                    if self.stencil is not None:
                        # Look at current object from the side, perpendicular to z-axis
                        view3d = context.space_data
                        bpy.ops.view3d.view_axis(type='LEFT', align_active=False, relative=False)
                        region_view3d = view3d.region_3d
                        region_view3d.view_rotation.rotate(Euler((0, 0, self.stencil.rotation_euler.z + pi/2)))
                    self.adjust_elevation = 'SIDEVIEW'
            elif event.value == 'RELEASE':
                if self.adjust_elevation == 'SIDEVIEW':
                    # Restore previous view
                    self.view_memory.restore_view(context)
                self.adjust_elevation = 'DISABLED'
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
