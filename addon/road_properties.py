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
def callback_lane_width(self, context):
    self.update_lane_width(context)
def callback_road_mark_weight(self, context):
    self.update_road_mark_weight(context)
def callback_num_lanes(self, context):
    self.update_num_lanes()
def callback_road_split(self, context):
    self.update_road_split(context)

class DSC_enum_lane(bpy.types.PropertyGroup):
    idx: bpy.props.IntProperty(min=0)
    side: bpy.props.EnumProperty(
        items=(('left', 'left', '', 0),
               ('right', 'right', '', 1),
               ('center', 'center', '', 2),
              ),
        default='right',
    )
    width: bpy.props.FloatProperty(
        name='Width',
        default=4.0, min=0.01, max=10.0, step=1
    )
    # Used to open up a new lane or end a lane
    width_change: bpy.props.EnumProperty(
        name = 'Width change',
        items=(('none', 'None', '', 0),
               ('open', 'Open', '', 1),
               ('close', 'Close', '', 2),
              ),
        default='none',
    )
    type: bpy.props.EnumProperty(
        name = 'Type',
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
               ('entry', 'Entry', '', 13),
               ('exit', 'Exit', '', 14),
               ('onRamp', 'On ramp', '', 15),
               ('offRamp', 'Off ramp', '', 16),
               #('connectingRamp', 'Connecting ramp', '', 17),
               ('none', 'None', '', 18),
               ('center', 'Center', '', 19),
              ),
        default='driving',
        update=callback_lane_width,
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
    road_mark_color: bpy.props.EnumProperty(
        name = 'Color',
        items=(('none', 'None', '', 0),
               ('white', 'White', '', 1),
               ('yellow', 'Yellow', '', 2),
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
        update=callback_road_mark_weight,
    )
    road_mark_width: bpy.props.FloatProperty(
        name='Width of road mark line',
        default=0.12, min=0.0, max=10.0, step=1
    )

    # False for the lanes/lanes going left, True for those going right
    split_right: bpy.props.BoolProperty(description='Split above here', update=callback_road_split)

    def update_lane_width(self, context):
        mapping_width_type_lane = {
            'driving' : context.scene.road_properties.width_driving,
            'entry' : context.scene.road_properties.width_driving,
            'exit' : context.scene.road_properties.width_driving,
            'onRamp' : context.scene.road_properties.width_driving,
            'offRamp' : context.scene.road_properties.width_driving,
            'stop' : context.scene.road_properties.width_stop,
            'border' : context.scene.road_properties.width_border,
            'shoulder' : context.scene.road_properties.width_shoulder,
            'median' : context.scene.road_properties.width_median,
            'none' : context.scene.road_properties.width_none,
            'center': 0,
        }
        self.width = mapping_width_type_lane[self.type]

    def update_road_mark_weight(self, context):
        mapping_width_type_road_mark = {
            'none' : 0,
            'standard' : context.scene.road_properties.width_line_standard,
            'bold' : context.scene.road_properties.width_line_bold,
        }
        self.road_mark_width = mapping_width_type_road_mark[self.road_mark_weight]

    def update_road_split(self, context):
        # Avoid updating recursively
        if context.scene.road_properties.lock_lanes:
            return
        context.scene.road_properties.lock_lanes = True
        # Toggle
        if self.split_right == True:
            self.split_right = True
            road_split_lane_idx = self.idx
        else:
            self.split_right = False
            road_split_lane_idx = self.idx + 1
        # Handle edge case for lane 0 and split at lane -1
        num_lanes_left = context.scene.road_properties.num_lanes_left
        num_lanes_right = context.scene.road_properties.num_lanes_right
        center_lane_idx = num_lanes_left
        if road_split_lane_idx == center_lane_idx:
            if num_lanes_right > 0:
                road_split_lane_idx += 1
        # Handle first and last lane edge cases (minimum 1 split lane)
        if road_split_lane_idx == 0:
            road_split_lane_idx += 1
        if road_split_lane_idx > num_lanes_left + num_lanes_right:
            road_split_lane_idx = num_lanes_left + num_lanes_right
        # Store new split index
        context.scene.road_properties.road_split_lane_idx = road_split_lane_idx
        # Split at the desired lane
        for idx, lane in enumerate(context.scene.road_properties.lanes):
            if idx < road_split_lane_idx:
                lane.split_right = False
            else:
                lane.split_right = True
        # Unlock updating
        context.scene.road_properties.lock_lanes = False


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

    road_split_type: bpy.props.EnumProperty(
        name = 'Split type',
        items=(('none', 'None', '', 0),
               ('start', 'Start', '', 1),
               ('end', 'End', '', 2),
              ),
        default='none',
    )
    # Lane idx of first right lane in case of a split road (counting in -t direction)
    road_split_lane_idx: bpy.props.IntProperty(default=0, min=0)

    lane_idx_current: bpy.props.IntProperty(default=0, min=0)
    lanes: bpy.props.CollectionProperty(type=DSC_enum_lane)

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
                ('eka1_rq31_exit_lane_right_open', 'EKA 1, RQ 31 - exit lane right open', 'EKA 1, RQ 31 - exit lane right open'),
                ('eka1_rq31_exit_lane_right', 'EKA 1, RQ 31 - exit lane right', 'EKA 1, RQ 31 - exit lane right'),
                ('eka1_rq31_exit_right_continuation_begin_end', 'EKA 1, RQ 31 - exit right continuation begin/end', 'EKA 1, RQ 31 - exit right continuation begin/end'),
                ('eka1_rq31_exit_right_continuation_shoulder_begin', 'EKA 1, RQ 31 - exit right continuation shoulder begin', 'EKA 1, RQ 31 - exit right continuation shoulder begin'),
                ('eka1_rq31_exit_right_continuation_shoulder_end', 'EKA 1, RQ 31 - exit right continuation shoulder end', 'EKA 1, RQ 31 - exit right continuation shoulder end'),
                ('eka1_rq31_entry_right', 'EKA 1, RQ 31 - entry right', 'EKA 1, RQ 31 - entry right'),
                ('eka1_rq31_entry_right_close', 'EKA 1, RQ 31 - entry right close', 'EKA 1, RQ 31 - entry right close'),
                ('eka1_rq36', 'EKA 1, RQ 36', 'EKA 1, RQ 36'),
                ('eka1_rq43_5', 'EKA 1, RQ 43.5', 'EKA 1, RQ 43.5'),
                ('on_ramp_end', 'On ramp end', 'On ramp end'),
                ('on_ramp_shoulder_end', 'On ramp shoulder end', 'On ramp shoulder end'),
                ('on_ramp', 'On ramp', 'On ramp'),
                ('off_ramp_begin', 'Off ramp begin', 'Off ramp begin'),
                ('off_ramp_shoulder_begin', 'Off ramp shoulder begin', 'Off ramp shoulder begin'),
                ('off_ramp', 'Off ramp', 'Off ramp'),
                ('shoulder_left', 'Shoulder left', 'Shoulder left'),
                ('shoulder_right', 'Shoulder right', 'Shoulder right'),
            ),
            name='cross_section',
            description='Road cross section presets',
            default='two_lanes_default',
            update=callback_cross_section,
            )

    # A lock for deactivating callbacks
    lock_lanes: bpy.props.BoolProperty(default=False)

    def init(self):
        self.update_cross_section()

    def clear_lanes(self):
        self.lanes.clear()
        self.lane_idx_current = 0
        self.road_split_type = 'none'
        self.road_split_lane_idx = 1

    def update_num_lanes(self):
        # Do not update recursively when switching presets
        if self.lock_lanes:
            return
        # Avoid callbacks
        self.lock_lanes = True
        self.clear_lanes()
        # Left lanes
        for idx in range(self.num_lanes_left - 1,-1,-1):
            if self.num_lanes_left == 1:
                self.add_lane('left', 'driving', self.width_driving, 'none', 'solid', 'standard', 0.12, 'white')
            else:
                if idx == self.num_lanes_left - 1:
                    self.add_lane('left', 'border', self.width_border, 'none', 'none', 'none', 0.0, 'none')
                elif idx == 0:
                    self.add_lane('left', 'driving', self.width_driving, 'none', 'solid', 'standard', 0.12, 'white')
                else:
                    self.add_lane('left', 'driving', self.width_driving, 'none', 'broken', 'standard', 0.12, 'white')
        # Center line
        if self.num_lanes_left == 0:
            self.add_lane('center', 'driving', 0.0, 'none', 'solid', 'standard', 0.12, 'white')
        elif self.num_lanes_right == 0:
            self.add_lane('center', 'driving', 0.0, 'none', 'solid', 'standard', 0.12, 'white')
        else:
            self.add_lane('center', 'driving', 0.0, 'none', 'broken', 'standard', 0.12, 'white')
        # Right lanes
        for idx in range(self.num_lanes_right):
            if self.num_lanes_right == 1:
                self.add_lane('right', 'driving', self.width_driving, 'none', 'solid', 'standard', 0.12, 'white')
            else:
                if idx == self.num_lanes_right - 1:
                    self.add_lane('right', 'border', self.width_border, 'none', 'none', 'none', 0.0, 'none')
                elif idx == self.num_lanes_right - 2:
                    self.add_lane('right', 'driving', self.width_driving, 'none', 'solid', 'standard', 0.12, 'white')
                else:
                    self.add_lane('right', 'driving', self.width_driving, 'none', 'broken', 'standard', 0.12, 'white')
        self.road_split_type = 'none'
        # Set split index one above maximum to make all lanes go left
        self.road_split_lane_idx = self.num_lanes_left + self.num_lanes_right
        self.lanes[-1].split_right = True
        # Allow callbacks again
        self.lock_lanes = False

    def add_lane(self, side, type, width, width_change,
                 road_mark_type, road_mark_weight, road_mark_width, road_mark_color,
                 split_right=False):
        lane = self.lanes.add()
        lane.idx = self.lane_idx_current
        self.lane_idx_current += 1
        lane.side = side
        lane.type = type
        lane.width = width
        lane.width_change = width_change
        lane.road_mark_type = road_mark_type
        lane.road_mark_weight = road_mark_weight
        lane.road_mark_width = road_mark_width
        lane.road_mark_color = road_mark_color
        lane.split_right = split_right

    def update_cross_section(self):
        # Do not update recursively when switching presets
        if self.lock_lanes:
            return
        # Avoid callbacks
        self.lock_lanes = True
        # Reset
        self.clear_lanes()
        num_lanes_left = 0
        num_lanes_right = 0
        # Build up cross section
        params = params_cross_section[self.cross_section_preset]
        for idx in range(len(params['sides'])):
            self.add_lane(params['sides'][idx], params['types'][idx],
                params['widths'][idx], params['widths_change'][idx], params['road_mark_types'][idx],
                params['road_mark_weights'][idx], params['road_mark_widths'][idx],
                params['road_mark_colors'][idx])
            if params['sides'][idx] == 'left':
                num_lanes_left += 1
            if params['sides'][idx] == 'right':
                num_lanes_right += 1
        self.road_split_type = params['road_split_type']
        self.road_split_lane_idx = params['road_split_lane_idx']
        for idx, lane in enumerate(self.lanes):
            if idx < self.road_split_lane_idx:
                lane.split_right = False
            else:
                lane.split_right = True
        self.print_cross_section()
        # Block recursive callbacks
        self.num_lanes_left = num_lanes_left
        self.num_lanes_right = num_lanes_right
        # Allow callbacks again
        self.lock_lanes = False

    def print_cross_section(self):
        print('New cross section:', self.cross_section_preset)
        sides = []
        widths = []
        types = []
        road_mark_types = []
        for lane in self.lanes:
            sides.append(lane.side)
            widths.append(lane.width)
            types.append(lane.type)
            road_mark_types.append(lane.road_mark_type)
