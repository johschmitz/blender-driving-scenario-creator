# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

from types import SimpleNamespace

from addon.geometry_clothoid_triple import DSC_geometry_clothoid_triple
from addon.road import road


def test_clothoid_triple_sampling_breakpoints_include_short_middle_segment():
    geometry = DSC_geometry_clothoid_triple()
    geometry.total_length = 4.0
    geometry.section_curves = [SimpleNamespace(segments=[
        SimpleNamespace(length=1.0),
        SimpleNamespace(length=0.2),
        SimpleNamespace(length=2.8),
    ])]

    breakpoints = geometry.get_sampling_breakpoints()

    expected_breakpoints = [
        0.2, 0.4, 0.6, 0.8, 1.0,
        1.04, 1.08, 1.12, 1.16, 1.2,
        1.76, 2.32, 2.88, 3.44,
    ]
    assert len(breakpoints) == len(expected_breakpoints)
    assert all(abs(actual - expected) < 1e-9
               for actual, expected in zip(breakpoints, expected_breakpoints))


def test_road_mesh_sampling_visits_short_clothoid_interior():
    class FakeGeometry:
        total_length = 4.0
        sections = [{'curve_type': 'spiral_triple'}]

        def __init__(self):
            self.sampled_s = []

        def get_sampling_breakpoints(self):
            return [1.04, 1.08, 1.12, 1.16, 1.2]

        def sample_cross_section(self, s, t_values, with_lane_offset, z_values):
            self.sampled_s.append(s)
            return [(s, 0.0, 0.0), (s, 1.0, 0.0)], 0.0, 0.0

    geometry = FakeGeometry()
    road_obj = road(None, 'road', geometry, 'default')
    road_obj.get_strips_t_values = lambda _lanes, _s: ([0.0, 1.0], [0.0, 0.0])

    road_obj.get_road_sample_points([], [(None, [0.0, geometry.total_length])])

    for s in geometry.get_sampling_breakpoints():
        assert s in geometry.sampled_s
