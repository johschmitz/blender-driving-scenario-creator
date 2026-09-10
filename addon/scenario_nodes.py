"""Blender custom-node editor for OpenSCENARIO action graphs."""

import bpy

from .scenario_node_xml import append_storyboard


NODE_TREE_ID = 'DSC_XOSC_NodeTree'
NO_ENTITY = '__NONE__'
INITIAL_NODE_EDITOR_ZOOM = 0.3


def get_entity_items(self, context):
    del self, context
    entity_names = get_entity_names()
    items = [(NO_ENTITY, 'Select an entity', 'Choose an existing OpenSCENARIO entity')]
    items.extend((name, name, 'Use entity {}'.format(name)) for name in entity_names)
    return items


def get_entity_names():
    return sorted({
        obj.name for obj in bpy.data.objects
        if obj.get('dsc_type') == 'entity'
    })


def _node_add_menu(self, context):
    del context
    for node_class in NODE_CLASSES[1:10]:
        operator = self.layout.operator('node.add_node', text=node_class.bl_label)
        operator.type = node_class.bl_idname


class DSC_XOSC_NodeTree(bpy.types.NodeTree):
    bl_idname = NODE_TREE_ID
    bl_label = 'OpenSCENARIO Actions'
    bl_icon = 'SCENE_DATA'


class DSC_XOSC_ActionNode(bpy.types.Node):
    bl_label = 'OpenSCENARIO Action'
    bl_icon = 'ACTION'
    width = 240

    action_type: bpy.props.StringProperty(default='user_defined')
    action_name: bpy.props.StringProperty(name='Action name', default='Action')
    entity_ref: bpy.props.EnumProperty(
        name='Entity',
        description='Existing OpenSCENARIO entity controlled by this action',
        items=get_entity_items,
    )
    next_node: bpy.props.StringProperty(name='Next action', default='')
    priority: bpy.props.EnumProperty(
        name='Priority',
        items=(
            ('override', 'Override', ''),
            ('skip', 'Skip', ''),
            ('parallel', 'Parallel', ''),
        ),
        default='override',
    )
    dynamics_shape: bpy.props.EnumProperty(
        name='Shape',
        items=(('step', 'Step', ''), ('linear', 'Linear', ''), ('cubic', 'Cubic', '')),
        default='step',
    )
    dynamics_dimension: bpy.props.EnumProperty(
        name='Dimension',
        items=(('time', 'Time', ''), ('rate', 'Rate', ''), ('distance', 'Distance', '')),
        default='time',
    )
    dynamics_value: bpy.props.FloatProperty(name='Dynamics value', default=1.0, min=0.0)
    speed: bpy.props.FloatProperty(name='Speed (m/s)', default=10.0, min=0.0)
    target_lane: bpy.props.IntProperty(name='Target lane', default=0)
    offset: bpy.props.FloatProperty(name='Lane offset', default=0.0)
    max_lateral_acc: bpy.props.FloatProperty(name='Max lateral acceleration', default=2.0, min=0.0)
    continuous: bpy.props.BoolProperty(name='Continuous', default=False)
    distance: bpy.props.FloatProperty(name='Distance', default=10.0, min=0.0)
    distance_type: bpy.props.EnumProperty(
        name='Distance type', items=(('cartesianDistance', 'Cartesian', ''), ('euclideanDistance', 'Euclidean', '')),
        default='cartesianDistance')
    command_type: bpy.props.StringProperty(name='Command type', default='custom')

    def init(self, context):
        del context
        self.width = 240
        self.inputs.new('NodeSocketString', 'Trigger')
        self.outputs.new('NodeSocketString', 'Complete')
        self.outputs.new('NodeSocketString', 'Next')

    def draw_buttons(self, context, layout):
        del context
        self._draw_property(layout, 'action_name', 'Action name')
        self._draw_property(layout, 'entity_ref', 'Entity')
        if self.action_type == 'absolute_speed':
            self._draw_property(layout, 'speed', 'Speed (m/s)')
            self._draw_dynamics(layout)
        elif self.action_type == 'lane_change':
            self._draw_property(layout, 'target_lane', 'Target lane')
            self._draw_dynamics(layout)
        elif self.action_type == 'lane_offset':
            self._draw_property(layout, 'offset', 'Lane offset')
            self._draw_property(layout, 'max_lateral_acc', 'Max lateral acc.')
            self._draw_property(layout, 'continuous', 'Continuous')
            self._draw_property(layout, 'dynamics_shape', 'Shape')
        elif self.action_type == 'longitudinal_distance':
            self._draw_property(layout, 'distance', 'Distance')
            self._draw_property(layout, 'distance_type', 'Distance type')
        elif self.action_type == 'user_defined':
            self._draw_property(layout, 'command_type', 'Command type')

    def _draw_dynamics(self, layout):
        self._draw_property(layout, 'dynamics_shape', 'Shape')
        self._draw_property(layout, 'dynamics_dimension', 'Dimension')
        self._draw_property(layout, 'dynamics_value', 'Value')

    def _draw_property(self, layout, property_name, label):
        row = layout.row(align=True)
        split = row.split(factor=0.48, align=True)
        split.label(text=label)
        split.prop(self, property_name, text='')

    def to_xml_data(self):
        data = {identifier: getattr(self, identifier) for identifier in (
            'action_type', 'entity_ref', 'next_node', 'priority', 'dynamics_shape',
            'dynamics_dimension', 'dynamics_value', 'speed', 'target_lane', 'offset',
            'max_lateral_acc', 'continuous', 'distance', 'distance_type', 'command_type')}
        data['name'] = self.action_name
        data['next'] = data.pop('next_node')
        return data

    def trigger_data(self):
        trigger_socket = self.inputs.get('Trigger')
        if trigger_socket is None or not trigger_socket.links:
            return None
        source = trigger_socket.links[0].from_node
        if isinstance(source, DSC_XOSC_ActionNode):
            return {'type': 'event_complete', 'event_ref': source.action_name}
        if isinstance(source, DSC_XOSC_SimulationTimeTriggerNode):
            return {
                'type': 'simulation_time',
                'value': source.value,
                'rule': source.rule,
            }
        return None


class DSC_XOSC_SimulationTimeTriggerNode(bpy.types.Node):
    bl_idname = 'DSC_XOSC_SimulationTimeTriggerNode'
    bl_label = 'Simulation Time Trigger'
    bl_icon = 'TIME'
    width = 240

    value: bpy.props.FloatProperty(name='Time (s)', default=0.0, min=0.0)
    rule: bpy.props.EnumProperty(
        name='Rule',
        items=(
            ('greaterThan', 'Greater than', ''),
            ('greaterOrEqual', 'Greater or equal', ''),
            ('equalTo', 'Equal', ''),
        ),
        default='greaterOrEqual',
    )

    def init(self, context):
        del context
        self.width = 240
        self.outputs.new('NodeSocketString', 'Trigger')

    def draw_buttons(self, context, layout):
        del context
        self._draw_property(layout, 'value', 'Time (s)')
        self._draw_property(layout, 'rule', 'Rule')

    def _draw_property(self, layout, property_name, label):
        row = layout.row(align=True)
        split = row.split(factor=0.48, align=True)
        split.label(text=label)
        split.prop(self, property_name, text='')


class DSC_XOSC_SpeedNode(DSC_XOSC_ActionNode):
    bl_idname = 'DSC_XOSC_SpeedNode'
    bl_label = 'Absolute Speed'
    def init(self, context):
        super().init(context)
        self.action_type = 'absolute_speed'


class DSC_XOSC_LaneChangeNode(DSC_XOSC_ActionNode):
    bl_idname = 'DSC_XOSC_LaneChangeNode'
    bl_label = 'Lane Change'
    def init(self, context):
        super().init(context)
        self.action_type = 'lane_change'


class DSC_XOSC_LaneOffsetNode(DSC_XOSC_ActionNode):
    bl_idname = 'DSC_XOSC_LaneOffsetNode'
    bl_label = 'Lane Offset'
    def init(self, context):
        super().init(context)
        self.action_type = 'lane_offset'


class DSC_XOSC_DistanceNode(DSC_XOSC_ActionNode):
    bl_idname = 'DSC_XOSC_DistanceNode'
    bl_label = 'Longitudinal Distance'
    def init(self, context):
        super().init(context)
        self.action_type = 'longitudinal_distance'


class DSC_XOSC_UserDefinedNode(DSC_XOSC_ActionNode):
    bl_idname = 'DSC_XOSC_UserDefinedNode'
    bl_label = 'User Defined Action'
    def init(self, context):
        super().init(context)
        self.action_type = 'user_defined'


class DSC_OT_create_xosc_node_tree(bpy.types.Operator):
    bl_idname = 'dsc.create_xosc_node_tree'
    bl_label = 'Create OpenSCENARIO action graph'

    def execute(self, context):
        tree = _get_or_create_node_tree()
        for area in context.screen.areas:
            if area.type == 'NODE_EDITOR':
                _configure_node_editor(area, tree)
        return {'FINISHED'}


class DSC_OT_toggle_xosc_node_editor(bpy.types.Operator):
    bl_idname = 'dsc.toggle_xosc_node_editor'
    bl_label = 'Toggle node editor'
    bl_description = 'Show or hide the OpenSCENARIO action node editor'

    def execute(self, context):
        screen = context.screen
        tree = _get_or_create_node_tree()
        existing_area = next(
            (area for area in screen.areas
             if area.type == 'NODE_EDITOR' and area.spaces.active.tree_type == NODE_TREE_ID),
            None,
        )
        if existing_area is not None:
            target_area = self._find_adjacent_view_area(screen, existing_area)
            if target_area is None:
                self.report({'WARNING'}, 'No adjacent 3D View found to join')
                return {'CANCELLED'}
            with bpy.context.temp_override(window=context.window, area=existing_area):
                result = bpy.ops.screen.area_join(
                    source_xy=(target_area.x + target_area.width // 2,
                               target_area.y + target_area.height // 2),
                    target_xy=(existing_area.x + 1, existing_area.y + 1),
                )
            if 'FINISHED' not in result:
                self.report({'WARNING'}, 'Could not join the node editor area')
                return {'CANCELLED'}
            return {'FINISHED'}

        view_area = max(
            (area for area in screen.areas if area.type == 'VIEW_3D'),
            key=lambda area: area.width * area.height,
            default=None,
        )
        if view_area is None:
            self.report({'WARNING'}, 'No 3D View is available to split')
            return {'CANCELLED'}

        before = {area.as_pointer() for area in screen.areas}
        with bpy.context.temp_override(window=context.window, area=view_area):
            result = bpy.ops.screen.area_split(direction='HORIZONTAL', factor=0.4)
        if 'FINISHED' not in result:
            self.report({'WARNING'}, 'Could not split the 3D View')
            return {'CANCELLED'}

        new_areas = [area for area in screen.areas if area.as_pointer() not in before]
        if new_areas:
            node_area = new_areas[0]
            _configure_node_editor(node_area, tree)
            _frame_node_editor(context.window, node_area)
        return {'FINISHED'}

    @staticmethod
    def _find_adjacent_view_area(screen, node_area):
        candidates = [area for area in screen.areas if area.type == 'VIEW_3D']
        if not candidates:
            return None

        def score(area):
            horizontal_overlap = max(
                0,
                min(node_area.x + node_area.width, area.x + area.width)
                - max(node_area.x, area.x),
            )
            vertical_gap = min(
                abs((node_area.y + node_area.height) - area.y),
                abs((area.y + area.height) - node_area.y),
            )
            return (horizontal_overlap, -vertical_gap, area.width * area.height)

        return max(candidates, key=score)


def _get_or_create_node_tree():
    tree = next((tree for tree in bpy.data.node_groups if tree.bl_idname == NODE_TREE_ID), None)
    if tree is None:
        tree = bpy.data.node_groups.new('OpenSCENARIO Actions', NODE_TREE_ID)
    return tree


def _configure_node_editor(area, tree):
    area.type = 'NODE_EDITOR'
    area.spaces.active.tree_type = NODE_TREE_ID
    area.spaces.active.pin = True
    area.spaces.active.node_tree = tree


def _frame_node_editor(window, area):
    region = next((region for region in area.regions if region.type == 'WINDOW'), None)
    if region is None:
        return
    with bpy.context.temp_override(window=window, area=area, region=region):
        bpy.ops.node.view_all()
        bpy.ops.view2d.zoom_in(
            zoomfacx=INITIAL_NODE_EDITOR_ZOOM,
            zoomfacy=INITIAL_NODE_EDITOR_ZOOM,
        )


class DSC_PT_xosc_node_tools(bpy.types.Panel):
    bl_idname = 'DSC_PT_xosc_node_tools'
    bl_label = 'OpenSCENARIO Actions'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == NODE_TREE_ID

    def draw(self, context):
        del context
        self.layout.operator('dsc.create_xosc_node_tree', icon='NODETREE')


NODE_CLASSES = (
    DSC_XOSC_NodeTree,
    DSC_XOSC_SimulationTimeTriggerNode,
    DSC_XOSC_SpeedNode,
    DSC_XOSC_LaneChangeNode,
    DSC_XOSC_LaneOffsetNode,
    DSC_XOSC_DistanceNode,
    DSC_XOSC_UserDefinedNode,
    DSC_OT_create_xosc_node_tree,
    DSC_OT_toggle_xosc_node_editor,
    DSC_PT_xosc_node_tools,
)


def get_node_data():
    node_groups = [tree for tree in bpy.data.node_groups if tree.bl_idname == NODE_TREE_ID]
    if not node_groups:
        return []
    nodes = [node for node in node_groups[0].nodes if isinstance(node, DSC_XOSC_ActionNode)]
    entity_names = set(get_entity_names())
    invalid_nodes = []
    data = []
    for node in nodes:
        if node.entity_ref == NO_ENTITY and len(entity_names) == 1:
            node.entity_ref = next(iter(entity_names))
        if node.entity_ref not in entity_names:
            invalid_nodes.append('{} ({})'.format(node.name, node.entity_ref or 'no entity'))
        node_data = node.to_xml_data()
        if node_data['priority'] == 'overwrite':
            node_data['priority'] = 'override'
        complete_socket = node.outputs.get('Complete') or node.outputs.get('Next')
        if complete_socket and complete_socket.links:
            node_data['next'] = complete_socket.links[0].to_node.action_name
        node_data['trigger'] = node.trigger_data()
        data.append(node_data)
    if invalid_nodes:
        raise ValueError('Select an existing entity for action node(s): {}'.format(
            ', '.join(invalid_nodes)))
    return data


def append_node_storyboard(root):
    return append_storyboard(root, get_node_data())


def write_node_storyboard(path):
    import xml.etree.ElementTree as ET
    tree = ET.parse(path)
    append_node_storyboard(tree.getroot())
    ET.indent(tree, space='  ')
    tree.write(path, encoding='utf-8', xml_declaration=True)


def register_node_menu():
    bpy.types.NODE_MT_add.append(_node_add_menu)


def unregister_node_menu():
    bpy.types.NODE_MT_add.remove(_node_add_menu)
