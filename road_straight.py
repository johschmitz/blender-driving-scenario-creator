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


class DSC_OT_road_straight(bpy.types.Operator):
    bl_idname = 'dsc.road_straight'
    bl_label = 'Straight'
    bl_description = 'Create a straight road'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def create_object_xodr(self, context, point_start, point_end, snapped_start):
        '''
            Create a straight road object
        '''
        if point_end == point_start:
            self.report({"WARNING"}, "Impossible to create zero length road!")
            return
        obj_id = helpers.get_new_id_opendrive(context)
        mesh = bpy.data.meshes.new('road_straight_' + str(obj_id))
        obj = bpy.data.objects.new(mesh.name, mesh)
        helpers.link_object_opendrive(context, obj)

        # vertices = [(0.0, 0.0, 0.0),
        #             (0.0, 1.0, 0.0),
        #             (4.0, 1.0, 0.0),
        #             (4.0, 0.0, 0.0),
        #             (-4.0, 0.0, 0.0),
        #             (-4.0, 1.0, 0.0)
        #             ]
        vertices = [(0.0, 0.0, 0.0),
                    (1.0, 0.0, 0.0),
                    (1.0, -4.0, 0.0),
                    (0.0, -4.0, 0.0),
                    (0.0, 4.0, 0.0),
                    (1.0, 4.0, 0.0)
                    ]
        edges = [[0, 1],[1, 2],[2, 3],[3, 4],
                    [0, 4,],[4, 5],[5, 1]]
        faces = [[0, 1, 2, 3],[0, 4, 5, 1]]
        mesh.from_pydata(vertices, edges, faces)

        helpers.select_activate_object(context, obj)

        # Rotate, translate, scale according to selected points
        vector_start_end_xy = (point_end - point_start).to_2d()
        vector_obj = obj.data.vertices[1].co - obj.data.vertices[0].co
        heading_start = vector_start_end_xy.angle_signed(vector_obj.to_2d())
        self.transform_object_wrt_start(obj, point_start, heading_start)
        vector_obj = obj.data.vertices[1].co - obj.data.vertices[0].co
        self.transform_object_wrt_end(obj, vector_obj, point_end, snapped_start)

        # Remember connecting points for road snapping
        obj['cp_start'] = point_start
        obj['cp_end'] = point_end

        # Set OpenDRIVE custom properties
        obj['id_xodr'] = obj_id
        obj['t_road_planView_geometry'] = 'line'
        obj['t_road_planView_geometry_s'] = 0
        obj['t_road_planView_geometry_x'] = point_start.x
        obj['t_road_planView_geometry_y'] = point_start.y
        vector_start_end = point_end - point_start
        obj['t_road_planView_geometry_hdg'] = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        obj['t_road_planView_geometry_length'] = vector_start_end.length

        return obj

    def create_stencil(self, context, point_start, heading_start):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene, currently only support OBJECT mode.
        '''
        stencil = bpy.data.objects.get('dsc_stencil_object')
        if stencil is not None:
            if context.scene.objects.get('dsc_stencil_object') is None:
                context.scene.collection.objects.link(stencil)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new("dsc_stencil_object")
            vertices = [(0.0,   0.0, 0.0),
                        (0.01,  0.0, 0.0),
                        (0.01, -4.0, 0.0),
                        (0.0,  -4.0, 0.0),
                        (0.0,   4.0, 0.0),
                        (0.01,  4.0, 0.0)
                        ]
            edges = [[0, 1],[1, 2],[2, 3],[3, 4],
                     [0, 4,],[4, 5],[5, 1]]
            faces = []
            mesh.from_pydata(vertices, edges, faces)
            self.stencil = bpy.data.objects.new("dsc_stencil_object", mesh)
            self.transform_object_wrt_start(self.stencil, point_start, heading_start)
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
        stencil = bpy.data.objects.get('dsc_stencil_object')
        if stencil is not None:
            bpy.data.objects.remove(stencil, do_unlink=True)

    def update_stencil(self, point_end, snapped_start):
        # Transform stencil object to follow the mouse pointer
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
        vector_selected = point_end - obj.location
        # Make sure vectors are not 0 length to avoid division error
        if vector_selected.length > 0 and vector_obj.length > 0:

            # Apply transformation
            mat_scale = Matrix.Scale(vector_selected.length/vector_obj.length, 4, vector_obj)
            if snapped_start:
                obj.data.transform(mat_scale)
            else:
                if vector_selected.angle(vector_obj)-pi > 0:
                    # Avoid numerical issues due to vectors directly facing each other
                    mat_rotation = Matrix.Rotation(pi, 4, 'Z')
                else:
                    mat_rotation = vector_obj.rotation_difference(vector_selected).to_matrix().to_4x4()
                obj.data.transform(mat_rotation @ mat_scale)
            obj.data.update()

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
            context.workspace.status_text_set("Place road by clicking, hold CTRL to snap to grid, "
                "press ESCAPE, RIGHTMOUSE to exit.")
            # Set custom cursor
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            # Reset road snap
            self.snapped_start = False
            self.state = 'SELECT_START'
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update on move
        if event.type == 'MOUSEMOVE':
            # Snap to existing road objects if any, otherwise xy plane
            self.hit, self.id_xodr_hit, self.cp_type, point_selected, heading_selected = \
                helpers.raycast_mouse_to_object_else_xy(context, event)
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
                # For snapped straight roads use projected end point
                if self.snapped_start:
                    point_selected = self.project_point_end(
                        self.point_selected_start, self.heading_selected_start, point_selected)
                    context.scene.cursor.location = point_selected
                    self.update_stencil(point_selected, snapped_start=True)
                else:
                    self.update_stencil(point_selected, snapped_start=False)
                self.point_selected_end = point_selected
                self.heading_selected_end = heading_selected
        # Select start and end
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_START':
                    self.snapped_start = self.hit
                    self.id_xodr_start = self.id_xodr_hit
                    self.cp_type_start = self.cp_type
                    self.create_stencil(context, context.scene.cursor.location, self.heading_selected_start)
                    self.state = 'SELECT_END'
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_END':
                    self.snapped_end = self.hit
                    cp_type_end = self.cp_type
                    # Create the final object
                    obj = self.create_object_xodr(context, self.point_selected_start,
                        self.point_selected_end, self.snapped_start)
                    if self.snapped_start:
                        link_type = 'start'
                        helpers.create_object_xodr_links(context, obj, link_type, self.id_xodr_start, self.cp_type_start)
                    if self.snapped_end:
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
        # possible states: {'INIT','SELECTE_BEGINNING', 'SELECT_END'}
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
