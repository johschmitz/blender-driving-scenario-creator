import importlib.util
import pathlib
import xml.etree.ElementTree as ET

import pytest


MODULE_PATH = pathlib.Path(__file__).parents[1] / 'addon' / 'scenario_node_xml.py'
SPEC = importlib.util.spec_from_file_location('scenario_node_xml', MODULE_PATH)
scenario_node_xml = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scenario_node_xml)


def node(name, action_type, next_name='', **values):
    data = {
        'name': name,
        'action_type': action_type,
        'next': next_name,
        'priority': 'override',
        'entity_ref': 'TestEntity',
        'target_entity_ref': 'TargetEntity',
        'dynamics_shape': 'step',
        'dynamics_dimension': 'time',
        'dynamics_value': 1.0,
        'speed': 12.0,
        'speed_target_type': 'absolute',
        'lane_change_target': 'absolute',
        'target_lane': 1,
        'offset': 0.5,
        'max_lateral_acc': 2.0,
        'continuous': False,
        'x': 1.0,
        'y': 2.0,
        'z': 0.0,
        'heading': 0.0,
        'distance': 10.0,
        'distance_type': 'cartesianDistance',
        'activate_longitudinal': True,
        'activate_lateral': True,
        'command_type': 'horn',
    }
    data.update(values)
    return data


def test_storyboard_orders_actions():
    xml = scenario_node_xml.serialize_storyboard([
        node('Brake', 'absolute_speed', 'LaneChange', speed=0.0),
        node('LaneChange', 'lane_change', target_lane=2),
    ])
    root = ET.fromstring(xml)
    events = root.findall('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event')
    assert [event.attrib['name'] for event in events] == ['Brake', 'LaneChange']
    assert all(event.attrib['maximumExecutionCount'] == '1' for event in events)
    assert events[0].find('.//AbsoluteTargetSpeed').attrib['value'] == '0.0'
    assert events[0].find('.//LongitudinalAction/SpeedAction/SpeedActionDynamics') is not None
    lane_change = events[1].find('.//LaneChangeAction')
    assert lane_change is not None
    assert lane_change.find('LaneChangeActionDynamics') is not None
    assert lane_change.find('LaneChangeTarget/AbsoluteTargetLane').attrib['value'] == '2'
    assert events[1].find('.//LateralAction/LaneChangeAction') is not None


def test_unconnected_actions_start_in_parallel():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Speed', 'absolute_speed'),
        node('LaneChange', 'lane_change'),
    ]))
    conditions = root.findall('./Storyboard/Story/Act/StartTrigger/ConditionGroup/Condition')
    assert len(conditions) == 2
    assert all(condition.find('./ByValueCondition/SimulationTimeCondition').attrib == {
        'value': '0.0', 'rule': 'greaterOrEqual',
    } for condition in conditions)


def test_connected_speed_then_lane_change_uses_completion_trigger():
    xml = scenario_node_xml.serialize_storyboard([
        node('Speed', 'absolute_speed'),
        node('LaneChange', 'lane_change', trigger={
            'type': 'event_complete', 'event_ref': 'Speed',
        }),
    ])
    root = ET.fromstring(xml)
    acts = root.findall('./Storyboard/Story/Act')
    state = acts[1].find(
        './StartTrigger/ConditionGroup/Condition/ByValueCondition/'
        'StoryboardElementStateCondition'
    )
    assert state.attrib == {
        'storyboardElementType': 'event',
        'storyboardElementRef': 'Speed',
        'state': 'completeState',
    }


def test_storyboard_rejects_cycles():
    with pytest.raises(ValueError, match='cycle'):
        scenario_node_xml.serialize_storyboard([
            node('A', 'absolute_speed', 'B'),
            node('B', 'user_defined', 'A'),
        ])


def test_storyboard_rejects_duplicate_action_names():
    with pytest.raises(ValueError, match='unique action names'):
        scenario_node_xml.serialize_storyboard([
            node('Action', 'absolute_speed'),
            node('Action', 'lane_change'),
        ])


def test_storyboard_rejects_unselected_entity():
    with pytest.raises(ValueError, match='select an existing entity'):
        scenario_node_xml.serialize_storyboard([
            node('Speed', 'absolute_speed', entity_ref='__NONE__'),
        ])


def test_storyboard_rejects_unselected_distance_target():
    with pytest.raises(ValueError, match='target entity'):
        scenario_node_xml.serialize_storyboard([
            node('Distance', 'longitudinal_distance', target_entity_ref='__NONE__'),
        ])


def test_lane_offset_uses_lateral_action_schema():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Offset', 'lane_offset'),
    ]))
    action = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/Action')
    assert action.find('.//LateralAction/LaneOffsetAction/LaneOffsetActionDynamics') is not None
    assert action.find('.//LateralAction/LaneOffsetAction/LaneOffsetTarget/AbsoluteTargetLaneOffset') is not None


def test_lane_offset_duration_calculates_lateral_acceleration():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Offset', 'lane_offset', offset=1.0, duration=2.0),
    ]))
    action = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/Action')
    lane_offset = action.find('.//LaneOffsetAction')
    dynamics = lane_offset.find('LaneOffsetActionDynamics')
    assert lane_offset.attrib['continuous'] == 'false'
    assert dynamics.attrib['maxLateralAcc'] == '1.0'


def test_relative_lane_change_uses_reference_entity():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('RelativeChange', 'lane_change', lane_change_target='relative', target_lane=-1),
    ]))
    action = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/Action')
    target = action.find('.//RelativeTargetLane')
    assert target.attrib == {'value': '-1', 'entityRef': 'TestEntity'}


def test_relative_speed_uses_relative_target_speed():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Speed', 'absolute_speed', speed_target_type='relative', speed=4.0),
    ]))
    action = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/Action')
    target = action.find('.//RelativeTargetSpeed')
    assert target.attrib == {
        'entityRef': 'TargetEntity',
        'value': '4.0',
        'speedTargetValueType': 'delta',
        'continuous': 'true',
    }


def test_longitudinal_distance_uses_library_action_schema():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Distance', 'longitudinal_distance'),
    ]))
    action = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/Action')
    distance = action.find('.//LongitudinalDistanceAction')
    assert distance.attrib['entityRef'] == 'TargetEntity'
    assert distance.attrib['distance'] == '10.0'
    assert distance.attrib['coordinateSystem'] == 'entity'
    actors = root.findall('./Storyboard/Story/Act/ManeuverGroup/Actors/EntityRef')
    assert [actor.attrib['entityRef'] for actor in actors] == ['TestEntity']


def test_continuous_action_duration_adds_delayed_stop_trigger():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Offset', 'lane_offset', continuous=True, duration=5.0),
    ]))
    stop_condition = root.find('./Storyboard/Story/Act/StopTrigger/ConditionGroup/Condition')
    assert stop_condition.attrib['delay'] == '5.0'
    state = stop_condition.find('./ByValueCondition/StoryboardElementStateCondition')
    assert state.attrib == {
        'storyboardElementType': 'event',
        'storyboardElementRef': 'Offset',
        'state': 'startTransition',
    }


def test_non_continuous_action_does_not_get_duration_stop_trigger():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Offset', 'lane_offset', continuous=False, duration=5.0),
    ]))
    assert root.find('./Storyboard/Story/Act/StopTrigger') is not None
    assert root.find('./Storyboard/Story/Act/StopTrigger/ConditionGroup') is None


def test_scenario_stop_trigger_replaces_storyboard_stop_trigger():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard(
        [node('Speed', 'absolute_speed')],
        stop_condition={'type': 'simulation_time', 'value': 20.0, 'rule': 'greaterThan'},
    ))
    stop_condition = root.find('./Storyboard/StopTrigger/ConditionGroup/Condition')
    assert stop_condition.attrib['name'] == 'NodeActions_stop_0'
    simulation_time = stop_condition.find('./ByValueCondition/SimulationTimeCondition')
    assert simulation_time.attrib == {'value': '20.0', 'rule': 'greaterThan'}


def test_scenario_stop_trigger_can_follow_last_action():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard(
        [node('LastAction', 'absolute_speed')],
        stop_condition={'type': 'event_complete', 'event_ref': 'LastAction'},
    ))
    stop_condition = root.find('./Storyboard/StopTrigger/ConditionGroup/Condition')
    state = stop_condition.find('./ByValueCondition/StoryboardElementStateCondition')
    assert state.attrib == {
        'storyboardElementType': 'event',
        'storyboardElementRef': 'LastAction',
        'state': 'completeState',
    }


def test_scenario_stop_trigger_uses_time_or_last_action():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard(
        [node('LastAction', 'absolute_speed')],
        stop_condition=[
            {'type': 'simulation_time', 'value': 60.0, 'rule': 'greaterThan'},
            {'type': 'event_complete', 'event_ref': 'LastAction'},
        ],
    ))
    groups = root.findall('./Storyboard/StopTrigger/ConditionGroup')
    assert len(groups) == 2
    assert groups[0].find('./Condition/ByValueCondition/SimulationTimeCondition').attrib == {
        'value': '60.0', 'rule': 'greaterThan',
    }
    assert groups[1].find('./Condition/ByValueCondition/StoryboardElementStateCondition').attrib['state'] == 'completeState'


def test_or_trigger_uses_separate_condition_groups():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Speed', 'absolute_speed'),
    ], stop_condition={
        'type': 'or',
        'conditions': [
            {'type': 'simulation_time', 'value': 5.0, 'rule': 'greaterThan'},
            {'type': 'event_complete', 'event_ref': 'Speed'},
        ],
    }))
    groups = root.findall('./Storyboard/StopTrigger/ConditionGroup')
    assert len(groups) == 2
    assert groups[0].find('./Condition/ByValueCondition/SimulationTimeCondition').attrib == {
        'value': '5.0', 'rule': 'greaterThan',
    }
    assert groups[1].find('./Condition/ByValueCondition/StoryboardElementStateCondition').attrib['storyboardElementRef'] == 'Speed'


def test_and_trigger_uses_one_condition_group():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Speed', 'absolute_speed'),
    ], stop_condition={
        'type': 'and',
        'conditions': [
            {'type': 'simulation_time', 'value': 5.0, 'rule': 'greaterThan'},
            {'type': 'event_complete', 'event_ref': 'Speed'},
        ],
    }))
    groups = root.findall('./Storyboard/StopTrigger/ConditionGroup')
    assert len(groups) == 1
    assert len(groups[0].findall('Condition')) == 2


def test_and_trigger_starts_action_only_after_all_conditions():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Speed', 'absolute_speed', trigger={
            'type': 'and',
            'conditions': [
                {'type': 'simulation_time', 'value': 1.0, 'rule': 'greaterOrEqual'},
                {'type': 'simulation_time', 'value': 5.0, 'rule': 'greaterOrEqual'},
            ],
        }),
    ]))
    group = root.find('./Storyboard/Story/Act/StartTrigger/ConditionGroup')
    conditions = group.findall('Condition')
    assert len(conditions) == 2
    assert [condition.find('./ByValueCondition/SimulationTimeCondition').attrib['value']
            for condition in conditions] == ['1.0', '5.0']


def test_and_trigger_waits_for_two_completed_actions():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Third', 'lane_change', trigger={
            'type': 'and',
            'conditions': [
                {'type': 'event_complete', 'event_ref': 'First'},
                {'type': 'event_complete', 'event_ref': 'Second'},
            ],
        }),
    ]))
    conditions = root.findall('./Storyboard/Story/Act/StartTrigger/ConditionGroup/Condition')
    assert [condition.find('./ByValueCondition/StoryboardElementStateCondition').attrib['storyboardElementRef']
            for condition in conditions] == ['First', 'Second']
    assert [condition.attrib['conditionEdge'] for condition in conditions] == ['none', 'none']


def test_or_trigger_starts_after_either_completed_action():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Third', 'lane_change', trigger={
            'type': 'or',
            'conditions': [
                {'type': 'event_complete', 'event_ref': 'First'},
                {'type': 'event_complete', 'event_ref': 'Second'},
            ],
        }),
    ]))
    groups = root.findall('./Storyboard/Story/Act/StartTrigger/ConditionGroup')
    assert [group.find('./Condition/ByValueCondition/StoryboardElementStateCondition').attrib['storyboardElementRef']
            for group in groups] == ['First', 'Second']


def test_logic_trigger_conditions_are_on_downstream_action_act():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Speed', 'absolute_speed', trigger={
            'type': 'or',
            'conditions': [
                {'type': 'simulation_time', 'value': 1.0, 'rule': 'greaterOrEqual'},
                {'type': 'simulation_time', 'value': 5.0, 'rule': 'greaterOrEqual'},
            ],
        }),
    ]))
    groups = root.findall('./Storyboard/Story/Act/StartTrigger/ConditionGroup')
    assert len(groups) == 2


def test_explicit_simulation_time_trigger_starts_action():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('LaneChange', 'lane_change', trigger={
            'type': 'simulation_time', 'value': 4.5, 'rule': 'greaterThan',
        }),
    ]))
    condition = root.find('./Storyboard/Story/Act/StartTrigger/ConditionGroup/Condition')
    assert condition.attrib['conditionEdge'] == 'none'
    simulation_time = condition.find('./ByValueCondition/SimulationTimeCondition')
    assert simulation_time.attrib == {'value': '4.5', 'rule': 'greaterThan'}


def test_default_simulation_time_trigger_uses_esmini_rule_name():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('LaneChange', 'lane_change'),
    ]))
    condition = root.find('./Storyboard/Story/Act/StartTrigger/ConditionGroup/Condition')
    simulation_time = condition.find('./ByValueCondition/SimulationTimeCondition')
    assert simulation_time.attrib == {'value': '0.0', 'rule': 'greaterOrEqual'}


def test_legacy_greater_than_or_equal_rule_is_normalized():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('LaneChange', 'lane_change', trigger={
            'type': 'simulation_time', 'value': 4.5, 'rule': 'greaterThanOrEqualTo',
        }),
    ]))
    condition = root.find('./Storyboard/Story/Act/StartTrigger/ConditionGroup/Condition')
    simulation_time = condition.find('./ByValueCondition/SimulationTimeCondition')
    assert simulation_time.attrib == {'value': '4.5', 'rule': 'greaterOrEqual'}


def test_explicit_previous_action_trigger_starts_action():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('First', 'absolute_speed'),
        node('Second', 'lane_change', trigger={
            'type': 'event_complete', 'event_ref': 'First',
        }),
    ]))
    condition = root.findall('./Storyboard/Story/Act')[1]
    state = condition.find('./StartTrigger/ConditionGroup/Condition/ByValueCondition/StoryboardElementStateCondition')
    assert state.attrib['storyboardElementRef'] == 'First'
    assert state.attrib['state'] == 'completeState'
