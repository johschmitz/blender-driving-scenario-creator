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


class DSC_OT_object_properties_popup(bpy.types.Operator):
    bl_idname = 'dsc.object_properties_popup'
    bl_label = ''

    operators = {'object_car': bpy.ops.dsc.object_car,
                 'object_truck': bpy.ops.dsc.object_truck,
                 'object_motorbike': bpy.ops.dsc.object_motorbike,
                 'object_pedestrian': bpy.ops.dsc.object_pedestrian,
                 'object_bicycle': bpy.ops.dsc.object_bicycle,
                }

    operator: bpy.props.StringProperty(
        name='Object operator', description='Type of the object operator to call.', options={'HIDDEN'})

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        # Popup closed, call operator for the specified road operator
        op = self.operators[self.operator]
        op('INVOKE_DEFAULT')
        return None

    def invoke(self, context, event):
        if len(context.scene.road_properties.lanes) == 0:
            context.scene.road_properties.init()
        # TODO: for now only straight road parameterization implemented
        if self.operator == 'object_car':
            return context.window_manager.invoke_popup(self)
        else:
            op = self.operators[self.operator]
            op('INVOKE_DEFAULT')
            return {'FINISHED'}

    def draw(self, context):
        box = self.layout.box()

        row = box.row(align=True)
        row.label(text='Name:')
        row.prop(context.scene.object_properties, 'name', text='')
        row = box.row(align=True)
        row.label(text='Speed initial [km/h]:')
        row.prop(context.scene.object_properties, 'speed_initial', text='')
        row = box.row(align=True)
        row.label(text='Color:')
        row.prop(context.scene.object_properties, 'color', text='')
