import math
from types import MethodType, SimpleNamespace

import bpy
from mathutils import Vector

from addon.entity import entity as EntityMesh
from addon.entity import VEHICLE_PAINT_MATERIALS
from addon.entity_trailer import DSC_OT_entity_trailer
from addon.entity_vehicle import (
    DSC_OT_entity_vehicle,
    VEHICLE_GEOMETRY_DIMENSIONS,
)


VEHICLE_SUBTYPES = (
    'motorcycle', 'bicycle', 'van', 'bus', 'heavyTruck', 'semiTrailer',
)
REQUIRED_MATERIALS = {
    'motorcycle': {'frame', 'metal', 'headlight', 'taillight', 'indicator',
                   'rider_skin', 'rider_clothing', 'rider_trousers',
                   'rider_helmet'},
    'bicycle': {'frame', 'metal', 'rubber', 'rider_skin', 'rider_clothing',
                'rider_trousers', 'rider_hair', 'rider_eyes'},
    'van': {'glass', 'headlight', 'taillight'},
    'bus': {'glass', 'headlight', 'taillight', 'indicator'},
    'heavyTruck': {'glass', 'headlight', 'indicator', 'cab_paint'},
    'semiTrailer': {'trailer_paint', 'kingpin'},
}


def operator_probe(operator_class, subtype):
    operator = SimpleNamespace(entity_subtype=subtype)
    for base in reversed(operator_class.__mro__):
        for name, member in base.__dict__.items():
            if isinstance(member, staticmethod):
                setattr(operator, name, member.__func__)
            elif callable(member):
                setattr(operator, name, MethodType(member, operator))
            elif not name.startswith('__') and not hasattr(operator, name):
                try:
                    setattr(operator, name, member)
                except (AttributeError, TypeError):
                    pass
    return operator


def vehicle_probe(subtype):
    return operator_probe(DSC_OT_entity_vehicle, subtype)


def trailer_probe():
    return operator_probe(DSC_OT_entity_trailer, 'semiTrailer')


def assert_mesh_is_sound(vertices, edges, faces, materials):
    assert vertices and faces
    assert len(faces) == len(materials)

    face_edges = {
        (min(first, second), max(first, second))
        for face in faces
        for first, second in zip(face, face[1:] + face[:1])
    }
    assert all((min(first, second), max(first, second)) in face_edges
               for first, second in edges)
    signatures = {
        tuple(sorted(tuple(round(value, 7) for value in vertices[index])
                     for index in face))
        for face in faces
    }
    assert len(signatures) == len(faces)

    mesh = bpy.data.meshes.new('VehicleGeometryTest')
    try:
        mesh.from_pydata(vertices, edges, faces)
        mesh.update()
        assert len(mesh.polygons) == len(faces)
        assert all(polygon.area > 1e-8 for polygon in mesh.polygons)
    finally:
        bpy.data.meshes.remove(mesh)


def material_names(materials):
    return {assignment[0] for assignment in materials if assignment}


def test_vehicle_registration_and_paint_material_targets():
    assert DSC_OT_entity_vehicle.bl_idname == 'dsc.entity_vehicle'
    assert DSC_OT_entity_trailer.bl_idname == 'dsc.entity_trailer'
    assert DSC_OT_entity_trailer.bl_idname != DSC_OT_entity_vehicle.bl_idname
    assert VEHICLE_PAINT_MATERIALS['heavyTruck'] == frozenset({'cab_paint'})
    assert VEHICLE_PAINT_MATERIALS['semiTrailer'] == frozenset({'trailer_paint'})


def test_non_car_vehicle_meshes_have_valid_geometry_and_expected_features():
    for subtype in VEHICLE_SUBTYPES:
        operator = trailer_probe() if subtype == 'semiTrailer' else vehicle_probe(subtype)
        vertices, edges, faces = operator.get_vertices_edges_faces()
        materials = operator.get_face_materials()

        assert_mesh_is_sound(vertices, edges, faces, materials)
        assert REQUIRED_MATERIALS[subtype] <= material_names(materials), subtype
        assert len(operator.get_wheel_configs()) == len(
            VEHICLE_GEOMETRY_DIMENSIONS[subtype]['wheel_positions'])

    bicycle = vehicle_probe('bicycle')
    bicycle.get_vertices_edges_faces()
    bicycle_materials = bicycle.get_face_materials()
    assert 'rider_helmet' not in material_names(bicycle_materials)
    assert 'rider_visor' not in material_names(bicycle_materials)


def test_vehicle_dimensions_and_rear_axle_origins():
    expected_dimensions = {
        'van': (5.93, 2.02, 2.62),
        'bus': (13.115, 2.50, 3.25),
        'heavyTruck': (16.5, 2.50, 4.0),
    }
    for subtype, (length, width, height) in expected_dimensions.items():
        config = VEHICLE_GEOMETRY_DIMENSIONS[subtype]
        assert math.isclose(config['length'], length)
        assert math.isclose(config['half_width'] * 2, width)
        assert math.isclose(config['height'], height)

    bicycle = VEHICLE_GEOMETRY_DIMENSIONS['bicycle']
    motorcycle = VEHICLE_GEOMETRY_DIMENSIONS['motorcycle']
    assert math.isclose(bicycle['wheel_radius'] * 2, 28 * 0.0254)
    assert math.isclose(
        bicycle['wheel_positions'][0][1] - bicycle['wheel_positions'][1][1],
        1.0928,
    )
    assert math.isclose(
        motorcycle['wheel_positions'][0][1] - motorcycle['wheel_positions'][1][1],
        1.46,
    )

    rear_wheels = {
        'van': ('wheel_rl', 'wheel_rr'),
        'bicycle': ('wheel_r',),
        'motorcycle': ('wheel_r',),
    }
    for subtype, names in rear_wheels.items():
        config = VEHICLE_GEOMETRY_DIMENSIONS[subtype]
        rear_axle_x = next(
            x for name, x, _y in config['wheel_positions'] if name == names[0])
        assert math.isclose(config['origin_x'], rear_axle_x)
        wheels = {
            name: center for name, center, *_rest
            in vehicle_probe(subtype).get_wheel_configs()
        }
        for name in names:
            assert math.isclose(wheels[name][0], 0.0)
            assert math.isclose(wheels[name][2], config['wheel_radius'])


def test_semi_trailer_kingpin_matches_tractor_fifth_wheel():
    trailer_config = VEHICLE_GEOMETRY_DIMENSIONS['semiTrailer']
    truck_config = VEHICLE_GEOMETRY_DIMENSIONS['heavyTruck']
    assert math.isclose(trailer_config['kingpin_x'], truck_config['fifth_wheel_x'])

    trailer = trailer_probe()
    vertices, edges, faces = trailer.get_vertices_edges_faces()
    materials = trailer.get_face_materials()
    pin_vertices = {
        index
        for face, assignment in zip(faces, materials)
        if assignment and assignment[0] == 'kingpin'
        for index in face
    }
    assert pin_vertices
    pin_center_x = trailer_config['kingpin_x'] - trailer_config['origin_x']
    assert math.isclose(
        sum(vertices[index][0] for index in pin_vertices) / len(pin_vertices),
        pin_center_x, abs_tol=1e-5)
    assert math.isclose(
        min(vertices[index][2] for index in pin_vertices),
        trailer_config['kingpin_bottom_z'], abs_tol=1e-5)
    assert math.isclose(
        max(vertices[index][2] for index in pin_vertices),
        trailer_config['kingpin_top_z'], abs_tol=1e-5)
    assert_mesh_is_sound(vertices, edges, faces, materials)


def test_bus_and_van_mirrors_extend_beyond_both_sides():
    for subtype in ('bus', 'van'):
        config = VEHICLE_GEOMETRY_DIMENSIONS[subtype]
        vertices, _edges, _faces = vehicle_probe(subtype).get_vertices_edges_faces()
        outer_upper_vertices = [
            vertex for vertex in vertices
            if vertex[0] > 0.0
            and vertex[2] > config['height'] * 0.50
            and abs(vertex[1]) > config['half_width'] + 0.01
        ]
        assert {1 if vertex[1] > 0 else -1
                for vertex in outer_upper_vertices} == {-1, 1}, subtype


def test_car_wheel_arches_follow_wheel_radius():
    car = vehicle_probe('car')
    vertices, _edges, _faces = car.get_vertices_edges_faces()
    for wheel_x in (car.wheel_x_rear, car.wheel_x_front):
        center_x = -wheel_x + 1.5
        center_z = car.wheel_radius
        arch_radius = car.wheel_radius + 0.05
        arch_vertices = [
            vertex for vertex in vertices
            if math.isclose(abs(vertex[1]), 1.0, abs_tol=1e-6)
            and center_z <= vertex[2] <= center_z + arch_radius
            and math.isclose(
                math.hypot(vertex[0] - center_x, vertex[2] - center_z),
                arch_radius, abs_tol=1e-5)
        ]
        assert len(arch_vertices) >= 5


def test_wireframe_preview_contains_vehicle_wheel_edges():
    context = SimpleNamespace(scene=SimpleNamespace(dsc_properties=SimpleNamespace(
        entity_properties_vehicle=SimpleNamespace(
            name='Preview', speed_initial=0.0, color=(0.2, 0.4, 0.6, 1.0)))))
    params = {
        'point_start': Vector((0.0, 0.0, 0.0)),
        'point_end': Vector((1.0, 0.0, 0.0)),
        'normal_start': Vector((0.0, 0.0, 1.0)),
        'heading_override': 0.0,
    }

    for subtype in ('car',) + VEHICLE_SUBTYPES[:-1]:
        vehicle = vehicle_probe(subtype)
        body_vertices, body_edges, _body_faces = vehicle.get_vertices_edges_faces()
        wheel_configs = vehicle.get_wheel_configs()
        entity_mesh = EntityMesh(
            context, 'vehicle', subtype, vehicle.get_vertices_edges_faces,
            get_wheel_configs=vehicle.get_wheel_configs)
        valid, mesh, _matrix_world, _materials = entity_mesh.update_params_get_mesh(
            context, params, wireframe=True)
        try:
            assert valid, subtype
            assert not mesh.polygons, subtype
            actual_edges = {tuple(sorted(edge.vertices)) for edge in mesh.edges}
            vertex_offset = len(body_vertices)
            for _name, position, wheel_vertices, wheel_edges, wheel_faces in wheel_configs:
                assert len(mesh.vertices) >= vertex_offset + len(wheel_vertices)
                assert all(
                    tuple(sorted((vertex_offset + first, vertex_offset + second)))
                    in actual_edges
                    for first, second in wheel_edges
                ), subtype
                vertex_offset += len(wheel_vertices)
            assert len(mesh.edges) > len(body_edges), subtype
        finally:
            bpy.data.meshes.remove(mesh)
