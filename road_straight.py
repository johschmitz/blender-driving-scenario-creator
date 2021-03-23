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
from . import helpers

class DSC_OT_road_straight(bpy.types.Operator):
    bl_idname = 'dsc.road_straight'
    bl_label = 'Straight'
    bl_description = 'Create a straight road'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def create_object_xodr(self, context):
        """
            Create a straight road object
        """
        if self.point_raycast_end == self.point_raycast_start:
            self.report({"WARNING"}, "Impossible to create zero length road!")
            return
        mesh = bpy.data.meshes.new('road_straight')
        obj = bpy.data.objects.new(mesh.name, mesh)
        helpers.link_object_opendrive(context, obj)

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

        # Make active object to set cursor and origin
        helpers.select_activate_object(context, obj)
        context.scene.cursor.location = self.point_raycast_start
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        context.scene.cursor.location = self.point_raycast_end
        # Rotate and translate to correct x,y, heading wrt to origin
        mat_translation = Matrix.Translation(self.point_raycast_start - self.stencil.data.vertices[0].co)
        mat_rotation = Matrix.Rotation(self.heading_start,4,'Z')
        obj.data.transform(mat_translation @ mat_rotation)
        obj.data.update()
        # Transform mesh wrt to selected end point
        self.transform_object_wrt_end(obj)

        # Remember connecting points for tool snapping
        obj['point_start'] = self.point_raycast_start
        obj['point_end'] = self.point_raycast_end

        # Set OpenDRIVE custom properties
        obj['id_opendrive'] = helpers.get_new_id_opendrive(context)
        obj['t_road_planView_geometry'] = 'line'
        obj['t_road_planView_geometry_s'] = 0
        obj['t_road_planView_geometry_x'] = self.point_raycast_start.x
        obj['t_road_planView_geometry_y'] = self.point_raycast_end.y
        vector_start_end = self.point_raycast_end - self.point_raycast_start
        obj['t_road_planView_geometry_hdg'] = vector_start_end.angle(Vector((0.0, 1.0, 0.0)))
        obj['t_road_planView_geometry_length'] = vector_start_end.length

        return obj

    def create_draw_helper(self, context):
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
                        (0.0, 0.01, 0.0),
                        (4.0, 0.01, 0.0),
                        (4.0, 0.0, 0.0),
                        (-4.0, 0.0, 0.0),
                        (-4.0, 0.01, 0.0)
                        ]
            edges = [[0, 1],[1, 2],[2, 3],[3, 4],
                     [0, 4,],[4, 5],[5, 1]]
            faces = []
            mesh.from_pydata(vertices, edges, faces)
            self.stencil = bpy.data.objects.new("dsc_draw_helper_object", mesh)
            # Rotate and translate to correct x,y, heading
            mat_translation = Matrix.Translation(self.point_raycast_start - self.stencil.data.vertices[0].co)
            mat_rotation = Matrix.Rotation(self.heading_start,4,'Z')
            self.stencil.data.transform(mat_translation @ mat_rotation)
            self.stencil.data.update()
            # Link
            context.scene.collection.objects.link(self.stencil)
            self.stencil.use_fake_user = True
            self.stencil.data.use_fake_user = True

    def remove_draw_helper(self):
        """
            Unlink helper, needs to be in OBJECT mode
        """
        helper = bpy.data.objects.get('dsc_draw_helper_object')
        if helper is not None:
            bpy.data.objects.remove(helper, do_unlink=True)

    def update_draw_helper(self):
        # Transform helper object to follow the mouse pointer
        self.transform_object_wrt_end(self.stencil)

    def transform_object_wrt_end(self, obj):
        # Transform object according to selected end point (no start point translation)
        vector_selected = self.point_raycast_end - self.point_raycast_start
        vector_object = obj.data.vertices[1].co - obj.data.vertices[0].co
        if vector_selected.length > 0 and vector_object.length > 0:
            # Apply transformation
            if self.snapped_start:
                dot_product = vector_object @ vector_selected
                mat_scale = Matrix.Scale(dot_product/(vector_object.length*vector_object.length), 4, vector_object)
                obj.data.transform(mat_scale)
            else:
                mat_rotation = vector_object.rotation_difference(vector_selected).to_matrix().to_4x4()
                mat_scale = Matrix.Scale(vector_selected.length/vector_object.length, 4, vector_object)
                obj.data.transform(mat_rotation @ mat_scale)
            obj.data.update()

    def modal(self, context, event):
        # Display help text
        if self.state == 'INIT':
            context.area.header_text_set("Place road by clicking, press ESCAPE, RIGHTMOUSE to exit.")
            # Set custom cursor
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            # Reset snapping
            self.snapped_start = False
            self.state = 'SELECT_BEGINNING'
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}
        # Update on move
        if event.type == 'MOUSEMOVE':
            hit, self.point_raycast_end, self.heading_end = self.mouse_to_road_else_xy_raycast(context, event)
            context.scene.cursor.location = self.point_raycast_end
            if self.state == 'SELECT_END':
                self.update_draw_helper()
        # Select start and end
        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':
                if self.state == 'SELECT_BEGINNING':
                    # Find clickpoint in 3D and create helper mesh
                    hit, self.point_raycast_start, self.heading_start = self.mouse_to_road_else_xy_raycast(context, event)
                    self.snapped_start = hit
                    self.create_draw_helper(context)
                    # Make helper active object to set cursor and origin
                    helpers.select_activate_object(context, self.stencil)
                    context.scene.cursor.location = self.point_raycast_start
                    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                    self.state = 'SELECT_END'
                    return {'RUNNING_MODAL'}
                if self.state == 'SELECT_END':
                    # Set cursor to endpoint
                    hit, self.point_raycast_end, self.heading_end = self.mouse_to_road_else_xy_raycast(context, event)
                    context.scene.cursor.location = self.point_raycast_end
                    # Create the final object
                    self.create_object_xodr(context)
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

    def mouse_to_xy_plane(self, context, event):
        """
            Convert mouse pointer position to 3D point in xy-plane
        """
        region = context.region
        rv3d = context.region_data
        co2d = (event.mouse_region_x, event.mouse_region_y)
        view_vector_mouse = region_2d_to_vector_3d(region, rv3d, co2d)
        ray_origin_mouse = region_2d_to_origin_3d(region, rv3d, co2d)
        point = intersect_line_plane(ray_origin_mouse, ray_origin_mouse + view_vector_mouse,
           (0, 0, 0), (0, 0, 1), False)
        # Fix parallel plane issue
        if point is None:
            point = intersect_line_plane(ray_origin_mouse, ray_origin_mouse + view_vector_mouse,
                (0, 0, 0), view_vector_mouse, False)
        return point

    def mouse_to_road_connector_raycast(self, context, event):
        """
            Convert mouse pointer position to road connect point
        """
        region = context.region
        rv3d = context.region_data
        co2d = (event.mouse_region_x, event.mouse_region_y)
        view_vector_mouse = region_2d_to_vector_3d(region, rv3d, co2d)
        ray_origin_mouse = region_2d_to_origin_3d(region, rv3d, co2d)
        hit, point, normal, index_face, obj, matrix_world = context.scene.ray_cast(
            depsgraph=context.view_layer.depsgraph,
            origin=ray_origin_mouse,
            direction=view_vector_mouse)
        if hit and obj.data is not None and 'road_straight' in obj.name:
            return True, Vector(obj['point_end']), obj['t_road_planView_geometry_hdg']
        else:
            return False, point, 0

    def mouse_to_road_else_xy_raycast(self, context, event):
        hit, point_raycast, heading = self.mouse_to_road_connector_raycast(context, event)
        if not hit:
            point_raycast = self.mouse_to_xy_plane(context, event)
        return hit, point_raycast, heading