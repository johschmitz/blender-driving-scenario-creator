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

from mathutils import Vector
from math import isfinite

from . import helpers
from .trajectory_properties import load_vertex_metadata
from .trajectory_properties import serialize_vertex_metadata
from .trajectory_properties import TRAJECTORY_VERTEX_METADATA_KEY


def _is_polyline_trajectory_object(obj):
    if obj is None:
        return False
    if obj.get('dsc_type') != 'trajectory':
        return False
    if obj.get('dsc_subtype') != 'polyline':
        return False
    return obj.type == 'MESH'


class DSC_OT_trajectory_vertex_focus_in_view(bpy.types.Operator):
    bl_idname = 'dsc.trajectory_vertex_focus_in_view'
    bl_label = 'Show vertex in 3D'
    bl_description = 'Select this trajectory vertex in 3D Edit Mode'

    trajectory_name: bpy.props.StringProperty(options={'HIDDEN'})
    vertex_index: bpy.props.IntProperty(min=0, options={'HIDDEN'})

    def execute(self, context):
        obj = bpy.data.objects.get(self.trajectory_name)
        if not _is_polyline_trajectory_object(obj):
            self.report({'ERROR'}, 'Trajectory object not found or invalid.')
            return {'CANCELLED'}

        helpers.select_activate_object(context, obj)
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        if self.vertex_index >= len(bm.verts):
            self.report({'ERROR'}, 'Vertex index out of range.')
            return {'CANCELLED'}

        for vert in bm.verts:
            vert.select = False
        target = bm.verts[self.vertex_index]
        target.select = True
        bm.select_history.clear()
        bm.select_history.add(target)
        bmesh.update_edit_mesh(obj.data)

        context.scene.dsc_properties.trajectory_properties.active_vertex_index = self.vertex_index
        return {'FINISHED'}


class DSC_OT_trajectory_enter_edit_mode(bpy.types.Operator):
    bl_idname = 'dsc.trajectory_enter_edit_mode'
    bl_label = 'Enter Edit Mode'
    bl_description = 'Enter Edit Mode on the trajectory so you can see vertex selection in 3D'

    trajectory_name: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        obj = bpy.data.objects.get(self.trajectory_name)
        if not _is_polyline_trajectory_object(obj):
            self.report({'ERROR'}, 'Trajectory object not found or invalid.')
            return {'CANCELLED'}
        helpers.select_activate_object(context, obj)
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class DSC_OT_popup_trajectory_polyline_editor(bpy.types.Operator):
    bl_idname = 'dsc.popup_trajectory_polyline_editor'
    bl_label = 'Edit selected polyline (hint: Ctrl+MOUSEWHEEL on numeric values)'
    bl_description = 'Edit vertices and OpenSCENARIO Motion values of the selected polyline trajectory'

    trajectory_name: bpy.props.StringProperty(
        name='Trajectory name', description='Polyline trajectory to edit', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == 'VIEW_3D'

    def _get_target_object(self, context):
        if self.trajectory_name:
            return bpy.data.objects.get(self.trajectory_name)
        return context.active_object

    def _is_polyline_trajectory(self, obj):
        return _is_polyline_trajectory_object(obj)

    def _validate_rows(self, rows):
        if len(rows) < 2:
            return False, 'A polyline trajectory requires at least 2 vertices.'

        time_previous = None
        for row in rows:
            if not isfinite(row.x) or not isfinite(row.y) or not isfinite(row.z):
                return False, 'Vertex coordinates must be finite numeric values.'

            if row.use_h and not isfinite(row.h):
                return False, 'h must be a finite numeric value when enabled.'

            if row.use_p and not isfinite(row.p):
                return False, 'p must be a finite numeric value when enabled.'

            if row.use_r and not isfinite(row.r):
                return False, 'r must be a finite numeric value when enabled.'

            if row.use_time:
                if not isfinite(row.time):
                    return False, 'Time values must be finite numeric values.'
                if time_previous is not None and row.time < time_previous:
                    return False, 'Time values must be non-decreasing.'
                time_previous = row.time

            if row.use_speed_longitudinal and not isfinite(row.speed_longitudinal):
                return False, 'speed_longitudinal must be finite when enabled.'

            if row.use_acceleration_longitudinal and not isfinite(row.acceleration_longitudinal):
                return False, 'acceleration_longitudinal must be finite when enabled.'

            if row.use_standstill:
                if not isfinite(row.standstill):
                    return False, 'standstill must be a finite numeric value.'
                if row.standstill < 0.0:
                    return False, 'standstill must be non-negative.'

        return True, ''

    def _load_rows_from_selected_object(self, context):
        trajectory_props = context.scene.dsc_properties.trajectory_properties
        obj = self._get_target_object(context)

        trajectory_props.selected_trajectory_name = obj.name
        trajectory_props.trajectory_vertices.clear()

        metadata_rows = load_vertex_metadata(obj)

        for idx, vert in enumerate(obj.data.vertices):
            point_world = obj.matrix_world @ vert.co
            row = trajectory_props.trajectory_vertices.add()
            row.idx = idx
            row.x = point_world.x
            row.y = point_world.y
            row.z = point_world.z

            if idx < len(metadata_rows):
                item = metadata_rows[idx]
                if 'time' in item:
                    row.use_time = True
                    row.time = item['time']
                if 'speed_longitudinal' in item:
                    row.use_speed_longitudinal = True
                    row.speed_longitudinal = item['speed_longitudinal']
                if 'acceleration_longitudinal' in item:
                    row.use_acceleration_longitudinal = True
                    row.acceleration_longitudinal = item['acceleration_longitudinal']
                if 'h' in item:
                    row.use_h = True
                    row.h = item['h']
                if 'p' in item:
                    row.use_p = True
                    row.p = item.get('p', 0.0)
                if 'r' in item:
                    row.use_r = True
                    row.r = item.get('r', 0.0)
                if 'standstill' in item:
                    row.use_standstill = True
                    row.standstill = item['standstill']

    def _build_polyline_mesh(self, rows):
        point_start = Vector((rows[0].x, rows[0].y, rows[0].z))
        vertices = []
        for row in rows:
            point = Vector((row.x, row.y, row.z))
            vertices.append(point - point_start)

        edges = []
        for idx in range(len(vertices)-1):
            edges.append([idx, idx + 1])

        mesh = bpy.data.meshes.new('trajectory')
        mesh.from_pydata(vertices, edges, [])
        return mesh, point_start

    def execute(self, context):
        trajectory_props = context.scene.dsc_properties.trajectory_properties
        obj = bpy.data.objects.get(trajectory_props.selected_trajectory_name)

        if obj is None:
            self.report({'ERROR'}, 'Selected trajectory no longer exists.')
            return {'CANCELLED'}
        if obj.get('dsc_type') != 'trajectory' or obj.get('dsc_subtype') != 'polyline':
            self.report({'ERROR'}, 'Selected object is not a polyline trajectory.')
            return {'CANCELLED'}

        rows = trajectory_props.trajectory_vertices
        valid, message = self._validate_rows(rows)
        if not valid:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}

        if obj.mode == 'EDIT':
            helpers.select_activate_object(context, obj)
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh, point_start = self._build_polyline_mesh(rows)
        helpers.replace_mesh(obj, mesh)
        obj.location = point_start
        obj[TRAJECTORY_VERTEX_METADATA_KEY] = serialize_vertex_metadata(rows)

        self.report({'INFO'}, 'Updated trajectory with {} vertices.'.format(len(rows)))
        return {'FINISHED'}

    def cancel(self, context):
        trajectory_props = context.scene.dsc_properties.trajectory_properties
        obj = bpy.data.objects.get(trajectory_props.selected_trajectory_name)
        if obj is not None and obj.mode == 'EDIT':
            helpers.select_activate_object(context, obj)
            bpy.ops.object.mode_set(mode='OBJECT')

    def invoke(self, context, event):
        del event

        obj = self._get_target_object(context)
        if not self._is_polyline_trajectory(obj):
            self.report({'ERROR'}, 'Select a polyline trajectory first.')
            return {'CANCELLED'}

        self._load_rows_from_selected_object(context)
        return context.window_manager.invoke_props_dialog(self, width=1200)

    def draw(self, context):
        trajectory_props = context.scene.dsc_properties.trajectory_properties
        obj = bpy.data.objects.get(trajectory_props.selected_trajectory_name)

        # Live-read selected vertex from Edit Mode without closing the popup
        active_idx = trajectory_props.active_vertex_index
        if obj is not None and obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            selected = [v.index for v in bm.verts if v.select]
            if selected:
                active_idx = selected[0]

        box = self.layout.box()
        row = box.row(align=True)
        row.label(text='Trajectory: {}'.format(trajectory_props.selected_trajectory_name))
        op = row.operator('dsc.trajectory_enter_edit_mode', text='', icon='EDITMODE_HLT')
        op.trajectory_name = trajectory_props.selected_trajectory_name
        row.prop(trajectory_props, 'active_vertex_index', text='Vertex')

        row = box.row(align=True)
        col = row.column(align=True)
        col.label(text='# / 3D')
        col = row.column(align=True)
        col.label(text='x / y / z')
        col = row.column(align=True)
        col.label(text='use')
        col = row.column(align=True)
        col.label(text='h / p / r')
        col = row.column(align=True)
        col.label(text='use')
        col = row.column(align=True)
        col.label(text='speed / acceleration')
        col = row.column(align=True)
        col.label(text='use')
        col = row.column(align=True)
        col.label(text='time / standstill')

        for item in trajectory_props.trajectory_vertices:
            row_box = box.box()
            row_box.alert = item.idx == active_idx
            row = row_box.row(align=True)

            col = row.column(align=True)
            col.label(text=str(item.idx))
            op = col.operator('dsc.trajectory_vertex_focus_in_view', text='show', icon='HIDE_OFF')
            op.trajectory_name = trajectory_props.selected_trajectory_name
            op.vertex_index = item.idx

            col = row.column(align=True)
            col.prop(item, 'x', text='x')
            col.prop(item, 'y', text='y')
            col.prop(item, 'z', text='z')

            col = row.column(align=True)
            orient_row = col.row(align=True)
            orient_row.prop(item, 'use_h', text='heading')
            orient_row.prop(item, 'h', text='')
            orient_row = col.row(align=True)
            orient_row.prop(item, 'use_p', text='pitch')
            orient_row.prop(item, 'p', text='')
            orient_row = col.row(align=True)
            orient_row.prop(item, 'use_r', text='roll')
            orient_row.prop(item, 'r', text='')

            col = row.column(align=True)
            motion_row = col.row(align=True)
            motion_row.prop(item, 'use_speed_longitudinal', text='speed')
            motion_row.prop(item, 'speed_longitudinal', text='')
            motion_row = col.row(align=True)
            motion_row.prop(item, 'use_acceleration_longitudinal', text='acceleration')
            motion_row.prop(item, 'acceleration_longitudinal', text='')

            col = row.column(align=True)
            time_row = col.row(align=True)
            time_row.prop(item, 'use_time', text='time')
            standstill_row = col.row(align=True)
            standstill_row.prop(item, 'use_standstill', text='standstill')
            col = row.column(align=True)
            standstill_row = col.row(align=True)
            standstill_row.prop(item, 'standstill', text='seconds')
            time_row = col.row(align=True)
            time_row.prop(item, 'time', text='seconds')


class DSC_OT_pick_trajectory_polyline_editor(bpy.types.Operator):
    bl_idname = 'dsc.pick_trajectory_polyline_editor'
    bl_label = 'Edit polyline trajectory'
    bl_description = 'Select a polyline trajectory to edit its vertices and motion values'

    state = 'INIT'

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == 'VIEW_3D'

    def _is_polyline_trajectory(self, obj):
        if obj is None:
            return False
        if obj.get('dsc_category') != 'OpenSCENARIO':
            return False
        if obj.get('dsc_type') != 'trajectory':
            return False
        if obj.get('dsc_subtype') != 'polyline':
            return False
        return obj.type == 'MESH'

    def _pick_polyline_trajectory(self, context, event):
        try:
            bpy.ops.view3d.select(
                extend=False,
                deselect_all=True,
                toggle=False,
                center=False,
                enumerate=False,
                object=False,
                location=(event.mouse_region_x, event.mouse_region_y),
            )
        except RuntimeError:
            return None

        obj = context.active_object
        if not self._is_polyline_trajectory(obj):
            return None
        return obj

    def modal(self, context, event):
        if self.state == 'INIT':
            context.workspace.status_text_set(
                'LEFTMOUSE: select a polyline trajectory to edit, RIGHTMOUSE/ESC: cancel, '
                'ALT+MIDDLEMOUSE: move view center'
            )
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.state = 'SELECT_OBJECT'

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            selected_obj = self._pick_polyline_trajectory(context, event)
            if selected_obj is None:
                self.report({'INFO'}, 'Select a polyline trajectory.')
                return {'RUNNING_MODAL'}

            trajectory_name = selected_obj.name
            helpers.select_activate_object(context, selected_obj)
            self.clean_up(context)
            bpy.ops.dsc.popup_trajectory_polyline_editor(
                'INVOKE_DEFAULT', trajectory_name=trajectory_name)
            return {'FINISHED'}

        elif event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
            self.clean_up(context)
            return {'FINISHED'}

        elif event.type == 'ESC':
            self.clean_up(context)
            return {'FINISHED'}

        elif event.type in {'WHEELUPMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type in {'WHEELDOWNMOUSE'}:
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        elif event.type in {'MIDDLEMOUSE'}:
            if event.alt and event.value == 'RELEASE':
                bpy.ops.view3d.view_center_cursor()

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        del event
        self.state = 'INIT'
        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        context.workspace.status_text_set(None)
        bpy.context.window.cursor_modal_restore()
        self.state = 'INIT'
