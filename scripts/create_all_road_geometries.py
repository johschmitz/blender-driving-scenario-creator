import importlib

import addon_utils
import bpy


def _find_dsc_module_name():
    for mod in addon_utils.modules():
        bl_info = getattr(mod, 'bl_info', None)
        if bl_info and bl_info.get('name') == 'Driving Scenario Creator':
            return mod.__name__
    raise RuntimeError('Driving Scenario Creator add-on is not enabled')


def _get_script_api():
    module_name = _find_dsc_module_name()
    return importlib.import_module(module_name + '.script_api')


def _active_object_or_fail(expected_prefix):
    obj = bpy.context.view_layer.objects.active
    if obj is not None and obj.name.startswith(expected_prefix):
        return obj
    collection = bpy.data.collections.get('OpenDRIVE')
    if collection is None:
        raise RuntimeError('OpenDRIVE collection not found')
    matches = [candidate for candidate in collection.objects if candidate.name.startswith(expected_prefix)]
    if len(matches) == 0:
        raise RuntimeError('Expected object with prefix: ' + expected_prefix)
    matches.sort(key=lambda item: int(item['id_odr']) if 'id_odr' in item else -1)
    return matches[-1]


def _road_link_from_end(script_api, road_obj):
    return script_api.make_link(
        cp_type='cp_end_l',
        id_obj=road_obj['id_odr'],
        id_extra=road_obj.get('id_direct_junction_end'),
    )


def _road_link_from_start(script_api, road_obj):
    return script_api.make_link(
        cp_type='cp_start_l',
        id_obj=road_obj['id_odr'],
        id_extra=road_obj.get('id_direct_junction_start'),
    )


def _road_end_pose(road_obj):
    section = road_obj['geometry'][-1]
    return road_obj['cp_end_l'], float(section['heading_end'])


def _run_road_operator(op_name, payload, geometry_solver='default'):
    op = getattr(bpy.ops.dsc, op_name)
    return op(script_payload=payload, geometry_solver=geometry_solver)


def _run_junction_operator(op_name, payload):
    op = getattr(bpy.ops.dsc, op_name)
    return op(script_payload=payload)


def _clear_opendrive_collection():
    collection = bpy.data.collections.get('OpenDRIVE')
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def create_demo():
    script_api = _get_script_api()
    _clear_opendrive_collection()

    if len(bpy.context.scene.dsc_properties.road_properties.lanes) == 0:
        bpy.context.scene.dsc_properties.road_properties.init()
    if len(bpy.context.scene.dsc_properties.connecting_road_properties.lanes) == 0:
        bpy.context.scene.dsc_properties.connecting_road_properties.init()

    road_overrides = {
        'cross_section_preset': 'two_lanes_default',
        'design_speed': 90.0,
    }

    payload = script_api.make_road_payload(
        start_point=(0.0, 0.0, 0.0),
        start_heading=0.0,
        sections=[script_api.make_road_section(point=(80.0, 0.0, 0.0))],
        road_properties=road_overrides,
    )
    _run_road_operator('road_straight', script_api.payload_to_json(payload))
    road_straight = _active_object_or_fail('road_straight_')

    start_point, start_heading = _road_end_pose(road_straight)
    payload = script_api.make_road_payload(
        start_point=start_point,
        start_heading=start_heading,
        sections=[script_api.make_road_section(point=(115.0, 24.0, 0.0))],
        link_start=_road_link_from_end(script_api, road_straight),
        road_properties=road_overrides,
    )
    _run_road_operator('road_arc', script_api.payload_to_json(payload))
    road_arc = _active_object_or_fail('road_arc_')

    start_point, start_heading = _road_end_pose(road_arc)
    payload = script_api.make_road_payload(
        start_point=start_point,
        start_heading=start_heading,
        sections=[script_api.make_road_section(point=(150.0, 52.0, 1.0), heading_end=0.9)],
        link_start=_road_link_from_end(script_api, road_arc),
        road_properties=road_overrides,
    )
    _run_road_operator('road_clothoid', script_api.payload_to_json(payload), geometry_solver='hermite')
    road_clothoid_hermite = _active_object_or_fail('road_clothoid_')

    start_point, start_heading = _road_end_pose(road_clothoid_hermite)
    payload = script_api.make_road_payload(
        start_point=start_point,
        start_heading=start_heading,
        sections=[script_api.make_road_section(point=(190.0, 65.0, 1.0), heading_end=0.2)],
        link_start=_road_link_from_end(script_api, road_clothoid_hermite),
        road_properties=road_overrides,
    )
    _run_road_operator('road_clothoid', script_api.payload_to_json(payload), geometry_solver='forward')
    road_clothoid_forward = _active_object_or_fail('road_clothoid_')

    start_point, start_heading = _road_end_pose(road_clothoid_forward)
    payload = script_api.make_road_payload(
        start_point=start_point,
        start_heading=start_heading,
        sections=[script_api.make_road_section(point=(225.0, 40.0, 0.5), heading_end=-0.4)],
        link_start=_road_link_from_end(script_api, road_clothoid_forward),
        road_properties=road_overrides,
    )
    _run_road_operator('road_clothoid_triple', script_api.payload_to_json(payload))
    road_clothoid_triple = _active_object_or_fail('road_clothoid_triple_')

    start_point, start_heading = _road_end_pose(road_clothoid_triple)
    payload = script_api.make_road_payload(
        start_point=start_point,
        start_heading=start_heading,
        sections=[script_api.make_road_section(point=(265.0, 5.0, 0.0), heading_end=-0.7)],
        link_start=_road_link_from_end(script_api, road_clothoid_triple),
        road_properties=road_overrides,
    )
    _run_road_operator('road_parametric_polynomial', script_api.payload_to_json(payload))
    road_parampoly = _active_object_or_fail('road_parampoly3_')

    payload = script_api.make_road_payload(
        start_point=(320.0, 0.0, 0.0),
        start_heading=0.0,
        sections=[script_api.make_road_section(point=(360.0, 0.0, 0.0))],
        road_properties=road_overrides,
    )
    _run_road_operator('road_straight', script_api.payload_to_json(payload))
    road_for_junction_end = _active_object_or_fail('road_straight_')

    junction_payload = script_api.make_two_point_payload(
        point_start=road_parampoly['cp_end_l'],
        point_end=road_for_junction_end['cp_start_l'],
        heading_start=float(road_parampoly['geometry'][-1]['heading_end']),
        heading_end=float(road_for_junction_end['geometry'][0]['heading_start']),
        connected_start=True,
        connected_end=True,
        link_start=_road_link_from_end(script_api, road_parampoly),
        link_end=_road_link_from_start(script_api, road_for_junction_end),
        road_properties=road_overrides,
    )
    _run_junction_operator('junction_four_way', script_api.payload_to_json(junction_payload))
    junction = _active_object_or_fail('junction_area_')

    joint_start = junction['joints'][0]
    joint_end = junction['joints'][1]
    width_start = float(joint_start['lane_widths_right'][0]) if len(joint_start['lane_widths_right']) > 0 else 3.5
    width_end = float(joint_end['lane_widths_left'][0]) if len(joint_end['lane_widths_left']) > 0 else 3.5

    payload = script_api.make_road_payload(
        start_point=joint_start['contact_point_vec'],
        start_heading=float(joint_start['heading']),
        sections=[
            script_api.make_road_section(
                point=joint_end['contact_point_vec'],
                heading_end=float(joint_end['heading']),
                connected_end=True,
                link_end=script_api.make_link(
                    cp_type='junction_joint_open',
                    id_obj=junction['id_odr'],
                    id_extra=int(joint_end['id_joint']),
                    id_lane=1,
                ),
            )
        ],
        start_connected=True,
        link_start=script_api.make_link(
            cp_type='junction_joint_open',
            id_obj=junction['id_odr'],
            id_extra=int(joint_start['id_joint']),
            id_lane=-1,
        ),
        connecting_road_setup={
            'joint_side_start': 'right',
            'road_contact_point': 'start',
            'width_start': width_start,
            'width_end': width_end,
        },
    )
    _run_road_operator('junction_connecting_road', script_api.payload_to_json(payload), geometry_solver='hermite')
    _active_object_or_fail('junction_connecting_road_')


if __name__ == '__main__':
    create_demo()
