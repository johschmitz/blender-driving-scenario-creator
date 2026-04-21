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

from math import atan2

from . modal_two_point_base import DSC_OT_modal_two_point_base
from . entity import entity
from . import helpers


class DSC_OT_entity(DSC_OT_modal_two_point_base):
    bl_idname = 'dsc.entity'
    bl_label = 'Scenario entity'
    bl_description = 'Place a scenario entity object'
    bl_options = {'REGISTER', 'UNDO'}

    params = {}

    # Do not snap to other xodr or xosc objects in scene
    # TODO snap to road contact points, requires a lot of work
    snap_filter = 'surface'

    def create_object_model(self, context):
        '''
            Create a model object instance
        '''
        get_wheel_configs = getattr(self, 'get_wheel_configs', None)
        self.entity = entity(context, self.entity_type, self.entity_subtype,
            self.get_vertices_edges_faces, get_wheel_configs=get_wheel_configs)

    def create_object_3d(self, context):
        '''
            Create a 3d car object
        '''
        return self.entity.create_object_3d(context, self.params_input)

    def update_params_get_mesh(self, context, wireframe=True):
        '''
            Calculate and return the vertices, edges and faces to create an entity mesh.
        '''
        valid, mesh, matrix_world, materials = \
            self.entity.update_params_get_mesh(context, self.params_input, wireframe)
        if not valid:
            self.report({'WARNING'}, 'No valid entity geometry solution found!')
        return valid, mesh, matrix_world, materials

    def modal(self, context, event):
        # Single-click placement flow matching the move operator UX.
        if self.state == 'INIT':
            context.workspace.status_text_set(
                'LEFTMOUSE: place entity, '
                'hold SHIFT: lane center and orientation snap, '
                'hold ALT: heading-only mode, '
                'ALT+MIDDLEMOUSE: move view center, '
                'RIGHTMOUSE/ESCAPE: exit'
            )
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.reset_params_input()
            self.reset_params_snap()
            self.snapped_to_object = False
            self.selected_elevation = 0
            self.placement_position = helpers.mouse_to_xy_parallel_plane(
                context, event, 0)
            self.placement_heading = 0
            # Initialise stencil with a valid heading so it renders immediately.
            vec_heading = Vector((1.0, 0.0, 0.0))
            self.params_input['point_start'] = self.placement_position.copy()
            self.params_input['point_end'] = self.placement_position + vec_heading
            self.params_input['heading_override'] = self.placement_heading
            self.params_input['normal_start'] = Vector((0.0, 0.0, 1.0))
            self.create_stencil(context)
            self.update_stencil(context, update_start=False)
            self.state = 'PLACE'

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L',
                          'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            # Raycast to road surface
            params_snap = helpers.mouse_to_road_surface_params(context, event)
            if params_snap['hit_type'] is not None:
                self.params_snap = params_snap
                self.snapped_to_object = True
                self.selected_point = params_snap['point']
            else:
                self.reset_params_snap()
                self.snapped_to_object = False
                # In ALT heading mode project to the entity's height (like
                # the move operator) so heading direction stays sensible.
                z = (self.placement_position.z if event.alt
                     else self.selected_elevation)
                self.selected_point = helpers.mouse_to_xy_parallel_plane(
                    context, event, z)

            lane_heading = None

            # Lane-center snapping with SHIFT
            if (event.shift
                    and self.params_snap['hit_type'] == 'road_surface'):
                road_obj = bpy.data.objects.get(self.params_snap['id_obj'])
                if road_obj is not None:
                    lc_point, lh = \
                        helpers.get_lane_center_from_road_surface_hit(
                            road_obj, self.selected_point)
                    if lc_point is not None:
                        self.selected_point = lc_point
                        lane_heading = lh

            if not event.alt:
                # Normal mode: entity follows mouse
                self.placement_position = self.selected_point.copy()
                self.selected_elevation = self.selected_point.z
                if lane_heading is not None:
                    self.placement_heading = lane_heading
            else:
                # ALT heading-only mode: position stays, heading follows
                # mouse – exactly like the move operator.
                if lane_heading is not None:
                    self.placement_heading = lane_heading
                else:
                    vec = self.selected_point - self.placement_position
                    if vec.to_2d().length > 0.0001:
                        self.placement_heading = atan2(vec.y, vec.x)

            context.scene.cursor.location = self.selected_point.copy()

            # Update params and refresh stencil
            vec_dir = Vector((1.0, 0.0, 0.0))
            vec_dir.rotate(Matrix.Rotation(self.placement_heading, 4, 'Z'))
            self.params_input['point_start'] = self.placement_position.copy()
            self.params_input['point_end'] = self.placement_position + vec_dir
            self.params_input['point_end'].z = self.placement_position.z
            self.params_input['heading_override'] = self.placement_heading
            if self.snapped_to_object:
                self.params_input['normal_start'] = \
                    self.params_snap['normal'].copy()
            else:
                self.params_input['normal_start'] = Vector((0.0, 0.0, 1.0))

            self.update_stencil(context, update_start=False)

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.placement_position is not None:
                obj = self.create_object_3d(context)
                if obj is not None:
                    self.remove_stencil()
                    self.state = 'INIT'
            return {'RUNNING_MODAL'}

        elif event.type == 'RIGHTMOUSE':
            if event.value == 'RELEASE':
                self.clean_up(context)
                return {'FINISHED'}

        elif event.type == 'ESC':
            if event.value == 'RELEASE':
                self.clean_up(context)
                return {'FINISHED'}

        elif event.type == 'WHEELUPMOUSE':
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type == 'WHEELDOWNMOUSE':
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1,
                                use_cursor_init=True)
        elif event.type == 'MIDDLEMOUSE':
            if event.alt and event.value == 'RELEASE':
                bpy.ops.view3d.view_center_cursor()

        return {'RUNNING_MODAL'}
