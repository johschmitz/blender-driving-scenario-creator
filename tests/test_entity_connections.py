import xml.etree.ElementTree as ET
import math
from types import SimpleNamespace

from addon import entity_connections
from addon.entity_connections import (
    CONNECTION_SNAP_DISTANCE,
    ENTITY_CONNECTION_POINTS,
    _connection_anchor_world,
    add_connections_to_vehicle_catalog,
    get_connection_point_world,
    get_connection_snap,
    get_entity_position_from_connection_anchor,
    order_entities_for_scenario,
    record_entity_connection,
)
from addon.entity_vehicle import VEHICLE_GEOMETRY_DIMENSIONS
from mathutils import Matrix, Vector


def test_vehicle_catalog_gets_connection_points_and_trailer_reference(tmp_path):
    catalog_path = tmp_path / 'VehicleCatalog.xosc'
    root = ET.Element('OpenSCENARIO')
    catalog = ET.SubElement(root, 'Catalog')
    definition = ET.SubElement(catalog, 'CatalogDefinition')
    for name in ('tractor_1', 'trailer_1'):
        vehicle = ET.SubElement(definition, 'Vehicle', {'name': name})
        ET.SubElement(vehicle, 'BoundingBox')
    ET.ElementTree(root).write(catalog_path, encoding='utf-8')

    records = [
        ('tractor_1', 'heavyTruck', 'trailer_1'),
        ('trailer_1', 'semiTrailer', None),
    ]
    assert add_connections_to_vehicle_catalog(catalog_path, records)

    exported = ET.parse(catalog_path)
    tractor = exported.find(".//Vehicle[@name='tractor_1']")
    trailer = exported.find(".//Vehicle[@name='trailer_1']")
    assert tractor.find('TrailerHitch').attrib == {
        'dx': '0.55', 'dz': '1.08'}
    assert tractor.find('Trailer/TrailerRef').attrib == {
        'entityRef': 'trailer_1'}
    assert trailer.find('TrailerCoupler').attrib == {
        'dx': '8.4', 'dz': '1.08'}

    # Re-exporting a catalog is idempotent and does not duplicate XML nodes.
    assert add_connections_to_vehicle_catalog(catalog_path, records)
    exported = ET.parse(catalog_path)
    assert len(exported.findall(".//Vehicle[@name='tractor_1']/TrailerHitch")) == 1
    assert len(exported.findall(".//Vehicle[@name='tractor_1']/Trailer")) == 1


def test_connection_points_use_openscenario_tow_vehicle_and_trailer_roles():
    truck = VEHICLE_GEOMETRY_DIMENSIONS['heavyTruck']
    trailer = VEHICLE_GEOMETRY_DIMENSIONS['semiTrailer']
    assert ENTITY_CONNECTION_POINTS['heavyTruck']['element'] == 'TrailerHitch'
    assert ENTITY_CONNECTION_POINTS['semiTrailer']['element'] == 'TrailerCoupler'
    assert ENTITY_CONNECTION_POINTS['heavyTruck']['partner'] == 'semiTrailer'
    assert ENTITY_CONNECTION_POINTS['semiTrailer']['partner'] == 'heavyTruck'
    assert math.isclose(
        ENTITY_CONNECTION_POINTS['heavyTruck']['x'],
        truck['fifth_wheel_x'] - truck['origin_x'])
    assert math.isclose(
        ENTITY_CONNECTION_POINTS['semiTrailer']['x'],
        trailer['kingpin_x'] - trailer['source_origin_x']
        + trailer['source_origin_x'] - trailer['origin_x'])
    assert math.isclose(
        ENTITY_CONNECTION_POINTS['semiTrailer']['z'],
        (trailer['kingpin_bottom_z'] + trailer['kingpin_top_z']) * 0.5)
    assert math.isclose(
        ENTITY_CONNECTION_POINTS['heavyTruck']['z'],
        ENTITY_CONNECTION_POINTS['semiTrailer']['z'])


def test_connection_anchor_world_position_and_bidirectional_relation():
    class Entity(dict):
        def __init__(self, name, subtype, matrix_world):
            super().__init__(entity_subtype=subtype)
            self.name = name
            self.matrix_world = matrix_world

    truck = Entity('tractor_1', 'heavyTruck', Matrix.Translation((10, 20, 0)))
    trailer = Entity('trailer_1', 'semiTrailer', Matrix.Translation((0, 0, 0)))

    element, world_anchor = get_connection_point_world(truck)
    assert element == 'TrailerHitch'
    assert math.isclose(world_anchor.x, 10.55, abs_tol=1e-6)
    assert math.isclose(world_anchor.y, 20.0, abs_tol=1e-6)
    assert math.isclose(world_anchor.z, 1.08, abs_tol=1e-6)

    record_entity_connection(trailer, truck)
    assert truck['trailer_entity'] == trailer.name
    assert trailer['towing_vehicle_entity'] == truck.name


def test_connection_snap_uses_one_meter_world_space_radius(monkeypatch):
    class Entity(dict):
        def __init__(self, name, subtype, matrix_world):
            super().__init__(entity_subtype=subtype, dsc_type='entity')
            self.name = name
            self.matrix_world = matrix_world
            self.parent = None

    tractor = Entity('tractor_1', 'heavyTruck', Matrix.Identity(4))
    entities = SimpleNamespace(objects=[tractor])
    scenario = SimpleNamespace(children={'entities': entities})
    collections = {'OpenSCENARIO': scenario}
    monkeypatch.setattr(
        entity_connections, 'bpy',
        SimpleNamespace(data=SimpleNamespace(
            collections=SimpleNamespace(get=collections.get))))

    assert CONNECTION_SNAP_DISTANCE == 1.0
    target_anchor = get_connection_point_world(tractor)[1]
    coupler_x = ENTITY_CONNECTION_POINTS['semiTrailer']['x']

    def find_snap(gap):
        candidate_position = Vector((
            target_anchor.x + gap - coupler_x, 0.0, 0.0))
        return get_connection_snap(
            None, candidate_position, 0.0, Vector((0.0, 0.0, 1.0)),
            'semiTrailer')

    assert find_snap(0.9)[0] is tractor
    assert find_snap(1.1) is None


def test_trailer_coupler_position_is_transformed_with_candidate_entity():
    coupler_world = _connection_anchor_world(
        (-7.85, 0.0, 0.0), 0.0, (0.0, 0.0, 1.0), 'semiTrailer')
    hitch_world = _connection_anchor_world(
        (0.0, 0.0, 0.0), 0.0, (0.0, 0.0, 1.0), 'heavyTruck')

    # The trailer origin is metres away; its coupler, not the mouse/origin,
    # is the point that becomes coincident with the tractor hitch.
    assert math.isclose(coupler_world.x, hitch_world.x, abs_tol=1e-6)
    assert math.isclose(coupler_world.y, hitch_world.y, abs_tol=1e-6)
    assert math.isclose(coupler_world.z, hitch_world.z, abs_tol=1e-6)


def test_trailer_origin_can_rotate_around_fixed_coupler_anchor():
    class Entity(dict):
        def __init__(self, matrix_world):
            super().__init__(entity_subtype='semiTrailer')
            self.matrix_world = matrix_world

    pivot = Vector((12.0, -3.0, 1.08))
    for heading in (0.0, math.pi / 3.0, math.pi, -math.pi / 2.0):
        origin = get_entity_position_from_connection_anchor(
            pivot, heading, (0.0, 0.0, 1.0), 'semiTrailer')
        matrix_world = (Matrix.Translation(origin)
                        @ Matrix.Rotation(heading, 4, 'Z'))
        _element, coupler_world = get_connection_point_world(
            Entity(matrix_world))
        assert (coupler_world - pivot).length < 1e-6


def test_scenario_entity_order_resolves_trailer_before_towing_vehicle():
    class Entity(dict):
        def __init__(self, name, trailer_entity=None):
            super().__init__()
            self.name = name
            if trailer_entity is not None:
                self['trailer_entity'] = trailer_entity

    tractor = Entity('tractor_1', 'trailer_1')
    other_vehicle = Entity('car_1')
    trailer = Entity('trailer_1')

    ordered = order_entities_for_scenario([tractor, other_vehicle, trailer])
    assert [entity.name for entity in ordered] == [
        'car_1', 'trailer_1', 'tractor_1']
