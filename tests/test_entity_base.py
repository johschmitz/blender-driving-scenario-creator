import math

from mathutils import Matrix, Vector

from addon import entity_base
from addon.entity_base import (
    _heading_after_pointer_rotation,
    _quantize_rotation_delta,
    _choose_trailer_road_solution,
    _trailer_road_circle_intersections,
    _trailer_rotation_uses_lane_snap,
)


def test_trailer_rotation_pointer_delta_wraps_at_pi_boundary():
    heading = _heading_after_pointer_rotation(
        0.4, math.pi - 0.1, -math.pi + 0.1)

    assert math.isclose(heading, 0.6, abs_tol=1e-6)


def test_alt_rotation_delta_snaps_to_relative_15_degree_steps():
    delta = _quantize_rotation_delta(math.radians(22.0))

    assert math.isclose(delta, math.pi / 12.0, abs_tol=1e-6)


def test_trailer_rotation_snaps_only_without_shift_or_alt():
    event = type('Event', (), {'shift': False, 'alt': False})()
    assert _trailer_rotation_uses_lane_snap(event)

    event.shift = True
    assert not _trailer_rotation_uses_lane_snap(event)

    event.shift = False
    event.alt = True
    assert not _trailer_rotation_uses_lane_snap(event)


def test_trailer_rotation_keeps_cursor_at_origin_and_uses_pointer_target(monkeypatch):
    pivot = entity_base.Vector((0.0, 0.0, 1.08))
    pointer_target = entity_base.Vector((10.0, 10.0, 1.08))
    monkeypatch.setattr(
        entity_base.helpers, 'mouse_to_xy_parallel_plane',
        lambda _context, _event, _height: pointer_target)
    operator = type('Operator', (), {
        'rotation_pivot': pivot,
        'rotation_start_heading': 0.0,
        'rotation_normal': entity_base.Vector((0.0, 0.0, 1.0)),
        'rotation_start_pointer_angle': 0.0,
        'placement_heading': 0.0,
        'placement_position': entity_base.Vector((0.0, 0.0, 0.0)),
        'entity_subtype': 'semiTrailer',
        'selected_point': entity_base.Vector((0.0, 0.0, 0.0)),
        'params_input': {},
        '_apply_trailer_rotation_pose': lambda self, context, origin, heading:
            entity_base.DSC_OT_entity._apply_trailer_rotation_pose(
                self, context, origin, heading),
        'update_stencil': lambda *_args, **_kwargs: None,
    })()
    cursor = type('Cursor', (), {
        'location': entity_base.Vector((0.0, 0.0, 0.0))})()
    context = type('Context', (), {
        'scene': type('Scene', (), {'cursor': cursor})()})()
    event = type('Event', (), {'alt': False, 'shift': True})()

    entity_base.DSC_OT_entity._update_trailer_rotation(
        operator, context, event)

    assert (cursor.location - operator.placement_position).length < 1e-6
    assert (cursor.location - pointer_target).length > 1.0


def test_trailer_road_arc_intersections_are_exact_and_deterministic():
    class CircularLaneGeometry:
        total_length = 10.0 * math.pi
        matrix_world = Matrix.Identity(4)

        def sample_plan_view(self, station):
            angle = station / 5.0
            return (5.0 * math.cos(angle), 5.0 * math.sin(angle),
                    angle + math.pi / 2.0, 0.2)

        def sample_cross_section(self, station, offsets, _with_lane_offset):
            angle = station / 5.0
            return ([((5.0 - offset) * math.cos(angle),
                      (5.0 - offset) * math.sin(angle), 0.0)
                     for offset in offsets], 0.0, 0.0)

    geometry = CircularLaneGeometry()
    road = {
        'geometry_total_length': geometry.total_length,
        'lane_offset_coefficients': {'a': 0.0, 'b': 0.0, 'c': 0.0, 'd': 0.0},
        'lanes_left_widths_start': [],
        'lanes_left_widths_end': [],
        'lanes_left_types': [],
        'lanes_right_widths_start': [0.1],
        'lanes_right_widths_end': [0.1],
        'lanes_right_types': ['driving'],
    }
    pivot = Vector((2.0, 0.0, 1.08))
    intersections = _trailer_road_circle_intersections(
        road, geometry, 'right', 0, pivot, 4.0)

    assert len(intersections) == 2
    initial_origin = Vector((0.0, -5.05, 0.0))
    first_solution = _choose_trailer_road_solution(
        intersections, pivot, initial_origin)
    second_solution = _choose_trailer_road_solution(
        intersections, pivot, initial_origin)

    assert first_solution is not None
    assert (first_solution[0] - second_solution[0]).length < 1e-9
    assert math.isclose(
        (first_solution[0].to_2d() - pivot.to_2d()).length,
        4.0, abs_tol=1e-5)


def test_trailer_road_solution_stays_on_initial_intersection():
    pivot = Vector((0.0, 0.0, 1.08))
    first_origin = Vector((2.0, 0.0, 0.0))
    second_origin = Vector((-2.0, 0.0, 0.0))
    intersections = [
        (1.0, first_origin, math.pi),
        (2.0, second_origin, 0.0),
    ]

    first_solution = _choose_trailer_road_solution(
        intersections, pivot, first_origin)
    second_solution = _choose_trailer_road_solution(
        intersections, pivot, second_origin)

    assert (first_solution[0] - first_origin).length < 1e-6
    assert (second_solution[0] - second_origin).length < 1e-6
