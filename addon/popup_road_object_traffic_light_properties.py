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


class DSC_OT_popup_road_object_traffic_light_properties(bpy.types.Operator):
    bl_idname = 'dsc.popup_road_object_traffic_light_properties'
    bl_label = 'Road object sign'
    bl_description = 'Create an OpenDRIVE road sign (signal object)'

    operator: bpy.props.StringProperty(
        name='Object operator', description='Type of the object operator to call.', options={'HIDDEN'})

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        # Popup closed, call operator for the specified road object operator
        op = bpy.ops.dsc.road_object_traffic_light
        op('INVOKE_DEFAULT')
        return None

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=700)

    def draw(self, context):
        # TODO make local
        global dsc_road_traffic_light_previews

        box = self.layout.box()
        row = box.row(align=True)
        split = row.split(factor=0.125, align=True)
        split.label(text='Pole height:')
        split.prop(context.scene.dsc_properties.road_object_traffic_light_properties, 'pole_height', text='')
        row = box.row(align=True)
        split = row.split(factor=0.125, align=True)
        split.label(text='Housing height:')
        split.prop(context.scene.dsc_properties.road_object_traffic_light_properties, 'height', text='')