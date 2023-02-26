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


class DSC_OT_popup_entity_properties(bpy.types.Operator):
    bl_idname = 'dsc.popup_entity_properties'
    bl_label = 'Entity'
    bl_description = 'Create an OpenSCENARIO entity object'

    operators = {'entity_vehicle_car': bpy.ops.dsc.entity_car,
                 'entity_vehicle_truck': bpy.ops.dsc.entity_truck,
                 'entity_vehicle_motorbike': bpy.ops.dsc.entity_motorbike,
                 'entity_vehicle_bicycle': bpy.ops.dsc.entity_bicycle,
                 'entity_pedestrian_pedestrian': bpy.ops.dsc.entity_pedestrian,
                }

    names = {'entity_vehicle_car': 'car',
             'entity_vehicle_truck': 'truck',
             'entity_vehicle_motorbike': 'motorbike',
             'entity_vehicle_bicycle': 'bicycle',
             'entity_pedestrian_pedestrian': 'pedestrian',
            }

    operator: bpy.props.StringProperty(
        name='Object operator', description='Type of the object operator to call.', options={'HIDDEN'})

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        # Popup closed, call operator for the specified entity operator
        op = self.operators[self.operator]
        op('INVOKE_DEFAULT')
        return None

    def invoke(self, context, event):
        if self.operator.startswith('entity_vehicle'):
            entity_properties = context.scene.entity_properties_vehicle
        else:
            entity_properties = context.scene.entity_properties_pedestrian
        entity_properties.name = self.names[self.operator]
        return context.window_manager.invoke_popup(self)

    def draw(self, context):
        if self.operator.startswith('entity_vehicle'):
            entity_properties = context.scene.entity_properties_vehicle
        else:
            entity_properties = context.scene.entity_properties_pedestrian

        box = self.layout.box()

        row = box.row(align=True)
        row.label(text='Name:')
        row.prop(entity_properties, 'name', text='')
        row = box.row(align=True)
        row.label(text='Speed initial [km/h]:')
        row.prop(entity_properties, 'speed_initial', text='')
        row = box.row(align=True)
        row.label(text='Color:')
        row.prop(entity_properties, 'color', text='')
