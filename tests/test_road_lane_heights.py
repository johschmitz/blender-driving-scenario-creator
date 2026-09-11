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

from addon.road import road
from addon.geometry_line import DSC_geometry_line
from addon.params_cross_section import params_cross_section
from . helpers_test import params_input, get_heading_start

from mathutils import Vector
from pytest import approx

HEIGHT_CURB = 0.12


class Lane:
    '''
        Minimal stand-in for the DSC_enum_lane property group.
    '''
    def __init__(self, side, type, width_start, width_end, road_mark_type, road_mark_width):
        self.side = side
        self.type = type
        self.width_start = width_start
        self.width_end = width_end
        self.road_mark_type = road_mark_type
        self.road_mark_width = road_mark_width


def get_lanes(preset_name):
    params = params_cross_section[preset_name]
    return [Lane(params['sides'][idx], params['types'][idx],
                 params['widths_start'][idx], params['widths_end'][idx],
                 params['road_mark_types'][idx], params['road_mark_widths'][idx])
            for idx in range(len(params['sides']))]


def get_road(length=100.0):
    geometry = DSC_geometry_line()
    point_start = Vector((0.0, 0.0, 0.0))
    point_end = Vector((length, 0.0, 0.0))
    params = dict(params_input)
    params['points'] = [point_start, point_end]
    params['heading_start'] = get_heading_start(point_start, point_end)
    geometry.update(params, 0, 0, 'default')
    road_obj = road(None, 'road', geometry, 'default')
    road_obj.params = {'height_curb': HEIGHT_CURB}
    return road_obj


def test_lane_heights_without_curb():
    road_obj = get_road()
    lanes = get_lanes('two_lanes_default')
    heights = road_obj.get_lane_heights(lanes)
    assert heights == [(0.0, 0.0)] * len(lanes)


def test_lane_heights_urban_cross_section():
    road_obj = get_road()
    lanes = get_lanes('urban_two_lanes_walkway')
    heights = road_obj.get_lane_heights(lanes)
    # walking, curb, border, driving, center, driving, border, curb, walking
    assert heights == [
        (HEIGHT_CURB, HEIGHT_CURB),  # left walking stays lifted
        (0.0, HEIGHT_CURB),          # left curb ramps up towards the outside
        (0.0, 0.0),                  # left border
        (0.0, 0.0),                  # left driving
        (0.0, 0.0),                  # center
        (0.0, 0.0),                  # right driving
        (0.0, 0.0),                  # right border
        (0.0, HEIGHT_CURB),          # right curb ramps up towards the outside
        (HEIGHT_CURB, HEIGHT_CURB),  # right walking stays lifted
    ]


def test_strips_z_values_urban_cross_section():
    road_obj = get_road()
    lanes = get_lanes('urban_two_lanes_walkway')
    t_values, z_values = road_obj.get_strips_t_values(lanes, 0.0)
    assert len(t_values) == len(z_values)
    # Strip borders from left to right: outer edge of each lane plus the two
    # borders of the center line marking
    assert z_values == approx([
        HEIGHT_CURB,  # outer edge left walking
        HEIGHT_CURB,  # outer edge left curb (top of the curb)
        0.0,          # outer edge left border
        0.0,          # outer edge left driving
        0.0, 0.0,     # center line marking
        0.0,          # outer edge right driving
        0.0,          # outer edge right border
        HEIGHT_CURB,  # outer edge right curb (top of the curb)
        HEIGHT_CURB,  # outer edge right walking
    ])


def test_sample_cross_section_lifts_curb_and_walkway():
    road_obj = get_road()
    lanes = get_lanes('urban_two_lanes_walkway')
    t_values, z_values = road_obj.get_strips_t_values(lanes, 0.0)
    xyz, _, _ = road_obj.geometry.sample_cross_section(0.0, t_values, True, z_values)
    assert [point[2] for point in xyz] == approx(z_values)
    # Without offsets everything stays on the road surface
    xyz_flat, _, _ = road_obj.geometry.sample_cross_section(0.0, t_values, True)
    assert [point[2] for point in xyz_flat] == approx([0.0] * len(t_values))
