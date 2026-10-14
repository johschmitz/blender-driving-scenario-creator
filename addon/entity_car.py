"""Car-specific geometry for the shared vehicle placement operator."""

from math import sqrt

from mathutils import Vector, geometry


class CarGeometryMixin:
    """Build the car mesh without defining or registering an operator."""

    def _get_car_vertices_edges_faces(self):
        profile_xz = self._wheel_arch_profile(
            -2.20, 2.20, (self.wheel_x_rear, self.wheel_x_front),
            self.wheel_radius, 0.18, arch_clearance=0.05)
        upper_profile_start = len(profile_xz)
        profile_xz.extend([
            (2.20, 0.66), (1.90, 1.0), (0.95, 1.72),
            (-0.65, 1.72), (-1.30, 1.10), (-2.20, 0.80),
        ])
        glass = ('glass', (0.025, 0.11, 0.16, 1.0))
        headlamp = ('headlight', (1.0, 0.78, 0.35, 1.0))
        taillamp = ('taillight', (0.78, 0.025, 0.018, 1.0))
        indicator = ('indicator', (1.0, 0.22, 0.015, 1.0))
        front_side_window_edge_lower = (-1.0, 1.18)
        front_side_window_edge_upper = (-0.62, 1.56)
        side_windows = [
            [(x, z) for x, z in (
                (0.16, 1.12), (0.16, 1.56), (0.82, 1.56),
                (1.30, 1.146), (1.30, 1.12))],
            [(x, z) for x, z in (
                (0.0, 1.12), (0.0, 1.56), (-0.62, 1.56),
                front_side_window_edge_lower, (-1.0, 1.12))],
        ]

        vertices, edges, faces, face_materials = [], [], [], []
        vertex_lookup, edge_lookup = {}, set()

        def add_face(points, material=None, reverse=False):
            indices = []
            for point in points:
                key = tuple(round(value, 7) for value in point)
                if key not in vertex_lookup:
                    vertex_lookup[key] = len(vertices)
                    vertices.append(tuple(point))
                indices.append(vertex_lookup[key])
            if len(set(indices)) < 3:
                return
            if reverse:
                indices.reverse()
            faces.append(indices)
            face_materials.append(material)
            for first, second in zip(indices, indices[1:] + indices[:1]):
                edge = (min(first, second), max(first, second))
                if edge not in edge_lookup:
                    edge_lookup.add(edge)
                    edges.append(edge)

        def area(loop):
            return sum(a[0] * b[1] - b[0] * a[1]
                       for a, b in zip(loop, loop[1:] + loop[:1]))

        def cut_surface(loops, to_3d, materials, reverse=False):
            outer_positive = area(loops[0]) > 0
            contours = [loops[0]]
            for hole in loops[1:]:
                if (area(hole) > 0) == outer_positive:
                    hole = list(reversed(hole))
                contours.append(hole)
            flat = [point for contour in contours for point in contour]
            projected = [[Vector((u, v, 0.0)) for u, v in contour]
                         for contour in contours]
            for triangle in geometry.tessellate_polygon(projected):
                add_face([to_3d(*flat[index]) for index in triangle],
                         reverse=reverse)
            for hole, material in zip(contours[1:], materials):
                add_face([to_3d(*point) for point in reversed(hole)],
                         material, reverse)

        for side, reverse in ((-1.0, False), (1.0, True)):
            cut_surface([profile_xz] + side_windows,
                        lambda x, z: (x, side, z), [glass, glass], reverse)

        def rectangle(u0, u1, v0, v1):
            return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

        count = len(profile_xz)
        for index, (x0, z0) in enumerate(profile_xz):
            next_index = (index + 1) % count
            x1, z1 = profile_xz[next_index]
            holes, materials = [], []
            if index in (upper_profile_start + 1, upper_profile_start + 3):
                holes.append(rectangle(0.14, 0.86, -0.88, 0.88))
                materials.append(glass)
            if index in (upper_profile_start - 1, count - 1):
                front = index == count - 1
                for center, width, z_min, z_max, material in (
                    (0.75, 0.32, 0.47, 0.63, headlamp if front else taillamp),
                    (0.80, 0.213333, 0.327, 0.393, indicator),
                ):
                    u0 = (z_min - z0) / (z1 - z0)
                    u1 = (z_max - z0) / (z1 - z0)
                    for side in (-1.0, 1.0):
                        holes.append(rectangle(min(u0, u1), max(u0, u1),
                                               side * center - width / 2,
                                               side * center + width / 2))
                        materials.append(material)
            to_3d = lambda u, y: (x0 + (x1 - x0) * u, y,
                                  z0 + (z1 - z0) * u)
            outer = [(1.0, -1.0), (0.0, -1.0),
                     (0.0, 1.0), (1.0, 1.0)]
            if holes:
                cut_surface([outer] + holes, to_3d, materials)
            else:
                add_face([to_3d(*point) for point in outer])

        mirror_builder = self._vehicle_mesh_builder_cls()
        mirror_trim = self._material('trim', (0.055, 0.065, 0.075, 1.0))
        # The authored profile has its nose at -X; the final transform below
        # reflects it so the placed car faces +X. The front side-window A-pillar
        # is the sloped profile edge immediately ahead of that window.
        front_a_pillar_lower = (-1.30, 1.10)
        front_a_pillar_upper = (-0.65, 1.72)
        mirror_center_z = 1.18
        pillar_height_fraction = (
            (mirror_center_z - front_a_pillar_lower[1])
            / (front_a_pillar_upper[1] - front_a_pillar_lower[1])
        )
        pillar_outer_x = (
            front_a_pillar_lower[0]
            + pillar_height_fraction
            * (front_a_pillar_upper[0] - front_a_pillar_lower[0])
        )
        window_height_fraction = (
            (mirror_center_z - front_side_window_edge_lower[1])
            / (front_side_window_edge_upper[1]
               - front_side_window_edge_lower[1])
        )
        window_edge_x = (
            front_side_window_edge_lower[0]
            + window_height_fraction
            * (front_side_window_edge_upper[0]
               - front_side_window_edge_lower[0])
        )
        pillar_center_x = (pillar_outer_x + window_edge_x) * 0.5
        mirror_pillar_y = 1.0
        mirror_width_y = 0.18
        mirror_length_x = 0.16
        mirror_stem_radius = 0.035
        full_mount_lateral_offset = 0.17
        full_mount_backward_offset = 0.03 + mirror_stem_radius
        for _ in range(8):
            projected_radius = (
                mirror_stem_radius * full_mount_lateral_offset
                / sqrt(full_mount_backward_offset ** 2
                       + full_mount_lateral_offset ** 2)
            )
            full_mount_backward_offset = 0.03 + projected_radius
        mount_lateral_offset = full_mount_lateral_offset * 0.5
        mount_backward_offset = full_mount_backward_offset * 0.5
        mirror_center_y = mirror_pillar_y + mount_lateral_offset + mirror_width_y * 0.5
        projected_radius = (
            mirror_stem_radius * mount_lateral_offset
            / sqrt(mount_backward_offset ** 2 + mount_lateral_offset ** 2)
        )
        mirror_front_edge_x = (
            pillar_center_x + mount_backward_offset - projected_radius
        )
        mirror_stem_end_x = pillar_center_x + mount_backward_offset
        mirror_center_x = mirror_front_edge_x + mirror_length_x * 0.5
        mount_embed_depth = 0.025
        mount_x_per_y = mount_backward_offset / mount_lateral_offset
        for side in (-1.0, 1.0):
            mirror_builder.add_tube(
                (pillar_center_x - mount_x_per_y * mount_embed_depth,
                 side * (mirror_pillar_y - mount_embed_depth), mirror_center_z),
                (mirror_stem_end_x + mount_x_per_y * mount_embed_depth,
                 side * (mirror_center_y - mirror_width_y * 0.5
                         + mount_embed_depth), mirror_center_z),
                mirror_stem_radius, mirror_trim)
            mirror_builder.add_box(
                (mirror_center_x, side * mirror_center_y, mirror_center_z),
                (mirror_length_x, mirror_width_y, 0.09), mirror_trim)
        vertex_offset = len(vertices)
        vertices.extend(mirror_builder.vertices)
        edges.extend((first + vertex_offset, second + vertex_offset)
                     for first, second in mirror_builder.edges)
        faces.extend([index + vertex_offset for index in face]
                     for face in mirror_builder.faces)
        face_materials.extend(mirror_builder.face_materials)

        vertices = [(-x + 1.5, y, z) for x, y, z in vertices]
        faces = [list(reversed(face)) for face in faces]
        self.face_materials = face_materials
        return vertices, edges, faces


def __getattr__(name):
    if name == 'DSC_OT_entity_car':
        from .entity_vehicle import DSC_OT_entity_vehicle
        return DSC_OT_entity_vehicle
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')