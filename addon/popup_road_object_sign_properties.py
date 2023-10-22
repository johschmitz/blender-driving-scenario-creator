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
import os


class DSC_OT_popup_road_object_sign_properties(bpy.types.Operator):
    bl_idname = 'dsc.popup_road_object_sign_properties'
    bl_label = 'Road object sign'
    bl_description = 'Create an OpenDRIVE road sign (signal object)'

    operator: bpy.props.StringProperty(
        name='Object operator', description='Type of the object operator to call.', options={'HIDDEN'})

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        bpy.utils.previews.remove(self.preview_collection)
        # Popup closed, call operator for the specified road object operator
        op = bpy.ops.dsc.road_object_sign
        op('INVOKE_DEFAULT')
        return None

    def invoke(self, context, event):
        if len(context.scene.dsc_properties.road_object_sign_properties.sign_catalog) == 0:
            context.scene.dsc_properties.road_object_sign_properties.init()
        self.preview_collection = bpy.utils.previews.new()
        self.load_texture_road_sign_icons(context)
        return context.window_manager.invoke_popup(self, width=700)

    def load_texture_road_sign_icons(self, context):
        """Load road sign preview PNG files."""
        # TODO iterate over context.scene.dsc_properties.road_object_sign_properties.sign_catalog instead
        for sign in context.scene.dsc_properties.road_object_sign_properties.sign_catalog:
            # Load preview PNG files into the preview collection
            self.preview_collection.load(sign.name, os.path.join(context.scene.dsc_properties.road_object_sign_properties.texture_directory, sign.texture_name + '_preview.png'), 'IMAGE')

    def draw(self, context):
        # TODO make local
        global dsc_road_sign_previews

        box = self.layout.box()
        row = box.row(align=True)
        split = row.split(factor=0.125, align=True)
        split.label(text='Pole height:')
        split.prop(context.scene.dsc_properties.road_object_sign_properties, 'pole_height', text='')
        split.separator()
        row = box.row(align=True)
        split = row.split(factor=0.125, align=True)
        split.label(text='Sign width:')
        split.prop(context.scene.dsc_properties.road_object_sign_properties, 'width', text='')
        split.separator()
        row = box.row()
        box = row.box()
        row = box.row(align=True)
        split = row.split(factor=0.12, align=True)
        split.label(text='Select sign:')
        # row = box.row(align=True)
        grid = split.grid_flow(row_major=False, columns=5, even_columns=False, even_rows=False, align=True)
        for sign in context.scene.dsc_properties.road_object_sign_properties.sign_catalog:
            box = grid.box()
            row = box.row(align=True)
            row.template_icon(icon_value=self.preview_collection[sign.name].icon_id, scale=6)
            row = box.row(align=True)
            split = row.split(factor=0.6, align=True)
            split.label(text='Type:')
            split.prop(sign, "type", text='', emboss=False)
            row = box.row(align=True)
            split = row.split(factor=0.6, align=True)
            split.label(text='Subtype:')
            if sign.subtype == "":
                split.label(text='N/A')
            else:
                split.prop(sign, "subtype", text='', emboss=False)
            row = box.row(align=True)
            split = row.split(factor=0.6, align=True)
            split.label(text='Value:')
            if sign.value == 0:
                split.label(text='N/A')
            else:
                split.prop(sign, "value", text='', emboss=False)
            row = box.row(align=True)
            row.prop(sign, "selected", text='Select', toggle=True)
