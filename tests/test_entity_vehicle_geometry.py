import bpy
import bmesh
import math
from types import MethodType, SimpleNamespace

from addon.entity_vehicle import (
    DSC_OT_entity_vehicle,
    VEHICLE_GEOMETRY_DIMENSIONS,
)


NON_CAR_SUBTYPES = ('motorcycle', 'bicycle', 'bus', 'heavyTruck', 'van')


def assert_no_orphan_edges_or_duplicate_faces(vertices, edges, faces):
    face_edges = set()
    face_signatures = {}
    for face_index, face in enumerate(faces):
        for first, second in zip(face, face[1:] + face[:1]):
            face_edges.add((min(first, second), max(first, second)))
        signature = tuple(sorted(
            tuple(round(coordinate, 7) for coordinate in vertices[index])
            for index in face
        ))
        face_signatures.setdefault(signature, []).append(face_index)

    orphan_edges = [edge for edge in edges
                    if (min(edge), max(edge)) not in face_edges]
    duplicate_faces = [indices for indices in face_signatures.values()
                       if len(indices) > 1]
    assert not orphan_edges, f'Edges are not connected to faces: {orphan_edges}'
    assert not duplicate_faces, f'Coincident duplicate faces: {duplicate_faces}'


def test_two_wheeler_dimensions_match_realistic_wheel_and_wheelbase_sizes():
    bicycle = VEHICLE_GEOMETRY_DIMENSIONS['bicycle']
    motorcycle = VEHICLE_GEOMETRY_DIMENSIONS['motorcycle']

    assert math.isclose(bicycle['wheel_radius'] * 2, 28 * 0.0254)
    assert math.isclose(
        max(position[1] for position in bicycle['wheel_positions'])
        - min(position[1] for position in bicycle['wheel_positions']),
        1.0928,
    )
    assert math.isclose(
        max(position[1] for position in motorcycle['wheel_positions'])
        - min(position[1] for position in motorcycle['wheel_positions']),
        1.46,
    )

    bicycle_vehicle = vehicle_probe('bicycle')
    bicycle_wheels = {
        name: (wheel_vertices, wheel_faces)
        for name, _center, wheel_vertices, _edges, wheel_faces
        in bicycle_vehicle.get_wheel_configs()
    }
    wheel_radius = bicycle['wheel_radius']
    half_width = bicycle['wheel_half_width']
    for wheel_name in ('wheel_f', 'wheel_r'):
        wheel_vertices, wheel_faces = bicycle_wheels[wheel_name]
        outer_tire_vertices = [
            vertex for vertex in wheel_vertices
            if math.isclose(abs(vertex[1]), half_width, abs_tol=1e-6)
            and math.isclose(math.hypot(vertex[0], vertex[2]), wheel_radius,
                             abs_tol=1e-6)
        ]
        assert len(outer_tire_vertices) == 64, wheel_name
        sidewall_faces = [
            face for face in wheel_faces
            if all(math.isclose(wheel_vertices[index][1],
                                wheel_vertices[face[0]][1], abs_tol=1e-6)
                   and math.isclose(abs(wheel_vertices[index][1]), half_width,
                                    abs_tol=1e-6) for index in face)
        ]
        assert len(sidewall_faces) == 64, wheel_name
        assert all(min(math.hypot(wheel_vertices[index][0],
                                  wheel_vertices[index][2])
                       for index in face) > wheel_radius - 0.036
                   for face in sidewall_faces), wheel_name
        spoke_faces = [
            face for face in wheel_faces
            if max(abs(wheel_vertices[index][1]) for index in face) < 0.003
            and max(math.hypot(wheel_vertices[index][0],
                               wheel_vertices[index][2]) for index in face)
            - min(math.hypot(wheel_vertices[index][0],
                             wheel_vertices[index][2]) for index in face) > 0.1
        ]
        assert len(spoke_faces) >= 64, (wheel_name, len(spoke_faces))
        axle_vertices = [vertex for vertex in wheel_vertices
                         if math.isclose(abs(vertex[1]), half_width + 0.035,
                                         abs_tol=1e-6)]
        assert axle_vertices, wheel_name


def test_van_dimensions_and_embedded_window_light_regions():
    van = VEHICLE_GEOMETRY_DIMENSIONS['van']
    assert math.isclose(van['length'], 5.93)
    assert math.isclose(van['half_width'] * 2, 2.02)
    assert math.isclose(van['height'], 2.62)
    assert math.isclose(
        max(position[1] for position in van['wheel_positions'])
        - min(position[1] for position in van['wheel_positions']),
        3.665,
    )

    vehicle = vehicle_probe('van')
    vertices, edges, faces = vehicle.get_vertices_edges_faces()
    rear_axle_x = van['wheel_positions'][2][1]
    assert van['origin_x'] == rear_axle_x
    van_wheels = {name: center for name, center, *_rest
                  in vehicle.get_wheel_configs()}
    assert math.isclose(van_wheels['wheel_rl'][0], 0.0)
    assert math.isclose(van_wheels['wheel_rr'][0], 0.0)
    vertices = [(x + van['origin_x'], y, z) for x, y, z in vertices]
    materials = vehicle.get_face_materials()
    mesh = bpy.data.meshes.new('VanEmbeddedDetailsTest')
    bm = bmesh.new()
    try:
        mesh.from_pydata(vertices, edges, faces)
        mesh.update()
        bm.from_mesh(mesh)
        material_counts = {}
        material_centers = {}
        material_widths = {}
        side_window_faces = 0
        side_window_sides = []
        side_window_heights = []
        side_window_x_widths = []
        front_window_heights = []
        front_window_widths = []
        rear_window_heights = []
        rear_window_widths = []
        for polygon, assignment in zip(mesh.polygons, materials):
            if assignment:
                name, _color = assignment
                material_counts[name] = material_counts.get(name, 0) + 1
                material_centers.setdefault(name, []).append(
                    (polygon.center.x, polygon.center.y, polygon.center.z))
                y_values = [vertices[index][1] for index in polygon.vertices]
                material_widths.setdefault(name, []).append(
                    max(y_values) - min(y_values))
                if name == 'glass' and all(
                    abs(abs(vertices[index][1]) - van['half_width']) < 1e-5
                        for index in polygon.vertices):
                    side_window_faces += 1
                    side_window_sides.append(len(polygon.vertices))
                    z_values = [vertices[index][2] for index in polygon.vertices]
                    side_window_heights.append(max(z_values) - min(z_values))
                    x_values = [vertices[index][0] for index in polygon.vertices]
                    side_window_x_widths.append(max(x_values) - min(x_values))
                elif name == 'glass':
                    x_values = [vertices[index][0] for index in polygon.vertices]
                    if max(x_values) - min(x_values) > 0.5:
                        z_values = [vertices[index][2] for index in polygon.vertices]
                        front_window_heights.append(max(z_values) - min(z_values))
                        y_values = [vertices[index][1] for index in polygon.vertices]
                        front_window_widths.append(max(y_values) - min(y_values))
                    elif max(x_values) - min(x_values) < 1e-5:
                        z_values = [vertices[index][2] for index in polygon.vertices]
                        rear_window_heights.append(max(z_values) - min(z_values))
                        y_values = [vertices[index][1] for index in polygon.vertices]
                        rear_window_widths.append(max(y_values) - min(y_values))
        assert len(mesh.polygons) == len(materials)
        assert material_counts.get('glass', 0) >= 3
        assert material_counts.get('headlight', 0) == 2
        assert all(math.isclose(width, 0.36, abs_tol=1e-5)
               for width in material_widths['headlight'])
        assert material_counts.get('taillight', 0) == 2
        assert material_counts.get('indicator', 0) == 4
        assert side_window_faces == 2
        assert side_window_sides == [4, 4]
        assert len(front_window_heights) == 1
        assert abs(front_window_heights[0] - side_window_heights[0]) < 0.2
        assert all(math.isclose(window_height, van['height'] * 0.38,
                    abs_tol=1e-5)
               for window_height in side_window_heights)
        assert all(width > 1.1 for width in side_window_x_widths)
        assert len(rear_window_heights) == 0
        assert len(front_window_widths) == 1
        front_indicators = [center for center in material_centers['indicator']
                            if center[0] > 0]
        rear_indicators = [center for center in material_centers['indicator']
                           if center[0] < 0]
        headlights = material_centers['headlight']
        taillights = material_centers['taillight']
        assert all(abs(indicator[2] - lamp[2]) < 1e-5
                   for indicators, lamps in ((front_indicators, headlights),
                                             (rear_indicators, taillights))
                   for indicator, lamp in zip(
                       sorted(indicators, key=lambda center: abs(center[1])),
                       sorted(lamps, key=lambda center: abs(center[1]))))
        assert all(abs(indicator[1]) > abs(lamp[1])
                   for indicators, lamps in ((front_indicators, headlights),
                                             (rear_indicators, taillights))
                   for indicator, lamp in zip(
                       sorted(indicators, key=lambda center: abs(center[1])),
                       sorted(lamps, key=lambda center: abs(center[1]))))
        assert sum(center[2] for center in taillights) / 2 < van['height'] / 2
        assert all(poly.area > 1e-8 for poly in mesh.polygons)
        assert all(len(edge.link_faces) == 2 for edge in bm.edges)
        mirror_center_z = van['height'] * 0.60
        pillar_lower = (van['length'] * 0.5, van['height'] * 0.48)
        pillar_upper = (pillar_lower[0] - 0.88, van['height'] * 0.94)
        pillar_fraction = (
            (mirror_center_z - pillar_lower[1])
            / (pillar_upper[1] - pillar_lower[1])
        )
        pillar_outer_x = pillar_lower[0] + pillar_fraction * (
            pillar_upper[0] - pillar_lower[0])
        window_lower_z = van['height'] * 0.50
        lower_pillar_fraction = (
            (window_lower_z - pillar_lower[1])
            / (pillar_upper[1] - pillar_lower[1])
        )
        window_lower = (
            pillar_lower[0]
            + lower_pillar_fraction * (pillar_upper[0] - pillar_lower[0])
            - 0.21,
            window_lower_z,
        )
        window_upper = (
            window_lower[0]
            + (pillar_upper[0] - pillar_lower[0])
            * (van['height'] * 0.88 - window_lower[1])
            / (pillar_upper[1] - pillar_lower[1]),
            van['height'] * 0.88,
        )
        assert math.isclose(
            (window_upper[0] - window_lower[0])
            / (window_upper[1] - window_lower[1]),
            (pillar_upper[0] - pillar_lower[0])
            / (pillar_upper[1] - pillar_lower[1]),
            abs_tol=1e-8,
        )
        for pillar_z in (window_lower[1], window_upper[1]):
            pillar_t = ((pillar_z - pillar_lower[1])
                        / (pillar_upper[1] - pillar_lower[1]))
            pillar_edge_x = pillar_lower[0] + pillar_t * (
                pillar_upper[0] - pillar_lower[0])
            window_t = ((pillar_z - window_lower[1])
                        / (window_upper[1] - window_lower[1]))
            window_edge_x = window_lower[0] + window_t * (
                window_upper[0] - window_lower[0])
            assert math.isclose(pillar_edge_x - window_edge_x, 0.21,
                                abs_tol=1e-8)
        window_fraction = (
            (mirror_center_z - window_lower[1])
            / (window_upper[1] - window_lower[1])
        )
        window_edge_x = window_lower[0] + window_fraction * (
            window_upper[0] - window_lower[0])
        pillar_center_x = (pillar_outer_x + window_edge_x) * 0.5
        mount_lateral_offset = 0.115
        mount_backward_offset = 0.03 + 0.035
        for _ in range(8):
            projected_radius = (
                0.035 * mount_lateral_offset
                / math.sqrt(mount_backward_offset ** 2
                            + mount_lateral_offset ** 2)
            )
            mount_backward_offset = 0.03 + projected_radius
        projected_radius = (
            0.035 * mount_lateral_offset
            / math.sqrt(mount_backward_offset ** 2 + mount_lateral_offset ** 2)
        )
        mirror_center_x = pillar_center_x - mount_backward_offset + projected_radius - 0.08
        mirror_center_y = van['half_width'] + mount_lateral_offset + 0.09 - 0.025
        for side in (-1, 1):
            assert any(
                abs(vertex[0] - mirror_center_x) <= 0.080001
                and abs(abs(vertex[1]) - mirror_center_y) <= 0.090001
                and abs(vertex[2] - mirror_center_z) <= 0.090001
                for vertex in vertices
            )
            assert any(
                abs(vertex[0] - (mirror_center_x + 0.08)) <= 1e-5
                and abs(abs(vertex[1]) - (mirror_center_y + 0.09)) <= 1e-5
                and abs(abs(vertex[2] - mirror_center_z) - 0.09) <= 1e-5
                for vertex in vertices
            )
    finally:
        bm.free()
        bpy.data.meshes.remove(mesh)


def test_car_has_van_style_side_mirrors_on_both_sides():
    car = vehicle_probe('car')
    vertices, edges, faces = car.get_vertices_edges_faces()
    materials = car.get_face_materials()
    assert_no_orphan_edges_or_duplicate_faces(vertices, edges, faces)
    mirror_center_z = 1.18
    pillar_fraction = (mirror_center_z - 1.10) / (1.72 - 1.10)
    pillar_outer_x = -1.30 + pillar_fraction * (-0.65 + 1.30)
    window_fraction = (mirror_center_z - 1.18) / (1.56 - 1.18)
    window_edge_x = -1.0 + window_fraction * (-0.62 + 1.0)
    authored_a_pillar_center_x = (pillar_outer_x + window_edge_x) * 0.5
    front_a_pillar_center_x = -authored_a_pillar_center_x + 1.5
    front_a_pillar_center_z = mirror_center_z
    full_mount_lateral_offset = 0.17
    full_mount_backward_offset = 0.03 + 0.035
    for _ in range(8):
        projected_radius = (
            0.035 * full_mount_lateral_offset
            / math.sqrt(full_mount_backward_offset ** 2
                        + full_mount_lateral_offset ** 2)
        )
        full_mount_backward_offset = 0.03 + projected_radius
    mount_lateral_offset = full_mount_lateral_offset * 0.5
    mount_backward_offset = full_mount_backward_offset * 0.5
    mount_x_per_y = mount_backward_offset / mount_lateral_offset
    mirror_pillar_root = (
        front_a_pillar_center_x + mount_x_per_y * 0.025,
        1.0 - 0.025,
        front_a_pillar_center_z,
    )
    projected_radius = (
        0.035 * mount_lateral_offset
        / math.sqrt(mount_backward_offset ** 2 + mount_lateral_offset ** 2)
    )
    mirror_front_edge_x = (
        front_a_pillar_center_x - mount_backward_offset + projected_radius
    )
    mirror_center_x = mirror_front_edge_x - 0.08
    mirror_center_z = front_a_pillar_center_z
    mirror_width_y = 0.18
    mirror_center_y = 1.0 + mount_lateral_offset + mirror_width_y * 0.5
    for side in (-1.0, 1.0):
        assert any(
            math.dist(vertex, (mirror_pillar_root[0],
                               side * mirror_pillar_root[1],
                               mirror_pillar_root[2])) <= 0.035 + 1e-5
            for vertex in vertices
        )
        assert any(
            abs(vertex[0] - mirror_center_x) <= 0.080001
            and abs(abs(vertex[1]) - mirror_center_y) <= mirror_width_y * 0.5 + 1e-6
            and abs(vertex[2] - mirror_center_z) <= 0.045001
            for vertex in vertices
        )
        assert any(
            abs(vertex[0] - mirror_front_edge_x) <= 1e-5
            and abs(abs(vertex[1]) - (mirror_center_y + mirror_width_y * 0.5)) <= 1e-5
            and abs(abs(vertex[2] - mirror_center_z) - 0.045) <= 1e-5
            for vertex in vertices
        )
        mirror_stem_end = (
            front_a_pillar_center_x - mount_backward_offset
            - mount_x_per_y * 0.025,
            side * (1.0 + mount_lateral_offset + 0.025),
            mirror_center_z,
        )
        assert any(math.dist(vertex, mirror_stem_end) <= 0.035 + 1e-5
                   for vertex in vertices)
        assert mirror_stem_end[0] < mirror_pillar_root[0]
    assert all(vertex[0] > 0.0 for vertex in vertices
               if abs(abs(vertex[1]) - mirror_center_y) <= mirror_width_y * 0.5 + 1e-6
               and abs(vertex[2] - mirror_center_z) <= 0.045)
    assert max(vertex[0] for vertex in vertices) > 2.20
    front_axle_x = car.wheel_x_front + car.origin_offset_x
    assert max(vertex[0] for vertex in vertices) > front_axle_x
    light_centers = {'headlight': [], 'taillight': []}
    for face, assignment in zip(faces, materials):
        if assignment and assignment[0] in light_centers:
            light_centers[assignment[0]].append(
                sum(vertices[index][0] for index in face) / len(face)
            )
    assert min(light_centers['headlight']) > max(light_centers['taillight'])
    assert any(assignment and assignment[0] == 'trim' for assignment in materials)


def test_car_wheel_houses_use_rounded_arches():
    car = vehicle_probe('car')
    vertices, _edges, _faces = car.get_vertices_edges_faces()
    for authored_wheel_x in (car.wheel_x_rear, car.wheel_x_front):
        arch_center_x = -authored_wheel_x + 1.5
        arch_center_z = car.wheel_radius
        arch_vertices = [
            vertex for vertex in vertices
            if abs(abs(vertex[1]) - 1.0) <= 1e-6
                and arch_center_z <= vertex[2] <= arch_center_z + car.wheel_radius + 0.05 + 1e-6
            and abs(math.hypot(vertex[0] - arch_center_x,
                               vertex[2] - arch_center_z)
                    - (car.wheel_radius + 0.05)) <= 1e-5
        ]
        assert len(arch_vertices) >= 5
        assert any(abs(vertex[0] - arch_center_x) <= 1e-5
                   and abs(vertex[2] - (arch_center_z + car.wheel_radius + 0.05)) <= 1e-5
                   for vertex in arch_vertices)


def test_bus_has_van_style_embedded_glazing_lights_and_mirrors():
    bus_config = VEHICLE_GEOMETRY_DIMENSIONS['bus']
    assert math.isclose(bus_config['length'], 13.115)
    assert math.isclose(bus_config['front_overhang'], 2.890)
    assert math.isclose(bus_config['wheelbase'], 6.090)
    assert math.isclose(bus_config['rear_axle_spacing'], 1.350)
    assert math.isclose(bus_config['rear_overhang'], 2.785)
    assert math.isclose(bus_config['origin_x'], -2.4225)
    vehicle = vehicle_probe('bus')
    vertices, edges, faces = vehicle.get_vertices_edges_faces()
    materials = vehicle.get_face_materials()
    mesh = bpy.data.meshes.new('BusEmbeddedDetailsTest')
    bm = bmesh.new()
    try:
        mesh.from_pydata(vertices, edges, faces)
        mesh.update()
        bm.from_mesh(mesh)
        assert len(mesh.polygons) == len(materials)
        assert all(poly.area > 1e-8 for poly in mesh.polygons)
        assert all(len(edge.link_faces) == 2 for edge in bm.edges)
        assert max(vertex[2] for vertex in vertices) <= bus_config['height']

        glass_faces = []
        lights = {}
        for polygon, assignment in zip(mesh.polygons, materials):
            if not assignment:
                continue
            name, _color = assignment
            if name == 'glass':
                glass_faces.append((polygon, name))
            elif name in {'headlight', 'taillight', 'indicator'}:
                lights.setdefault(name, []).append(polygon)

        assert len(lights['headlight']) == 2
        assert len(lights['taillight']) == 2
        assert len(lights['indicator']) == 4
        side_windows = [polygon for polygon, _name in glass_faces
                        if all(abs(abs(vertices[index][1]) - bus_config['half_width']) < 1e-5
                               for index in polygon.vertices)]
        end_windows = [polygon for polygon, _name in glass_faces
                       if polygon not in side_windows]
        assert len(side_windows) == 2
        assert len(end_windows) == 2
        side_window_heights = [
            max(vertices[index][2] for index in polygon.vertices)
            - min(vertices[index][2] for index in polygon.vertices)
            for polygon in side_windows
        ]
        end_widths = []
        for polygon in end_windows:
            y_values = [vertices[index][1] for index in polygon.vertices]
            end_widths.append(max(y_values) - min(y_values))
        assert abs(end_widths[0] - end_widths[1]) < 1e-5
        common_window_top_z = bus_config['height'] * 0.87
        shoulder_z = bus_config['height'] * 0.45 - 0.50
        roof_z = bus_config['height'] * 0.97
        windshield_bottom_z = shoulder_z + (roof_z - shoulder_z) * 0.01
        side_window_height = common_window_top_z - windshield_bottom_z
        assert all(math.isclose(window_height, side_window_height, abs_tol=1e-5)
                   for window_height in side_window_heights)
        front_end_window = max(
            end_windows, key=lambda polygon: polygon.center.x)
        rear_end_window = min(
            end_windows, key=lambda polygon: polygon.center.x)
        front_window_z = [vertices[index][2]
                          for index in front_end_window.vertices]
        rear_window_z = [vertices[index][2]
                         for index in rear_end_window.vertices]
        assert math.isclose(min(front_window_z), windshield_bottom_z,
                            abs_tol=1e-5)
        assert math.isclose(max(front_window_z), common_window_top_z,
                            abs_tol=1e-5)
        assert math.isclose(max(front_window_z) - min(front_window_z),
                            side_window_height, abs_tol=1e-5)
        for polygon in side_windows + [front_end_window, rear_end_window]:
            window_z = [vertices[index][2] for index in polygon.vertices]
            assert math.isclose(max(window_z), common_window_top_z,
                                abs_tol=1e-5)
        assert math.isclose(min(rear_window_z), bus_config['height'] * 0.61,
                            abs_tol=1e-5)
        assert math.isclose(max(rear_window_z), bus_config['height'] * 0.87,
                            abs_tol=1e-5)
        front_side_window = max(
            side_windows, key=lambda polygon: polygon.center.x)
        side_window_points = [vertices[index] for index in front_side_window.vertices]
        low_front_points = [point for point in side_window_points
                    if math.isclose(point[2], windshield_bottom_z,
                                    abs_tol=1e-5)]
        high_front_points = [point for point in side_window_points
                     if math.isclose(point[2], common_window_top_z,
                                     abs_tol=1e-5)]
        assert low_front_points and high_front_points
        side_front_lower_x = max(point[0] for point in low_front_points)
        side_front_upper_x = max(point[0] for point in high_front_points)
        pillar_x_per_z = (
            -0.35
            / (roof_z - shoulder_z)
        )
        expected_lower_x = (
            bus_config['length'] * 0.5 - bus_config['origin_x']
            + pillar_x_per_z * (windshield_bottom_z - shoulder_z) - 0.21
        )
        expected_upper_x = (
            bus_config['length'] * 0.5 - bus_config['origin_x']
            + pillar_x_per_z * (common_window_top_z - shoulder_z) - 0.21
        )
        assert math.isclose(side_front_lower_x, expected_lower_x, abs_tol=1e-5)
        assert math.isclose(side_front_upper_x, expected_upper_x, abs_tol=1e-5)
        assert math.isclose(
            (side_front_upper_x - side_front_lower_x)
            / (common_window_top_z - windshield_bottom_z),
            pillar_x_per_z,
            abs_tol=1e-5,
        )

        lamp_centers = {
            name: [(poly.center.x, poly.center.y, poly.center.z) for poly in polygons]
            for name, polygons in lights.items()
        }
        front_lamps = [point for point in lamp_centers['headlight'] if point[0] > 0]
        rear_lamps = [point for point in lamp_centers['taillight'] if point[0] < 0]
        front_indicators = [point for point in lamp_centers['indicator'] if point[0] > 0]
        rear_indicators = [point for point in lamp_centers['indicator'] if point[0] < 0]
        for indicators, lamps in ((front_indicators, front_lamps),
                                  (rear_indicators, rear_lamps)):
            assert all(abs(indicator[2] - lamp[2]) < 1e-5
                       for indicator, lamp in zip(
                           sorted(indicators, key=lambda point: abs(point[1])),
                           sorted(lamps, key=lambda point: abs(point[1]))))
            assert all(abs(indicator[1]) > abs(lamp[1])
                       for indicator, lamp in zip(
                           sorted(indicators, key=lambda point: abs(point[1])),
                           sorted(lamps, key=lambda point: abs(point[1]))))
        assert sum(point[2] for point in rear_lamps) / 2 < bus_config['height'] / 2
        bus_axles = {name: position[0]
                 for name, position, *_rest in vehicle.get_wheel_configs()}
        front_end_x = bus_config['length'] / 2 - bus_config['origin_x']
        rear_end_x = -bus_config['length'] / 2 - bus_config['origin_x']
        assert math.isclose(bus_axles['wheel_ml'], 0.0, abs_tol=1e-5)
        assert math.isclose(front_end_x - bus_axles['wheel_fl'],
                    bus_config['front_overhang'], abs_tol=1e-5)
        assert math.isclose(bus_axles['wheel_fl'] - bus_axles['wheel_ml'],
                    bus_config['wheelbase'], abs_tol=1e-5)
        assert math.isclose(abs(bus_axles['wheel_ml'] - bus_axles['wheel_rl']),
                    bus_config['rear_axle_spacing'], abs_tol=1e-5)
        assert math.isclose(bus_axles['wheel_rl'] - rear_end_x,
                    bus_config['rear_overhang'], abs_tol=1e-5)

        mirror_x = bus_config['length'] / 2 - 0.38 - bus_config['origin_x']
        mirror_z = bus_config['height'] * 0.84
        mirror_y = bus_config['half_width'] + 0.32
        for side in (-1, 1):
            assert any(abs(vertex[0] - mirror_x) < 0.12
                       and abs(abs(vertex[1]) - mirror_y) < 0.08
                       and abs(vertex[2] - mirror_z) < 0.08
                       for vertex in vertices)
    finally:
        bm.free()
        bpy.data.meshes.remove(mesh)


def test_actros_dimensions_and_separate_tractor_trailer_meshes():
    config = VEHICLE_GEOMETRY_DIMENSIONS['heavyTruck']
    origin_x = config['origin_x']
    assert math.isclose(config['length'], 16.5)
    assert math.isclose(config['half_width'] * 2, 2.50)
    assert math.isclose(config['trailer_half_width'] * 2, 2.50)
    assert math.isclose(config['height'], 4.0)
    assert len(config['wheel_positions']) == 10
    assert math.isclose(config['tractor_length'], 6.00)
    assert math.isclose(config['tractor_front_x'], 7.90)
    assert math.isclose(config['wheelbase'], 3.85)
    assert math.isclose(config['fifth_wheel_x']
                        - config['wheel_positions'][2][1], 0.55)
    assert math.isclose(config['tractor_deck_z'], config['fifth_wheel_bottom_z'])
    assert math.isclose(config['cab_roof_z'], config['trailer_roof_z'])
    assert math.isclose(config['cab_rear_x'], 5.15)
    assert math.isclose(config['trailer_front_x'], 4.75)
    assert math.isclose(config['trailer_floor_z'], 1.15)
    assert math.isclose(config['trailer_roof_z'], 4.00)
    assert math.isclose(config['trailer_roof_z'] - config['trailer_floor_z'], 2.85)
    assert math.isclose(config['trailer_interior_height'], 2.68)
    assert math.isclose(config['trailer_side_loading_height'], 2.60)
    assert math.isclose(config['fifth_wheel_bottom_z'], 1.03)
    assert math.isclose(2 * config['fifth_wheel_radius'], 1.0)
    assert math.isclose(config['trailer_rim_diameter'], 22.5 * 0.0254)
    assert math.isclose(config['trailer_wheel_radius'], 0.536)
    assert math.isclose(config['trailer_wheel_half_width'] * 2,
                        config['trailer_tire_width'])
    assert math.isclose(config['trailer_front_x'] - config['fifth_wheel_x'], 1.60)
    assert math.isclose(config['cab_rear_x'] - config['trailer_front_x'], 0.40)

    truck = vehicle_probe('heavyTruck')
    tractor_vertices, tractor_edges, tractor_faces = truck.get_vertices_edges_faces()
    assert any(abs(vertex[0] - (config['tractor_front_x'] - origin_x)) < 1e-5
               for vertex in tractor_vertices)
    assert abs(2 * max(abs(vertex[1]) for vertex in tractor_vertices) - 2.95) < 1e-5
    tractor_materials = truck.get_face_materials()
    wheel_configs = {name: (position, vertices)
                     for name, position, vertices, _edges, _faces
                     in truck.get_wheel_configs()}
    assert math.isclose(wheel_configs['wheel_fl'][0][0]
                        - wheel_configs['wheel_rl'][0][0], config['wheelbase'])
    assert math.isclose(config['tractor_front_x'] - origin_x
                        - wheel_configs['wheel_fl'][0][0], 1.45)
    assert math.isclose(wheel_configs['wheel_rl'][0][0]
                        - (config['tractor_rear_x'] - origin_x), 0.70)
    assert math.isclose(wheel_configs['wheel_rl'][0][0], 0.0)
    rear_tire_half_width = config['rear_wheel_half_width']
    rear_tire_width = max(abs(vertex[1])
                          for vertex in wheel_configs['wheel_rl'][1])
    front_tire_width = max(abs(vertex[1])
                           for vertex in wheel_configs['wheel_fl'][1])
    assert math.isclose(rear_tire_width, rear_tire_half_width)
    assert rear_tire_width > front_tire_width
    assert math.isclose(rear_tire_width * 2, 0.685)
    assert math.isclose(abs(wheel_configs['wheel_rl'][0][1]),
                        config['rear_wheel_center_y'])
    assert math.isclose(config['tractor_front_x'] - config['tractor_rear_x'],
                        config['tractor_length'])
    rear_wheel_x = config['wheel_positions'][2][1]
    frame_rear_x = config['wheel_positions'][2][1] - 0.75
    frame_front_x = config['wheel_positions'][0][1] + 0.50
    frame_length = frame_front_x - frame_rear_x
    bed_cutout_x_min = max(config['tractor_rear_x'], frame_rear_x) + 0.002 - origin_x
    bed_cutout_x_max = frame_front_x - 0.002 - origin_x
    bed_deck_x_min = (
        rear_wheel_x + config['wheel_radius'] + 0.10 + 0.10
        + 0.002 - origin_x
    )
    bed_deck_x_max = config['cab_rear_x'] - 0.002 - origin_x
    frame_outer_half_width = 0.50
    frame_rail_width = 0.17
    bed_cutout_half_width = frame_outer_half_width + 0.005
    bed_cut_top_z = 2 * config['wheel_radius'] + 0.25
    assert bed_cutout_half_width > frame_outer_half_width
    assert bed_cutout_half_width - frame_outer_half_width <= 0.01
    assert math.isclose(config['wheel_positions'][2][1] - frame_rear_x, 0.75)
    assert math.isclose(frame_front_x - config['wheel_positions'][0][1], 0.50)
    rear_cap_x = config['tractor_rear_x'] - origin_x
    rear_cap_faces = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'cab_paint'
        and all(abs(tractor_vertices[index][0] - rear_cap_x) < 1e-5
                for index in face)
    ]
    assert not rear_cap_faces
    rear_wheel_x_object = rear_wheel_x - origin_x
    body_rear_x_object = (
        rear_wheel_x + config['wheel_radius'] + 0.10 + 0.10 - origin_x
    )
    side_box_front_top_x_object = (
        rear_wheel_x + config['wheel_radius'] + 0.04 + 0.05 - origin_x
    )
    side_box_front_bottom_x_object = side_box_front_top_x_object + 0.10
    outer_painted_side_vertices = [
        tractor_vertices[index]
        for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'cab_paint'
        for index in face
        if abs(abs(tractor_vertices[index][1]) - config['half_width']) < 1e-5
    ]
    assert all(vertex[0] >= side_box_front_top_x_object - 1e-5
               for vertex in outer_painted_side_vertices)
    side_box_lateral_edges = (
        bed_cutout_half_width,
        config['half_width'],
    )
    for side in (-1.0, 1.0):
        for y_abs in side_box_lateral_edges:
            assert any(
                math.dist(vertex, (side_box_front_top_x_object,
                                   side * y_abs,
                                   config['tractor_deck_z'] - 0.002)) < 1e-5
                for vertex in tractor_vertices
            )
            assert any(
                math.dist(vertex, (side_box_front_bottom_x_object,
                                   side * y_abs,
                                   config['clearance'] + 0.002)) < 1e-5
                for vertex in tractor_vertices
            )
    rear_body_end_faces = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'cab_paint'
        and all(abs(tractor_vertices[index][0] - body_rear_x_object) < 1e-5
                for index in face)
    ]
    assert not any(
        max(tractor_vertices[index][1] for index in face)
        - min(tractor_vertices[index][1] for index in face) > 1.0
        for face in rear_body_end_faces
    )
    assert not any(
        math.dist(vertex, (-0.70, config['half_width'], config['clearance'])) < 1e-5
        for vertex in tractor_vertices
    )
    painted_faces_covering_rear_tire = []
    rear_fender_radius = config['wheel_radius'] + 0.10
    rear_arch_radius = rear_fender_radius + 0.08
    for face, assignment in zip(tractor_faces, tractor_materials):
        if not assignment or assignment[0] != 'cab_paint':
            continue
        points = [tractor_vertices[index] for index in face]
        if not all(abs(abs(point[1]) - config['half_width']) < 1e-5
                   for point in points):
            continue
        center_x = sum(point[0] for point in points) / len(points)
        center_z = sum(point[2] for point in points) / len(points)
        if (center_z >= config['clearance']
                and math.hypot(center_x - rear_wheel_x_object,
                               center_z - config['wheel_radius'])
                < rear_arch_radius - 0.03):
            painted_faces_covering_rear_tire.append(face)
    assert not painted_faces_covering_rear_tire
    blue_wheelhouse_facets = []
    for face, assignment in zip(tractor_faces, tractor_materials):
        if not assignment or assignment[0] != 'cab_paint':
            continue
        points = [tractor_vertices[index] for index in face]
        if max(point[1] for point in points) - min(point[1] for point in points) \
                < 2 * config['half_width'] - 1e-5:
            continue
        center_x = sum(point[0] for point in points) / len(points)
        center_z = sum(point[2] for point in points) / len(points)
        if (center_z > config['clearance'] + 0.01
                and math.hypot(center_x - rear_wheel_x_object,
                               center_z - config['wheel_radius'])
                < rear_arch_radius - 0.03):
            blue_wheelhouse_facets.append(face)
    assert not blue_wheelhouse_facets
    rear_guard_faces = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'trim'
        and max(tractor_vertices[index][0] for index in face)
        >= rear_wheel_x_object + config['wheel_radius'] + 0.08
        and min(tractor_vertices[index][0] for index in face)
        <= rear_wheel_x_object - config['wheel_radius'] - 0.08
        and max(tractor_vertices[index][2] for index in face)
        > 2 * config['wheel_radius']
        and min(abs(abs(sum(tractor_vertices[index][1] for index in face)
                       / len(face)) - y_position)
                for y_position in (
                    config['rear_wheel_center_y'] - 0.3525,
                    config['rear_wheel_center_y'] + 0.3525,
                )) < 0.03
    ]
    assert rear_guard_faces
    assert {
        1 if sum(tractor_vertices[index][1] for index in face) > 0 else -1
        for face in rear_guard_faces
    } == {-1, 1}
    rear_fender_side_y_positions = (
        config['rear_wheel_center_y']
        - (config['rear_wheel_half_width'] * 2 + 0.02) * 0.5,
        config['rear_wheel_center_y']
        + (config['rear_wheel_half_width'] * 2 + 0.02) * 0.5,
    )
    rear_fender_side_faces = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'trim'
        and len(face) == 8
        and any(
            all(abs(tractor_vertices[index][1] - side * y_position) < 1e-5
                for index in face)
            for side in (-1.0, 1.0)
            for y_position in rear_fender_side_y_positions
        )
        and min(tractor_vertices[index][0] for index in face)
        >= rear_wheel_x_object - config['wheel_radius'] - 0.18 - 1e-5
        and max(tractor_vertices[index][0] for index in face)
        <= rear_wheel_x_object + config['wheel_radius'] + 0.18 + 1e-5
    ]
    assert len(rear_fender_side_faces) == 4
    cab_rear_x = config['cab_rear_x'] - origin_x
    cab_bottom_gap_faces = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'cab_paint'
        and all(abs(tractor_vertices[index][0] - cab_rear_x) < 1e-5
                and abs(tractor_vertices[index][1]) < bed_cutout_half_width - 1e-5
                and config['tractor_deck_z'] - 1e-5
                <= tractor_vertices[index][2] < bed_cut_top_z - 1e-5
                for index in face)
    ]
    assert not cab_bottom_gap_faces
    frame_vertices = [
        tractor_vertices[index]
        for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'trim'
        for index in face
        if 0.32 <= abs(tractor_vertices[index][1]) <= 0.51
        and config['tractor_deck_z'] - 0.27
        <= tractor_vertices[index][2] <= config['tractor_deck_z'] + 1e-5
    ]
    assert frame_vertices
    assert math.isclose(min(vertex[0] for vertex in frame_vertices),
                        frame_rear_x - origin_x, abs_tol=1e-5)
    assert math.isclose(max(vertex[0] for vertex in frame_vertices),
                        frame_front_x - origin_x, abs_tol=1e-5)
    rail_face_z = {
        round(tractor_vertices[index][2], 5)
        for face, assignment in zip(tractor_faces, tractor_materials)
        for index in face
        if assignment and assignment[0] == 'trim'
        and max(tractor_vertices[index][0] for index in face)
        - min(tractor_vertices[index][0] for index in face) >= frame_length - 1e-5
        and abs((max(tractor_vertices[index][1] for index in face)
             - min(tractor_vertices[index][1] for index in face))
            - frame_rail_width) < 1e-5
        and max(tractor_vertices[index][2] for index in face)
        - min(tractor_vertices[index][2] for index in face) < 1e-5
    }
    assert rail_face_z == {
        round(config['tractor_deck_z'] - 0.26, 5),
        round(config['tractor_deck_z'] - 0.10, 5),
    }
    deck_plate_face_z = {
        round(tractor_vertices[index][2], 5)
        for face, assignment in zip(tractor_faces, tractor_materials)
        for index in face
        if assignment and assignment[0] == 'trim'
        and max(tractor_vertices[index][0] for index in face)
        - min(tractor_vertices[index][0] for index in face) >= frame_length - 1e-5
        and 0.999 <= max(tractor_vertices[index][1] for index in face)
        - min(tractor_vertices[index][1] for index in face) <= 1.001
        and max(tractor_vertices[index][2] for index in face)
        - min(tractor_vertices[index][2] for index in face) < 1e-5
    }
    assert deck_plate_face_z == {
        round(config['tractor_deck_z'] - 0.10, 5),
        round(config['tractor_deck_z'], 5),
    }
    frame_front_closure = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'trim'
        and all(abs(tractor_vertices[index][0] - (frame_front_x - origin_x))
                < 1e-5
                and abs(tractor_vertices[index][1])
                <= frame_outer_half_width - 0.08 + 1e-5
                and config['tractor_deck_z'] - 0.26 - 1e-5
                <= tractor_vertices[index][2]
                <= config['tractor_deck_z'] - 0.10 + 1e-5
                for index in face)
    ]
    assert frame_front_closure
    center_deck_faces = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'trim'
        and max(tractor_vertices[index][0] for index in face)
        - min(tractor_vertices[index][0] for index in face) >= frame_length - 1e-5
        and max(tractor_vertices[index][1] for index in face)
        - min(tractor_vertices[index][1] for index in face) > 0.99
        and min(tractor_vertices[index][2] for index in face)
        >= config['tractor_deck_z'] - 0.11
        and max(tractor_vertices[index][2] for index in face)
        <= config['tractor_deck_z'] + 1e-5
    ]
    assert center_deck_faces
    cab_paint_deck_faces = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'cab_paint'
        and all(abs(tractor_vertices[index][2] - config['tractor_deck_z']) < 1e-5
                for index in face)
    ]
    assert cab_paint_deck_faces
    for face in cab_paint_deck_faces:
        center_x = sum(tractor_vertices[index][0] for index in face) / len(face)
        center_y = sum(tractor_vertices[index][1] for index in face) / len(face)
        assert not (bed_deck_x_min < center_x < bed_deck_x_max
                    and abs(center_y) < bed_cutout_half_width)
    generated_gap_faces = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'cab_paint'
        and all(abs(abs(tractor_vertices[index][1]) - bed_cutout_half_width) < 1e-5
                and bed_cutout_x_min - 1e-5 <= tractor_vertices[index][0]
                <= bed_cutout_x_max + 1e-5
                and 0.0 <= tractor_vertices[index][2] <= bed_cut_top_z + 1e-5
                for index in face)
    ]
    assert generated_gap_faces
    gap_side_signs = {
        1 if sum(tractor_vertices[index][1] for index in face) > 0 else -1
        for face in generated_gap_faces
    }
    assert gap_side_signs == {-1, 1}
    assert max(tractor_vertices[index][2]
               for face in generated_gap_faces for index in face) >= bed_cut_top_z - 1e-5
    hood_cover_faces = [
        face for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'cab_paint'
        and all(abs(tractor_vertices[index][2] - bed_cut_top_z) < 1e-5
                and abs(tractor_vertices[index][1]) <= bed_cutout_half_width + 1e-5
                for index in face)
        and math.isclose(min(tractor_vertices[index][0] for index in face),
                 config['cab_rear_x'] + 0.002 - origin_x, abs_tol=1e-5)
        and math.isclose(max(tractor_vertices[index][0] for index in face),
                 bed_cutout_x_max, abs_tol=1e-5)
    ]
    assert hood_cover_faces
    assert not any(
        assignment and assignment[0] == 'cab_paint'
        and all(bed_cutout_x_min - 1e-5 <= tractor_vertices[index][0]
            <= bed_cutout_x_max + 1e-5
            and abs(tractor_vertices[index][1]) < bed_cutout_half_width - 1e-5
                and tractor_vertices[index][2] < bed_cut_top_z - 0.05
                for index in face)
        for face, assignment in zip(tractor_faces, tractor_materials)
    )
    assert not any(
        assignment and assignment[0] == 'cab_paint'
        and bed_cutout_x_min - 1e-5 <= min(tractor_vertices[index][0]
                                          for index in face)
        and max(tractor_vertices[index][0] for index in face)
        <= bed_cutout_x_max + 1e-5
        and max(tractor_vertices[index][0] for index in face)
        - min(tractor_vertices[index][0] for index in face) > 0.02
        and max(tractor_vertices[index][1] for index in face)
        - min(tractor_vertices[index][1] for index in face) > 1.0
        and max(tractor_vertices[index][2] for index in face)
        < bed_cut_top_z - 0.05
        for face, assignment in zip(tractor_faces, tractor_materials)
    )
    assert math.isclose(wheel_configs['wheel_t1l'][0][2],
                        config['trailer_wheel_radius'])
    assert math.isclose(wheel_configs['wheel_fl'][0][2], config['wheel_radius'])
    assert math.isclose(max(vertex[2] for vertex in wheel_configs['wheel_t1l'][1]),
                        config['trailer_wheel_radius'])
    sidebar_x_min, sidebar_x_max = -4.5 - origin_x, -0.5 - origin_x
    for name, (position, _vertices) in wheel_configs.items():
        if name.startswith('wheel_t'):
            wheel_x, wheel_y, _wheel_z = position
            assert (wheel_x + config['trailer_wheel_radius'] < sidebar_x_min
                    or wheel_x - config['trailer_wheel_radius'] > sidebar_x_max)
            assert abs(wheel_y) + config['trailer_wheel_half_width'] < 1.23
            truck.get_vertices_edges_faces()
    components = truck.get_additional_meshes()
    assert len(components) == 2
    assert components[0][0] == 'trailer'
    trailer_vertices, trailer_edges, trailer_faces, trailer_materials = components[0][1]
    assert abs((max(vertex[1] for vertex in trailer_vertices)
                - min(vertex[1] for vertex in trailer_vertices)) - 2.50) < 1e-5
    assert max(abs(vertex[1]) for vertex in trailer_vertices) <= 1.25 + 1e-5
    assert components[1][0] == 'fifth_wheel'
    plate_vertices, plate_edges, plate_faces, plate_materials = components[1][1]
    fifth_wheel_outline = DSC_OT_entity_vehicle._get_heavy_truck_fifth_wheel_outline(config)
    fifth_wheel_width = (max(point[1] for point in fifth_wheel_outline)
                         - min(point[1] for point in fifth_wheel_outline))
    assert 0.99 <= fifth_wheel_width <= 1.0
    plate_outline = plate_vertices[:len(fifth_wheel_outline)]
    assert len(plate_vertices) == 2 * len(fifth_wheel_outline)
    assert all(abs(plate_outline[index][0] - (fifth_wheel_outline[index][0] - origin_x))
               < 1e-5
               and abs(plate_outline[index][1] - fifth_wheel_outline[index][1]) < 1e-5
               for index in range(len(fifth_wheel_outline)))
    throat_lower = fifth_wheel_outline[0]
    outer_arc_segments = 30
    throat_upper = fifth_wheel_outline[outer_arc_segments]
    assert abs(throat_lower[1] + throat_upper[1]) < 1e-5
    assert abs(throat_lower[0] - throat_upper[0]) < 1e-5
    cutout_radius = config['fifth_wheel_center_cutout_radius']
    cutout_outline = fifth_wheel_outline[outer_arc_segments + 1:]
    cutout_lower = cutout_outline[-1]
    cutout_upper = cutout_outline[0]
    assert len(cutout_outline) >= 9
    assert abs(cutout_upper[1] + cutout_lower[1]) < 1e-5
    assert abs(cutout_upper[0] - cutout_lower[0]) < 1e-5
    assert all(abs(math.hypot(point[0] - config['fifth_wheel_x'], point[1])
                   - cutout_radius) < 1e-5 for point in cutout_outline)
    assert any(abs(point[0] - (config['fifth_wheel_x'] + cutout_radius)) < 1e-5
               and abs(point[1]) < 1e-5 for point in cutout_outline)
    lower_slope = ((cutout_lower[1] - throat_lower[1])
                   / (cutout_lower[0] - throat_lower[0]))
    upper_slope = ((cutout_upper[1] - throat_upper[1])
                   / (cutout_upper[0] - throat_upper[0]))
    assert lower_slope > 0.25
    assert upper_slope < -0.25
    assert abs(abs(lower_slope) - abs(upper_slope)) < 1e-5

    for name, vertices, edges, faces, materials in (
        ('ActrosTractorTest', tractor_vertices, tractor_edges,
         tractor_faces, tractor_materials),
        ('ActrosTrailerTest', trailer_vertices, trailer_edges,
         trailer_faces, trailer_materials),
        ('ActrosFifthWheelTest', plate_vertices, plate_edges,
         plate_faces, plate_materials),
    ):
        assert_no_orphan_edges_or_duplicate_faces(vertices, edges, faces)
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        try:
            mesh.from_pydata(vertices, edges, faces)
            mesh.update()
            bm.from_mesh(mesh)
            assert len(mesh.polygons) == len(materials)
            assert len(mesh.polygons) > (10 if name == 'ActrosFifthWheelTest' else 20)
            assert all(poly.area > 1e-8 for poly in mesh.polygons)
            if name == 'ActrosTractorTest':
                boundary_edges = [edge for edge in bm.edges
                                  if len(edge.link_faces) == 1]
                assert boundary_edges
                exterior_cut_vertices = []
                for edge in boundary_edges:
                    points = [tuple(vertex.co) for vertex in edge.verts]
                    on_side_cut = all(
                        abs(abs(y) - config['half_width']) < 1e-5
                        and bed_cutout_x_min - 1e-5 <= x <= bed_cutout_x_max + 1e-5
                        and config['clearance'] - 1e-5 <= z <= bed_cut_top_z + 1e-5
                        for x, y, z in points
                    )
                    on_deck_cut = all(
                        abs(z - config['tractor_deck_z']) < 1e-5
                        and abs(abs(y) - bed_cutout_half_width) < 1e-5
                        and bed_deck_x_min - 1e-5 <= x <= bed_deck_x_max + 1e-5
                        for x, y, z in points
                    )
                    on_inner_panel_edge = all(
                        abs(abs(y) - bed_cutout_half_width) < 1e-5
                        for x, y, z in points
                    )
                    on_open_rear_edge = all(
                        abs(x - rear_cap_x) < 1e-5 for x, _y, _z in points
                    )
                    on_cab_rear_edge = all(
                        abs(x - (config['cab_rear_x'] - origin_x)) < 1e-5
                        and abs(abs(y) - config['half_width']) < 1e-5
                        for x, y, _z in points
                    )
                    on_channel_edge = (
                        all(bed_cutout_x_min - 1e-5 <= x <= bed_cutout_x_max + 1e-5
                            and config['clearance'] - 1e-5 <= z <= bed_cut_top_z + 1e-5
                            for x, _y, z in points)
                        and (
                            all(abs(abs(y) - bed_cutout_half_width) < 1e-5
                                for _x, y, _z in points)
                            or (abs(points[0][0] - points[1][0]) < 1e-5
                                and abs(points[0][2] - points[1][2]) < 1e-5
                                and all(abs(y) <= bed_cutout_half_width + 1e-5
                                        for _x, y, _z in points))
                        )
                    )
                    if on_side_cut:
                        exterior_cut_vertices.extend(points)
                assert all(len(edge.link_faces) <= 4 for edge in bm.edges)
                for edge in bm.edges:
                    if len(edge.link_faces) > 2:
                        points = [tuple(vertex.co) for vertex in edge.verts]
                        assert all(
                            min(abs(abs(y) - expected_y)
                                for expected_y in (
                                    config['half_width'], bed_cutout_half_width,
                                    frame_outer_half_width - frame_rail_width,
                                    frame_outer_half_width,
                                )) < 1e-5
                            for _x, y, _z in points
                        )
                assert exterior_cut_vertices
            else:
                assert all(len(edge.link_faces) == 2 for edge in bm.edges)
        finally:
            bm.free()
            bpy.data.meshes.remove(mesh)

    tractor_material_names = {item[0] for item in tractor_materials if item}
    trailer_material_names = {item[0] for item in trailer_materials if item}
    assert {'glass', 'headlight', 'indicator', 'cab_paint'} <= tractor_material_names
    assert {'trailer_paint', 'trailer_door', 'taillight', 'indicator',
            'trailer_trim', 'trailer_rear_panel'} <= trailer_material_names
    trim_vertices = [trailer_vertices[index]
                     for face, assignment in zip(trailer_faces, trailer_materials)
                     if assignment and assignment[0] == 'trailer_trim'
                     for index in face]
    assert min(vertex[2] for vertex in trim_vertices) < 0.5
    assert max(abs(vertex[1]) for vertex in trim_vertices) > 1.2
    side_guard_vertices = [trailer_vertices[index]
                           for face, assignment in zip(trailer_faces, trailer_materials)
                           if assignment and assignment[0] == 'trailer_trim'
                           and abs(max(trailer_vertices[vertex][0] for vertex in face)
                                   - min(trailer_vertices[vertex][0] for vertex in face)
                                   - 4.00) < 1e-5
                           for index in face
                           if (-4.51 - origin_x <= trailer_vertices[index][0]
                               <= -0.49 - origin_x)]
    expected_side_guard_top = config['trailer_floor_z']
    assert abs(min(vertex[2] for vertex in side_guard_vertices)
               - config['clearance']) < 1e-5
    assert abs(max(vertex[2] for vertex in side_guard_vertices)
               - expected_side_guard_top) < 1e-5
    assert abs(max(vertex[2] for vertex in side_guard_vertices)
               - config['trailer_floor_z']) < 1e-5
    guard_bottom_z = 2 * config['trailer_wheel_radius'] + 0.025
    trailer_wheel_x_positions = [
        position[1] for position in config['wheel_positions']
        if position[0].startswith('wheel_t')
    ]
    wheel_clearance = 0.04
    slope_run = 0.10
    guard_front_top_x = (trailer_wheel_x_positions[0]
                         + config['trailer_wheel_radius']
                         + wheel_clearance)
    guard_front_lower_x = guard_front_top_x + slope_run
    guard_rear_top_x = (trailer_wheel_x_positions[-1]
                        - config['trailer_wheel_radius']
                        - wheel_clearance)
    guard_rear_lower_x = guard_rear_top_x - slope_run
    guard_profiles = [
        [trailer_vertices[index] for index in face]
        for face, assignment in zip(trailer_faces, trailer_materials)
        if assignment and assignment[0] == 'trailer_trim'
        and len(face) == 8
        and max(trailer_vertices[index][0] for index in face)
        - min(trailer_vertices[index][0] for index in face) > 3.0
        and max(trailer_vertices[index][1] for index in face)
        - min(trailer_vertices[index][1] for index in face) < 1e-5
    ]
    assert len(guard_profiles) == 4
    for profile in guard_profiles:
        profile_area = abs(sum(
            first[0] * second[2] - second[0] * first[2]
            for first, second in zip(profile, profile[1:] + profile[:1])
        )) * 0.5
        assert profile_area < 0.5
        assert any(abs(vertex[0] - (guard_front_lower_x - origin_x)) < 0.025
                   and abs(vertex[2] - config['clearance']) < 0.01
                   for vertex in profile)
        assert any(abs(vertex[0] - (guard_front_top_x - origin_x)) < 0.025
                   and abs(vertex[2] - (guard_bottom_z + 0.04)) < 0.01
                   for vertex in profile)
        assert any(abs(vertex[0] - (guard_rear_lower_x - origin_x)) < 0.025
                   and abs(vertex[2] - config['clearance']) < 0.01
                   for vertex in profile)
    slope_faces = [
        [trailer_vertices[index] for index in face]
        for face, assignment in zip(trailer_faces, trailer_materials)
        if assignment and assignment[0] == 'trailer_trim'
        and 0.08 < max(trailer_vertices[index][0] for index in face)
        - min(trailer_vertices[index][0] for index in face) < 0.14
        and max(trailer_vertices[index][2] for index in face)
        - min(trailer_vertices[index][2] for index in face) > 0.8
        and max(trailer_vertices[index][1] for index in face)
        - min(trailer_vertices[index][1] for index in face) > 0.4
    ]
    assert len(slope_faces) == 4
    slope_directions = []
    for face in slope_faces:
        lower_z = min(vertex[2] for vertex in face)
        upper_z = max(vertex[2] for vertex in face)
        lower_x = sum(vertex[0] for vertex in face
                      if abs(vertex[2] - lower_z) < 1e-5) / 2
        upper_x = sum(vertex[0] for vertex in face
                      if abs(vertex[2] - upper_z) < 1e-5) / 2
        slope_directions.append(upper_x - lower_x)
    assert sum(direction < 0 for direction in slope_directions) == 2
    assert sum(direction > 0 for direction in slope_directions) == 2
    front_tire_front_x = (trailer_wheel_x_positions[0]
                          + config['trailer_wheel_radius'])
    rear_tire_rear_x = (trailer_wheel_x_positions[-1]
                        - config['trailer_wheel_radius'])
    assert math.isclose(guard_front_lower_x - guard_front_top_x, slope_run)
    assert math.isclose(guard_rear_top_x - guard_rear_lower_x, slope_run)
    assert abs((guard_front_lower_x - front_tire_front_x)
               - (rear_tire_rear_x - guard_rear_lower_x)) < 1e-5
    rear_panel_vertices = [trailer_vertices[index]
                           for face, assignment in zip(trailer_faces, trailer_materials)
                           if assignment and assignment[0] == 'trailer_rear_panel'
                           for index in face]
    assert min(vertex[2] for vertex in rear_panel_vertices) > 0.6
    assert abs(max(vertex[2] for vertex in rear_panel_vertices)
               - config['trailer_floor_z']) < 1e-5
    rear_x = config['tractor_front_x'] - config['length'] - origin_x
    tractor_body_front_x = max(vertex[0] for vertex in tractor_vertices
                               if abs(vertex[1]) <= config['half_width'] + 1e-5)
    assert abs(tractor_body_front_x
               - min(vertex[0] for vertex in trailer_vertices)
               - config['length']) < 0.02
    crash_bar_front_x = rear_x + 0.18
    assert abs(min(vertex[0] for vertex in rear_panel_vertices)
               - (crash_bar_front_x - 0.07)) < 1e-5
    assert abs(max(vertex[0] for vertex in rear_panel_vertices)
               - crash_bar_front_x) < 1e-5
    rear_panel_color = next(item[1] for item in trailer_materials
                            if item and item[0] == 'trailer_rear_panel')
    door_color = next(item[1] for item in trailer_materials
                      if item and item[0] == 'trailer_door')
    assert rear_panel_color == door_color
    crash_bar_vertices = [trailer_vertices[index]
                          for face, assignment in zip(trailer_faces, trailer_materials)
                          if assignment and assignment[0] == 'trailer_trim'
                          for index in face
                          if abs(trailer_vertices[index][2] - 0.62) < 1e-5]
    assert crash_bar_vertices
    assert abs(max(vertex[1] for vertex in crash_bar_vertices) - 1.19) < 1e-5
    assert abs(min(vertex[1] for vertex in crash_bar_vertices) + 1.19) < 1e-5
    assert abs(max(vertex[0] for vertex in crash_bar_vertices)
               - crash_bar_front_x) < 1e-5
    assert {item[0] for item in plate_materials if item} == {'fifth_wheel'}
    assert math.isclose(max(vertex[2] for vertex in plate_vertices),
                        config['trailer_floor_z'])

    side_windows = [index for index, item in enumerate(tractor_materials)
                    if item and item[0] == 'glass'
                    and all(abs(abs(tractor_vertices[vertex][1])
                                - config['half_width']) < 1e-5
                            for vertex in tractor_faces[index])]
    assert len(side_windows) == 2
    assert all(len(tractor_faces[index]) == 4 for index in side_windows)
    front_indicator_vertices = [
        tractor_vertices[vertex]
        for face, assignment in zip(tractor_faces, tractor_materials)
        if assignment and assignment[0] == 'indicator'
        for vertex in face
    ]
    assert abs(max(abs(vertex[1]) for vertex in front_indicator_vertices)
               - (config['half_width'] - 0.04)) < 1e-5
    side_window_bottom = min(tractor_vertices[vertex][2]
                            for index in side_windows for vertex in tractor_faces[index])
    side_window_top = max(tractor_vertices[vertex][2]
                         for index in side_windows for vertex in tractor_faces[index])
    assert abs(side_window_bottom - 2.1) < 1e-5
    assert abs(side_window_top - 3.1) < 1e-5
    for index in side_windows:
        face_vertices = [tractor_vertices[vertex] for vertex in tractor_faces[index]]
        front_lower_x = max(vertex[0] for vertex in face_vertices
                            if abs(vertex[2] - 2.1) < 1e-5)
        front_upper_x = max(vertex[0] for vertex in face_vertices
                            if abs(vertex[2] - 3.1) < 1e-5)
        rear_lower_x = min(vertex[0] for vertex in face_vertices
                   if abs(vertex[2] - 2.1) < 1e-5)
        rear_upper_x = min(vertex[0] for vertex in face_vertices
                   if abs(vertex[2] - 3.1) < 1e-5)
        assert abs(rear_upper_x - rear_lower_x) < 1e-5
        assert abs(rear_lower_x
               - (config['wheel_positions'][0][1] - origin_x)) < 1e-5
        assert abs((front_upper_x - front_lower_x)
                         + 0.12 / (3.2 - 1.98)) < 1e-5
        pillar_front_lower_x = (config['tractor_front_x'] - origin_x
                    - 0.12 * (2.1 - 1.98) / (3.2 - 1.98))
        assert abs(pillar_front_lower_x - front_lower_x - 0.10) < 1e-5
    windshield_vertices = {
        vertex for index, item in enumerate(tractor_materials)
        if item and item[0] == 'glass'
        and max(tractor_vertices[vertex][1] for vertex in tractor_faces[index])
        - min(tractor_vertices[vertex][1] for vertex in tractor_faces[index]) > 1.5
        for vertex in tractor_faces[index]
    }
    assert windshield_vertices
    windshield_bottom = min(tractor_vertices[vertex][2]
                            for vertex in windshield_vertices)
    windshield_top = max(tractor_vertices[vertex][2]
                         for vertex in windshield_vertices)
    assert abs(windshield_bottom - 2.1) < 1e-5
    assert abs(windshield_top - 3.1) < 1e-5
    assert abs((max(tractor_vertices[vertex][1] for vertex in windshield_vertices)
                - min(tractor_vertices[vertex][1] for vertex in windshield_vertices))
               - (2 * config['half_width'] - 0.20)) < 1e-5
    assert any(config['tractor_front_x'] - origin_x - 0.02
               <= tractor_vertices[index][0]
               <= config['tractor_front_x'] - origin_x
               and abs(tractor_vertices[index][2] - side_window_bottom) < 1e-5
               for index in range(len(tractor_vertices)))
    assert any(abs(tractor_vertices[index][0]
                   - (config['tractor_front_x'] - origin_x - 0.12)) < 1e-5
               and abs(tractor_vertices[index][2] - 3.2) < 1e-5
               for index in range(len(tractor_vertices)))
    assert any(abs(tractor_vertices[index][0]
                   - (config['tractor_front_x'] - origin_x - 0.35)) < 1e-5
               and abs(tractor_vertices[index][2] - config['cab_roof_z']) < 1e-5
               for index in range(len(tractor_vertices)))

    mirror_z = 2.60
    pillar_dx_dz = -0.12 / (3.2 - 1.98)
    pillar_axis_z = 1.0 / math.sqrt(1.0 + pillar_dx_dz ** 2)
    mirror_x = (config['tractor_front_x'] - origin_x
                + pillar_dx_dz * (mirror_z - 1.98)
                - 0.05 - 0.10 / pillar_axis_z)
    for side in (-1.0, 1.0):
        mirror_faces = [face for face, assignment in zip(tractor_faces, tractor_materials)
                        if assignment and assignment[0] == 'trim'
                        and max(tractor_vertices[index][2] for index in face)
                        - min(tractor_vertices[index][2] for index in face) > 0.79
                        and all(abs(tractor_vertices[index][1] - side * 1.475)
                                < 1e-5 for index in face)]
        assert mirror_faces
        face_vertices = [tractor_vertices[index] for index in mirror_faces[0]]
        assert abs(min(vertex[2] for vertex in face_vertices) - 2.2) < 1e-5
        assert abs(max(vertex[2] for vertex in face_vertices) - 3.0) < 1e-5
        long_edges = [(first, second)
                      for index, first in enumerate(face_vertices)
                      for second in face_vertices[index + 1:]
                      if abs(second[2] - first[2]) > 0.75]
        assert long_edges
        assert any(abs((second[0] - first[0]) / (second[2] - first[2])
                       + 0.12 / (3.2 - 1.98)) < 1e-5
                   for first, second in long_edges)
        assert abs((min(vertex[0] for vertex in face_vertices)
                    + max(vertex[0] for vertex in face_vertices)) * 0.5
                   - mirror_x) < 1e-5

        mirror_axis_x = pillar_dx_dz / math.sqrt(1.0 + pillar_dx_dz ** 2)
        mirror_axis_z = 1.0 / math.sqrt(1.0 + pillar_dx_dz ** 2)
        mirror_normal_x = mirror_axis_z
        mirror_normal_z = -mirror_axis_x
        mirror_half_height = (0.40 - abs(mirror_normal_z) * 0.10) / mirror_axis_z
        for corner_index in (2, 3):
            along_sign = 1.0 if corner_index == 2 else -1.0
            expected_corner_x = (mirror_x + mirror_axis_x * along_sign
                                 * mirror_half_height + mirror_normal_x * 0.10)
            expected_corner_z = (mirror_z + mirror_axis_z * along_sign
                                 * mirror_half_height + mirror_normal_z * 0.10)
            mirror_inner_y = 1.475 - 0.16
            expected_corner_y = side * (mirror_inner_y + 0.16 / 3)
            mount_faces = [
                face for face, assignment in zip(tractor_faces, tractor_materials)
                if assignment and assignment[0] == 'trim'
                and abs(min(side * tractor_vertices[index][1] for index in face)
                    - config['half_width']) < 1e-5
                and abs(max(side * tractor_vertices[index][1] for index in face)
                    - (mirror_inner_y + 0.16 / 3)) < 1e-5
            ]
            assert mount_faces
            lateral_mount_faces = [
                face for face in mount_faces
                if (max(tractor_vertices[index][0] for index in face)
                    - min(tractor_vertices[index][0] for index in face) < 0.08
                    and max(tractor_vertices[index][2] for index in face)
                    - min(tractor_vertices[index][2] for index in face) < 0.11)
            ]
            assert lateral_mount_faces
            assert any(
                abs((max(tractor_vertices[index][2] for index in face)
                     - min(tractor_vertices[index][2] for index in face))
                     - 0.05) < 0.002
                for face in lateral_mount_faces
            )
            mount_axis_offsets = [
                ((tractor_vertices[index][0] - expected_corner_x) * mirror_axis_x
                 + (tractor_vertices[index][2] - expected_corner_z) * mirror_axis_z)
                for face in lateral_mount_faces for index in face
                if abs(tractor_vertices[index][1] - expected_corner_y) < 1e-5
                if abs(tractor_vertices[index][0] - expected_corner_x) < 0.22
                and abs(tractor_vertices[index][2] - expected_corner_z) < 0.22
            ]
            assert mount_axis_offsets
            if corner_index == 2:
                assert abs(min(mount_axis_offsets)) < 1e-5
                assert abs(max(mount_axis_offsets) * mirror_axis_z - 0.05) < 1e-5
            else:
                assert abs(min(mount_axis_offsets) * mirror_axis_z + 0.05) < 1e-5
                assert abs(max(mount_axis_offsets)) < 1e-5

    rear_door_vertices = {
        vertex for index, assignment in enumerate(trailer_materials)
        if assignment and assignment[0] == 'trailer_door'
        and all(abs(trailer_vertices[vertex][0] - rear_x) < 1e-5
                for vertex in trailer_faces[index])
        for vertex in trailer_faces[index]
    }
    assert rear_door_vertices
    rear_door_height = (max(trailer_vertices[index][2] for index in rear_door_vertices)
                        - min(trailer_vertices[index][2] for index in rear_door_vertices))
    assert rear_door_height > (config['trailer_roof_z']
                               - config['trailer_floor_z']) * 0.90

    trailer_light_centers = {}
    trailer_light_face_x = {'taillight': set(), 'indicator': set()}
    for face, assignment in zip(trailer_faces, trailer_materials):
        if assignment and assignment[0] in {'taillight', 'indicator'}:
            center = tuple(sum(trailer_vertices[index][axis] for index in face)
                           / len(face) for axis in range(3))
            if (abs(center[2] - 0.91) < 1e-6
                    and all(abs(trailer_vertices[index][0]
                                - trailer_vertices[face[0]][0]) < 1e-6
                            for index in face)):
                trailer_light_centers.setdefault(assignment[0], set()).add(
                    (0.0, round(center[1], 6), round(center[2], 6)))
                trailer_light_face_x[assignment[0]].add(round(center[0], 6))
    assert len(trailer_light_centers['taillight']) == 2
    assert len(trailer_light_centers['indicator']) == 2
    expected_light_face_x = {round(crash_bar_front_x - 0.085, 6),
                             round(crash_bar_front_x - 0.07, 6)}
    assert trailer_light_face_x['taillight'] == expected_light_face_x
    assert trailer_light_face_x['indicator'] == expected_light_face_x
    assert all(center[2] < config['trailer_floor_z'] + 0.25
               for centers in trailer_light_centers.values() for center in centers)
    for indicator_center, tail_center in zip(
            sorted(trailer_light_centers['indicator'], key=lambda point: abs(point[1])),
            sorted(trailer_light_centers['taillight'], key=lambda point: abs(point[1]))):
        assert abs(indicator_center[2] - tail_center[2]) < 1e-5
        assert abs(indicator_center[1]) > abs(tail_center[1])


def vehicle_probe(subtype):
    vehicle = SimpleNamespace(entity_subtype=subtype)
    for name, descriptor in DSC_OT_entity_vehicle.__dict__.items():
        if isinstance(descriptor, staticmethod):
            setattr(vehicle, name, descriptor.__func__)
        elif callable(descriptor):
            setattr(vehicle, name, MethodType(descriptor, vehicle))
        elif not name.startswith('__') and not hasattr(vehicle, name):
            try:
                setattr(vehicle, name, descriptor)
            except (AttributeError, TypeError):
                pass
    return vehicle


def test_non_car_vehicle_meshes_have_detailed_geometry_and_valid_materials():
    for subtype in NON_CAR_SUBTYPES:
        vehicle = vehicle_probe(subtype)
        vertices, edges, faces = vehicle.get_vertices_edges_faces()
        assert_no_orphan_edges_or_duplicate_faces(vertices, edges, faces)
        face_materials = vehicle.get_face_materials()
        mesh = bpy.data.meshes.new('VehicleGeometryTest_' + subtype)
        try:
            mesh.from_pydata(vertices, edges, faces)
            mesh.update()

            assert len(vertices) > 30, subtype
            assert len(mesh.polygons) > 20, subtype
            assert len(mesh.polygons) == len(face_materials), subtype
            assert all(len(poly.vertices) >= 3 and poly.area > 1e-8
                       for poly in mesh.polygons), subtype

            material_names = {
                name
                for assignment in face_materials if assignment
                for name, _color in (assignment,)
            }
            if subtype in {'bus', 'heavyTruck', 'van'}:
                assert 'glass' in material_names, subtype
            assert len(vehicle.get_wheel_configs()) == len(
                VEHICLE_GEOMETRY_DIMENSIONS[subtype]['wheel_positions'])
        finally:
            bpy.data.meshes.remove(mesh)


def test_two_wheelers_and_commercial_vehicles_have_category_details():
    for subtype, expected_materials in (
        ('bicycle', {'frame', 'metal', 'rubber', 'rider_skin',
                     'rider_clothing', 'rider_trousers', 'rider_hair',
                     'rider_eyes'}),
        ('motorcycle', {'frame', 'metal', 'headlight', 'taillight', 'indicator',
                        'rider_skin', 'rider_clothing', 'rider_trousers',
                        'rider_helmet'}),
        ('bus', {'glass', 'headlight', 'taillight', 'indicator'}),
        ('heavyTruck', {'glass', 'headlight', 'indicator', 'cab_paint'}),
        ('van', {'glass', 'headlight', 'taillight'}),
    ):
        vehicle = vehicle_probe(subtype)
        vehicle.get_vertices_edges_faces()
        material_names = {
            name
            for assignment in vehicle.get_face_materials() if assignment
            for name, _color in (assignment,)
        }
        assert expected_materials <= material_names, subtype
        if subtype == 'bicycle':
            assert 'rider_helmet' not in material_names
            assert 'rider_visor' not in material_names
        if subtype in {'bicycle', 'motorcycle'}:
            trouser_face_count = sum(
                bool(assignment) and assignment[0] == 'rider_trousers'
                for assignment in vehicle.get_face_materials()
            )
            assert trouser_face_count == 24, subtype


def test_two_wheeler_frame_and_rider_geometry():
    bicycle = vehicle_probe('bicycle')
    bike_vertices, _edges, bike_faces = bicycle.get_vertices_edges_faces()
    bicycle_origin_x = VEHICLE_GEOMETRY_DIMENSIONS['bicycle']['origin_x']
    bike_vertices = [(x + bicycle_origin_x, y, z)
                     for x, y, z in bike_vertices]
    bike_materials = bicycle.get_face_materials()
    bike_frame_vertices = [
        bike_vertices[index]
        for face, assignment in zip(bike_faces, bike_materials)
        if assignment and assignment[0] == 'frame'
        for index in face
    ]
    bike_clothing_vertices = [
        bike_vertices[index]
        for face, assignment in zip(bike_faces, bike_materials)
        if assignment and assignment[0] == 'rider_clothing'
        for index in face
    ]
    bike_rubber_vertices = [
        bike_vertices[index]
        for face, assignment in zip(bike_faces, bike_materials)
        if assignment and assignment[0] == 'rubber'
        for index in face
    ]
    bike_shoe_vertices = [
        bike_vertices[index]
        for face, assignment in zip(bike_faces, bike_materials)
        if assignment and assignment[0] == 'rider_shoes'
        for index in face
    ]
    bike_trouser_vertices = [
        bike_vertices[index]
        for face, assignment in zip(bike_faces, bike_materials)
        if assignment and assignment[0] == 'rider_trousers'
        for index in face
    ]
    bike_skin_vertices = [
        bike_vertices[index]
        for face, assignment in zip(bike_faces, bike_materials)
        if assignment and assignment[0] == 'rider_skin'
        for index in face
    ]
    bike_hair_vertices = [
        bike_vertices[index]
        for face, assignment in zip(bike_faces, bike_materials)
        if assignment and assignment[0] == 'rider_hair'
        for index in face
    ]
    assert math.isclose(
        max(point[0] for point in bike_hair_vertices)
        - min(point[0] for point in bike_hair_vertices), 0.23, abs_tol=1e-6)
    assert math.isclose(
        max(point[1] for point in bike_hair_vertices)
        - min(point[1] for point in bike_hair_vertices), 0.23, abs_tol=1e-6)
    torso_bottom = [vertex[2] for vertex in bike_clothing_vertices
                    if vertex[0] < -0.10]
    assert min(torso_bottom) > 0.9675
    assert any(abs(vertex[0] - 0.25) < 0.05
               and abs(vertex[2] - 0.795) < 0.04
               and abs(vertex[1]) < 0.041
               for vertex in bike_frame_vertices)
    assert any(abs(vertex[0] + 0.197058823529) < 0.04
               and abs(vertex[2] - 0.34) < 0.04
               for vertex in bike_frame_vertices)
    assert 0.355 > 0.34  # The chainstay rises toward the rear hub.
    seat_axis_slope = (0.82 - 0.34) / (-0.31 + 0.197058823529)
    post_axis_slope = (0.925 - 0.82) / (-0.3347058823529 + 0.31)
    assert math.isclose(seat_axis_slope, post_axis_slope, abs_tol=1e-8)
    post_length = math.hypot(0.0247058823529, 0.105)
    assert math.isclose(post_length, 0.1079, abs_tol=1e-4)
    assert post_length > math.hypot(0.02, 0.085)
    assert any(abs(vertex[0] + 0.21) < 1e-5
               and abs(vertex[2] - 0.9675) < 1e-5
               for vertex in bike_rubber_vertices)
    assert any(abs(vertex[0] + 0.47) < 1e-5
               and abs(vertex[2] - 0.9125) < 1e-5
               for vertex in bike_rubber_vertices)
    head_axis_slope = (0.73 - 0.86) / (0.28 - 0.22)
    fork_axis_slope = (28 * 0.0254 / 2 - 0.73) / (
        VEHICLE_GEOMETRY_DIMENSIONS['bicycle']['wheel_positions'][0][1] - 0.28)
    assert math.isclose(head_axis_slope, fork_axis_slope, abs_tol=1e-6)
    down_tube_x_at_midheight = (-0.197058823529 + 0.22) * 0.5
    fork_x_at_midheight = 0.22 + (0.60 - 0.86) / head_axis_slope
    assert fork_x_at_midheight - down_tube_x_at_midheight > 0.075
    assert any(abs(vertex[0] - 0.275) < 0.04
               and abs(vertex[2] - 0.95) < 0.03
               and abs(vertex[1]) > 0.25
               for vertex in bike_vertices)
    assert any(abs(vertex[0] - 0.275) < 0.03
               and abs(vertex[1] - 0.29) < 1e-5
               and abs(vertex[2] - 0.95) < 0.02
               for vertex in bike_vertices)
    assert any(abs(vertex[0] - 0.295) < 0.04
               and abs(vertex[2] - 0.95) < 0.03
               and abs(vertex[1]) < 0.03
               for vertex in bike_vertices)

    rear_x = VEHICLE_GEOMETRY_DIMENSIONS['bicycle']['wheel_positions'][1][1]
    wheel_radius = VEHICLE_GEOMETRY_DIMENSIONS['bicycle']['wheel_radius']
    crank_x, crank_z = -0.197058823529, 0.34
    seat_x, seat_z = -0.31, 0.82
    tube_dx, tube_dz = seat_x - crank_x, seat_z - crank_z
    projection = ((rear_x - crank_x) * tube_dx
                  + (wheel_radius - crank_z) * tube_dz) / (
                      tube_dx * tube_dx + tube_dz * tube_dz)
    closest_x = crank_x + max(0.0, min(1.0, projection)) * tube_dx
    closest_z = crank_z + max(0.0, min(1.0, projection)) * tube_dz
    centerline_clearance = math.hypot(rear_x - closest_x,
                                      wheel_radius - closest_z)
    assert centerline_clearance - wheel_radius - 0.035 > 0.02

    for side, pedal_x, pedal_z in ((1.0, -0.067058823529, 0.22),
                                   (-1.0, -0.327058823529, 0.46)):
        assert any(abs(vertex[0] - (pedal_x + 0.07)) < 1e-5
                   and abs(vertex[1] - (side * 0.23)) < 1e-5
                   and abs(vertex[2] - (pedal_z + 0.02)) < 1e-5
                   for vertex in bike_rubber_vertices)
        assert any(abs(vertex[0] - (pedal_x + 0.09)) < 1e-5
                   and abs(vertex[1] - (side * 0.22)) < 1e-5
                   and abs(vertex[2] - (pedal_z + 0.065)) < 1e-5
                   for vertex in bike_shoe_vertices)
        assert any(abs(vertex[0] - (pedal_x - 0.13)) < 1e-5
                   and abs(vertex[1] - (side * 0.22)) < 1e-5
                   and abs(vertex[2] - (pedal_z + 0.02)) < 1e-5
                   for vertex in bike_shoe_vertices)

    neck_tip = (0.015, 0.0, 1.40)
    assert any(math.dist(vertex, neck_tip) < 0.055
               for vertex in bike_skin_vertices)
    assert any(vertex[0] > -0.34 and vertex[0] < -0.27
               and 0.965 < vertex[2] < 1.01
               for vertex in bike_trouser_vertices)
    thigh_section_vertices = [
        vertex for vertex in bike_trouser_vertices
        if abs(vertex[0] + 0.04) < 0.08 and abs(vertex[2] - 0.65) < 0.07
        and vertex[1] > 0.0
    ]
    assert thigh_section_vertices
    thigh_knee = (-0.04, 0.19, 0.65)
    thigh_ring_radius = 0.075
    thigh_ring_vertices = [
        vertex for vertex in bike_trouser_vertices
        if abs(math.dist(vertex, thigh_knee) - thigh_ring_radius) < 1e-5
    ]
    assert len({tuple(round(component, 5) for component in vertex)
                for vertex in thigh_ring_vertices}) == 4

    for subtype, elbow_x, elbow_z, elbow_y, hand_y in (
        ('bicycle', 0.10, 1.12, 0.32, 0.27),
        ('motorcycle', 0.065, 1.165, 0.38, 0.36),
    ):
        vehicle = vehicle_probe(subtype)
        vertices, _edges, faces = vehicle.get_vertices_edges_faces()
        origin_x = VEHICLE_GEOMETRY_DIMENSIONS[subtype]['origin_x']
        vertices = [(x + origin_x, y, z) for x, y, z in vertices]
        materials = vehicle.get_face_materials()
        clothing_vertices = [
            vertices[index]
            for face, assignment in zip(faces, materials)
            if assignment and assignment[0] == 'rider_clothing'
            for index in face
        ]
        skin_vertices = {
            tuple(round(coordinate, 6) for coordinate in vertices[index])
            for face, assignment in zip(faces, materials)
            if assignment and assignment[0] == 'rider_skin'
            for index in face
        }
        for side in (-1.0, 1.0):
            elbow_vertices = [
                vertex for vertex in clothing_vertices
                if abs(vertex[0] - elbow_x) < 0.065
                and abs(vertex[2] - elbow_z) < 0.065
                and vertex[1] * side > 0.0
            ]
            assert elbow_vertices, subtype
            assert max(vertex[1] * side for vertex in elbow_vertices) > hand_y
            elbow = (elbow_x, side * elbow_y, elbow_z)
            hand = ((0.275, side * hand_y, 0.95) if subtype == 'bicycle'
                    else (0.3352631578947, side * hand_y, 1.08))
            shoulder = ((-0.015, side * 0.15, 1.245)
                        if subtype == 'bicycle'
                        else (-0.08, side * 0.15, 1.205))
            arm_roll = math.pi / 4
            axis = tuple(elbow[index] - shoulder[index]
                         for index in range(3))
            axis_length = math.sqrt(sum(component * component
                                        for component in axis))
            axis = tuple(component / axis_length for component in axis)
            first = (-axis[2], 0.0, axis[0])
            first_length = math.sqrt(sum(component * component
                                         for component in first))
            first = tuple(component / first_length for component in first)
            second = (axis[1] * first[2] - axis[2] * first[1],
                      axis[2] * first[0] - axis[0] * first[2],
                      axis[0] * first[1] - axis[1] * first[0])
            rolled_first = tuple(
                first[index] * math.cos(arm_roll)
                + second[index] * math.sin(arm_roll)
                for index in range(3)
            )
            rolled_second = tuple(
                second[index] * math.cos(arm_roll)
                - first[index] * math.sin(arm_roll)
                for index in range(3)
            )
            for section_offset in (rolled_first, rolled_second,
                                   tuple(-component for component in rolled_first),
                                   tuple(-component for component in rolled_second)):
                section_corner = tuple(
                    shoulder[index] + 0.052 * section_offset[index]
                    for index in range(3)
                )
                assert any(math.dist(point, section_corner) < 1e-5
                           for point in clothing_vertices), section_corner

            arm_dx = hand[0] - elbow[0]
            arm_dz = hand[2] - elbow[2]
            hand_rotation = math.atan2(-arm_dz, arm_dx) * 0.12
            if subtype == 'bicycle':
                hand_rotation += math.pi / 9
            for x_sign, z_sign, y_sign in (
                (-1.0, -1.0, -1.0), (-1.0, 1.0, -1.0),
                (1.0, -1.0, -1.0), (1.0, 1.0, -1.0),
                (-1.0, -1.0, 1.0), (-1.0, 1.0, 1.0),
                (1.0, -1.0, 1.0), (1.0, 1.0, 1.0),
            ):
                hand_corner = (
                    hand[0] + math.cos(hand_rotation) * x_sign * 0.055
                    + math.sin(hand_rotation) * z_sign * 0.0375,
                    hand[1] + y_sign * 0.045,
                    hand[2] - math.sin(hand_rotation) * x_sign * 0.055
                    + math.cos(hand_rotation) * z_sign * 0.0375,
                )
                assert tuple(round(value, 6) for value in hand_corner) in skin_vertices

            upper_length = math.dist(shoulder, elbow)
            lower_length = math.dist(elbow, hand)
            assert upper_length <= lower_length, subtype
            assert lower_length - upper_length < 0.01, subtype
            if subtype == 'motorcycle':
                motorbike_hip = (-0.38, side * 0.12, 0.83)
                motorbike_knee = (0.0, side * 0.19, 0.75)
                motorbike_ankle = (0.04, side * 0.21, 0.46)
                thigh_length = math.dist(motorbike_hip, motorbike_knee) * 0.96
                lower_leg_length = math.dist(motorbike_knee, motorbike_ankle)
                assert thigh_length > 0.37
                assert lower_leg_length > 0.29
                assert -0.24 < motorbike_knee[0] < 0.18
                assert abs(motorbike_ankle[1]) - 0.06 > 0.13
            arm_vector = tuple(hand[index] - elbow[index]
                               for index in range(3))
            arm_length = math.sqrt(sum(component * component
                                       for component in arm_vector))
            direction = tuple(component / arm_length for component in arm_vector)
            lower_start = tuple(
                elbow[index] - arm_vector[index] * 0.018 / arm_length
                for index in range(3)
            )
            assert math.dist(elbow, lower_start) < 0.052 + 0.043
            hand_half_extents = (0.055, 0.045, 0.0375)
            surface_distance = sum(
                extent * abs(component)
                for extent, component in zip(hand_half_extents, direction)
            )
            wrist = tuple(hand[index] - direction[index]
                          * (surface_distance - 0.012)
                          for index in range(3))
            assert any(abs(math.dist(vertex, wrist) - 0.043) < 1e-5
                       for vertex in clothing_vertices), subtype
            if subtype == 'motorcycle':
                assert math.isclose(hand[0], 0.3352631578947)
                assert math.isclose(hand[2], 1.08)
                assert math.isclose(hand[1], side * 0.36)


def test_van_and_two_wheeler_origins_are_below_rear_axles():
    for subtype, rear_names in (
        ('van', ('wheel_rl', 'wheel_rr')),
        ('bicycle', ('wheel_r',)),
        ('motorcycle', ('wheel_r',)),
    ):
        config = VEHICLE_GEOMETRY_DIMENSIONS[subtype]
        rear_wheel_x = next(x for name, x, _y in config['wheel_positions']
                            if name == rear_names[0])
        assert math.isclose(config['origin_x'], rear_wheel_x)
        vehicle = vehicle_probe(subtype)
        wheels = {name: center for name, center, *_rest
                  in vehicle.get_wheel_configs()}
        for name in rear_names:
            assert math.isclose(wheels[name][0], 0.0)
            assert math.isclose(wheels[name][2], config['wheel_radius'])
    motorcycle = vehicle_probe('motorcycle')
    motorcycle_wheels = {
        name: mesh_vertices
        for name, _center, mesh_vertices, *_rest
        in motorcycle.get_wheel_configs()
    }
    assert math.isclose(max(abs(vertex[1])
                            for vertex in motorcycle_wheels['wheel_f']), 0.055)
    assert math.isclose(max(abs(vertex[1])
                            for vertex in motorcycle_wheels['wheel_r']), 0.085)


def test_motorcycle_engine_seat_lighting_and_footrests():
    motorcycle = vehicle_probe('motorcycle')
    vertices, _edges, faces = motorcycle.get_vertices_edges_faces()
    origin_x = VEHICLE_GEOMETRY_DIMENSIONS['motorcycle']['origin_x']
    vertices = [(x + origin_x, y, z) for x, y, z in vertices]
    materials = motorcycle.get_face_materials()
    material_vertices = {}
    material_centers = {}
    for face, assignment in zip(faces, materials):
        if not assignment:
            continue
        name = assignment[0]
        points = [vertices[index] for index in face]
        material_vertices.setdefault(name, []).extend(points)
        material_centers.setdefault(name, []).append(tuple(
            sum(point[axis] for point in points) / len(points)
            for axis in range(3)
        ))

    # Engine sits farther forward under the slimmer tank.
    assert any(abs(point[0] - 0.18) < 1e-5
               and abs(point[1] - 0.13) < 1e-5
               and abs(point[2] - 0.71) < 1e-5
               for point in material_vertices['metal'])

    # The wheel-side ends retain two separate legs without changing their
    # lateral spacing; both rear leg sections are unrolled and rectangular.
    for side in (-1.0, 1.0):
        center = (0.73, side * 0.095, 0.33)
        ring = {
            tuple(round(coordinate, 6) for coordinate in point)
            for point in material_vertices['metal']
            if abs(math.dist(point, center) - 0.025) < 1e-5
        }
        assert len(ring) == 4, ('front fork', center, ring)

        rear_center = (-0.73, side * 0.13, 0.33)
        rear_ring = {
            tuple(round(coordinate, 6) for coordinate in point)
            for point in material_vertices['frame']
            if abs(math.dist(point, rear_center) - math.hypot(0.05, 0.025)) < 1e-5
        }
        assert len(rear_ring) == 4, ('rear fork', rear_center, rear_ring)
        rear_ring_points = list(rear_ring)
        rear_edge_lengths = sorted(
            math.dist(first, second)
            for index, first in enumerate(rear_ring_points)
            for second in rear_ring_points[index + 1:]
        )
        assert math.isclose(rear_edge_lengths[0], 0.05, abs_tol=1e-5)
        assert math.isclose(rear_edge_lengths[1], 0.05, abs_tol=1e-5)
        assert math.isclose(rear_edge_lengths[2], 0.10, abs_tol=1e-5)
        assert math.isclose(rear_edge_lengths[3], 0.10, abs_tol=1e-5)
        assert all(length > 0.11 for length in rear_edge_lengths[4:])

    for center_x, center_z, axle_half_width in (
        (0.73, 0.33, 0.12),
        (-0.73, 0.33, 0.16),
    ):
        for side in (-1.0, 1.0):
            axle_center = (center_x, side * axle_half_width, center_z)
            axle_ring = {
                tuple(round(coordinate, 6) for coordinate in point)
                for point in material_vertices['metal']
                if abs(math.dist(point, axle_center) - 0.025) < 1e-5
            }
            assert len(axle_ring) == 4, (axle_center, axle_ring)
            if center_x > 0.0:
                fork_roll = math.pi / 2 - math.atan2(0.33 - 0.736,
                                                    0.73 - 0.5163157894737)
                expected_corner = (
                    center_x + 0.025 * math.cos(fork_roll),
                    side * axle_half_width,
                    center_z - 0.025 * math.sin(fork_roll),
                )
                assert tuple(round(value, 6) for value in expected_corner) in axle_ring

    for material, x, z, half_width, roll in (
        ('frame', -0.32, 0.3885714285714, 0.13,
         math.pi / 2 - math.atan2(0.3885714285714 - 0.33, 0.41)),
        ('metal', 0.5163157894737, 0.736, 0.095,
         math.pi / 2 - math.atan2(0.33 - 0.736,
                                  0.73 - 0.5163157894737)),
    ):
        long_half = 0.05 if material == 'frame' else 0.036
        short_half = 0.025 if material == 'frame' else 0.018
        first = (long_half * math.cos(roll), -long_half * math.sin(roll))
        second = (-short_half * math.sin(roll), -short_half * math.cos(roll))
        splitter_half_width = 0.155 if material == 'frame' else 0.125
        for side in (-1.0, 1.0):
            for first_sign in (-1.0, 1.0):
                for second_sign in (-1.0, 1.0):
                    corner = (
                        x + first_sign * first[0] + second_sign * second[0],
                        side * splitter_half_width,
                        z + first_sign * first[1] + second_sign * second[1],
                    )
                    assert any(math.dist(point, corner) < 1e-5
                               for point in material_vertices[material]), corner

    assert any(abs(point[0] + 0.12) < 1e-5
               and abs(point[1] - 0.13) < 1e-5
               and abs(point[2] - 0.71) < 1e-5
               for point in material_vertices['metal'])
    assert any(abs(point[1] - 0.17) < 1e-5
               and abs(point[2] - 1.03) < 1e-5
               for point in material_vertices['body_highlight'])
    fork_slope = (0.90 - 0.33) / (0.43 - 0.73)
    upper_fork_slope = (0.86 - 0.736) / (
        0.4510526315789 - 0.5163157894737)
    lower_fork_slope = (0.736 - 0.33) / (0.5163157894737 - 0.73)
    assert math.isclose(upper_fork_slope, fork_slope, abs_tol=1e-4)
    assert math.isclose(lower_fork_slope, fork_slope, abs_tol=1e-4)
    assert 0.736 + 0.035 + 0.025 < 0.85
    front_housing_edge = (0.43 + (0.91 - 0.86) / 1.9, 0.86)
    front_wheel_edge = (0.73 - 0.33 * 0.3 / math.hypot(0.3, 0.57),
                        0.33 + 0.33 * 0.57 / math.hypot(0.3, 0.57))
    assert math.isclose(0.5163157894737,
                        (front_housing_edge[0] + front_wheel_edge[0]) * 0.5,
                        abs_tol=1e-4)
    assert math.isclose(front_housing_edge[1], 0.86, abs_tol=1e-6)
    assert 0.4510526315789 > 0.445 - 0.14 * 0.5
    assert 0.86 < 0.90 + 0.10 * 0.5

    swingarm_slope = (0.42 - 0.33) / (-0.10 + 0.73)
    rear_single_slope = (0.42 - 0.3885714285714) / (-0.10 + 0.32)
    rear_double_slope = (0.3885714285714 - 0.33) / (-0.32 + 0.73)
    assert math.isclose(rear_single_slope, swingarm_slope, abs_tol=1e-4)
    assert math.isclose(rear_double_slope, swingarm_slope, abs_tol=1e-4)
    assert math.isclose(-0.32, (-0.24 + (-0.73 + 0.33)) * 0.5,
                        abs_tol=1e-6)
    stem_slope = (1.08 - 0.90) / (0.3352631578947 - 0.43)
    assert math.isclose(fork_slope, stem_slope, abs_tol=1e-4)
    assert math.hypot(0.3352631578947 - 0.43, 1.08 - 0.90) < 0.21

    # Extended saddle ties the tank's lower-forward corner to the engine's top.
    assert any(abs(point[0] + 0.73) < 1e-5
               and abs(point[1] - 0.13) < 1e-5
               and abs(point[2] - 0.71) < 1e-5
               for point in material_vertices['rubber'])
    assert any(abs(point[0] + 0.18) < 1e-5
               and abs(point[1] - 0.13) < 1e-5
               and abs(point[2] - 0.79) < 1e-5
               for point in material_vertices['rubber'])
    assert any(abs(point[0] - 0.24) < 1e-5
               and abs(point[1] - 0.13) < 1e-5
               and abs(point[2] - 0.79) < 1e-5
               for point in material_vertices['rubber'])
    assert any(abs(point[0] - 0.18) < 1e-5
               and abs(point[1] - 0.13) < 1e-5
               and abs(point[2] - 0.71) < 1e-5
               for point in material_vertices['rubber'])
    assert any(abs(point[0] + 0.805) < 1e-5
               and abs(point[1] - 0.105) < 1e-5
               and abs(point[2] - 0.795) < 1e-5
               for point in material_vertices['taillight'])

    headlight_points = material_vertices['headlight']
    taillight_points = material_vertices['taillight']
    assert math.isclose(max(point[1] for point in headlight_points)
                        - min(point[1] for point in headlight_points), 0.23,
                        abs_tol=1e-6)
    assert math.isclose(max(point[2] for point in headlight_points)
                        - min(point[2] for point in headlight_points), 0.08,
                        abs_tol=1e-6)
    headlight_border_y = (0.25 - 0.23) * 0.5
    headlight_border_z = (0.10 - 0.08) * 0.5
    assert math.isclose(headlight_border_y, headlight_border_z, abs_tol=1e-6)
    assert math.isclose(max(point[0] for point in headlight_points), 0.505,
                        abs_tol=1e-6)
    assert math.isclose((max(point[2] for point in headlight_points)
                         + min(point[2] for point in headlight_points)) * 0.5,
                        0.91, abs_tol=1e-6)
    assert any(abs(point[0] - 0.505) < 1e-6
               and abs(point[1] - 0.125) < 1e-6
               and abs(point[2] - 0.96) < 1e-6
               for point in material_vertices['frame'])
    assert any(abs(point[0] + 0.805) < 1e-6
               and abs(point[1] - 0.12) < 1e-6
               and abs(point[2] - 0.81) < 1e-6
               for point in material_vertices['frame'])
    assert math.isclose(max(point[1] for point in taillight_points)
                        - min(point[1] for point in taillight_points), 0.21,
                        abs_tol=1e-6)
    assert math.isclose(max(point[2] for point in taillight_points)
                        - min(point[2] for point in taillight_points), 0.09,
                        abs_tol=1e-6)
    taillight_border_y = (0.24 - 0.21) * 0.5
    taillight_border_z = (0.12 - 0.09) * 0.5
    assert math.isclose(taillight_border_y, taillight_border_z, abs_tol=1e-6)
    front_indicator_points = [
        point for point in material_vertices['indicator'] if point[0] > 0.0
    ]
    rear_indicator_points = [
        point for point in material_vertices['indicator'] if point[0] < 0.0
    ]
    for points in (front_indicator_points, rear_indicator_points):
        assert math.isclose(max(point[0] for point in points)
                            - min(point[0] for point in points), 0.07,
                            abs_tol=1e-6)
        assert math.isclose(max(point[2] for point in points)
                            - min(point[2] for point in points), 0.07,
                            abs_tol=1e-6)
    assert len(material_centers['indicator']) == 24
    front_indicators = [center for center in material_centers['indicator']
                        if center[0] > 0]
    rear_indicators = [center for center in material_centers['indicator']
                       if center[0] < 0]
    assert front_indicators and rear_indicators
    assert max(abs(center[1]) for center in front_indicators) > 0.15
    assert max(abs(center[1]) for center in rear_indicators) > 0.15
    assert any(math.isclose(center[2], 0.91, abs_tol=1e-6)
               for center in front_indicators)
    for side in (-1, 1):
        assert any(abs(point[0] + 0.805) < 1e-5
               and abs(point[1] - side * 0.12) < 1e-5
               and abs(point[2] - 0.785) < 1e-5
                   for point in material_vertices['indicator'])

    frame_vertices = material_vertices['frame']
    assert not any(-0.05 < point[0] < 0.30 and 0.55 < point[2] < 0.90
                   for point in frame_vertices)

    # Simple pegs project from both sides at the engine's lower front;
    # each shoe sole meets the top of a peg.
    for side in (-1.0, 1.0):
        shoe_tip = (0.085 + 0.11 * math.cos(math.radians(10))
                - 0.0225 * math.sin(math.radians(10)),
                side * 0.27,
                0.4475 + 0.11 * math.sin(math.radians(10))
                + 0.0225 * math.cos(math.radians(10)))
        assert any(math.dist(point, shoe_tip) < 1e-5
               for point in material_vertices['rider_shoes'])
        footrest_corner = (0.085 + 0.0625 * math.cos(math.radians(10))
                           - 0.025 * math.sin(math.radians(10)),
               side * 0.27,
                   0.40 + 0.0625 * math.sin(math.radians(10))
                           + 0.025 * math.cos(math.radians(10)))
        assert any(math.dist(point, footrest_corner) < 1e-5
               for point in material_vertices['metal'])
        assert any(abs(point[1] - side * 0.27) < 1e-5
               and abs(math.dist(point, (0.085, side * 0.27, 0.40))
                   - math.hypot(0.0625, 0.025)) < 1e-5
               for point in material_vertices['metal'])

    helmet_vertices = material_vertices['rider_helmet']
    assert any(assignment and assignment[0] == 'rider_helmet'
               and assignment[1] == (1.0, 1.0, 1.0, 1.0)
               for assignment in materials)
    assert math.isclose(min(point[2] for point in helmet_vertices), 1.37,
                        abs_tol=1e-6)
    assert math.isclose(max(point[2] for point in helmet_vertices), 1.61,
                        abs_tol=1e-6)
    assert max(point[2] for point in material_vertices['rider_skin']) < 1.53
    assert max(point[0] for point in material_vertices['rider_visor']) > 0.05