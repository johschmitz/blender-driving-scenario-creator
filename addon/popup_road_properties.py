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

import json
import os
from . helpers import get_user_cross_sections_path


# Operator to save the current cross-section as a user preset
class DSC_OT_save_cross_section_preset(bpy.types.Operator):
    bl_idname = 'dsc.save_cross_section_preset'
    bl_label = 'Save user cross section preset'
    bl_description = 'Save the current cross section as a user preset'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.scene.dsc_properties.road_properties.new_cross_section_preset_name.strip() != ''

    def invoke(self, context, event):
        preset_name = context.scene.dsc_properties.road_properties.new_cross_section_preset_name.strip()
        user_json_path = get_user_cross_sections_path()

        # Show confirmation dialog if preset exists
        if os.path.exists(user_json_path):
            with open(user_json_path, 'r') as f:
                user_presets = json.load(f)
                if preset_name in user_presets:
                    return context.window_manager.invoke_confirm(self, event, message=f"Preset '{preset_name}' already exists. Overwrite?")

        # If preset doesn't exist, execute directly
        return self.execute(context)

    def execute(self, context):
        props = context.scene.dsc_properties.road_properties
        preset_name = props.new_cross_section_preset_name.strip()
        if not preset_name:
            self.report({'ERROR'}, "Please enter a name for the new preset")
            return {'CANCELLED'}

        # Collect the current cross-section data from the UI state
        data = {
            'sides': [],
            'widths_start': [],
            'widths_end': [],
            'types': [],
            'road_mark_types': [],
            'road_mark_weights': [],
            'road_mark_widths': [],
            'road_mark_colors': [],
            'lane_offset_start': props.lane_offset_start,
            'lane_offset_end': props.lane_offset_end,
            'road_split_type': props.road_split_type,
            'road_split_lane_idx': props.road_split_lane_idx
        }

        # Add lane data in correct order
        for lane in props.lanes:
            data['sides'].append(lane.side)
            data['widths_start'].append(lane.width_start)
            data['widths_end'].append(lane.width_end)
            data['types'].append(lane.type)
            data['road_mark_types'].append(lane.road_mark_type)
            data['road_mark_weights'].append(lane.road_mark_weight)
            data['road_mark_widths'].append(lane.road_mark_width)
            data['road_mark_colors'].append(lane.road_mark_color)

        # Get user JSON file path
        user_json_path = get_user_cross_sections_path()
        # Load or create user presets
        if os.path.exists(user_json_path):
            with open(user_json_path, 'r') as f:
                user_presets = json.load(f)
        else:
            user_presets = {}

        # Save or update the preset
        user_presets[preset_name] = data
        with open(user_json_path, 'w') as f:
            json.dump(user_presets, f, indent=2)

        self.report({'INFO'}, f"Preset '{preset_name}' saved to {user_json_path}.")
        # Force UI update to refresh preset list
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}

class DSC_OT_copy_cross_section_preset_name(bpy.types.Operator):
    bl_idname = 'dsc.copy_cross_section_preset_name'
    bl_label = 'Copy Cross Section Preset Name'
    bl_description = 'Copy the current preset name to create a new similar preset'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        props = context.scene.dsc_properties.road_properties
        current_preset = props.cross_section_preset
        props.new_cross_section_preset_name = current_preset
        return {'FINISHED'}

class DSC_OT_delete_cross_section_preset(bpy.types.Operator):
    bl_idname = 'dsc.delete_cross_section_preset'
    bl_label = 'Delete user cross section preset'
    bl_description = 'Delete the current user cross section preset'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        # Check if user preset is selected in UI, otherwise disable delete button
        preset_name = context.scene.dsc_properties.road_properties.cross_section_preset
        user_json_path = get_user_cross_sections_path()
        if os.path.exists(user_json_path):
            with open(user_json_path, 'r') as f:
                user_presets = json.load(f)
                return preset_name in user_presets
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        preset_name = context.scene.dsc_properties.road_properties.cross_section_preset
        user_json_path = get_user_cross_sections_path()
        if os.path.exists(user_json_path):
            with open(user_json_path, 'r') as f:
                # Check if file empty or invalid
                user_presets = json.load(f)
            if preset_name in user_presets:
                del user_presets[preset_name]
                with open(user_json_path, 'w') as f:
                    json.dump(user_presets, f, indent=2)
                self.report({'INFO'}, f"Preset '{preset_name}' deleted.")
                # Switch to default preset
                context.scene.dsc_properties.road_properties.cross_section_preset = 'two_lanes_default'
                # Force UI update
                for area in context.screen.areas:
                    area.tag_redraw()
                return {'FINISHED'}
        return {'CANCELLED'}

class DSC_OT_popup_road_properties(bpy.types.Operator):
    bl_idname = 'dsc.popup_road_properties'
    bl_label = 'Road'
    bl_description = 'Construct a piece of road'

    operators = {'road_straight': bpy.ops.dsc.road_straight,
                 'road_arc': bpy.ops.dsc.road_arc,
                 'road_clothoid_hermite': bpy.ops.dsc.road_clothoid,
                 'road_clothoid_forward': bpy.ops.dsc.road_clothoid,
                 'road_clothoid_triple': bpy.ops.dsc.road_clothoid_triple,
                 'road_parametric_polynomial': bpy.ops.dsc.road_parametric_polynomial,
                 'junction_connecting_road': bpy.ops.dsc.junction_connecting_road,
                 'junction_four_way': bpy.ops.dsc.junction_four_way}

    operator: bpy.props.StringProperty(
        name='Road operator', description='Type of the road operator to call.', options={'HIDDEN'})
    expand_parameters: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        return {'FINISHED'}

    def cancel(self, context):
        # Popup closed, call operator for the specified road operator
        if self.operator == 'road_clothoid_hermite' or self.operator == 'junction_connecting_road':
            geometry_solver = 'hermite'
        elif self.operator == 'road_clothoid_forward':
            geometry_solver = 'forward'
        else:
            geometry_solver = 'default'
        op = self.operators[self.operator]
        op('INVOKE_DEFAULT', geometry_solver=geometry_solver)
        return None

    def invoke(self, context, event):
        if len(context.scene.dsc_properties.road_properties.lanes) == 0:
            context.scene.dsc_properties.road_properties.init()
        return context.window_manager.invoke_popup(self, width=700)


    def draw(self, context):
        box = self.layout.box()
        row = box.row(align=True)
        box_info = row.box()
        box_info.label(text='Note: Lines are centered between lanes and do not ')
        box_info.label(text='contribute to overall road width or number of lanes.')
        row = box.row(align=True)

        # Cross section preset row with text field, save and delete buttons
        row.label(text='Cross section preset:')
        row.prop(context.scene.dsc_properties.road_properties, 'cross_section_preset', text='')
        row.operator('dsc.delete_cross_section_preset', text='', icon='TRASH')
        row.operator('dsc.copy_cross_section_preset_name', text='', icon='COPYDOWN')
        row.prop(context.scene.dsc_properties.road_properties, 'new_cross_section_preset_name', text='')
        row.operator('dsc.save_cross_section_preset', text='', icon='FILE_TICK')
        row = box.row(align=True)

        box_params = row.box()
        if self.expand_parameters == False:
            box_params.prop(self, 'expand_parameters', icon="TRIA_RIGHT", text="Parameters", emboss=False)
        else:
            # Expand
            box_params.prop(self, 'expand_parameters', icon="TRIA_DOWN", text="Parameters", emboss=False)
            row = box_params.row(align=True)
            row.label(text='Width line standard:')
            row.prop(context.scene.dsc_properties.road_properties, 'width_line_standard', text='')
            row = box_params.row(align=True)
            row.label(text='Width line bold:')
            row.prop(context.scene.dsc_properties.road_properties, 'width_line_bold', text='')
            row = box_params.row(align=True)
            # row.label(text='Length line broken:')
            # row.prop(context.scene.dsc_properties.road_properties, 'length_broken_line', text='')
            # row = box_params.row(align=True)
            # row.label(text='Ratio broken line gap:')
            # row.prop(context.scene.dsc_properties.road_properties, 'ratio_broken_line_gap', text='')
            row = box_params.row(align=True)

            row = box_params.row(align=True)
            row.label(text='Width driving:')
            row.prop(context.scene.dsc_properties.road_properties, 'width_driving', text='')
            row = box_params.row(align=True)
            row.label(text='Width border:')
            row.prop(context.scene.dsc_properties.road_properties, 'width_border', text='')
            # row = box_params.row(align=True)
            # row.label(text='Width curb:')
            # row.prop(context.scene.dsc_properties.road_properties, 'width_curb', text='')
            row = box_params.row(align=True)
            row.label(text='Width median:')
            row.prop(context.scene.dsc_properties.road_properties, 'width_median', text='')
            row = box_params.row(align=True)
            row.label(text='Width stop:')
            row.prop(context.scene.dsc_properties.road_properties, 'width_stop', text='')
            row = box_params.row(align=True)
            row.label(text='Width shoulder:')
            row.prop(context.scene.dsc_properties.road_properties, 'width_shoulder', text='')
            row = box_params.row(align=True)
            row.label(text='Width none (offroad lane):')
            row.prop(context.scene.dsc_properties.road_properties, 'width_none', text='')
            row = box_params.row(align=True)

            row = box_params.row(align=True)
            row.label(text='Design speed:')
            row.prop(context.scene.dsc_properties.road_properties, 'design_speed', text='')

        row = box.row()
        row.label(text='Number of lanes:')
        row = box.row()
        row.separator()
        row.label(text='Left:')
        row.prop(context.scene.dsc_properties.road_properties, 'num_lanes_left', text='')
        row.separator()
        row.separator()
        row.separator()
        row.label(text='Right:')
        row.prop(context.scene.dsc_properties.road_properties, 'num_lanes_right', text='')
        row.separator()

        row = box.row()
        row.label(text='Lane offset:')
        row = box.row()
        row.separator()
        row.label(text='Start:')
        row.prop(context.scene.dsc_properties.road_properties, 'lane_offset_start', text='')
        row.separator()
        row.separator()
        row.separator()
        row.label(text='End:')
        row.prop(context.scene.dsc_properties.road_properties, 'lane_offset_end', text='')
        row.separator()

        row = box.row()
        row.label(text='Road split at:')
        row.prop(context.scene.dsc_properties.road_properties, 'road_split_type', text='')
        row = box.row(align=True)

        row = box.row(align=True)
        row = box.row(align=True)

        num_lanes_left = context.scene.dsc_properties.road_properties.num_lanes_left
        for idx, lane in enumerate(context.scene.dsc_properties.road_properties.lanes):
            # Lane marking left side
            if lane.side == 'left':
                row = box.row(align=True)
                split = row.split(factor=0.12, align=True)
                split.label(text='─ Line ─ :')
                split.label(text='Type:')
                split.prop(lane, 'road_mark_type', text='')
                split.label(text='Color:')
                split.prop(lane, 'road_mark_color', text='')
                split.label(text='Weight:')
                split.prop(lane, 'road_mark_weight', text='')
                split.label(text='Width:')
                split.prop(lane, 'road_mark_width', text='')
            # Basic lane settings
            if lane.side != 'center':
                row = box.row(align=True)
                split = row.split(factor=0.12, align=True)
                split.label(text=' Lane ' + str(num_lanes_left-idx) + ':')
                split.label(text='Type:')
                split.prop(lane, 'type', text='')
                split.label(text='Width start:')
                split.prop(lane, 'width_start', text='')
                split.label(text='Width end:')
                split.prop(lane, 'width_end', text='')
                if context.scene.dsc_properties.road_properties.road_split_type != 'none':
                    # Splitting of lanes (creates direct junction)
                    split.label(text='Split:')
                    if lane.split_right == False:
                        split.prop(lane, 'split_right',icon="SORT_DESC", icon_only=True)
                    else:
                        split.prop(lane, 'split_right',icon="SORT_ASC", icon_only=True)
                else:
                    split.separator()
                    split.separator()
            # Lane marking right side
            if lane.side == 'right' or lane.side == 'center':
                row = box.row(align=True)
                split = row.split(factor=0.12, align=True)
                split.label(text='─ Line ─ :')
                split.label(text='Type:')
                split.prop(lane, 'road_mark_type', text='')
                split.label(text='Color:')
                split.prop(lane, 'road_mark_color', text='')
                split.label(text='Weight:')
                split.prop(lane, 'road_mark_weight', text='')
                split.label(text='Width:')
                split.prop(lane, 'road_mark_width', text='')
