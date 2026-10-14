"""Van-specific geometry for the shared vehicle placement operator."""

from math import sqrt

from .entity_vehicle_geometry_helpers import transverse_rectangle as transverse_window


class VanGeometryMixin:
    """Build van geometry without defining or registering an operator."""

    def _get_van_vertices_edges_faces(self):
        config = self.VEHICLE_GEOMETRY_DIMENSIONS['van']
        length, height = config['length'], config['height']
        x_rear, x_front = -length * 0.5, length * 0.5
        half_width = config['half_width']
        clearance = config['clearance']
        wheel_radius = config['wheel_radius']
        axle_positions = [position[1] for position in config['wheel_positions']]

        profile = self._wheel_arch_profile(
            x_rear, x_front, axle_positions, wheel_radius, clearance)
        front_axle_index = profile.index((x_front, clearance))
        profile.extend([
            (x_front, height * 0.48),
            (x_front - 0.88, height * 0.94),
            (x_rear + 0.22, height * 0.96),
            (x_rear, height * 0.91),
            (x_rear, clearance + 0.05),
        ])
        front_window_edge = front_axle_index + 1
        rear_window_edge = front_axle_index + 4

        glass = self._material('glass', (0.025, 0.11, 0.16, 1.0))
        headlamp = self._material('headlight', (1.0, 0.78, 0.35, 1.0))
        taillamp = self._material('taillight', (0.78, 0.025, 0.018, 1.0))
        indicator = self._material('indicator', (1.0, 0.22, 0.015, 1.0))
        body_paint = self._material('body_highlight', (0.18, 0.34, 0.48, 1.0))
        dark_trim = self._material('trim', (0.055, 0.065, 0.075, 1.0))

        pillar_lower = (x_front, height * 0.48)
        pillar_upper = (x_front - 0.88, height * 0.94)
        window_edge_lower_z = height * 0.50
        lower_pillar_fraction = (
            (window_edge_lower_z - pillar_lower[1])
            / (pillar_upper[1] - pillar_lower[1]))
        window_edge_lower = (
            pillar_lower[0]
            + lower_pillar_fraction * (pillar_upper[0] - pillar_lower[0]) - 0.21,
            window_edge_lower_z,
        )
        window_edge_upper = (
            window_edge_lower[0]
            + (pillar_upper[0] - pillar_lower[0])
            * (height * 0.88 - window_edge_lower[1])
            / (pillar_upper[1] - pillar_lower[1]),
            height * 0.88,
        )
        side_windows = [(
            [
                (x_front - 1.58, height * 0.50),
                window_edge_lower,
                window_edge_upper,
                (x_front - 1.58, height * 0.88),
            ],
            glass,
        )]

        facet_windows = {
            front_axle_index: [
                (transverse_window(0.48, 0.76, -0.91, -0.55), headlamp),
                (transverse_window(0.48, 0.76, 0.55, 0.91), headlamp),
                (transverse_window(0.48, 0.76, -0.99, -0.93), indicator),
                (transverse_window(0.48, 0.76, 0.93, 0.99), indicator),
            ],
            front_window_edge: [
                (transverse_window(0.08, 0.84, -half_width * 0.82,
                                   half_width * 0.82), glass),
            ],
            rear_window_edge: [
                (transverse_window(0.64, 0.74, -0.82, -0.64), taillamp),
                (transverse_window(0.64, 0.74, 0.64, 0.82), taillamp),
                (transverse_window(0.64, 0.74, -0.98, -0.84), indicator),
                (transverse_window(0.64, 0.74, 0.84, 0.98), indicator),
            ],
        }

        builder = self._vehicle_mesh_builder_cls()
        builder.add_shell(profile, half_width, side_windows,
                          body_material=body_paint,
                          facet_windows=facet_windows)

        mirror_center_z = height * 0.60
        pillar_fraction = (
            (mirror_center_z - pillar_lower[1])
            / (pillar_upper[1] - pillar_lower[1]))
        pillar_outer_x = (
            pillar_lower[0]
            + pillar_fraction * (pillar_upper[0] - pillar_lower[0]))
        window_fraction = (
            (mirror_center_z - window_edge_lower[1])
            / (window_edge_upper[1] - window_edge_lower[1]))
        window_edge_x = (
            window_edge_lower[0]
            + window_fraction * (window_edge_upper[0] - window_edge_lower[0]))
        pillar_center_x = (pillar_outer_x + window_edge_x) * 0.5
        mirror_width_y = 0.18
        mirror_length_x = 0.16
        mirror_height_z = 0.18
        mirror_embed_depth = 0.025
        mirror_stem_radius = 0.035
        mirror_pillar_y = half_width
        mount_lateral_offset = 0.115
        mount_backward_offset = 0.03 + mirror_stem_radius
        for _ in range(8):
            projected_radius = (
                mirror_stem_radius * mount_lateral_offset
                / sqrt(mount_backward_offset ** 2 + mount_lateral_offset ** 2))
            mount_backward_offset = 0.03 + projected_radius
        mirror_center_y = (
            mirror_pillar_y + mount_lateral_offset
            + mirror_width_y * 0.5 - mirror_embed_depth)
        projected_radius = (
            mirror_stem_radius * mount_lateral_offset
            / sqrt(mount_backward_offset ** 2 + mount_lateral_offset ** 2))
        mirror_front_edge_x = (
            pillar_center_x - mount_backward_offset + projected_radius)
        mirror_center_x = mirror_front_edge_x - mirror_length_x * 0.5
        mount_x_per_y = mount_backward_offset / mount_lateral_offset
        for side in (-1.0, 1.0):
            builder.add_tube(
                (pillar_center_x + mount_x_per_y * mirror_embed_depth,
                 side * (mirror_pillar_y - mirror_embed_depth), mirror_center_z),
                (pillar_center_x - mount_backward_offset
                 - mount_x_per_y * mirror_embed_depth,
                 side * (mirror_center_y - mirror_width_y * 0.5
                         + mirror_embed_depth), mirror_center_z),
                mirror_stem_radius, dark_trim)
            builder.add_box(
                (mirror_center_x, side * mirror_center_y, mirror_center_z),
                (mirror_length_x, mirror_width_y, mirror_height_z), dark_trim)

        self.face_materials = builder.face_materials
        origin_x = config['origin_x']
        vertices = [(x - origin_x, y, z) for x, y, z in builder.vertices]
        return vertices, builder.edges, builder.faces
