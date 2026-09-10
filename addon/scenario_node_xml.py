"""OpenSCENARIO action-node serialization using scenariogeneration."""

import xml.etree.ElementTree as ET

from scenariogeneration import xosc


def _enum(enum_class, value):
    return getattr(enum_class, value)


def _transition(node):
    return xosc.TransitionDynamics(
        _enum(xosc.DynamicsShapes, node['dynamics_shape']),
        _enum(xosc.DynamicsDimension, node['dynamics_dimension']),
        node['dynamics_value'],
    )


def _action(node):
    action_type = node['action_type']
    if action_type == 'absolute_speed':
        return xosc.AbsoluteSpeedAction(node['speed'], _transition(node))
    if action_type == 'lane_change':
        return xosc.AbsoluteLaneChangeAction(node['target_lane'], _transition(node))
    if action_type == 'lane_offset':
        return xosc.AbsoluteLaneOffsetAction(
            node['offset'],
            _enum(xosc.DynamicsShapes, node['dynamics_shape']),
            node['max_lateral_acc'],
            node['continuous'],
        )
    if action_type == 'longitudinal_distance':
        coordinate_system = {
            'cartesianDistance': xosc.CoordinateSystem.entity,
            'euclideanDistance': xosc.CoordinateSystem.world,
        }[node['distance_type']]
        return xosc.LongitudinalDistanceAction(
            node['entity_ref'],
            distance=node['distance'],
            coordinate_system=coordinate_system,
        )
    if action_type == 'user_defined':
        return xosc.UserDefinedAction(xosc.CustomCommandAction(node['command_type'], ''))
    raise ValueError('Unsupported action type: {}'.format(action_type))


def _trigger(condition, name):
    if condition.get('type') == 'event_complete':
        value_condition = xosc.StoryboardElementStateCondition(
            xosc.StoryboardElementType.event,
            condition['event_ref'],
            xosc.StoryboardElementState.completeState,
        )
        edge = xosc.ConditionEdge.rising
    else:
        rule = condition.get('rule', 'greaterOrEqual')
        if rule == 'greaterThanOrEqualTo':
            rule = 'greaterOrEqual'
        value_condition = xosc.SimulationTimeCondition(
            condition.get('value', 0.0),
            _enum(xosc.Rule, rule),
        )
        edge = xosc.ConditionEdge.none
    return xosc.ValueTrigger(name, 0, edge, value_condition)


def _ordered_nodes(nodes):
    by_name = {node['name']: node for node in nodes}
    incoming = {node['name']: 0 for node in nodes}
    outgoing = {node['name']: [] for node in nodes}
    for node in nodes:
        next_name = node.get('next')
        if next_name in by_name:
            outgoing[node['name']].append(next_name)
            incoming[next_name] += 1
    ready = [node['name'] for node in nodes if incoming[node['name']] == 0]
    ordered = []
    while ready:
        name = ready.pop(0)
        ordered.append(by_name[name])
        for next_name in outgoing[name]:
            incoming[next_name] -= 1
            if incoming[next_name] == 0:
                ready.append(next_name)
    if len(ordered) != len(nodes):
        raise ValueError('Scenario action nodes contain a cycle')
    return ordered


def _story(nodes, story_name):
    entity_refs = sorted({node.get('entity_ref', '') for node in nodes})
    if any(not entity_ref or entity_ref == '__NONE__' for entity_ref in entity_refs):
        raise ValueError('Every action node must select an existing entity')
    story = xosc.Story(story_name)
    story_start = _trigger(
        {'type': 'simulation_time', 'value': 0.0},
        '{}_start'.format(story_name),
    )
    act = xosc.Act('NodeAct', story_start)
    group = xosc.ManeuverGroup('NodeManeuverGroup', maxexecution=1)
    for entity_ref in sorted({node.get('entity_ref', '') for node in nodes}):
        group.add_actor(entity_ref)
    maneuver = xosc.Maneuver('NodeManeuver')
    ordered_nodes = _ordered_nodes(nodes)
    for index, node in enumerate(ordered_nodes):
        event = xosc.Event(
            node['name'],
            _enum(xosc.Priority, node.get('priority', 'override')),
            maxexecution=1,
        )
        condition = node.get('trigger')
        if condition is None:
            if index == 0:
                condition = {'type': 'simulation_time', 'value': 0.0}
            else:
                condition = {
                    'type': 'event_complete',
                    'event_ref': ordered_nodes[index - 1]['name'],
                }
        event.add_trigger(_trigger(condition, '{}_start'.format(node['name'])))
        event.add_action('{}_action'.format(node['name']), _action(node))
        maneuver.add_event(event)
    group.add_maneuver(maneuver)
    act.add_maneuver_group(group)
    story.add_act(act)
    return story


def append_storyboard(root, nodes, story_name='NodeActions'):
    """Append a scenariogeneration-built Story to an OpenSCENARIO root."""
    if not nodes:
        return root
    storyboard = root.find('Storyboard')
    if storyboard is None:
        storyboard = ET.SubElement(root, 'Storyboard')
    storyboard.append(_story(nodes, story_name).get_element())
    return root


def serialize_storyboard(nodes, story_name='NodeActions'):
    root = ET.Element('OpenSCENARIO')
    append_storyboard(root, nodes, story_name)
    return ET.tostring(root, encoding='unicode')
