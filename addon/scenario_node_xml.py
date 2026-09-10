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
        if node.get('speed_target_type', 'absolute') == 'relative':
            return xosc.RelativeSpeedAction(
                node['speed'],
                node['target_entity_ref'],
                _transition(node),
            )
        return xosc.AbsoluteSpeedAction(node['speed'], _transition(node))
    if action_type == 'lane_change':
        if node.get('lane_change_target', 'absolute') == 'relative':
            return xosc.RelativeLaneChangeAction(
                node['target_lane'],
                node['entity_ref'],
                _transition(node),
            )
        return xosc.AbsoluteLaneChangeAction(node['target_lane'], _transition(node))
    if action_type == 'lane_offset':
        duration = node.get('duration', 0.0)
        max_lateral_acc = node['max_lateral_acc']
        if duration > 0.0 and node['offset'] != 0.0:
            max_lateral_acc = 4.0 * abs(node['offset']) / (duration ** 2)
        return xosc.AbsoluteLaneOffsetAction(
            node['offset'],
            _enum(xosc.DynamicsShapes, node['dynamics_shape']),
            max_lateral_acc,
            False,
        )
    if action_type == 'longitudinal_distance':
        optional_limits = (
            'max_acceleration', 'max_deceleration', 'max_speed',
            'max_acceleration_rate', 'max_deceleration_rate',
        )
        limits = {
            key: (node.get(key) or None)
            for key in optional_limits
        }
        return xosc.LongitudinalDistanceAction(
            node['target_entity_ref'],
            freespace=node.get('freespace', True),
            continuous=node.get('continuous', True),
            max_acceleration=limits['max_acceleration'],
            max_deceleration=limits['max_deceleration'],
            max_speed=limits['max_speed'],
            distance=node['distance'] if node.get('distance_target_type', 'distance') == 'distance' else None,
            timeGap=node.get('time_gap') if node.get('distance_target_type', 'distance') == 'time_gap' else None,
            coordinate_system=_enum(xosc.CoordinateSystem, node.get('coordinate_system', 'entity')),
            displacement=_enum(xosc.LongitudinalDisplacement, node.get('displacement', 'any')),
            max_acceleration_rate=limits['max_acceleration_rate'],
            max_deceleration_rate=limits['max_deceleration_rate'],
        )
    if action_type == 'user_defined':
        return xosc.UserDefinedAction(xosc.CustomCommandAction(node['command_type'], ''))
    raise ValueError('Unsupported action type: {}'.format(action_type))


def _trigger(condition, name, triggeringpoint='start', condition_edge=None):
    if condition.get('type') == 'or':
        trigger = xosc.Trigger(triggeringpoint)
        for index, child_condition in enumerate(condition['conditions']):
            group = xosc.ConditionGroup(triggeringpoint)
            group.add_condition(_trigger(
                child_condition,
                '{}_{}'.format(name, index),
                triggeringpoint=triggeringpoint,
                condition_edge=condition_edge,
            ))
            trigger.add_conditiongroup(group)
        return trigger
    if condition.get('type') == 'and':
        group = xosc.ConditionGroup(triggeringpoint)
        for index, child_condition in enumerate(condition['conditions']):
            if child_condition.get('type') in ('and', 'or'):
                raise ValueError('Nested trigger logic is not supported inside Trigger AND')
            group.add_condition(_trigger(
                child_condition,
                '{}_{}'.format(name, index),
                triggeringpoint=triggeringpoint,
                condition_edge='none',
            ))
        trigger = xosc.Trigger(triggeringpoint)
        trigger.add_conditiongroup(group)
        return trigger
    if condition.get('type') == 'event_complete':
        value_condition = xosc.StoryboardElementStateCondition(
            xosc.StoryboardElementType.event,
            condition['event_ref'],
            xosc.StoryboardElementState.completeState,
        )
        edge = xosc.ConditionEdge.rising
        if condition_edge is not None:
            edge = _enum(xosc.ConditionEdge, condition_edge)
    else:
        rule = condition.get('rule', 'greaterOrEqual')
        if rule == 'greaterThanOrEqualTo':
            rule = 'greaterOrEqual'
        value_condition = xosc.SimulationTimeCondition(
            condition.get('value', 0.0),
            _enum(xosc.Rule, rule),
        )
        edge = xosc.ConditionEdge.none
    return xosc.ValueTrigger(name, 0, edge, value_condition, triggeringpoint=triggeringpoint)


def _ordered_nodes(nodes):
    by_name = {node['name']: node for node in nodes}
    if len(by_name) != len(nodes):
        raise ValueError('Scenario action nodes must have unique action names')
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


def _or_conditions(condition):
    if condition.get('type') != 'or':
        return [condition]
    conditions = []
    for child in condition['conditions']:
        conditions.extend(_or_conditions(child))
    return conditions


def _story(nodes, story_name):
    entity_refs = sorted({node.get('entity_ref', '') for node in nodes})
    if any(not entity_ref or entity_ref == '__NONE__' for entity_ref in entity_refs):
        raise ValueError('Every action node must select an existing entity')
    for node in nodes:
        if node['action_type'] == 'absolute_speed' and node.get('speed_target_type', 'absolute') == 'relative':
            target_entity_ref = node.get('target_entity_ref', '')
            if not target_entity_ref or target_entity_ref == '__NONE__':
                raise ValueError('Every relative speed action must select a target entity')
        if node['action_type'] == 'longitudinal_distance':
            target_entity_ref = node.get('target_entity_ref', '')
            if not target_entity_ref or target_entity_ref == '__NONE__':
                raise ValueError('Every longitudinal distance action must select a target entity')
    story = xosc.Story(story_name)
    ordered_nodes = _ordered_nodes(nodes)
    for node in ordered_nodes:
        condition = node.get('trigger')
        if condition is None:
            condition = {'type': 'simulation_time', 'value': 0.0}
        stop_trigger = None
        if node.get('continuous') and node.get('duration', 0.0) > 0.0:
            stop_condition = xosc.StoryboardElementStateCondition(
                xosc.StoryboardElementType.event,
                node['name'],
                xosc.StoryboardElementState.startTransition,
            )
            stop_trigger = xosc.ValueTrigger(
                '{}_stop'.format(node['name']),
                node['duration'],
                xosc.ConditionEdge.none,
                stop_condition,
                triggeringpoint='stop',
            )
        act = xosc.Act(
            'NodeAct_{}'.format(node['name']),
            _trigger(condition, '{}_start'.format(node['name'])),
            stop_trigger,
        )
        group = xosc.ManeuverGroup('NodeManeuverGroup_{}'.format(node['name']), maxexecution=1)
        group.add_actor(node['entity_ref'])
        maneuver = xosc.Maneuver('NodeManeuver_{}'.format(node['name']))
        event = xosc.Event(
            node['name'],
            _enum(xosc.Priority, node.get('priority', 'override')),
            maxexecution=1,
        )
        event.add_trigger(_trigger(
            {'type': 'simulation_time', 'value': 0.0},
            '{}_event_start'.format(node['name']),
        ))
        event.add_action('{}_action'.format(node['name']), _action(node))
        maneuver.add_event(event)
        group.add_maneuver(maneuver)
        act.add_maneuver_group(group)
        story.add_act(act)
    return story


def append_storyboard(root, nodes, story_name='NodeActions', stop_condition=None):
    """Append a scenariogeneration-built Story to an OpenSCENARIO root."""
    if not nodes and stop_condition is None:
        return root
    storyboard = root.find('Storyboard')
    if storyboard is None:
        storyboard = ET.SubElement(root, 'Storyboard')
    if nodes:
        storyboard.append(_story(nodes, story_name).get_element())
    if stop_condition is not None:
        existing_stop = storyboard.find('StopTrigger')
        if existing_stop is not None:
            storyboard.remove(existing_stop)
        conditions = stop_condition if isinstance(stop_condition, list) else [stop_condition]
        stop_trigger = xosc.Trigger('stop')
        flattened_conditions = []
        for condition in conditions:
            flattened_conditions.extend(_or_conditions(condition))
        for index, condition in enumerate(flattened_conditions):
            if condition.get('type') == 'and':
                nested_trigger = _trigger(
                    condition,
                    '{}_stop_{}'.format(story_name, index),
                    triggeringpoint='stop',
                )
                for group in nested_trigger.conditiongroups:
                    stop_trigger.add_conditiongroup(group)
                continue
            group = xosc.ConditionGroup('stop')
            group.add_condition(_trigger(
                condition,
                '{}_stop_{}'.format(story_name, index),
                triggeringpoint='stop',
                condition_edge='none',
            ))
            stop_trigger.add_conditiongroup(group)
        storyboard.append(stop_trigger.get_element())
    return root


def serialize_storyboard(nodes, story_name='NodeActions', stop_condition=None):
    root = ET.Element('OpenSCENARIO')
    append_storyboard(root, nodes, story_name, stop_condition)
    return ET.tostring(root, encoding='unicode')
