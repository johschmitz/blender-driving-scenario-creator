# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import bpy

from . import helpers


class DSC_OT_scenario_entity_edit(bpy.types.Operator):
    bl_idname = 'dsc.scenario_entity_edit'
    bl_label = 'Edit scenario entity'
    bl_description = 'Select an OpenSCENARIO entity to edit'

    hovered_obj = None

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        del event
        self.hovered_obj = None
        bpy.ops.object.select_all(action='DESELECT')
        context.workspace.status_text_set(
            'LEFTMOUSE: select entity, RIGHTMOUSE/ESC: exit')
        context.window.cursor_modal_set('CROSSHAIR')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L',
                          'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.type == 'MOUSEMOVE':
            dsc_hit, raycast_point, raycast_normal, obj = \
                helpers.raycast_mouse_to_dsc_object(context, event)
            del raycast_point, raycast_normal
            if (dsc_hit and obj.get('dsc_category') == 'OpenSCENARIO'
                    and obj.get('dsc_type') == 'entity'):
                self.hovered_obj = obj
            else:
                self.hovered_obj = None

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if self.hovered_obj is None:
                self.report({'INFO'}, 'Select an OpenSCENARIO entity.')
                return {'RUNNING_MODAL'}
            helpers.select_activate_object(context, self.hovered_obj)
            self.clean_up(context)
            helpers.call_operator_deferred(
                lambda: bpy.ops.dsc.popup_entity_edit_properties('INVOKE_DEFAULT'))
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.clean_up(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def clean_up(self, context):
        context.workspace.status_text_set(None)
        context.window.cursor_modal_restore()


class DSC_OT_popup_entity_edit_properties(bpy.types.Operator):
    bl_idname = 'dsc.popup_entity_edit_properties'
    bl_label = 'Edit entity'
    bl_description = 'Edit the selected OpenSCENARIO entity'

    name: bpy.props.StringProperty(name='Name')
    speed_initial: bpy.props.FloatProperty(
        name='Speed initial [km/h]', min=0.1, max=500.0)
    color: bpy.props.FloatVectorProperty(
        name='Color', subtype='COLOR_GAMMA', size=4, min=0.0, max=1.0)

    entity = None

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and
                (obj.get('dsc_type') == 'entity' or
                 (obj.parent is not None and
                  obj.parent.get('dsc_type') == 'entity')))

    def _get_entity(self, context):
        obj = context.active_object
        if obj is not None and obj.get('dsc_type') == 'entity':
            return obj
        if obj is not None and obj.parent is not None:
            parent = obj.parent
            if parent.get('dsc_type') == 'entity':
                return parent
        return None

    def _apply_changes(self):
        if self.entity is None:
            return

        old_name = self.entity.name
        self.entity.name = self.name
        self.entity.data.name = self.entity.name
        if old_name != self.entity.name:
            trajectories = bpy.data.collections.get('OpenSCENARIO')
            if trajectories is not None:
                trajectories = trajectories.children.get('trajectories')
            if trajectories is not None:
                for trajectory in trajectories.objects:
                    if trajectory.get('owner_name') == old_name:
                        trajectory['owner_name'] = self.entity.name
        self.entity['speed_initial'] = self.speed_initial
        self.entity['color'] = tuple(self.color)

        helpers.assign_object_materials(self.entity, self.entity['color'])
        material_index = helpers.get_material_index(
            self.entity, helpers.get_paint_material_name(self.entity['color']))
        if material_index is not None:
            for polygon in self.entity.data.polygons:
                polygon.material_index = material_index

    def invoke(self, context, event):
        del event
        self.entity = self._get_entity(context)
        if self.entity is None:
            self.report({'WARNING'}, 'Select an OpenSCENARIO entity first.')
            return {'CANCELLED'}

        self.name = self.entity.name
        self.speed_initial = self.entity.get('speed_initial', 50.0)
        self.color = self.entity.get('color', (0.9, 0.1, 0.1, 1.0))
        return context.window_manager.invoke_popup(self)

    def execute(self, context):
        del context
        self._apply_changes()
        return {'FINISHED'}

    def cancel(self, context):
        del context
        self._apply_changes()
        return None

    def draw(self, context):
        del context
        box = self.layout.box()

        row = box.row(align=True)
        row.label(text='Name:')
        row.prop(self, 'name', text='')
        row = box.row(align=True)
        row.label(text='Speed initial [km/h]:')
        row.prop(self, 'speed_initial', text='')
        row = box.row(align=True)
        row.label(text='Color:')
        row.prop(self, 'color', text='')