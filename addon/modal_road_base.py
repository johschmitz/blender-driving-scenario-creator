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
from mathutils import Vector, Matrix, Euler
from mathutils.geometry import distance_point_to_plane

from math import pi

from . import helpers
from . import view_memory_helper


class DSC_OT_modal_road_base(bpy.types.Operator):
    bl_idname = 'dsc.modal_road_base'
    bl_label = 'DSC snap draw road modal operator'
    bl_options = {'REGISTER', 'UNDO'}

    only_snapped_to_object = False
    always_adjust_heading = False
    linear_selection = False

    # Elevation adjustment can be 'DISABLED', 'SIDEVIEW', 'GENERIC'
    adjust_elevation = 'DISABLED'

    stencil = None

    params_input = {}
    params_snap = {}

    geometry = None

    view_memory = view_memory_helper.view_memory_helper()

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def create_object_model(self, context):
        '''
            Create a model object instance
        '''
        raise NotImplementedError()

    def reset_geometry(self):
        '''
            Reset geometry.
        '''
        self.geometry.reset()

    def add_geometry_section(self):
        '''
            Add a piece of geometry to the road.
        '''
        self.geometry.add_section()

    def remove_last_geometry_section(self):
        '''
            Remove last piece of geometry from the road.
        '''
        self.geometry.remove_last_section()

    def create_object_3d(self, context):
        '''
            Create a 3d object from the model
        '''
        raise NotImplementedError()

    def update_road_properties(self, context):
        '''
            Dynamically update the road properties based on the user input if
            necessary.
        '''
        raise NotImplementedError()

    def create_stencil(self, context):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene currently only support OBJECT mode.
        '''
        self.stencil = bpy.data.objects.get('dsc_stencil')
        if self.stencil is not None:
            if context.scene.objects.get('dsc_stencil') is None:
                context.scene.collection.objects.link(self.stencil)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new('dsc_stencil')
            vertices, edges, faces = self.get_initial_vertices_edges_faces(context)
            mesh.from_pydata(vertices, edges, faces)
            # Rotate in start heading direction
            self.stencil = bpy.data.objects.new('dsc_stencil', mesh)
            self.stencil.location = self.params_input['points'][-2]
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

    def update_stencil(self, context, update_start):
        '''
            Transform stencil object to follow the mouse pointer.
        '''
        if update_start:
            self.remove_stencil()
            self.create_stencil(context)
        else:
            if self.params_input['points'][-1] == self.params_input['points'][-2]:
                # This can happen due to start point snapping -> ignore
                return
            # Try getting data for a new mesh
            valid, mesh, matrix_world, materials = self.update_params_get_mesh(context, wireframe=True)
            # If we get a valid solution we can update the mesh, otherwise just return
            if valid:
                helpers.replace_mesh(self.stencil, mesh)
                # Set stencil global transform
                self.stencil.matrix_world = matrix_world

    def get_initial_vertices_edges_faces(self, context):
        '''
            Calculate and return the vertices, edges and faces to create the initial stencil mesh.
        '''
        vector_hdg = Vector((1.0, 0.0))
        vector_hdg.rotate(Matrix.Rotation(self.params_input['heading_start'] + pi/2, 2))
        if self.object_type == 'junction_connecting_road':
            width_lanes_left = sum([lane.width_start if lane.side == 'left' else 0 for lane in context.scene.dsc_properties.connecting_road_properties.lanes])
            width_lanes_right = sum([lane.width_start if lane.side == 'right' else 0 for lane in context.scene.dsc_properties.connecting_road_properties.lanes])
        else:
            width_lanes_left = sum([lane.width_start if lane.side == 'left' else 0 for lane in context.scene.dsc_properties.road_properties.lanes])
            width_lanes_right = sum([lane.width_start if lane.side == 'right' else 0 for lane in context.scene.dsc_properties.road_properties.lanes])
        vector_left = (vector_hdg * width_lanes_left).to_3d().to_tuple()
        vector_right = (vector_hdg * -width_lanes_right).to_3d().to_tuple()
        vertices = [vector_left, vector_right, (0.0, 0.0, 0.0), (0.0, 0.0, -self.params_input['points'][-2].z)]
        edges = [[0,1],[2,3]]
        faces = []
        return vertices, edges, faces

    def update_params_get_mesh(self, context, wireframe=True):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        raise NotImplementedError()

    def calculate_heading_end(self, point_start, heading_start, point_end):
        '''
            Calcuate the end angle based on heading ratio.
        '''
        vector_start_end = (point_end - point_start).to_2d()
        if vector_start_end.length == 0:
            return 0
        else:
            vector_hdg = Vector((1.0, 0.0))
            vector_hdg.rotate(Matrix.Rotation(heading_start, 2))
            angle_base = vector_start_end.angle_signed(Vector((1.0, 0.0)))
            if angle_base >= 0:
                return angle_base + self.heading_end_extra
            else:
                return angle_base - self.heading_end_extra

    def update_stencil_heading_end(self, context):
        '''
            Update the stencil when the heading end is changed.
        '''
        self.params_input['heading_end'] = self.calculate_heading_end(self.params_input['points'][-2],
            self.params_input['heading_start'], self.params_input['points'][-1])
        self.update_stencil(context, update_start=False)

    def calculate_heading_start_difference(self, point_start, heading_start_old, point_end_new):
        '''
            Return angle between vector in (old) heading start direction and
            (new) start-end vector
        '''
        vector_hdg = Vector((1.0, 0.0))
        vector_hdg.rotate(Matrix.Rotation(heading_start_old, 2))
        vector_start_end = (point_end_new - point_start).to_2d()
        if vector_start_end.length == 0:
            return 0
        else:
            return vector_hdg.angle_signed(vector_start_end)

    def input_valid(self, wireframe):
        '''
            Return False if start and end point are identical, otherwise True.
        '''
        if self.params_input['points'][-2].to_2d() == self.params_input['points'][-1].to_2d():
            if not wireframe:
                self.report({'WARNING'}, 'Start and end point can not be the same!')
            return False
        elif (self.params_input['points'][-1].to_2d()-self.params_input['points'][-2].to_2d()).length > 10000:
            # Limit length of objects to 10km
            self.report({'WARNING'}, 'Start and end point can not be more than 10km apart!')
            return False
        else:
            return True

    def reset_params_input(self):
        self.params_input = {
            'points': [Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0, 0.0))],
            'heading_start': 0.0,
            'heading_end': 0.0,
            'curvature_start': 0.0,
            'curvature_end': 0.0,
            'slope_start': 0.0,
            'slope_end': 0.0,
            'connected_start': False,
            'connected_end': False,
            'normal_start': Vector((0.0,0.0,1.0)),
            'design_speed': 130.0,
        }

    def reset_params_snap(self):
        self.params_snap = {
            'hit_type': None,
            'id_obj': None,
            'id_extra': None,
            'id_lane': None,
            'joint_side': None,
            'point': Vector((0.0,0.0,0.0)),
            'normal': Vector((0.0,0.0,1.0)),
            'point_type': None,
            'heading': 0.0,
            'curvature': 0.0,
            'slope': 0.0,
            'lane_widths_left': [],
            'lane_widths_right': [],
        }

    def create_object_modal(self, context):
        '''
            Helper function to create the object in the modal operator
        '''
        obj = self.create_object_3d(context)
        if obj != None:
            obj.select_set(state=False)
            if self.params_input['connected_start']:
                link_type = 'start'
                # TODO do not get the direct junction information from the object
                if 'id_direct_junction_start' in obj:
                    id_extra = obj['id_direct_junction_start']
                    if self.id_extra_start != None:
                        self.report({'WARNING'}, 'Avoid connecting two split road' \
                            ' ends (direct junctions) to each other!')
                else:
                    id_extra = self.id_extra_start
                helpers.create_object_xodr_links(obj, link_type, self.cp_type_start,
                    self.id_odr_start, id_extra, self.id_lane_start)
            if self.params_input['connected_end']:
                link_type = 'end'
                # TODO keep it generic, direct junction should not appear at this point!
                if 'id_direct_junction_end' in obj:
                    id_extra = obj['id_direct_junction_end']
                    if self.params_snap['id_extra'] != None:
                        self.report({'WARNING'}, 'Avoid connecting two split road' \
                            ' ends (direct junctions) to each other!')
                else:
                    id_extra = self.params_snap['id_extra']
                    id_lane = self.params_snap['id_lane']
                helpers.create_object_xodr_links(obj, link_type, self.cp_type_end,
                    self.params_snap['id_obj'], id_extra, id_lane)

    def modal(self, context, event):
        # Display help text
        if self.state == 'INIT':
            context.workspace.status_text_set(
                'LEFTMOUSE: place, '
                'hold SHIFT: place more points, '
                'hold CTRL: snap to grid, '
                'hold ALT: change start heading, '
                'hold E: adjust elevation, '
                'hold S: sideview adjust elevation, '
                'SHIFT+MIDDLEMOUSE: adjust heading end, '
                'ALT+MIDDLEMOUSE: move view center, '
                'RIGHTMOUSE: cancel selection, '
                'RETURN/SPACE: finish, '
                'ESCAPE: cancel and exit'
            )
            # Set custom cursor
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.reset_geometry()
            self.reset_params_input()
            self.reset_params_snap()
            self.snapped_to_grid = False
            self.snapped_to_object = False
            self.selected_elevation = 0.0
            self.heading_end_extra = 0.0
            self.selected_point = helpers.mouse_to_xy_parallel_plane(context, event,
                self.selected_elevation)
            self.params_input['points'][-2] = self.selected_point
            self.selected_normal_start = Vector((0.0,0.0,1.0))
            self.selected_heading_start = 0.0
            self.selected_heading_end = 0.0
            self.selected_curvature = 0.0
            self.selected_slope = 0.0
            self.joint_side_start = None
            self.state = 'SELECT_START'
            if self.object_type == 'junction_connecting_road':
                self.params_input['design_speed'] = context.scene.dsc_properties.connecting_road_properties.design_speed
            else:
                self.params_input['design_speed'] = context.scene.dsc_properties.road_properties.design_speed
            # Create helper stencil mesh
            self.create_stencil(context)
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update on move
        if event.type == 'MOUSEMOVE':
            if self.adjust_elevation != 'DISABLED':
                # Get the selected point
                self.selected_elevation = helpers.mouse_to_elevation(context, event,
                    self.selected_point)
                if self.state == 'SELECT_START':
                    self.selected_point = self.params_input['points'][-2]
                elif self.state == 'SELECT_POINT':
                    self.selected_point = self.params_input['points'][-1]
                self.selected_point.z = self.selected_elevation
                context.scene.cursor.location = self.selected_point
            else:
                # Snap to existing objects if any, otherwise xy plane
                if self.object_type == 'junction_connecting_road':
                    if self.state == 'SELECT_START':
                        params_snap = helpers.mouse_to_road_joint_params(
                            context, event, road_type='junction_connecting_road', joint_side='right')
                    else:
                        params_snap = helpers.mouse_to_road_joint_params(
                            context, event, road_type='junction_connecting_road', joint_side='left')
                else:
                    params_snap = helpers.mouse_to_road_joint_params(
                        context, event, road_type='road')
                # Snap to object if not snapping to grid (by holding CTRL)
                if params_snap['hit_type'] is not None and not event.ctrl:
                    self.params_snap = params_snap
                    self.snapped_to_object = True
                    selected_point_new = self.params_snap['point']
                    if self.state == 'SELECT_START':
                        self.selected_heading_start = self.params_snap['heading']
                        self.selected_normal_start = self.params_snap['normal']
                        self.joint_side_start = self.params_snap['joint_side']
                        if self.object_type == 'junction_connecting_road':
                            self.update_road_properties(context, 'start')
                    elif self.state == 'SELECT_POINT':
                        self.selected_heading_end = self.params_snap['heading']
                        if self.object_type == 'junction_connecting_road':
                            self.update_road_properties(context, 'end')
                    self.selected_curvature = self.params_snap['curvature']
                    self.selected_slope = self.params_snap['slope']
                    context.scene.cursor.location = selected_point_new

                else:
                    self.reset_params_snap()
                    self.snapped_to_object = False
                    selected_point_new = helpers.mouse_to_xy_parallel_plane(context, event,
                        self.selected_elevation)
                    if (self.params_input['connected_start'] == True or \
                        self.state == 'SELECT_POINT' and len(self.params_input['points']) > 2) \
                        and self.linear_selection:
                        # Constrain point for linear case
                        selected_point_new = helpers.project_point_vector_2d(self.params_input['points'][-2],
                            self.params_input['heading_start'], selected_point_new)
                        selected_point_new.z = self.selected_elevation
                        # Check if road section direction is positive
                        vector_hdg = Vector((1.0, 0.0, 0.0))
                        vector_hdg.rotate(Matrix.Rotation(self.params_input['heading_start'], 3, 'Z'))
                        distance = distance_point_to_plane(
                            selected_point_new, self.params_input['points'][-2], vector_hdg)
                        if distance < 0.0:
                            selected_point_new = self.params_input['points'][-1]
                    context.scene.cursor.location = selected_point_new
                    # Activate grid snapping when holding CTRL
                    if not self.only_snapped_to_object and event.ctrl:
                        bpy.ops.view3d.snap_cursor_to_grid()
                        selected_point_new = context.scene.cursor.location
                    self.selected_curvature = 0
                    self.selected_slope = 0
                    self.selected_normal_start = Vector((0.0,0.0,1.0))
                    if (event.alt or self.always_adjust_heading) \
                        and self.params_input['connected_start'] == False \
                        and len(self.params_input['points']) == 2:
                        # Calculate angular change to update start heading
                        heading_difference = self.calculate_heading_start_difference(
                                self.params_input['points'][-2], self.selected_heading_start,
                                selected_point_new)
                        self.selected_heading_start = self.selected_heading_start - heading_difference
                self.selected_point = selected_point_new
            # Process and remember plan view (floor) points according to modal state machine
            if self.state == 'SELECT_START':
                self.params_input['points'][-2] = self.selected_point.copy()
                self.params_input['heading_start'] = self.selected_heading_start
                self.params_input['normal_start'] = self.selected_normal_start.copy()
                if self.params_snap['point_type'] is not None:
                    self.params_input['connected_start'] = True
                else:
                    self.params_input['connected_start'] = False
                self.params_input['curvature_start'] = self.selected_curvature
                self.params_input['slope_start'] = self.selected_slope
                self.update_stencil(context, update_start=True)
            # Always update end parameters to have them set even if mouse is not
            # moved in SELECT_POINT state
            self.params_input['points'][-1] = self.selected_point.copy()
            self.params_input['heading_start'] = self.selected_heading_start
            if self.params_snap['point_type'] is not None:
                self.params_input['connected_end'] = True
                self.params_input['heading_end'] = self.selected_heading_end + pi
                self.params_input['curvature_end'] = self.selected_curvature
                self.params_input['slope_end'] = self.selected_slope
            else:
                self.params_input['connected_end'] = False
                self.params_input['heading_end'] = self.calculate_heading_end(self.params_input['points'][-2],
                    self.params_input['heading_start'], self.params_input['points'][-1])
            if self.state == 'SELECT_POINT':
                if self.input_valid(wireframe=True):
                    self.update_stencil(context, update_start=False)
        # Select start, intermediate/end points
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                # For junction connecting roads we may only proceed snapped to the junction joints
                if self.only_snapped_to_object and not self.snapped_to_object:
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_START':
                    self.id_odr_start = self.params_snap['id_obj']
                    self.id_extra_start = self.params_snap['id_extra']
                    self.id_lane_start = self.params_snap['id_lane']
                    self.cp_type_start = self.params_snap['point_type']
                    # Set elevation so that end point selection starts on the same level
                    self.selected_elevation = self.params_input['points'][-1].z
                    self.state = 'SELECT_POINT'
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_POINT':
                    self.cp_type_end = self.params_snap['point_type']
                    if self.input_valid(wireframe=False):
                        if event.shift and self.params_input['connected_end'] == False:
                            # Make sure not to work with identical points
                            if self.params_input['points'][-1] != self.params_input['points'][-2]:
                                # Add another section based on the last selected point
                                self.add_geometry_section()
                                # Add new point for potential next selection
                                self.params_input['points'].append(self.selected_point)
                        else:
                            # Create the final object
                            self.create_object_modal(context)
                            # Remove stencil and go back to initial state to draw again
                            self.remove_stencil()
                            self.state = 'INIT'
                    return {'RUNNING_MODAL'}
        # Cancel step by step
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'RELEASE':
                # Back to beginning
                if self.state == 'SELECT_POINT':
                    if len(self.params_input['points']) > 2:
                        self.remove_last_geometry_section()
                        self.params_input['points'].pop()
                        self.state = 'SELECT_POINT'
                    else:
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
        # Zoom / End heading adjustment
        elif event.type == 'WHEELUPMOUSE':
            if event.shift:
                # Adjust end heading
                if self.heading_end_extra < 1.0:
                    self.heading_end_extra += 0.2
                else:
                    self.heading_end_extra = 1.0
                self.update_stencil_heading_end(context)
            else:
                # Zoom out
                bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type == 'WHEELDOWNMOUSE':
            if event.shift:
                # Adjust end heading
                if self.heading_end_extra > -1.0:
                    self.heading_end_extra -= 0.2
                else:
                    self.heading_end_extra = -1.0
                self.update_stencil_heading_end(context)
            else:
                # Zoom in
                bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        # Finish
        elif event.type in {'RET'} or event.type in {'SPACE'}:
            if self.state == 'SELECT_POINT':
                self.create_object_modal(context)
                # Remove stencil and go back to initial state to draw again
                self.remove_stencil()
                self.state = 'INIT'
                return {'RUNNING_MODAL'}
        # Exit immediately
        elif event.type == 'ESC':
            if event.value == 'RELEASE':
                self.clean_up(context)
                return {'FINISHED'}
        # View centering
        elif event.type == 'MIDDLEMOUSE':
            if event.alt:
                if event.value == 'RELEASE':
                    bpy.ops.view3d.view_center_cursor()

        # Catch everything else arriving here
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        # For operator state machine
        # possible states: {'INIT','SELECT_START', 'SELECT_POINT'}
        self.state = 'INIT'
        self.create_object_model(context)
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
