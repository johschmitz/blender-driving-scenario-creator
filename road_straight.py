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
from mathutils import Matrix
from mathutils.geometry import intersect_line_plane


class DSC_OT_road_straight(bpy.types.Operator):
    bl_idname = 'dsc.road_straight'
    bl_label = 'Straight'
    bl_description = 'Create a straight road'
    bl_options = {'REGISTER', 'UNDO'}

    # For operator state machine 
    # possible states: {'INIT','SELECTE_BEGINNING', 'SELECT_END'}
    state = 'INIT'

    @classmethod
    def poll(cls, context):
        return True

    def create_object(self, context, event):
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
                    (0.0, 6.0, 0.0),
                    (4.0, 6.0, 0.0),
                    (4.0, 0.0, 0.0),
                    (-4.0, 0.0, 0.0),
                    (-4.0, 6.0, 0.0)
                    ]
        edges = [[0,1]]
        faces = [[0, 1, 2, 3],[0, 4, 5, 1]]
        mesh.from_pydata(vertices, edges, faces)

        # OpenDRIVE custom properties
        obj['xodr'] = {'atribute_test':'999888777'}
        return obj

    def create_draw_helper_object(self, context, point_start):
        """
            Create a helper object with fake user
            or find older one in bpy data and relink to scene
            currently only support OBJECT mode
        """
        helper = bpy.data.objects.get('dsc_draw_helper_object')
        if helper is not None:
            if context.scene.objects.get('dsc_draw_helper_line') is None:
                context.scene.collection.objects.link(helper)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new("dsc_draw_helper_object")
            vertices = [(0.0, 0.0, 0.0),
                        (0.0, 6.0, 0.0),
                        (4.0, 6.0, 0.0),
                        (4.0, 0.0, 0.0),
                        (-4.0, 0.0, 0.0),
                        (-4.0, 6.0, 0.0)
                        ]
            edges = [[0, 1],[1, 2],[2, 3],[3, 4],
                     [0, 4,],[4, 5],[5, 1]]
            #faces = [[0, 1, 2, 3],[0, 4, 5, 1]]
            faces = []
            mesh.from_pydata(vertices, edges, faces)
            helper = bpy.data.objects.new("dsc_draw_helper_object", mesh)
            helper.location = point_start
            # Link
            context.scene.collection.objects.link(helper)
            helper.use_fake_user = True
            helper.data.use_fake_user = True

        return helper

    def remove_draw_helper_object(self, context):
        """
            Unlink helper
            currently only support OBJECT mode
        """
        helper = bpy.data.objects.get('dsc_draw_helper_object')
        if helper is not None:
            bpy.data.objects.remove(helper, do_unlink=True)

    def create_draw_helper_line(self, context, point_start):
        """
            Create a helper line with fake user
            or find older one in bpy data and relink to scene
            currently only support OBJECT mode
        """
        helper = bpy.data.objects.get('dsc_draw_helper_line')
        if helper is not None:
            if context.scene.objects.get('dsc_draw_helper_line') is None:
                context.scene.collection.objects.link(helper)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new("dsc_draw_helper_line")
            vertices = [point_start,
                        point_start,
                        ]
            edges = [[0,1]]
            faces = []
            mesh.from_pydata(vertices, edges, faces)
            helper = bpy.data.objects.new("dsc_draw_helper_line", mesh)
            # Link
            context.scene.collection.objects.link(helper)
            helper.use_fake_user = True
            helper.data.use_fake_user = True

        return helper

    def remove_draw_helper_line(self, context):
        """
            Unlink helper
            currently only support OBJECT mode
        """
        helper = bpy.data.objects.get('dsc_draw_helper_line')
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
        # Display help
        if self.state == 'INIT':
            context.area.header_text_set("Place road by clicking, press ESCAPE, RIGHTMOUSE to exit.")
            # Set custom cursor
            bpy.context.window.cursor_modal_set('NONE')
            self.state = 'SELECT_BEGINNING'
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update
        if event.type == 'MOUSEMOVE':
            point_raycast = self.mouse_to_xy_plane(context, event)
            context.scene.cursor.location = point_raycast
        # Select
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_BEGINNING':
                    # Find clickpoint in 3D and create helper line
                    point_raycast = self.mouse_to_xy_plane(context, event)
                    helper = self.create_draw_helper_line(context, point_raycast)
                    helper.select_set(state=True)
                    context.view_layer.objects.active = helper
                    # Set cursor and origin
                    context.scene.cursor.location = point_raycast
                    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                    # Select end point vertex
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.mesh.select_mode(type='VERT')
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    helper.data.vertices[1].select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    # Use translate operator to move around
                    bpy.ops.transform.translate('INVOKE_DEFAULT',
                                                constraint_axis=(True, True, False),
                                                orient_type='GLOBAL',
                                                release_confirm=True)
                    self.state = 'SELECT_END'
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_END':
                    # Set cursor to endpoint
                    point_raycast = self.mouse_to_xy_plane(context, event)
                    context.scene.cursor.location = point_raycast
                    self.remove_draw_helper_line(context)
                    self.state = 'INIT'
                    return {'RUNNING_MODAL'}
        # Cancel
        elif event.type in {'ESC', 'RIGHTMOUSE'}:
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

        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
