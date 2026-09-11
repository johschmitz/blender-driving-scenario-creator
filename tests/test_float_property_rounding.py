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

from addon.helpers import round_float_property

import struct


def as_float_property(value):
    '''
        Return the value as it comes back from a single precision Blender float
        property, e.g. 0.15 becomes 0.15000000596046448.
    '''
    return struct.unpack('f', struct.pack('f', value))[0]


def test_single_precision_values_are_cleaned_up():
    # Lane widths and curb heights are the values which suffer the most
    for value in (0.12, 0.15, 0.3, 0.5, 1.75, 2.0, 3.5, 100.0):
        assert round_float_property(as_float_property(value)) == value
        assert round_float_property(as_float_property(-value)) == -value


def test_single_precision_artifacts_are_actually_present():
    # Make sure the test values are not clean by accident
    assert as_float_property(0.15) != 0.15
    assert as_float_property(0.12) != 0.12
    # Values which are exactly representable stay untouched
    assert as_float_property(3.5) == 3.5


def test_zero_and_exact_values_stay_unchanged():
    assert round_float_property(0.0) == 0.0
    assert round_float_property(3.5) == 3.5
    assert round_float_property(-0.25) == -0.25


class LaneStub:
    '''
        Minimal stand-in for a scenariogeneration lane recording its heights.
    '''
    def __init__(self):
        self.heights = []

    def add_height(self, inner, outer):
        self.heights.append((inner, outer))


def test_exported_lane_widths_are_cleaned_up():
    from addon.export import DSC_OT_export
    # Width of a curb lane as it is stored by a Blender float property
    width_curb = as_float_property(0.15)
    a, b, c, d = DSC_OT_export.get_lane_width_coefficients(None, width_curb, width_curb, 100.0)
    assert (a, b, c, d) == (0.15, 0.0, 0.0, 0.0)
    # Widening lane, the polynomial coefficients stay readable as well
    a, b, c, d = DSC_OT_export.get_lane_width_coefficients(
        None, as_float_property(3.5), as_float_property(0.15), 100.0)
    assert (a, b, c, d) == (3.5, 0.0, -0.001005, 6.7e-06)


def test_exported_lane_heights_are_cleaned_up():
    from addon.export import DSC_OT_export
    height_curb = as_float_property(0.12)
    lane = LaneStub()
    height_outer = DSC_OT_export.add_lane_height(None, lane, 'curb', 0.0, height_curb)
    assert lane.heights == [(0.12, 0.12)]
    # A walking lane behind the curb stays lifted at the curb height
    lane_walking = LaneStub()
    DSC_OT_export.add_lane_height(None, lane_walking, 'walking', height_outer, height_curb)
    assert lane_walking.heights == [(0.12, 0.12)]


def test_exported_curb_height_is_a_vertical_step():
    from addon.export import DSC_OT_export
    height_curb = 0.12
    # The lanes of one road side from the center outwards: border, curb, walking
    lane_border, lane_curb, lane_walking = LaneStub(), LaneStub(), LaneStub()
    height = 0.0
    height = DSC_OT_export.add_lane_height(None, lane_border, 'border', height, height_curb)
    height = DSC_OT_export.add_lane_height(None, lane_curb, 'curb', height, height_curb)
    height = DSC_OT_export.add_lane_height(None, lane_walking, 'walking', height, height_curb)
    # The curb surface is flat, the vertical face is the height step between
    # the border lane on the road surface and the raised curb lane
    assert lane_border.heights == []
    assert lane_curb.heights == [(height_curb, height_curb)]
    assert lane_walking.heights == [(height_curb, height_curb)]
    assert height == height_curb


def test_exported_curb_heights_accumulate():
    from addon.export import DSC_OT_export
    height_curb = 0.1
    lane_curb_1, lane_curb_2 = LaneStub(), LaneStub()
    height = DSC_OT_export.add_lane_height(None, lane_curb_1, 'curb', 0.0, height_curb)
    height = DSC_OT_export.add_lane_height(None, lane_curb_2, 'curb', height, height_curb)
    assert lane_curb_1.heights == [(0.1, 0.1)]
    assert lane_curb_2.heights == [(0.2, 0.2)]
