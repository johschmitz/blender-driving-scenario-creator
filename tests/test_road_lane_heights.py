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
    def __init__(self, side, type, width_start, width_end, road_mark_type, road_mark_width,
                 road_mark_color='none'):
        self.side = side
        self.type = type
        self.width_start = width_start
        self.width_end = width_end
        self.road_mark_type = road_mark_type
        self.road_mark_width = road_mark_width
        self.road_mark_color = road_mark_color


def get_lanes(preset_name):
    params = params_cross_section[preset_name]
    return [Lane(params['sides'][idx], params['types'][idx],
                 params['widths_start'][idx], params['widths_end'][idx],
                 params['road_mark_types'][idx], params['road_mark_widths'][idx],
                 params['road_mark_colors'][idx])
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
    # borders of the center line marking and the vertical face of each curb
    assert z_values == approx([
        HEIGHT_CURB,  # outer edge left walking
        HEIGHT_CURB,  # outer edge left curb (top of the curb)
        HEIGHT_CURB,  # inner edge left curb, top of the vertical curb face
        0.0,          # inner edge left curb, bottom of the vertical curb face
        0.0,          # outer edge left driving
        0.0, 0.0,     # center line marking
        0.0,          # outer edge right driving
        0.0,          # inner edge right curb, bottom of the vertical curb face
        HEIGHT_CURB,  # inner edge right curb, top of the vertical curb face
        HEIGHT_CURB,  # outer edge right curb (top of the curb)
        HEIGHT_CURB,  # outer edge right walking
    ])


def test_curb_face_is_vertical():
    road_obj = get_road()
    lanes = get_lanes('urban_two_lanes_walkway')
    params = params_cross_section['urban_two_lanes_walkway']
    width_curb = params['widths_start'][1]
    t_values, z_values = road_obj.get_strips_t_values(lanes, 0.0)
    # The two strip borders of the vertical curb face share the same t value,
    # the curb top spans the curb width at the upper end of that face
    for idx_face, idx_top in ((2, 1), (8, 10)):
        assert t_values[idx_face] == approx(t_values[idx_face + 1])
        assert sorted([z_values[idx_face], z_values[idx_face + 1]]) == \
            approx([0.0, HEIGHT_CURB])
        assert abs(t_values[idx_top] - t_values[idx_face]) == approx(width_curb)
        assert z_values[idx_top] == approx(HEIGHT_CURB)


def test_strips_stay_consistent_with_vertical_curb_faces():
    road_obj = get_road()
    lanes = get_lanes('urban_two_lanes_walkway')
    t_values, _ = road_obj.get_strips_t_values(lanes, 0.0)
    strip_to_lane, strip_is_road_mark = road_obj.get_strip_to_lane_mapping(lanes)
    strips_s_boundaries = road_obj.get_strips_s_boundaries(lanes, 3.0, 6.0)
    num_strips = len(t_values) - 1
    assert len(strip_to_lane) == num_strips
    assert len(strip_is_road_mark) == num_strips
    assert len(strips_s_boundaries) == num_strips
    # Both the top and the vertical face of a curb belong to the curb lane
    assert [strip_to_lane[idx] for idx in (1, 2)] == [1, 1]
    assert [strip_to_lane[idx] for idx in (8, 9)] == [7, 7]


def test_face_materials_urban_cross_section():
    road_obj = get_road()
    lanes = get_lanes('urban_two_lanes_walkway')
    strips_s_boundaries = road_obj.get_strips_s_boundaries(lanes, 3.0, 6.0)
    materials = road_obj.get_face_materials(lanes, strips_s_boundaries)
    # Curbs and walking lanes get their own materials, the curbs contribute
    # twice as many faces because of their vertical faces
    num_faces_walking = len(strips_s_boundaries[0][1]) - 1
    assert len(materials['walking']) == 2 * num_faces_walking
    assert len(materials['curb']) == 4 * num_faces_walking
    assert not set(materials['curb']) & set(materials['walking'])
    assert not set(materials['curb']) & set(materials['asphalt'])


def test_sample_cross_section_lifts_curb_and_walkway():
    road_obj = get_road()
    lanes = get_lanes('urban_two_lanes_walkway')
    t_values, z_values = road_obj.get_strips_t_values(lanes, 0.0)
    xyz, _, _ = road_obj.geometry.sample_cross_section(0.0, t_values, True, z_values)
    assert [point[2] for point in xyz] == approx(z_values)
    # Without offsets everything stays on the road surface
    xyz_flat, _, _ = road_obj.geometry.sample_cross_section(0.0, t_values, True)
    assert [point[2] for point in xyz_flat] == approx([0.0] * len(t_values))
