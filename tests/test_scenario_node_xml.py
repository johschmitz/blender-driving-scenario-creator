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
        'dynamics_shape': 'step',
        'dynamics_dimension': 'time',
        'dynamics_value': 1.0,
        'speed': 12.0,
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


def test_storyboard_orders_connected_actions():
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


def test_storyboard_rejects_cycles():
    with pytest.raises(ValueError, match='cycle'):
        scenario_node_xml.serialize_storyboard([
            node('A', 'absolute_speed', 'B'),
            node('B', 'user_defined', 'A'),
        ])


def test_storyboard_rejects_unselected_entity():
    with pytest.raises(ValueError, match='select an existing entity'):
        scenario_node_xml.serialize_storyboard([
            node('Speed', 'absolute_speed', entity_ref='__NONE__'),
        ])


def test_lane_offset_uses_lateral_action_schema():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Offset', 'lane_offset'),
    ]))
    action = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/Action')
    assert action.find('.//LateralAction/LaneOffsetAction/LaneOffsetActionDynamics') is not None
    assert action.find('.//LateralAction/LaneOffsetAction/LaneOffsetTarget/AbsoluteTargetLaneOffset') is not None


def test_longitudinal_distance_uses_library_action_schema():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('Distance', 'longitudinal_distance'),
    ]))
    action = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/Action')
    distance = action.find('.//LongitudinalDistanceAction')
    assert distance.attrib['entityRef'] == 'TestEntity'
    assert distance.attrib['distance'] == '10.0'
    assert distance.attrib['coordinateSystem'] == 'entity'


def test_explicit_simulation_time_trigger_starts_action():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('LaneChange', 'lane_change', trigger={
            'type': 'simulation_time', 'value': 4.5, 'rule': 'greaterThan',
        }),
    ]))
    condition = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/StartTrigger/ConditionGroup/Condition')
    assert condition.attrib['conditionEdge'] == 'none'
    simulation_time = condition.find('./ByValueCondition/SimulationTimeCondition')
    assert simulation_time.attrib == {'value': '4.5', 'rule': 'greaterThan'}


def test_default_simulation_time_trigger_uses_esmini_rule_name():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('LaneChange', 'lane_change'),
    ]))
    condition = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/StartTrigger/ConditionGroup/Condition')
    simulation_time = condition.find('./ByValueCondition/SimulationTimeCondition')
    assert simulation_time.attrib == {'value': '0.0', 'rule': 'greaterOrEqual'}


def test_legacy_greater_than_or_equal_rule_is_normalized():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('LaneChange', 'lane_change', trigger={
            'type': 'simulation_time', 'value': 4.5, 'rule': 'greaterThanOrEqualTo',
        }),
    ]))
    condition = root.find('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event/StartTrigger/ConditionGroup/Condition')
    simulation_time = condition.find('./ByValueCondition/SimulationTimeCondition')
    assert simulation_time.attrib == {'value': '4.5', 'rule': 'greaterOrEqual'}


def test_explicit_previous_action_trigger_starts_action():
    root = ET.fromstring(scenario_node_xml.serialize_storyboard([
        node('First', 'absolute_speed'),
        node('Second', 'lane_change', trigger={
            'type': 'event_complete', 'event_ref': 'First',
        }),
    ]))
    condition = root.findall('./Storyboard/Story/Act/ManeuverGroup/Maneuver/Event')[1]
    state = condition.find('./StartTrigger/ConditionGroup/Condition/ByValueCondition/StoryboardElementStateCondition')
    assert state.attrib['storyboardElementRef'] == 'First'
    assert state.attrib['state'] == 'completeState'
