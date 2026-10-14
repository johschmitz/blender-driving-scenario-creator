import math
from types import SimpleNamespace

from mathutils import Matrix, Vector

from addon import scenario_entity_move
from addon.entity_connections import ENTITY_CONNECTION_POINTS
from addon.scenario_entity_move import (
    _entity_transform_matrix,
    _fallback_move_point,
    _heading_only_target,
    _move_entity_origin,
    _should_rotate_connected_trailer,
    _set_cursor_to_object_origin,
)


def test_move_entity_transform_matches_placement_on_horizontal_surface():
    position = Vector((12.0, -4.0, 0.0))
    heading = math.pi / 3.0
    matrix = _entity_transform_matrix(
        position, heading, Vector((0.0, 0.0, 1.0)), Vector((1.0, 1.0, 1.0)))

    forward = matrix.to_3x3() @ Vector((1.0, 0.0, 0.0))
    assert (matrix.translation - position).length < 1e-6
    assert math.isclose(math.atan2(forward.y, forward.x), heading, abs_tol=1e-6)
    assert (matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))
            - Vector((0.0, 0.0, 1.0))).length < 1e-6


def test_move_entity_transform_aligns_to_sloped_road_normal():
    normal = Vector((0.0, -0.5, math.sqrt(0.75))).normalized()
    heading = math.pi / 4.0
    matrix = _entity_transform_matrix(
        Vector((2.0, 3.0, 1.0)), heading, normal, Vector((1.0, 1.0, 1.0)))

    transformed_up = matrix.to_3x3() @ Vector((0.0, 0.0, 1.0))
    assert (transformed_up - normal).length < 1e-6


def test_offroad_move_uses_drag_anchor_elevation(monkeypatch):
    requested_heights = []

    def project(_context, _event, height):
        requested_heights.append(height)
        return Vector((3.0, 4.0, height))

    monkeypatch.setattr(
        scenario_entity_move.helpers, 'mouse_to_xy_parallel_plane', project)
    event = type('Event', (), {'alt': False})()
    selected_elevation = 5.0

    result = _fallback_move_point(
        None, event, selected_elevation)

    assert requested_heights == [5.0]
    assert result == Vector((3.0, 4.0, 5.0))


def test_heading_only_move_uses_offroad_plane_without_road_snap(monkeypatch):
    requested_heights = []

    def project(_context, _event, height):
        requested_heights.append(height)
        return Vector((3.0, 4.0, height))

    monkeypatch.setattr(
        scenario_entity_move.helpers, 'mouse_to_xy_parallel_plane', project)
    event = type('Event', (), {'alt': True})()
    current_location = Vector((5.0, 7.0, 2.0))

    point, heading = _heading_only_target(
        None, event, current_location, 0.0)

    assert requested_heights == [2.0]
    assert point == Vector((3.0, 4.0, 2.0))
    assert math.isclose(heading, math.atan2(-3.0, -2.0), abs_tol=1e-6)


def test_alt_move_rotates_at_current_position_not_move_start(monkeypatch):
    current_position = Vector((10.0, 20.0, 0.0))
    current_matrix = _entity_transform_matrix(
        current_position, math.pi / 6.0, Vector((0.0, 0.0, 1.0)),
        Vector((1.0, 1.0, 1.0)))
    selected_obj = SimpleNamespace(matrix_world=current_matrix)
    captured = {}
    operator = SimpleNamespace(
        selected_obj=selected_obj,
        selected_obj_type='entity',
        initial_matrix=Matrix.Identity(4),
        pending_connection_target=None,
        transform_changed=False,
        _set_entity_transform=lambda location, heading, normal: captured.update(
            location=location.copy(), heading=heading, normal=normal.copy()),
    )
    context = SimpleNamespace(scene=SimpleNamespace(
        cursor=SimpleNamespace(location=Vector((0.0, 0.0, 0.0)))))
    event = SimpleNamespace(alt=True)
    monkeypatch.setattr(
        scenario_entity_move.helpers, 'mouse_to_xy_parallel_plane',
        lambda _context, _event, height: Vector((12.0, 22.0, height)))

    scenario_entity_move.DSC_OT_scenario_entity_move._update_transform(
        operator, context, event)

    assert (captured['location'] - current_position).length < 1e-6
    assert math.isclose(captured['heading'], math.pi / 4.0, abs_tol=1e-6)
    assert operator.transform_changed


def test_move_after_alt_rotation_keeps_the_new_heading(monkeypatch):
    class Entity(dict):
        name = 'trailer_1'

        def __init__(self):
            super().__init__(entity_subtype='semiTrailer', dsc_type='entity')
            self.matrix_world = _entity_transform_matrix(
                Vector((0.0, 0.0, 0.0)), 0.0,
                Vector((0.0, 0.0, 1.0)), Vector((1.0, 1.0, 1.0)))

    selected_obj = Entity()
    captured = {}

    def set_transform(location, heading, normal):
        selected_obj.matrix_world = _entity_transform_matrix(
            location, heading, normal, Vector((1.0, 1.0, 1.0)))
        captured['heading'] = heading

    operator = SimpleNamespace(
        selected_obj=selected_obj,
        selected_obj_type='entity',
        selected_elevation=0.0,
        initial_location=Vector((0.0, 0.0, 0.0)),
        initial_rotation_euler=SimpleNamespace(z=0.0),
        initial_matrix=selected_obj.matrix_world.copy(),
        anchor_point=Vector((0.0, 0.0, 0.0)),
        _raycast_to_road_surface=lambda _context, _event: (
            Vector((5.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)), None),
        _set_entity_transform=set_transform,
    )
    context = SimpleNamespace(scene=SimpleNamespace(
        cursor=SimpleNamespace(location=Vector((0.0, 0.0, 0.0)))))
    monkeypatch.setattr(
        scenario_entity_move.helpers, 'mouse_to_xy_parallel_plane',
        lambda _context, _event, height: Vector((0.0, 1.0, height)))
    monkeypatch.setattr(
        scenario_entity_move, 'get_connection_snap',
        lambda *_args, **_kwargs: None)

    scenario_entity_move.DSC_OT_scenario_entity_move._update_transform(
        operator, context, SimpleNamespace(alt=True))
    scenario_entity_move.DSC_OT_scenario_entity_move._update_transform(
        operator, context, SimpleNamespace(alt=False, shift=True))

    assert math.isclose(captured['heading'], math.pi / 2.0, abs_tol=1e-6)


def test_move_operator_cursor_tracks_object_world_origin():
    origin = Vector((12.0, -4.0, 2.5))
    obj = type('Object', (), {
        'matrix_world': _entity_transform_matrix(
            origin, math.pi / 4.0, Vector((0.0, 0.0, 1.0)),
            Vector((1.0, 1.0, 1.0)))
    })()
    context = type('Context', (), {
        'scene': type('Scene', (), {
            'cursor': type('Cursor', (), {'location': Vector()})(),
        })(),
    })()

    _set_cursor_to_object_origin(context, obj)

    assert (context.scene.cursor.location - origin).length < 1e-6


def test_move_operator_places_entity_origin_at_pointer_target():
    entity_origin = Vector((5.0, 8.0, 0.0))
    pointer_target = Vector((12.0, -3.0, 0.0))

    moved_origin = _move_entity_origin(
        entity_origin, entity_origin, pointer_target)

    assert (moved_origin - pointer_target).length < 1e-6


def test_move_operator_enters_rotation_only_for_snapped_trailer():
    trailer = {'entity_subtype': 'semiTrailer'}
    truck = {'entity_subtype': 'heavyTruck'}
    car = {'entity_subtype': 'car'}

    assert _should_rotate_connected_trailer('entity', trailer, truck)
    assert not _should_rotate_connected_trailer('entity', car, truck)
    assert not _should_rotate_connected_trailer('entity', trailer, car)
    assert not _should_rotate_connected_trailer('trajectory', trailer, truck)


def test_move_snap_preserves_trailer_heading_and_connects_coupler(monkeypatch):
    heading = math.pi / 2.0
    target_anchor = Vector((12.0, -4.0, 1.08))
    truck = SimpleNamespace(
        matrix_world=Matrix.Identity(4),
        get=lambda key, default=None: {
            'entity_subtype': 'heavyTruck',
        }.get(key, default),
    )
    class Trailer(dict):
        def __init__(self):
            super().__init__(entity_subtype='semiTrailer', dsc_type='entity')
            self.matrix_world = Matrix.Rotation(heading, 4, 'Z')

    trailer = Trailer()
    captured = {}
    operator = SimpleNamespace(
        selected_obj=trailer,
        selected_obj_type='entity',
        selected_elevation=0.0,
        initial_location=Vector((0.0, 0.0, 0.0)),
        initial_rotation_euler=SimpleNamespace(z=heading),
        initial_matrix=Matrix.Identity(4),
        anchor_point=Vector((0.0, 0.0, 0.0)),
        _raycast_to_road_surface=lambda _context, _event: (
            Vector((1.0, 2.0, 0.0)), Vector((0.0, 0.0, 1.0)), None),
        _set_entity_transform=lambda location, current_heading, normal: captured.update(
            location=location.copy(), heading=current_heading,
            normal=normal.copy()),
    )
    context = SimpleNamespace(scene=SimpleNamespace(
        cursor=SimpleNamespace(location=Vector((0.0, 0.0, 0.0)))))
    event = SimpleNamespace(alt=False, shift=True)
    monkeypatch.setattr(
        scenario_entity_move, 'get_connection_snap',
        lambda *_args, **_kwargs: (truck, target_anchor))
    monkeypatch.setattr(
        scenario_entity_move.helpers, 'clear_legacy_entity_transform_properties',
        lambda _obj: None)

    scenario_entity_move.DSC_OT_scenario_entity_move._update_transform(
        operator, context, event)

    assert math.isclose(captured['heading'], heading, abs_tol=1e-6)
    moved_matrix = _entity_transform_matrix(
        captured['location'], captured['heading'], captured['normal'],
        Vector((1.0, 1.0, 1.0)))
    coupler = moved_matrix @ Vector((
        ENTITY_CONNECTION_POINTS['semiTrailer']['x'], 0.0,
        ENTITY_CONNECTION_POINTS['semiTrailer']['z']))
    assert (coupler - target_anchor).length < 2e-6


def test_move_trailer_rotation_keeps_coupler_at_hitch(monkeypatch):
    pivot = Vector((12.0, -4.0, 1.08))
    heading = 0.0
    origin = scenario_entity_move.get_entity_position_from_connection_anchor(
        pivot, heading, Vector((0.0, 0.0, 1.0)), 'semiTrailer')
    selected_obj = SimpleNamespace(
        matrix_world=_entity_transform_matrix(
            origin, heading, Vector((0.0, 0.0, 1.0)), Vector((1.0, 1.0, 1.0))))
    operator = SimpleNamespace(
        selected_obj=selected_obj,
        rotation_pivot=pivot,
        rotation_start_heading=heading,
        rotation_normal=Vector((0.0, 0.0, 1.0)),
        rotation_start_pointer_angle=0.0,
        initial_matrix=selected_obj.matrix_world.copy(),
        transform_changed=False,
        _set_entity_transform=lambda location, target_heading, normal: setattr(
            selected_obj, 'matrix_world', _entity_transform_matrix(
                location, target_heading, normal, Vector((1.0, 1.0, 1.0)))),
    )
    context = SimpleNamespace(scene=SimpleNamespace(
        cursor=SimpleNamespace(location=Vector((0.0, 0.0, 0.0)))))
    event = SimpleNamespace(shift=True, alt=False)
    monkeypatch.setattr(
        scenario_entity_move.helpers, 'mouse_to_xy_parallel_plane',
        lambda _context, _event, _height: Vector((12.0, -3.0, 1.08)))

    scenario_entity_move.DSC_OT_scenario_entity_move._update_trailer_rotation(
        operator, context, event)

    coupler = selected_obj.matrix_world @ Vector((
        ENTITY_CONNECTION_POINTS['semiTrailer']['x'], 0.0,
        ENTITY_CONNECTION_POINTS['semiTrailer']['z']))
    assert (coupler - pivot).length < 2e-6
    assert operator.transform_changed
