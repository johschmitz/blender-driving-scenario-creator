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
from . geometry_line import DSC_geometry_line
from . geometry_arc import DSC_geometry_arc
from . geometry_clothoid import DSC_geometry_clothoid
from . geometry_clothoid_triple import DSC_geometry_clothoid_triple
from . geometry_parampoly3 import DSC_geometry_parampoly3


def load_geometry(road_type, section_data, lane_offset_coefficients):
    '''
        Load geometry from stored geometry data.
    '''
    geometry = None
    if road_type == 'road_straight':
        geometry = DSC_geometry_line()
    if road_type == 'road_arc':
        geometry = DSC_geometry_arc()
    if road_type == 'road_clothoid':
        geometry = DSC_geometry_clothoid()
    if road_type == 'road_clothoid_triple':
        geometry = DSC_geometry_clothoid_triple()
    if road_type == 'road_parampoly3':
        geometry = DSC_geometry_parampoly3()

    if geometry != None:
        geometry.load_sections(section_data)
        geometry.lane_offset_coefficients = lane_offset_coefficients

    return geometry

class DSC_OT_modal_road_object_base(bpy.types.Operator):
    bl_idname = 'dsc.modal_road_object_base'
    bl_label = 'DSC snap draw road object modal operator'
    bl_options = {'REGISTER', 'UNDO'}

    stencil = None

    reference_object_mode = False
    reference_object_name = 'reference object'

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
            if self.state == 'SELECT_REFERENCE_OBJECT':
                vertices, edges, faces = self.get_initial_vertices_edges_faces_reference_object()
            else:
                vertices, edges, faces = self.get_initial_vertices_edges_faces_road_object()
            mesh.from_pydata(vertices, edges, faces)
            # Rotate in start heading direction
            self.stencil = bpy.data.objects.new('dsc_stencil', mesh)
            self.stencil.location = self.params_input['point']
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
            # Try getting data for a new mesh
            valid, mesh, matrix_world, materials = self.update_params_get_mesh(context, wireframe=True)
            # If we get a valid solution we can update the mesh, otherwise just return
            if valid:
                helpers.replace_mesh(self.stencil, mesh)
                # Set stencil global transform
                self.stencil.matrix_world = matrix_world

    def get_initial_vertices_edges_faces_reference_object(self):
        '''
            Calculate and return the vertices, edges and faces to create the
            initial stencil mesh for the reference object link visulization.
        '''
        vector_hdg = Vector((1.0, 0.0))
        vector_hdg.rotate(Matrix.Rotation(self.params_input['heading'] + pi/2, 2))
        vertices = [(0.0, 0.0, 0.0), (0.0, 0.0, -self.params_input['point'].z)]
        edges = [[0,1]]
        faces = []
        return vertices, edges, faces

    def get_initial_vertices_edges_faces_road_object(self):
        '''
            Calculate and return the vertices, edges and faces to create the
            initial stencil mesh for the road object.
        '''
        vector_hdg = Vector((1.0, 0.0))
        vector_hdg.rotate(Matrix.Rotation(self.params_input['heading'] + pi/2, 2))
        vector_left = (vector_hdg * sum(self.params_snap['lane_widths_left'])).to_3d().to_tuple()
        vector_right = (vector_hdg * -sum(self.params_snap['lane_widths_right'])).to_3d().to_tuple()
        vertices = [vector_left, vector_right, (0.0, 0.0, 0.0), (0.0, 0.0, -self.params_input['point'].z)]
        edges = [[0,1],[2,3]]
        faces = []
        return vertices, edges, faces

    def update_params_get_mesh(self, context, wireframe=True):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        raise NotImplementedError()

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
            Return False if some criteria are not met, otherwise True.
        '''
        # TODO currently just a dummy
        return True

    def reset_params_input(self):
        self.params_input = {
            'point': Vector((0.0,0.0,0.0)),
            'point_s': 0.0,
            'point_t': 0.0,
            'point_ref_line': None,
            'heading': 0.0,
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
        return obj

    def modal(self, context, event):
        # Display help text
        if self.state == 'INIT':
            context.workspace.status_text_set(
                'LEFTMOUSE: select road,place, '
                'hold CTRL: snap to grid, '
                'hold ALT: change heading, '
                'ALT+MIDDLEMOUSE: move view center, '
                'RIGHTMOUSE: cancel selection, '
                'ESCAPE: cancel and exit'
            )
            # Set custom cursor
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.reset_params_input()
            self.reset_params_snap()
            self.snapped_to_grid = False
            self.selected_reference_object = None
            self.selected_elevation = 0.0
            self.selected_point = helpers.mouse_to_xy_parallel_plane(context, event, self.selected_elevation)
            self.point_ref_line = None
            self.params_input['point'] = self.selected_point
            self.params_input['point_s'] = 0.0
            self.params_input['point_t'] = 0.0
            self.selected_heading = 0.0
            self.selected_road = None
            self.selected_geometry = None
            self.id_reference_object = None
            self.id_road = None
            self.id_lane = None
            if self.reference_object_mode == True:
                self.state = 'SELECT_REFERENCE_OBJECT'
            else:
                self.state = 'SELECT_ROAD'
            # Create helper stencil mesh
            self.create_stencil(context)
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update on move
        if event.type == 'MOUSEMOVE':
            self.reset_params_snap()
            if self.state == 'SELECT_REFERENCE_OBJECT':
                # Snap to existing objects if any, otherwise xy plane
                params_snap = helpers.mouse_to_road_object_params(
                    context, event, 'sign')
                # Snap to object
                if params_snap['hit_type'] is not None:
                    self.params_snap = params_snap
                    self.selected_reference_object_id = self.params_snap['id_obj']
                    self.selected_reference_object = helpers.get_object_xodr_by_id(self.params_snap['id_obj'])
                    selected_point_new = self.params_snap['point']
                    self.params_input['point_ref_object'] = selected_point_new
                    self.selected_heading = self.params_snap['heading']
                    self.selected_elevation = selected_point_new.z
                    context.scene.cursor.location = selected_point_new
                else:
                    selected_point_new = helpers.mouse_to_xy_parallel_plane(context, event,
                        self.selected_elevation)
                    self.selected_road = None
                    context.scene.cursor.location = selected_point_new
            elif self.state == 'SELECT_ROAD':
                # Snap to existing objects if any, otherwise xy plane
                params_snap = helpers.mouse_to_road_joint_params(
                    context, event, road_type='road')
                # Snap to object
                if params_snap['hit_type'] is not None and params_snap['hit_type'] == 'road':
                    self.params_snap = params_snap
                    self.selected_road = helpers.get_object_xodr_by_id(self.params_snap['id_obj'])
                    selected_point_new = self.params_snap['point']
                    self.selected_heading = self.params_snap['heading']
                    self.selected_elevation = selected_point_new.z
                    context.scene.cursor.location = selected_point_new
                else:
                    selected_point_new = helpers.mouse_to_xy_parallel_plane(context, event,
                        self.selected_elevation)
                    self.selected_road = None
                    context.scene.cursor.location = selected_point_new
            else: # self.state == 'SELECT_POINT'
                selected_point_new = helpers.mouse_to_xy_parallel_plane(context, event,
                    self.selected_elevation)
                context.scene.cursor.location = selected_point_new
                # Activate grid snapping when holding CTRL
                if event.ctrl:
                    bpy.ops.view3d.snap_cursor_to_grid()
                    selected_point_new = context.scene.cursor.location
                # Find closest point on reference line and the s, t coordinates for the selected point
                point_ref_line_local, heading_ref_line, self.params_input['point_s'], self.params_input['point_t'] = \
                    self.selected_geometry.get_closest_ref_line_x_y_heading_s_t(selected_point_new)
                # Transform to world coordinates
                self.params_input['point_ref_line'] = self.selected_geometry.matrix_world @ point_ref_line_local.to_3d()
                lane_offset = helpers.calculate_lane_offset(self.params_input['point_s'],
                                                            self.selected_geometry.lane_offset_coefficients,
                                                            self.selected_geometry.total_length)
                if self.params_input['point_t'] - lane_offset < 0:
                    self.selected_heading = self.selected_geometry.sections[0]['heading_start'] + heading_ref_line
                else:
                    self.selected_heading = self.selected_geometry.sections[0]['heading_start'] + heading_ref_line + pi
                # Recalculate the selected point by transforming back from the calculated Frenet coordinates
                selected_point_new = self.selected_geometry.matrix_world @ \
                    Vector(self.selected_geometry.sample_cross_section(
                        self.params_input['point_s'], [self.params_input['point_t']], False)[0][0])
                if event.alt:
                    # Calculate angular change to update start heading
                    heading_difference = self.calculate_heading_start_difference(
                            self.params_input['point'], self.selected_heading,
                            selected_point_new)
                    self.selected_heading = self.selected_heading - heading_difference
            self.selected_point = selected_point_new
            # Process and remember plan view (floor) points according to modal state machine
            self.params_input['point'] = self.selected_point.copy()
            self.params_input['heading'] = self.selected_heading
            if self.state == 'SELECT_ROAD' or self.state == 'SELECT_REFERENCE_OBJECT':
                self.update_stencil(context, update_start=True)
            if self.state == 'SELECT_POINT':
                if self.input_valid(wireframe=True):
                    self.update_stencil(context, update_start=False)
        # Select start, intermediate/end points
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_REFERENCE_OBJECT':
                    if self.params_snap['id_obj'] != None:
                        self.id_reference_object = self.params_snap['id_obj']
                        helpers.select_object(context, self.selected_reference_object)
                        self.state = 'SELECT_ROAD'
                    else:
                        self.report({'INFO'}, 'First select a ' + self.reference_object_name + '.')
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_ROAD':
                    if self.params_snap['id_obj'] != None:
                        self.selected_geometry = load_geometry(self.selected_road['dsc_type'], self.selected_road['geometry'], self.selected_road['lane_offset_coefficients'])
                        self.id_road = self.params_snap['id_obj']
                        self.id_lane = self.params_snap['id_lane']
                        # Set elevation so that end point selection starts on the same level
                        self.selected_elevation = self.params_input['point'].z
                        self.state = 'SELECT_POINT'
                    else:
                        self.report({'INFO'}, 'First select a road.')
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_POINT':
                    self.cp_type_end = self.params_snap['point_type']
                    if self.input_valid(wireframe=False):
                        # Create the final object
                        obj = self.create_object_modal(context)
                        # Link reference object to object
                        if self.reference_object_mode == True:
                            helpers.create_reference_object_xodr_link(self.selected_reference_object, obj['id_odr'])
                        # Make stencil active object again for next object
                        if obj is not None:
                            obj.select_set(state=False)
                            helpers.select_activate_object(context, self.stencil)
                    return {'RUNNING_MODAL'}
        # Cancel step by step
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'RELEASE':
                # Back to beginning
                if self.state == 'SELECT_POINT':
                    self.remove_stencil()
                    self.state = 'SELECT_ROAD'
                    return {'RUNNING_MODAL'}
                elif self.state == 'SELECT_ROAD':
                    if self.reference_object_mode == True:
                        self.state = 'SELECT_REFERENCE_OBJECT'
                        return {'RUNNING_MODAL'}
                    else:
                        # Exit
                        self.clean_up(context)
                        return {'FINISHED'}
                # Exit
                elif self.state == 'SELECT_REFERENCE_OBJECT':
                    self.clean_up(context)
                    return {'FINISHED'}
        # Zoom
        elif event.type == 'WHEELUPMOUSE':
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type == 'WHEELDOWNMOUSE':
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
        # possible states: {'INIT','SELECT_ROAD', 'SELECT_POINT'}
        self.state = 'INIT'
        self.create_object_model(context)
        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        # Remove geometry object
        del self.selected_geometry
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
