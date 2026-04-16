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

import json
from mathutils import Vector

from . import helpers


class ScriptPayloadError(ValueError):
    pass


def _ensure_dict(data, name):
    if not isinstance(data, dict):
        raise ScriptPayloadError(f'{name} must be a JSON object')
    return data


def _ensure_list(data, name):
    if not isinstance(data, list):
        raise ScriptPayloadError(f'{name} must be a JSON array')
    return data


def _to_float(value, name):
    try:
        return float(value)
    except Exception as exc:
        raise ScriptPayloadError(f'{name} must be a number') from exc


def _to_int(value, name):
    try:
        return int(value)
    except Exception as exc:
        raise ScriptPayloadError(f'{name} must be an integer') from exc


def _parse_point(value, name):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ScriptPayloadError(f'{name} must be [x, y, z]')
    return (
        _to_float(value[0], f'{name}[0]'),
        _to_float(value[1], f'{name}[1]'),
        _to_float(value[2], f'{name}[2]'),
    )


def _parse_bool(value, name, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ScriptPayloadError(f'{name} must be a boolean')


def _parse_link(link, name):
    if link is None:
        return None
    link = _ensure_dict(link, name)
    if 'cp_type' not in link or 'id_obj' not in link:
        raise ScriptPayloadError(f'{name} requires cp_type and id_obj')
    parsed = {
        'cp_type': str(link['cp_type']),
        'id_obj': _to_int(link['id_obj'], f'{name}.id_obj'),
        'id_extra': None,
        'id_lane': None,
    }
    if 'id_extra' in link and link['id_extra'] is not None:
        parsed['id_extra'] = _to_int(link['id_extra'], f'{name}.id_extra')
    if 'id_lane' in link and link['id_lane'] is not None:
        parsed['id_lane'] = _to_int(link['id_lane'], f'{name}.id_lane')
    return parsed


def _parse_script_payload(script_payload):
    if script_payload is None:
        raise ScriptPayloadError('script_payload is required')
    if isinstance(script_payload, dict):
        return script_payload
    if not isinstance(script_payload, str):
        raise ScriptPayloadError('script_payload must be a JSON string or dict')
    if script_payload.strip() == '':
        raise ScriptPayloadError('script_payload is required')
    try:
        data = json.loads(script_payload)
    except json.JSONDecodeError as exc:
        raise ScriptPayloadError(f'script_payload is not valid JSON: {exc.msg}') from exc
    return _ensure_dict(data, 'script_payload')


def normalize_road_payload(script_payload):
    payload = _parse_script_payload(script_payload)
    start = _ensure_dict(payload.get('start'), 'start')
    if 'point' not in start:
        raise ScriptPayloadError('start.point is required')
    if 'heading' not in start:
        raise ScriptPayloadError('start.heading is required')

    sections = _ensure_list(payload.get('sections'), 'sections')
    if len(sections) == 0:
        raise ScriptPayloadError('sections must contain at least one entry')

    normalized_sections = []
    for idx, section in enumerate(sections):
        section_name = f'sections[{idx}]'
        section = _ensure_dict(section, section_name)
        if 'point' not in section:
            raise ScriptPayloadError(f'{section_name}.point is required')
        normalized = {
            'point': _parse_point(section['point'], f'{section_name}.point'),
            'heading_end': None,
            'curvature_end': _to_float(section.get('curvature_end', 0.0), f'{section_name}.curvature_end'),
            'slope_end': _to_float(section.get('slope_end', 0.0), f'{section_name}.slope_end'),
            'connected_end': _parse_bool(section.get('connected_end'), f'{section_name}.connected_end', False),
            'link_end': _parse_link(section.get('link_end'), f'{section_name}.link_end'),
        }
        if 'heading_end' in section and section['heading_end'] is not None:
            normalized['heading_end'] = _to_float(section['heading_end'], f'{section_name}.heading_end')
        normalized_sections.append(normalized)

    normalized = {
        'start': {
            'point': _parse_point(start['point'], 'start.point'),
            'heading': _to_float(start['heading'], 'start.heading'),
            'curvature': _to_float(start.get('curvature', 0.0), 'start.curvature'),
            'slope': _to_float(start.get('slope', 0.0), 'start.slope'),
            'connected': _parse_bool(start.get('connected'), 'start.connected', False),
            'normal': _parse_point(start.get('normal', [0.0, 0.0, 1.0]), 'start.normal'),
            'design_speed': start.get('design_speed'),
        },
        'sections': normalized_sections,
        'road_properties': payload.get('road_properties'),
        'connecting_road_properties': payload.get('connecting_road_properties'),
        'connecting_road_setup': payload.get('connecting_road_setup'),
        'link_start': _parse_link(payload.get('link_start'), 'link_start'),
        'link_end': _parse_link(payload.get('link_end'), 'link_end'),
    }
    if normalized['link_start'] is not None:
        normalized['start']['connected'] = True
    if normalized['link_end'] is not None:
        normalized['sections'][-1]['connected_end'] = True
    return normalized


def normalize_two_point_payload(script_payload):
    payload = _parse_script_payload(script_payload)
    start = payload.get('start')
    end = payload.get('end')
    if start is None:
        start = {
            'point': payload.get('point_start'),
            'heading': payload.get('heading_start', 0.0),
            'curvature': payload.get('curvature_start', 0.0),
            'slope': payload.get('slope_start', 0.0),
            'connected': payload.get('connected_start', False),
            'normal': payload.get('normal_start', [0.0, 0.0, 1.0]),
        }
    if end is None:
        end = {
            'point': payload.get('point_end'),
            'heading': payload.get('heading_end', 0.0),
            'curvature': payload.get('curvature_end', 0.0),
            'slope': payload.get('slope_end', 0.0),
            'connected': payload.get('connected_end', False),
        }

    start = _ensure_dict(start, 'start')
    end = _ensure_dict(end, 'end')

    if 'point' not in start or 'point' not in end:
        raise ScriptPayloadError('start.point and end.point are required')

    normalized = {
        'start': {
            'point': _parse_point(start['point'], 'start.point'),
            'heading': _to_float(start.get('heading', 0.0), 'start.heading'),
            'curvature': _to_float(start.get('curvature', 0.0), 'start.curvature'),
            'slope': _to_float(start.get('slope', 0.0), 'start.slope'),
            'connected': _parse_bool(start.get('connected'), 'start.connected', False),
            'normal': _parse_point(start.get('normal', [0.0, 0.0, 1.0]), 'start.normal'),
        },
        'end': {
            'point': _parse_point(end['point'], 'end.point'),
            'heading': _to_float(end.get('heading', 0.0), 'end.heading'),
            'curvature': _to_float(end.get('curvature', 0.0), 'end.curvature'),
            'slope': _to_float(end.get('slope', 0.0), 'end.slope'),
            'connected': _parse_bool(end.get('connected'), 'end.connected', False),
        },
        'road_properties': payload.get('road_properties'),
        'link_start': _parse_link(payload.get('link_start'), 'link_start'),
        'link_end': _parse_link(payload.get('link_end'), 'link_end'),
    }
    if normalized['link_start'] is not None:
        normalized['start']['connected'] = True
    if normalized['link_end'] is not None:
        normalized['end']['connected'] = True
    return normalized


def _apply_scalar_overrides(prop_group, overrides, fields):
    for field in fields:
        if field in overrides:
            setattr(prop_group, field, overrides[field])


def _safe_default_road_mark_width(weight, width_line_standard, width_line_bold):
    if weight == 'bold':
        return width_line_bold
    if weight == 'standard':
        return width_line_standard
    return 0.0


def _apply_explicit_lanes(prop_group, lanes):
    lanes = _ensure_list(lanes, 'road_properties.lanes')
    if len(lanes) == 0:
        raise ScriptPayloadError('road_properties.lanes must not be empty')

    prop_group.lock_lanes = True
    prop_group.clear_lanes()
    num_lanes_left = 0
    num_lanes_right = 0
    has_center_lane = False

    for idx, lane in enumerate(lanes):
        lane = _ensure_dict(lane, f'road_properties.lanes[{idx}]')
        side = str(lane.get('side', 'right'))
        lane_type = str(lane.get('type', 'driving'))
        width_start = _to_float(lane.get('width_start', 3.5), f'road_properties.lanes[{idx}].width_start')
        width_end = _to_float(lane.get('width_end', width_start), f'road_properties.lanes[{idx}].width_end')
        road_mark_type = str(lane.get('road_mark_type', 'none'))
        road_mark_weight = str(lane.get('road_mark_weight', 'none'))
        road_mark_color = str(lane.get('road_mark_color', 'none'))
        if 'road_mark_width' in lane:
            road_mark_width = _to_float(lane['road_mark_width'], f'road_properties.lanes[{idx}].road_mark_width')
        else:
            road_mark_width = _safe_default_road_mark_width(
                road_mark_weight,
                prop_group.width_line_standard,
                prop_group.width_line_bold,
            )

        if side == 'left':
            num_lanes_left += 1
        elif side == 'right':
            num_lanes_right += 1
        elif side == 'center':
            has_center_lane = True
            width_start = 0.0
            width_end = 0.0
        else:
            raise ScriptPayloadError(f'road_properties.lanes[{idx}].side must be left/right/center')

        prop_group.add_lane(
            side,
            lane_type,
            width_start,
            width_end,
            road_mark_type,
            road_mark_weight,
            road_mark_width,
            road_mark_color,
        )

    if not has_center_lane:
        # Keep lane ordering compatible with how update_num_lanes would build it.
        prop_group.add_lane('center', 'driving', 0.0, 0.0, 'broken', 'standard', 0.12, 'white')

    prop_group.num_lanes_left = num_lanes_left
    prop_group.num_lanes_right = num_lanes_right
    prop_group.road_split_type = 'none'
    prop_group.road_split_lane_idx = max(1, num_lanes_left + num_lanes_right)
    if len(prop_group.lanes) > 0:
        prop_group.lanes[-1].split_right = True
    prop_group.lock_lanes = False


def apply_road_properties(prop_group, overrides):
    if len(prop_group.lanes) == 0:
        prop_group.init()
    if overrides is None:
        return

    overrides = _ensure_dict(overrides, 'road_properties')
    if 'cross_section_preset' in overrides:
        prop_group.cross_section_preset = str(overrides['cross_section_preset'])
        prop_group.update_cross_section()

    scalar_fields = [
        'width_line_standard',
        'width_line_bold',
        'length_broken_line',
        'ratio_broken_line_gap',
        'width_driving',
        'width_border',
        'width_median',
        'width_stop',
        'width_shoulder',
        'width_none',
        'design_speed',
        'lane_offset_start',
        'lane_offset_end',
        'road_split_type',
        'road_split_lane_idx',
    ]
    _apply_scalar_overrides(prop_group, overrides, scalar_fields)

    if 'num_lanes_left' in overrides:
        prop_group.num_lanes_left = _to_int(overrides['num_lanes_left'], 'road_properties.num_lanes_left')
    if 'num_lanes_right' in overrides:
        prop_group.num_lanes_right = _to_int(overrides['num_lanes_right'], 'road_properties.num_lanes_right')

    if 'lanes' in overrides:
        _apply_explicit_lanes(prop_group, overrides['lanes'])


def apply_connecting_road_setup(context, setup):
    if setup is None:
        return
    setup = _ensure_dict(setup, 'connecting_road_setup')

    if 'joint_side_start' not in setup:
        raise ScriptPayloadError('connecting_road_setup.joint_side_start is required')
    if 'width_start' not in setup or 'width_end' not in setup:
        raise ScriptPayloadError('connecting_road_setup.width_start and width_end are required')

    joint_side_start = str(setup['joint_side_start'])
    if joint_side_start not in {'left', 'right'}:
        raise ScriptPayloadError('connecting_road_setup.joint_side_start must be left or right')
    road_contact_point = str(setup.get('road_contact_point', 'start'))
    if road_contact_point not in {'start', 'end'}:
        raise ScriptPayloadError('connecting_road_setup.road_contact_point must be start or end')

    width_start = _to_float(setup['width_start'], 'connecting_road_setup.width_start')
    width_end = _to_float(setup['width_end'], 'connecting_road_setup.width_end')
    helpers.set_connecting_road_properties(
        context,
        joint_side_start,
        road_contact_point,
        width_start,
        width_end,
    )


def _default_heading_from_points(point_start, point_end):
    vector = (point_end - point_start).to_2d()
    if vector.length == 0:
        return 0.0
    return vector.angle_signed(Vector((1.0, 0.0)))


def _apply_link(obj, link_type, link_data):
    if link_data is None:
        return
    helpers.create_object_xodr_links(
        obj,
        link_type,
        link_data['cp_type'],
        link_data['id_obj'],
        link_data['id_extra'],
        link_data['id_lane'],
    )


def execute_scripted_road(operator, context, normalized_payload):
    if operator.object_type == 'junction_connecting_road':
        apply_road_properties(
            context.scene.dsc_properties.connecting_road_properties,
            normalized_payload.get('connecting_road_properties'),
        )
        apply_connecting_road_setup(context, normalized_payload.get('connecting_road_setup'))
        property_group = context.scene.dsc_properties.connecting_road_properties
    else:
        apply_road_properties(
            context.scene.dsc_properties.road_properties,
            normalized_payload.get('road_properties'),
        )
        property_group = context.scene.dsc_properties.road_properties

    operator.reset_geometry()
    operator.reset_params_input()

    start = normalized_payload['start']
    start_point = Vector(start['point'])
    operator.params_input['points'] = [start_point.copy(), start_point.copy()]
    operator.params_input['heading_start'] = start['heading']
    operator.params_input['curvature_start'] = start['curvature']
    operator.params_input['slope_start'] = start['slope']
    operator.params_input['normal_start'] = Vector(start['normal'])
    operator.params_input['connected_start'] = bool(start['connected'])

    design_speed = start.get('design_speed')
    if design_speed is None:
        operator.params_input['design_speed'] = property_group.design_speed
    else:
        operator.params_input['design_speed'] = _to_float(design_speed, 'start.design_speed')

    points = operator.params_input['points']
    for idx, section in enumerate(normalized_payload['sections']):
        if idx > 0:
            operator.add_geometry_section()
            points.append(points[-1].copy())
        end_point = Vector(section['point'])
        points[-1] = end_point
        if section['heading_end'] is None:
            operator.params_input['heading_end'] = _default_heading_from_points(points[-2], points[-1])
        else:
            operator.params_input['heading_end'] = section['heading_end']
        operator.params_input['curvature_end'] = section['curvature_end']
        operator.params_input['slope_end'] = section['slope_end']
        operator.params_input['connected_end'] = bool(section['connected_end'])

    obj = operator.create_object_3d(context)
    if obj is None:
        raise ScriptPayloadError('No valid road geometry solution found for script payload')

    _apply_link(obj, 'start', normalized_payload.get('link_start'))
    link_end = normalized_payload['sections'][-1].get('link_end') or normalized_payload.get('link_end')
    _apply_link(obj, 'end', link_end)

    return obj


def execute_scripted_two_point_operator(operator, context, normalized_payload):
    apply_road_properties(
        context.scene.dsc_properties.road_properties,
        normalized_payload.get('road_properties'),
    )

    operator.reset_params_input()
    start = normalized_payload['start']
    end = normalized_payload['end']

    operator.params_input['point_start'] = Vector(start['point'])
    operator.params_input['point_end'] = Vector(end['point'])
    operator.params_input['heading_start'] = start['heading']
    operator.params_input['heading_end'] = end['heading']
    operator.params_input['curvature_start'] = start['curvature']
    operator.params_input['curvature_end'] = end['curvature']
    operator.params_input['slope_start'] = start['slope']
    operator.params_input['slope_end'] = end['slope']
    operator.params_input['normal_start'] = Vector(start['normal'])
    operator.params_input['connected_start'] = bool(start['connected'])
    operator.params_input['connected_end'] = bool(end['connected'])
    operator.params_input['design_speed'] = context.scene.dsc_properties.road_properties.design_speed

    obj = operator.create_object_3d(context)
    if obj is None:
        raise ScriptPayloadError('No valid geometry solution found for script payload')

    _apply_link(obj, 'start', normalized_payload.get('link_start'))
    _apply_link(obj, 'end', normalized_payload.get('link_end'))

    return obj


def make_link(cp_type, id_obj, id_extra=None, id_lane=None):
    payload = {'cp_type': cp_type, 'id_obj': id_obj}
    if id_extra is not None:
        payload['id_extra'] = id_extra
    if id_lane is not None:
        payload['id_lane'] = id_lane
    return payload


def make_road_section(point, heading_end=None, curvature_end=0.0, slope_end=0.0, connected_end=False, link_end=None):
    section = {
        'point': list(point),
        'curvature_end': curvature_end,
        'slope_end': slope_end,
        'connected_end': connected_end,
    }
    if heading_end is not None:
        section['heading_end'] = heading_end
    if link_end is not None:
        section['link_end'] = link_end
    return section


def make_road_payload(start_point, start_heading, sections, start_curvature=0.0, start_slope=0.0,
                      start_connected=False, start_normal=(0.0, 0.0, 1.0), road_properties=None,
                      link_start=None, link_end=None, connecting_road_properties=None,
                      connecting_road_setup=None):
    payload = {
        'start': {
            'point': list(start_point),
            'heading': start_heading,
            'curvature': start_curvature,
            'slope': start_slope,
            'connected': start_connected,
            'normal': list(start_normal),
        },
        'sections': sections,
    }
    if road_properties is not None:
        payload['road_properties'] = road_properties
    if connecting_road_properties is not None:
        payload['connecting_road_properties'] = connecting_road_properties
    if connecting_road_setup is not None:
        payload['connecting_road_setup'] = connecting_road_setup
    if link_start is not None:
        payload['link_start'] = link_start
    if link_end is not None:
        payload['link_end'] = link_end
    return payload


def make_two_point_payload(point_start, point_end, heading_start=0.0, heading_end=0.0,
                           curvature_start=0.0, curvature_end=0.0,
                           slope_start=0.0, slope_end=0.0, connected_start=False,
                           connected_end=False, normal_start=(0.0, 0.0, 1.0),
                           road_properties=None, link_start=None, link_end=None):
    payload = {
        'start': {
            'point': list(point_start),
            'heading': heading_start,
            'curvature': curvature_start,
            'slope': slope_start,
            'connected': connected_start,
            'normal': list(normal_start),
        },
        'end': {
            'point': list(point_end),
            'heading': heading_end,
            'curvature': curvature_end,
            'slope': slope_end,
            'connected': connected_end,
        },
    }
    if road_properties is not None:
        payload['road_properties'] = road_properties
    if link_start is not None:
        payload['link_start'] = link_start
    if link_end is not None:
        payload['link_end'] = link_end
    return payload


def payload_to_json(payload):
    return json.dumps(payload)


def call_scripted_operator(operator_callable, payload, **kwargs):
    return operator_callable(script_payload=payload_to_json(payload), **kwargs)
