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

from addon import helpers

from mathutils import Vector
from pytest import approx

HEIGHT_CURB = 0.12

# Urban cross section, lanes ordered from the road center outwards
JOINT = {
    'id_joint': 0,
    'heading': 0.0,
    'lane_offset': 0.0,
    'contact_point_vec': Vector((0.0, 0.0, 0.0)),
    'lane_widths_left': [3.5, 0.3, 0.15, 2.0],
    'lane_widths_right': [3.5, 0.3, 0.15, 2.0],
    'lane_types_left': ['driving', 'border', 'curb', 'walking'],
    'lane_types_right': ['driving', 'border', 'curb', 'walking'],
    'height_curb': HEIGHT_CURB,
}


def test_lane_connection_groups():
    assert helpers.get_lane_connection_group('driving') == 'driving'
    assert helpers.get_lane_connection_group('onRamp') == 'driving'
    assert helpers.get_lane_connection_group('walking') == 'walking'
    assert helpers.get_lane_connection_group('sidewalk') == 'walking'
    assert helpers.get_lane_connection_group('biking') == 'biking'
    # Lanes which must not be connected by a connecting road
    assert helpers.get_lane_connection_group('curb') is None
    assert helpers.get_lane_connection_group('border') is None
    assert helpers.get_lane_connection_group('shoulder') is None
    assert helpers.get_lane_connection_group('none') is None


def test_joint_lane_height():
    # Only the lanes behind the curb are lifted
    assert helpers.get_joint_lane_height(JOINT, 'left', 0) == approx(0.0)
    assert helpers.get_joint_lane_height(JOINT, 'left', 1) == approx(0.0)
    assert helpers.get_joint_lane_height(JOINT, 'left', 2) == approx(0.0)
    assert helpers.get_joint_lane_height(JOINT, 'left', 3) == approx(HEIGHT_CURB)
    assert helpers.get_joint_lane_height(JOINT, 'right', 3) == approx(HEIGHT_CURB)
    # Junctions created before curb heights were introduced stay flat
    joint_without_curb_height = dict(JOINT)
    del joint_without_curb_height['height_curb']
    assert helpers.get_joint_lane_height(joint_without_curb_height, 'left', 3) == approx(0.0)


def test_snap_to_walking_lane_of_joint():
    # Point close to the center of the left walking lane
    point = Vector((0.0, 4.9, HEIGHT_CURB))
    _joint, id_lane, lane_width, lane_type, contact_point = \
        helpers.get_closest_joint_lane_contact_point(JOINT, point, joint_side='left')[:5]
    assert id_lane == 4
    assert lane_width == approx(2.0)
    assert lane_type == 'walking'
    # Contact point is the inner edge of the walking lane, lifted onto the curb
    assert contact_point.y == approx(3.95)
    assert contact_point.z == approx(HEIGHT_CURB)


def test_lane_type_group_restricts_snapping():
    point = Vector((0.0, 4.9, HEIGHT_CURB))
    # A connecting road started on a driving lane must not snap to the walkway
    _joint, id_lane, _width, lane_type, contact_point = \
        helpers.get_closest_joint_lane_contact_point(
            JOINT, point, joint_side='left', lane_type_group='driving')[:5]
    assert id_lane == 1
    assert lane_type == 'driving'
    assert contact_point.z == approx(0.0)
    # The other way round as well
    point = Vector((0.0, 1.75, 0.0))
    _joint, id_lane, _width, lane_type, _contact_point = \
        helpers.get_closest_joint_lane_contact_point(
            JOINT, point, joint_side='left', lane_type_group='walking')[:5]
    assert id_lane == 4
    assert lane_type == 'walking'


def test_border_and_curb_lanes_are_never_connected():
    # Point right on the curb lane center
    point = Vector((0.0, 3.875, 0.0))
    _joint, id_lane, _width, lane_type, _contact_point = \
        helpers.get_closest_joint_lane_contact_point(JOINT, point, joint_side='left')[:5]
    assert lane_type in ('driving', 'walking')
    assert id_lane in (1, 4)


def test_right_side_lanes_are_mirrored():
    point = Vector((0.0, -4.9, HEIGHT_CURB))
    _joint, id_lane, _width, lane_type, contact_point = \
        helpers.get_closest_joint_lane_contact_point(JOINT, point, joint_side='right')[:5]
    assert id_lane == -4
    assert lane_type == 'walking'
    assert contact_point.y == approx(-3.95)
    assert contact_point.z == approx(HEIGHT_CURB)
