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

from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_plane


class DSC_OT_road_straight(bpy.types.Operator):
    bl_idname = 'dsc.road_straight'
    bl_label = 'Straight'
    bl_description = 'Create a straight road'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def create_object_xodr(self, context, point_start, point_end):
        """
            Create a straight road object
        """
        scene = context.scene
        mesh = bpy.data.meshes.new('road_straight')
        obj = bpy.data.objects.new(mesh.name, mesh)
        if not 'OpenDRIVE' in bpy.data.collections:
            collection = bpy.data.collections.new('OpenDRIVE')
            scene.collection.children.link(collection)
        collection = bpy.data.collections.get('OpenDRIVE')
        collection.objects.link(obj)

        vertices = [(0.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0),
                    (4.0, 1.0, 0.0),
                    (4.0, 0.0, 0.0),
                    (-4.0, 0.0, 0.0),
                    (-4.0, 1.0, 0.0)
                    ]
        edges = [[0, 1],[1, 2],[2, 3],[3, 4],
                    [0, 4,],[4, 5],[5, 1]]
        faces = [[0, 1, 2, 3],[0, 4, 5, 1]]
        mesh.from_pydata(vertices, edges, faces)

        # Transform helper object to follow the mouse pointer
        v1 = point_end - point_start
        v2 = obj.data.vertices[1].co - obj.data.vertices[0].co
        if v2.length > 0:
            mat_rotation = v2.rotation_difference(v1).to_matrix().to_4x4()
            mat_scale = Matrix.Scale(v1.length/v2.length, 4, v2)
            mat_translation = Matrix.Translation(point_start)
            # Apply transformation
            obj.data.transform(mat_translation @ mat_rotation @ mat_scale)
            obj.data.update()

        # OpenDRIVE custom properties
        obj['xodr'] = {'atribute_test':'999888777'}
        return obj

    def create_draw_helper(self, context, point_start):
        """
            Create a helper object with fake user
            or find older one in bpy data and relink to scene
            currently only support OBJECT mode
        """
        helper = bpy.data.objects.get('dsc_draw_helper_object')
        if helper is not None:
            if context.scene.objects.get('dsc_draw_helper_object') is None:
                context.scene.collection.objects.link(helper)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new("dsc_draw_helper_object")
            vertices = [(0.0, 0.0, 0.0),
                        (0.0, 1.0, 0.0),
                        (4.0, 1.0, 0.0),
                        (4.0, 0.0, 0.0),
                        (-4.0, 0.0, 0.0),
                        (-4.0, 1.0, 0.0)
                        ]
            edges = [[0, 1],[1, 2],[2, 3],[3, 4],
                     [0, 4,],[4, 5],[5, 1]]
            faces = []
            mesh.from_pydata(vertices, edges, faces)
            helper = bpy.data.objects.new("dsc_draw_helper_object", mesh)
            location = helper.location
            helper.location = location + point_start
            # Link
            context.scene.collection.objects.link(helper)
            helper.use_fake_user = True
            helper.data.use_fake_user = True

        return helper

    def update_draw_helper(self, point_raycast):
        # Transform helper object to follow the mouse pointer
        v1 = point_raycast - self.point_raycast_start
        v2 = self.helper.data.vertices[1].co - self.helper.data.vertices[0].co
        if v2.length > 0:
            mat_rotation = v2.rotation_difference(v1).to_matrix().to_4x4()
            mat_scale = Matrix.Scale(v1.length/v2.length, 4, v2)
            # Apply transformation
            self.helper.data.transform(mat_rotation @ mat_scale)
            self.helper.data.update()

    def remove_draw_helper(self):
        """
            Unlink helper
            currently only support OBJECT mode
        """
        helper = bpy.data.objects.get('dsc_draw_helper_object')
        if helper is not None:
            bpy.data.objects.remove(helper, do_unlink=True)

    def mouse_to_xy_plane(self, context, event):
        """
            Convert mouse pointer pos to 3D point in xy-plane
        """
        region = context.region
        rv3d = context.region_data
        co2d = (event.mouse_region_x, event.mouse_region_y)
        view_vector_mouse = region_2d_to_vector_3d(region, rv3d, co2d)
        ray_origin_mouse = region_2d_to_origin_3d(region, rv3d, co2d)
        point = intersect_line_plane(ray_origin_mouse, ray_origin_mouse + view_vector_mouse,
           (0, 0, 0), (0, 0, 1), False)
        if point is None:
            point = intersect_line_plane(ray_origin_mouse, ray_origin_mouse + view_vector_mouse,
                (0, 0, 0), view_vector_mouse, False)
        return point

    def modal(self, context, event):
        # Display help text
        if self.state == 'INIT':
            context.area.header_text_set("Place road by clicking, press ESCAPE, RIGHTMOUSE to exit.")
            ## Set custom cursor
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.state = 'SELECT_BEGINNING'
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update on move
        if event.type == 'MOUSEMOVE':
            point_raycast = self.mouse_to_xy_plane(context, event)
            if self.state == 'SELECT_BEGINNING':
                context.scene.cursor.location = point_raycast
            if self.state == 'SELECT_END':
                self.update_draw_helper(point_raycast)
        # Select start and end
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_BEGINNING':
                    # Find clickpoint in 3D and create helper line
                    self.point_raycast_start = self.mouse_to_xy_plane(context, event)
                    self.helper = self.create_draw_helper(context, self.point_raycast_start)
                    self.helper.select_set(state=True)
                    context.view_layer.objects.active = self.helper
                    # Set cursor and origin
                    context.scene.cursor.location = self.point_raycast_start
                    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                    self.state = 'SELECT_END'
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_END':
                    # Set cursor to endpoint
                    self.point_raycast_end = self.mouse_to_xy_plane(context, event)
                    context.scene.cursor.location = self.point_raycast_end
                    # Create the final object
                    self.create_object_xodr(context, self.point_raycast_start, self.point_raycast_end)
                    # Remove draw helper and go back to initial state to draw again
                    self.remove_draw_helper()
                    self.state = 'INIT'
                    return {'RUNNING_MODAL'}
        # Cancel
        elif event.type in {'ESC', 'RIGHTMOUSE'}:
            # Make sure draw helper is removed
            self.remove_draw_helper()
            # Remove header text with 'None'
            context.area.header_text_set(None)
            # Set custom cursor
            bpy.context.window.cursor_modal_restore()
            # Make sure to exit edit mode
            if bpy.context.active_object:
                if bpy.context.active_object.mode == 'EDIT':
                    bpy.ops.object.mode_set(mode='OBJECT')
            self.state = 'INIT'
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_loc_x = context.region.x
        self.value = event.mouse_x
        # For operator state machine 
        # possible states: {'INIT','SELECTE_BEGINNING', 'SELECT_END'}
        self.state = 'INIT'

        self.point_raycast_start = Vector((0.0,0.0,0.0))

        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
