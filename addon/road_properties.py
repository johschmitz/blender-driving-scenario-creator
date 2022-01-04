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

from . params_cross_section import params_cross_section


# We need global wrapper callbacks due to Blender update callback implementation
def callback_cross_section(self, context):
    self.update_cross_section()
def callback_width(self, context):
    self.update_width(context)
def callback_num_lanes(self, context):
    self.update_num_lanes()
def callback_road_split(self, context):
    self.update_road_split(context)

class DSC_enum_strip(bpy.types.PropertyGroup):
    idx: bpy.props.IntProperty(min=0)
    direction: bpy.props.EnumProperty(
        items=(('left', 'left', '', 0),
               ('right', 'right', '', 1),
               ('center', 'center', '', 2),
              ),
        default='right',
    )
    width: bpy.props.FloatProperty(
        name='Width of lane',
        default=4.0, min=0.01, max=10.0, step=1
    )
    type: bpy.props.EnumProperty(
        name = 'Strip type',
        items=(('driving', 'Driving', '', 0),
               #('bidirectional', 'Bidirectional', '', 1),
               #('bus', 'Bus', '', 2),
               ('stop', 'Stop', '', 3),
               #('parking', 'Parking', '', 4),
               #('biking', 'Biking', '', 5),
               #('restricted', 'Restricted', '', 6),
               #('roadWorks', 'Road works', '', 7),
               ('border', 'Border', '', 8),
               #('curb', 'Curb', '', 9),
               #('sidewalk', 'Sidewalk', '', 10),
               ('shoulder', 'Shoulder', '', 11),
               ('median', 'Median', '', 12),
               #('entry', 'Entry', '', 13),
               #('exit', 'Exit', '', 14),
               #('onRamp', 'On ramp', '', 15),
               #('offRamp', 'Off ramp', '', 16),
               #('connectingRamp', 'Connecting ramp', '', 17),
               ('none', 'None', '', 18),
               ('line', 'Line', '', 19),
              ),
        default='driving',
        update=callback_width,
    )
    road_mark_type: bpy.props.EnumProperty(
        name = 'Type',
        items=(('none', 'None', '', 0),
               ('solid', 'Solid', '', 1),
               ('broken', 'Broken', '', 2),
               ('solid_solid', 'Double solid solid', '', 3),
               #('solid_broken', 'Double solid broken', '', 4),
               #('broken_solid', 'Double broken solid', '', 5),
              ),
        default='none',
    )
    road_mark_weight: bpy.props.EnumProperty(
        name = 'Weight',
        items=(('none', 'None', '', 0),
               ('standard', 'Standard', '', 1),
               ('bold', 'Bold', '', 2),
              ),
        default='none',
    )
    road_mark_color: bpy.props.EnumProperty(
        name = 'Color',
        items=(('none', 'None', '', 0),
               ('white', 'White', '', 1),
               ('yellow', 'Yellow', '', 2),
              ),
        default='none',
    )

    # False for the strips/lanes going left, True for those going right
    split_right: bpy.props.BoolProperty(description='Split above here', update=callback_road_split)

    def update_width(self, context):
        if self.type == 'line':
            # We treat line width separately based on road mark line weights
            self.width = 0.0
        else:
            mapping_width_type_lane = {
                'driving' : context.scene.road_properties.width_driving,
                'stop' : context.scene.road_properties.width_stop,
                'border' : context.scene.road_properties.width_border,
                'shoulder' : context.scene.road_properties.width_shoulder,
                'median' : context.scene.road_properties.width_median,
                'none' : context.scene.road_properties.width_none,
            }
            self.width = mapping_width_type_lane[self.type]

    def update_road_split(self, context):
        # Avoid updating recursively
        if context.scene.road_properties.lock_strips:
            return
        context.scene.road_properties.lock_strips = True
        # Toggle
        if self.split_right == True:
            self.split_right = True
            road_split_strip_idx = self.idx
        else:
            self.split_right = False
            road_split_strip_idx = self.idx + 1
        # Split at the desired lane/strip
        for idx, strip in enumerate(context.scene.road_properties.strips):
            if idx < road_split_strip_idx:
                strip.split_right = False
            else:
                strip.split_right = True
        context.scene.road_properties.road_split_strip_idx = road_split_strip_idx
        # Unlock updating
        context.scene.road_properties.lock_strips = False


class DSC_road_properties(bpy.types.PropertyGroup):
    width_line_standard: bpy.props.FloatProperty(default=0.12, min=0.01, max=10.0, step=1)
    width_line_bold: bpy.props.FloatProperty(default=0.25, min=0.01, max=10.0, step=1)
    length_broken_line: bpy.props.FloatProperty(default=3.0, min=0.01, max=10.0, step=1)
    ratio_broken_line_gap: bpy.props.IntProperty(default=1, min=1, max=3)
    width_driving: bpy.props.FloatProperty(default=3.75, min=0.01, max=10.0, step=1)
    width_border: bpy.props.FloatProperty(default=0.5, min=0.01, max=1.0, step=1)
    # width_curb: bpy.props.FloatProperty(default=0.16, min=0.10, max=0.30, step=1)
    width_median: bpy.props.FloatProperty(default=2.0, min=0.01, max=10.0, step=1)
    width_stop: bpy.props.FloatProperty(default=2.5, min=0.01, max=10.0, step=1)
    width_shoulder: bpy.props.FloatProperty(default=1.5, min=0.01, max=10.0, step=1)
    width_none: bpy.props.FloatProperty(default=2.5, min=0.01, max=10.0, step=1)

    design_speed: bpy.props.FloatProperty(default=130.0, min=1.00, max=400.0, step=1)

    num_lanes_left: bpy.props.IntProperty(default=2, min=0, max=20, update=callback_num_lanes)
    num_lanes_right: bpy.props.IntProperty(default=2, min=0, max=20, update=callback_num_lanes)

    # Strip idx where the road is split at the end
    road_split_strip_idx: bpy.props.IntProperty(default=0, min=0)

    strip_idx_current: bpy.props.IntProperty(default=0, min=0)
    strips: bpy.props.CollectionProperty(type=DSC_enum_strip)

    cross_section_preset: bpy.props.EnumProperty(
            items=(
                ('two_lanes_default','Two lanes (default)','Two lanes (default)'),
                # Typical German road cross sections
                ('ekl4_rq9', 'EKL 4, RQ 9', 'EKL 4, RQ 9'),
                ('ekl3_rq11', 'EKL 3, RQ 11', 'EKL 3, RQ 11'),
                # ('ekl2_rq11.5', 'EKL 2, RQ 11.5', 'EKL 2, RQ 11.5'),
                # ('ekl1_rq15_5', 'EKL 1, RQ 15.5', 'EKL 1, RQ 15.5'),
                # ('eka3_rq25', 'EKA 3, RQ 25', 'EKA 3, RQ 25'),
                # ('eka3_rq31_5', 'EKA 3, RQ 31_5', 'EKA 3, RQ 31_5'),
                # ('eka3_rq38_5', 'EKA 3, RQ 38_5', 'EKA 3, RQ 38_5'),
                # ('eka2_rq28', 'EKA 1, RQ 28', 'EKA 1, RQ 28'),
                ('eka1_rq31', 'EKA 1, RQ 31', 'EKA 1, RQ 31'),
                ('eka1_rq36', 'EKA 1, RQ 36', 'EKA 1, RQ 36'),
                ('eka1_rq36_exit_right', 'EKA 1, RQ 36 - exit right', 'EKA 1, RQ 36 - exit right'),
                ('eka1_rq43_5', 'EKA 1, RQ 43.5', 'EKA 1, RQ 43.5'),
            ),
            name='cross_section',
            description='Road cross section presets',
            default='two_lanes_default',
            update=callback_cross_section,
            )

    lock_strips: bpy.props.BoolProperty(default=False)

    def init(self):
        self.update_cross_section()

    def clear_strips(self):
        self.strips.clear()
        self.strip_idx_current = 0
        self.road_split_strip_idx = 0

    def update_num_lanes(self):
        # Do not update recursively when switching presets
        if self.lock_strips:
            return
        self.clear_strips()
        # Left lanes
        for idx in range(self.num_lanes_left - 1,-1,-1):
            if self.num_lanes_left == 1:
                self.add_strip('left', 'line', 0.0, 'solid', 'standard', 'white')
                self.add_strip('left', 'driving', self.width_driving, 'none', 'none', 'none')
            else:
                if idx == self.num_lanes_left - 1:
                    self.add_strip('left', 'line', 0.0, 'none', 'none', 'none')
                    self.add_strip('left', 'border', self.width_border, 'none', 'none', 'none')
                    self.add_strip('left', 'line', 0.0, 'solid', 'standard', 'white')
                elif idx == 0:
                    self.add_strip('left', 'driving', self.width_driving, 'none', 'none', 'none')
                else:
                    self.add_strip('left', 'driving', self.width_driving, 'none', 'none', 'none')
                    self.add_strip('left', 'line', 0.0, 'broken', 'standard', 'white')
        # Center line
        if self.num_lanes_left == 0:
            self.add_strip('center', 'line', 0.0, 'solid', 'standard', 'white')
        elif self.num_lanes_right == 0:
            self.add_strip('center', 'line', 0.0, 'solid', 'standard', 'white')
        else:
            self.add_strip('center', 'line', 0.0, 'broken', 'standard', 'white')
        # Right lanes
        for idx in range(self.num_lanes_right):
            if self.num_lanes_right == 1:
                self.add_strip('right', 'driving', self.width_driving, 'none', 'none', 'none')
                self.add_strip('right', 'line', 0.0, 'solid', 'standard', 'white')
            else:
                if idx == self.num_lanes_right - 1:
                    self.add_strip('right', 'border', self.width_border, 'none', 'none', 'none')
                    self.add_strip('right', 'line', 0.0, 'none', 'none', 'none')
                elif idx == self.num_lanes_right - 2:
                    self.add_strip('right', 'driving', self.width_driving, 'none', 'none', 'none')
                    self.add_strip('right', 'line', 0.0, 'solid', 'standard', 'white')
                else:
                    self.add_strip('right', 'driving', self.width_driving, 'none', 'none', 'none')
                    self.add_strip('right', 'line', 0.0, 'broken', 'standard', 'white')

    def add_strip(self, direction, type, width, road_mark_type, road_mark_weight, road_mark_color, split_right=False):
        strip = self.strips.add()
        strip.idx = self.strip_idx_current
        self.strip_idx_current += 1
        strip.direction = direction
        strip.type = type
        strip.width = width
        strip.road_mark_type = road_mark_type
        strip.road_mark_weight = road_mark_weight
        strip.road_mark_color = road_mark_color
        strip.split_right = split_right

    def update_cross_section(self):
        # Reset
        self.clear_strips()
        num_lanes_left = 0
        num_lanes_right = 0
        # Build up cross section
        params = params_cross_section[self.cross_section_preset]
        for idx in range(len(params['directions'])):
            self.add_strip(params['directions'][idx], params['types'][idx],
                params['widths'][idx], params['road_mark_types'][idx],
                params['road_mark_weights'][idx], params['road_mark_colors'][idx])
            if params['types'][idx] != 'line':
                if params['directions'][idx] == 'left':
                    num_lanes_left += 1
                if params['directions'][idx] == 'right':
                    num_lanes_right += 1
        self.print_cross_section()
        # Block recursive callbacks
        self.lock_strips = True
        self.num_lanes_left = num_lanes_left
        self.num_lanes_right = num_lanes_right
        # Re-activate callbacks
        self.lock_strips = False

    def print_cross_section(self):
        print('New cross section:', self.cross_section_preset)
        directions = []
        widths = []
        types = []
        road_mark_types = []
        for strip in self.strips:
            directions.append(strip.direction)
            widths.append(strip.width)
            types.append(strip.type)
            road_mark_types.append(strip.road_mark_type)

# Helpers

def get_num_split_lanes_left(road_properties):
    '''
        Convert road split strip index to road split lane number.
    '''
    num_split_lanes_left = 0
    for idx, strip in enumerate(road_properties.strips):
        if idx < road_properties.road_split_strip_idx:
            if strip.type != 'line':
                num_split_lanes_left += 1
    return num_split_lanes_left
