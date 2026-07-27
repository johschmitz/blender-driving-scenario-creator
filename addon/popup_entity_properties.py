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

from . helpers import call_operator_deferred
from . entity_vehicle import VEHICLE_CATEGORY_ITEMS


PEDESTRIAN_CATEGORY_ITEMS = (
    ('adult', 'Adult', 'Create an adult pedestrian entity'),
    ('child', 'Child', 'Create a child pedestrian entity'),
)


class DSC_OT_popup_entity_vehicle_types(bpy.types.Operator):
    bl_idname = 'dsc.popup_entity_vehicle_types'
    bl_label = 'Vehicles'
    bl_description = 'Choose an OpenSCENARIO vehicle category'

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        bpy.utils.previews.remove(self.preview_collection)
        return None

    def invoke(self, context, event):
        self.preview_collection = bpy.utils.previews.new()
        self._load_previews()
        return context.window_manager.invoke_popup(self, width=700)

    def _load_previews(self):
        entities_dir = os.path.join(os.path.dirname(__file__), 'entities', 'vehicles')
        for category, _label, _desc in VEHICLE_CATEGORY_ITEMS:
            preview_name = 'entity_vehicle_{}'.format(category)
            preview_path = os.path.join(entities_dir, preview_name + '_preview.png')
            if os.path.exists(preview_path):
                self.preview_collection.load(preview_name, preview_path, 'IMAGE')

    def draw(self, context):
        del context

        box = self.layout.box()
        box.label(text='Vehicles')
        grid = box.grid_flow(row_major=False, columns=3, even_columns=True, even_rows=True, align=True)
        for category, label, _description in VEHICLE_CATEGORY_ITEMS:
            preview_name = 'entity_vehicle_{}'.format(category)
            tile_box = grid.box()
            row = tile_box.row(align=True)
            if preview_name in self.preview_collection:
                row.template_icon(icon_value=self.preview_collection[preview_name].icon_id, scale=6)
            row = tile_box.row(align=True)
            op = row.operator('dsc.popup_entity_properties', text=label)
            op.entity_type = 'vehicle'
            op.entity_subtype = category


class DSC_OT_popup_entity_pedestrian_types(bpy.types.Operator):
    bl_idname = 'dsc.popup_entity_pedestrian_types'
    bl_label = 'Pedestrians'
    bl_description = 'Choose an OpenSCENARIO pedestrian category'

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        bpy.utils.previews.remove(self.preview_collection)
        return None

    def invoke(self, context, event):
        self.preview_collection = bpy.utils.previews.new()
        self._load_previews()
        return context.window_manager.invoke_popup(self, width=400)

    def _load_previews(self):
        entities_dir = os.path.join(os.path.dirname(__file__), 'entities', 'pedestrians')
        for category, _label, _desc in PEDESTRIAN_CATEGORY_ITEMS:
            preview_name = 'entity_pedestrian_{}'.format(category)
            preview_path = os.path.join(entities_dir, preview_name + '_preview.png')
            if os.path.exists(preview_path):
                self.preview_collection.load(preview_name, preview_path, 'IMAGE')

    def draw(self, context):
        del context

        box = self.layout.box()
        box.label(text='Pedestrians')
        grid = box.grid_flow(row_major=False, columns=2, even_columns=True, even_rows=True, align=True)
        for category, label, _description in PEDESTRIAN_CATEGORY_ITEMS:
            preview_name = 'entity_pedestrian_{}'.format(category)
            tile_box = grid.box()
            row = tile_box.row(align=True)
            if preview_name in self.preview_collection:
                row.template_icon(icon_value=self.preview_collection[preview_name].icon_id, scale=6)
            row = tile_box.row(align=True)
            op = row.operator('dsc.popup_entity_properties', text=label)
            op.entity_type = 'pedestrian'
            op.entity_subtype = category


class DSC_OT_popup_entity_properties(bpy.types.Operator):
    bl_idname = 'dsc.popup_entity_properties'
    bl_label = 'Entity'
    bl_description = 'Create an OpenSCENARIO entity object'

    entity_type: bpy.props.StringProperty(
        name='Entity type', description='Entity type to create', options={'HIDDEN'})

    entity_subtype: bpy.props.StringProperty(
        name='Entity subtype', description='Entity subtype to create', options={'HIDDEN'})

    def _get_entity_properties(self, context):
        if self.entity_type == 'vehicle':
            return context.scene.dsc_properties.entity_properties_vehicle
        return context.scene.dsc_properties.entity_properties_pedestrian

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        del context

        entity_type = str(self.entity_type)
        entity_subtype = str(self.entity_subtype)

        if entity_type == 'vehicle':
            call_operator_deferred(lambda subtype=entity_subtype: bpy.ops.dsc.entity_vehicle(
                'INVOKE_DEFAULT', vehicle_category=subtype))
        else:
            call_operator_deferred(lambda subtype=entity_subtype: bpy.ops.dsc.entity_pedestrian(
                'INVOKE_DEFAULT', pedestrian_category=subtype))
        return None

    def invoke(self, context, event):
        del event

        entity_properties = self._get_entity_properties(context)
        entity_properties.name = self.entity_subtype
        return context.window_manager.invoke_popup(self)

    def draw(self, context):
        entity_properties = self._get_entity_properties(context)

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
