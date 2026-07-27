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
import json


TRAJECTORY_VERTEX_METADATA_KEY = 'trajectory_polyline_vertex_data'


class DSC_trajectory_vertex_property_item(bpy.types.PropertyGroup):
    idx: bpy.props.IntProperty(min=0)

    x: bpy.props.FloatProperty(name='x', default=0.0, precision=6)
    y: bpy.props.FloatProperty(name='y', default=0.0, precision=6)
    z: bpy.props.FloatProperty(name='z', default=0.0, precision=6)

    h: bpy.props.FloatProperty(name='h', default=0.0, precision=6)
    use_h: bpy.props.BoolProperty(name='Use h', default=False)
    p: bpy.props.FloatProperty(name='p', default=0.0, precision=6)
    use_p: bpy.props.BoolProperty(name='Use p', default=False)
    r: bpy.props.FloatProperty(name='r', default=0.0, precision=6)
    use_r: bpy.props.BoolProperty(name='Use r', default=False)

    time: bpy.props.FloatProperty(name='time', default=0.0, precision=6)
    use_time: bpy.props.BoolProperty(name='Use time', default=False)

    speed_longitudinal: bpy.props.FloatProperty(
        name='speed_longitudinal', default=0.0, precision=6)
    use_speed_longitudinal: bpy.props.BoolProperty(
        name='Use speed_longitudinal', default=False)

    acceleration_longitudinal: bpy.props.FloatProperty(
        name='acceleration_longitudinal', default=0.0, precision=6)
    use_acceleration_longitudinal: bpy.props.BoolProperty(
        name='Use acceleration_longitudinal', default=False)

    standstill: bpy.props.FloatProperty(
        name='standstill', default=0.0, min=0.0, precision=6)
    use_standstill: bpy.props.BoolProperty(
        name='Use standstill', default=False)


def _on_active_vertex_index_update(self, context):
    obj = bpy.data.objects.get(self.selected_trajectory_name)
    if obj is None:
        return
    if not (obj.get('dsc_type') == 'trajectory'
            and obj.get('dsc_subtype') == 'polyline'
            and obj.type == 'MESH'):
        return
    view_layer = context.view_layer if context else bpy.context.view_layer
    view_layer.objects.active = obj
    obj.select_set(True)
    if obj.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    if 0 <= self.active_vertex_index < len(bm.verts):
        for v in bm.verts:
            v.select = False
        target = bm.verts[self.active_vertex_index]
        target.select = True
        bm.select_history.clear()
        bm.select_history.add(target)
        bmesh.update_edit_mesh(obj.data)


class DSC_trajectory_properties(bpy.types.PropertyGroup):
    selected_trajectory_name: bpy.props.StringProperty(default='')
    active_vertex_index: bpy.props.IntProperty(
        default=0, min=0, update=_on_active_vertex_index_update)
    trajectory_vertices: bpy.props.CollectionProperty(type=DSC_trajectory_vertex_property_item)


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_vertex_metadata(obj):
    raw = obj.get(TRAJECTORY_VERTEX_METADATA_KEY)
    if not raw:
        return []

    if not isinstance(raw, str):
        return []

    try:
        payload = json.loads(raw)
    except ValueError:
        return []

    if not isinstance(payload, list):
        return []

    rows = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        cleaned = {}
        for key in (
            'time',
            'speed_longitudinal',
            'acceleration_longitudinal',
            'h',
            'p',
            'r',
            'standstill',
        ):
            if key in item:
                cleaned[key] = _safe_float(item[key])
        rows.append(cleaned)

    return rows


def serialize_vertex_metadata(rows):
    payload = []
    for row in rows:
        data = {}
        if row.use_time:
            data['time'] = float(row.time)
        if row.use_speed_longitudinal:
            data['speed_longitudinal'] = float(row.speed_longitudinal)
        if row.use_acceleration_longitudinal:
            data['acceleration_longitudinal'] = float(row.acceleration_longitudinal)
        if row.use_h:
            data['h'] = float(row.h)
        if row.use_p:
            data['p'] = float(row.p)
        if row.use_r:
            data['r'] = float(row.r)
        if row.use_standstill:
            data['standstill'] = float(row.standstill)
        payload.append(data)
    return json.dumps(payload)
