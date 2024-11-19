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


class DSC_OT_popup_road_object_stencil_properties(bpy.types.Operator):
    bl_idname = 'dsc.popup_road_object_stencil_properties'
    bl_label = 'Road object stencil'
    bl_description = 'Create an OpenDRIVE road stencil (stencilal object)'

    operator: bpy.props.StringProperty(
        name='Object operator', description='Type of the object operator to call.', options={'HIDDEN'})

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        bpy.utils.previews.remove(self.preview_collection)
        # Popup closed, call operator for the specified road object operator
        op = bpy.ops.dsc.road_object_stencil
        op('INVOKE_DEFAULT')
        return None

    def invoke(self, context, event):
        if len(context.scene.dsc_properties.road_object_stencil_properties.stencil_catalog) == 0:
            context.scene.dsc_properties.road_object_stencil_properties.init()
        self.preview_collection = bpy.utils.previews.new()
        self.load_texture_road_stencil_icons(context)
        return context.window_manager.invoke_popup(self, width=700)

    def load_texture_road_stencil_icons(self, context):
        """Load road stencil preview PNG files."""
        # TODO iterate over context.scene.dsc_properties.road_object_stencil_properties.stencil_catalog instead
        for stencil in context.scene.dsc_properties.road_object_stencil_properties.stencil_catalog:
            # Load preview PNG files into the preview collection
            self.preview_collection.load(stencil.name, os.path.join(
                context.scene.dsc_properties.road_object_stencil_properties.texture_directory,
                stencil.texture_name + '_preview.png'), 'IMAGE')

    def draw(self, context):
        # TODO make local
        global dsc_road_stencil_previews

        box = self.layout.box()
        row = box.row(align=True)
        split = row.split(factor=0.12, align=True)
        split.label(text='Select stencil:')
        # row = box.row(align=True)
        grid = split.grid_flow(row_major=False, columns=5, even_columns=False, even_rows=False, align=True)
        for stencil in context.scene.dsc_properties.road_object_stencil_properties.stencil_catalog:
            box = grid.box()
            row = box.row(align=True)
            row.template_icon(icon_value=self.preview_collection[stencil.name].icon_id, scale=6)
            row = box.row(align=True)
            split = row.split(factor=0.6, align=True)
            split.label(text='Type:')
            split.prop(stencil, "type", text='', emboss=False)
            row = box.row(align=True)
            split = row.split(factor=0.6, align=True)
            split.label(text='Subtype:')
            if stencil.subtype == "":
                split.label(text='N/A')
            else:
                split.prop(stencil, "subtype", text='', emboss=False)
            row = box.row(align=True)
            split = row.split(factor=0.6, align=True)
            row = box.row(align=True)
            row.prop(stencil, "selected", text='Select', toggle=True)
