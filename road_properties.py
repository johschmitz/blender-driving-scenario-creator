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

def update(self, context):
    self.update(context)

class DSC_enum_strip(bpy.types.PropertyGroup):
    direction: bpy.props.EnumProperty(
        items=(('left', 'left', '', 0),
               ('right', 'right', '', 1),
               ('center', 'center', '', 2),
              ),
        default='right',
    )
    width: bpy.props.FloatProperty(name='Width of strip',
        default=4.0, min=0.01, max=10.0, step=1)
    type: bpy.props.EnumProperty(
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
    )
    type_road_mark: bpy.props.EnumProperty(
        items=(('none', 'None', '', 0),
               ('solid', 'Solid', '', 1),
               ('broken', 'Broken', '', 2),
               #('solid_solid', 'Double solid solid', '', 3),
               #('solid_broken', 'Double solid broken', '', 4),
               #('broken_solid', 'Double broken solid', '', 5),
              ),
        default='none',
    )

class DSC_road_properties(bpy.types.PropertyGroup):
    lanes_left_num: bpy.props.IntProperty(default=2, min=0, max=20, update=update)
    lanes_right_num: bpy.props.IntProperty(default=2, min=1, max=20, update=update)
    width_line_thin: bpy.props.FloatProperty(default=0.12, min=0.01, max=1.0, step=1, update=update)
    width_line_bold: bpy.props.FloatProperty(default=0.25, min=0.01, max=1.0, step=1, update=update)
    length_line_broken: bpy.props.FloatProperty(default=3.0, min=0.01, max=10.0, step=1, update=update)
    ratio_line_gap: bpy.props.IntProperty(default=1, min=1, max=3, update=update)
    width_driving: bpy.props.FloatProperty(default=3.75, min=0.01, max=10.0, step=1, update=update)
    width_border: bpy.props.FloatProperty(default=0.2, min=0.01, max=1.0, step=1, update=update)
    # width_curb: bpy.props.FloatProperty(default=0.16, min=0.10, max=0.30, step=1, update=update)
    width_median: bpy.props.FloatProperty(default=1.75, min=0.01, max=10.0, step=1, update=update)
    width_stop: bpy.props.FloatProperty(default=2.5, min=0.01, max=10.0, step=1, update=update)
    width_shoulder: bpy.props.FloatProperty(default=2.5, min=0.01, max=10.0, step=1, update=update)
    width_none: bpy.props.FloatProperty(default=2.5, min=0.01, max=10.0, step=1, update=update)

    strips: bpy.props.CollectionProperty(type=DSC_enum_strip)

    def init(self):
        self.strips.clear()
        # Strips for standard double lane road
        self.add_strip('left', 'line', self.width_line_thin, 'none')
        self.add_strip('left', 'border', self.width_border, 'none')
        self.add_strip('left', 'line', self.width_line_thin, 'solid')
        self.add_strip('left', 'driving', self.width_driving, 'none')
        self.add_strip('center', 'line', self.width_line_thin, 'broken')
        self.add_strip('right', 'driving', self.width_driving, 'none')
        self.add_strip('right', 'line', self.width_line_thin, 'solid')
        self.add_strip('right', 'border', self.width_border, 'none')
        self.add_strip('right', 'line', self.width_line_thin, 'none')

    def update(self, context):
        self.strips.clear()
        # Left lanes
        for idx in range(self.lanes_left_num - 1,-1,-1):
            if self.lanes_left_num == 1:
                self.add_strip('left', 'line', self.width_line_thin, 'solid')
                self.add_strip('left', 'driving', self.width_driving, 'none')
            else:
                if idx == self.lanes_left_num - 1:
                    self.add_strip('left', 'line', self.width_line_thin, 'none')
                    self.add_strip('left', 'border', self.width_border, 'none')
                    self.add_strip('left', 'line', self.width_line_thin, 'solid')
                elif idx == 0:
                    self.add_strip('left', 'driving', self.width_driving, 'none')
                else:
                    self.add_strip('left', 'driving', self.width_driving, 'none')
                    self.add_strip('left', 'line', self.width_line_thin, 'broken')
        # Center line
        if self.lanes_left_num == 0:
            self.add_strip('center', 'line', self.width_line_thin, 'solid')
        elif self.lanes_right_num == 0:
            self.add_strip('center', 'line', self.width_line_thin, 'solid')
        else:
            self.add_strip('center', 'line', self.width_line_thin, 'broken')
        # Right lanes
        for idx in range(self.lanes_right_num):
            if self.lanes_right_num == 1:
                self.add_strip('right', 'driving', self.width_driving, 'none')
                self.add_strip('right', 'line', self.width_line_thin, 'solid')
            else:
                if idx == self.lanes_right_num - 1:
                    self.add_strip('right', 'border', self.width_border, 'none')
                    self.add_strip('right', 'line', self.width_line_thin, 'none')
                elif idx == self.lanes_right_num - 2:
                    self.add_strip('right', 'driving', self.width_driving, 'none')
                    self.add_strip('right', 'line', self.width_line_thin, 'solid')
                else:
                    self.add_strip('right', 'driving', self.width_driving, 'none')
                    self.add_strip('right', 'line', self.width_line_thin, 'broken')

    def add_strip(self, direction, type, width, type_road_mark='none'):
        strip = self.strips.add()
        strip.direction = direction
        strip.type = type
        strip.width = width
        strip.type_road_mark = type_road_mark