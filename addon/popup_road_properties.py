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


class DSC_OT_popup_road_properties(bpy.types.Operator):
    bl_idname = 'dsc.popup_road_properties'
    bl_label = 'Road'
    bl_description = 'Create an OpenDRIVE road'

    operators = {'road_straight': bpy.ops.dsc.road_straight,
                 'road_arc': bpy.ops.dsc.road_arc,
                 'road_clothoid_hermite': bpy.ops.dsc.road_clothoid,
                 'road_clothoid_forward': bpy.ops.dsc.road_clothoid,
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
        if len(context.scene.road_properties.lanes) == 0:
            context.scene.road_properties.init()
        return context.window_manager.invoke_popup(self, width=600)

    def draw(self, context):
        box = self.layout.box()
        row = box.row(align=True)
        box_info = row.box()
        box_info.label(text='Note: Lines are centered between lanes and do not ')
        box_info.label(text='contribute to overall road width or number of lanes.')
        row = box.row(align=True)

        row.label(text='Cross section preset:')
        row.prop(context.scene.road_properties, 'cross_section_preset', text='')
        row = box.row(align=True)

        box_params = row.box()
        if self.expand_parameters == False:
            box_params.prop(self, 'expand_parameters', icon="TRIA_RIGHT", text="Parameters", emboss=False)
        else:
            # Expand
            box_params.prop(self, 'expand_parameters', icon="TRIA_DOWN", text="Parameters", emboss=False)
            row = box_params.row(align=True)
            row.label(text='Width line standard:')
            row.prop(context.scene.road_properties, 'width_line_standard', text='')
            row = box_params.row(align=True)
            row.label(text='Width line bold:')
            row.prop(context.scene.road_properties, 'width_line_bold', text='')
            row = box_params.row(align=True)
            # row.label(text='Length line broken:')
            # row.prop(context.scene.road_properties, 'length_broken_line', text='')
            # row = box_params.row(align=True)
            # row.label(text='Ratio broken line gap:')
            # row.prop(context.scene.road_properties, 'ratio_broken_line_gap', text='')
            row = box_params.row(align=True)

            row = box_params.row(align=True)
            row.label(text='Width driving:')
            row.prop(context.scene.road_properties, 'width_driving', text='')
            row = box_params.row(align=True)
            row.label(text='Width border:')
            row.prop(context.scene.road_properties, 'width_border', text='')
            # row = box_params.row(align=True)
            # row.label(text='Width curb:')
            # row.prop(context.scene.road_properties, 'width_curb', text='')
            row = box_params.row(align=True)
            row.label(text='Width median:')
            row.prop(context.scene.road_properties, 'width_median', text='')
            row = box_params.row(align=True)
            row.label(text='Width stop:')
            row.prop(context.scene.road_properties, 'width_stop', text='')
            row = box_params.row(align=True)
            row.label(text='Width shoulder:')
            row.prop(context.scene.road_properties, 'width_shoulder', text='')
            row = box_params.row(align=True)
            row.label(text='Width none (offroad lane):')
            row.prop(context.scene.road_properties, 'width_none', text='')
            row = box_params.row(align=True)

            row = box_params.row(align=True)
            row.label(text='Design speed:')
            row.prop(context.scene.road_properties, 'design_speed', text='')

        row = box.row()
        row.label(text='Number of lanes:')
        row = box.row()
        row.separator()
        row.label(text='Left:')
        row.prop(context.scene.road_properties, 'num_lanes_left', text='')
        row.separator()
        row.separator()
        row.separator()
        row.label(text='Right:')
        row.prop(context.scene.road_properties, 'num_lanes_right', text='')
        row.separator()

        row = box.row()
        row.label(text='Road split at:')
        row.prop(context.scene.road_properties, 'road_split_type', text='')
        row = box.row(align=True)

        row = box.row(align=True)
        row = box.row(align=True)

        num_lanes_left = context.scene.road_properties.num_lanes_left
        for idx, lane in enumerate(context.scene.road_properties.lanes):
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
                split.label(text='Width:')
                split.prop(lane, 'width', text='')
                split.label(text='Open/close:')
                split.prop(lane, 'width_change', text='')
                if context.scene.road_properties.road_split_type != 'none':
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
