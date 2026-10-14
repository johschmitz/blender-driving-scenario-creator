"""Bus-specific geometry for the shared vehicle placement operator."""

from .entity_vehicle_geometry_helpers import transverse_rectangle as transverse_window


class BusGeometryMixin:
    """Build bus geometry without defining or registering an operator."""

    def _get_bus_vertices_edges_faces(self):
        config = self.VEHICLE_GEOMETRY_DIMENSIONS['bus']
        length, height = config['length'], config['height']
        x_rear, x_front = -length * 0.5, length * 0.5
        half_width, clearance = config['half_width'], config['clearance']
        axle_positions = [position[1] for position in config['wheel_positions']]

        profile = self._wheel_arch_profile(
            x_rear, x_front, axle_positions, config['wheel_radius'], clearance)
        arch_crown_z = config['wheel_radius'] * 2 + 0.10
        for index, axle_x in enumerate(sorted(set(axle_positions))):
            crown_index = profile.index((axle_x, arch_crown_z))
            crown_x, crown_z = profile[crown_index]
            profile[crown_index] = (
                crown_x, crown_z + (0.002 if index != 1 else -0.002))
        front_facet_index = profile.index((x_front, clearance))
        roof_front = x_front - 0.35
        roof_rear = x_rear + 0.55
        shoulder_z = height * 0.45 - 0.50
        roof_z = height * 0.97
        common_window_top_z = height * 0.87
        windshield_bottom_z = arch_crown_z
        windshield_bottom_fraction = (
            (windshield_bottom_z - shoulder_z) / (roof_z - shoulder_z))
        windshield_top_fraction = (
            (common_window_top_z - shoulder_z) / (roof_z - shoulder_z))
        profile.extend([
            (x_front, shoulder_z),
            (roof_front, roof_z),
            (roof_rear, roof_z),
            (x_rear, height * 0.92),
        ])
        windshield_facet = front_facet_index + 1
        rear_facet = front_facet_index + 4

        glass = self._material('glass', (0.025, 0.11, 0.16, 1.0))
        headlamp = self._material('headlight', (1.0, 0.78, 0.35, 1.0))
        taillamp = self._material('taillight', (0.78, 0.025, 0.018, 1.0))
        indicator = self._material('indicator', (1.0, 0.22, 0.015, 1.0))
        body_paint = self._material('body_highlight', (0.18, 0.34, 0.48, 1.0))
        dark_trim = self._material('trim', (0.055, 0.065, 0.075, 1.0))

        passenger_start = roof_rear
        door_start = x_front - 1.025
        pillar_x_per_z = (roof_front - x_front) / (roof_z - shoulder_z)
        window_front_edge_lower_x = (
            x_front + pillar_x_per_z * (windshield_bottom_z - shoulder_z) - 0.21)
        window_front_edge_upper_x = (
            x_front + pillar_x_per_z * (common_window_top_z - shoulder_z) - 0.21)
        passenger_window_lower_z = height * 0.61
        parallel_rear_edge_upper_x = (
            door_start + pillar_x_per_z
            * (windshield_bottom_z - passenger_window_lower_z))
        window_rear_edge_upper_x = window_front_edge_lower_x - 0.80
        rear_edge_backward_shift = (
            parallel_rear_edge_upper_x - window_rear_edge_upper_x)
        window_rear_edge_lower_x = door_start - rear_edge_backward_shift
        side_window = [
            (passenger_start, passenger_window_lower_z),
            (window_rear_edge_lower_x, passenger_window_lower_z),
            (window_rear_edge_upper_x, windshield_bottom_z),
            (window_front_edge_lower_x, windshield_bottom_z),
            (window_front_edge_upper_x, common_window_top_z),
            (passenger_start, common_window_top_z),
        ]
        side_windows = [(side_window, glass)]

        front_lamp_u_bottom = 0.16
        front_lamp_u_top = 0.31
        front_lamp_u_top += (front_lamp_u_top - front_lamp_u_bottom) * 0.25
        rear_edge_height = height * 0.92 - clearance
        rear_window_top_fraction = (
            (height * 0.92 - height * 0.87) / rear_edge_height)
        rear_window_bottom_fraction = (
            (height * 0.92 - height * 0.61) / rear_edge_height)
        facet_windows = {
            front_facet_index: [
                (transverse_window(front_lamp_u_bottom, front_lamp_u_top,
                                   -0.90, -0.68), headlamp),
                (transverse_window(front_lamp_u_bottom, front_lamp_u_top,
                                   0.68, 0.90), headlamp),
                (transverse_window(front_lamp_u_bottom, front_lamp_u_top,
                                   -1.19, -0.98), indicator),
                (transverse_window(front_lamp_u_bottom, front_lamp_u_top,
                                   0.98, 1.19), indicator),
            ],
            windshield_facet: [
                (transverse_window(windshield_bottom_fraction,
                                   windshield_top_fraction,
                                   -half_width * 0.82,
                                   half_width * 0.82), glass),
            ],
            rear_facet: [
                (transverse_window(rear_window_top_fraction,
                                   rear_window_bottom_fraction,
                                   -half_width * 0.82,
                                   half_width * 0.82), glass),
                (transverse_window(0.69, 0.80, -0.91, -0.70), taillamp),
                (transverse_window(0.69, 0.80, 0.70, 0.91), taillamp),
                (transverse_window(0.69, 0.80, -1.20, -0.99), indicator),
                (transverse_window(0.69, 0.80, 0.99, 1.20), indicator),
            ],
        }

        builder = self._vehicle_mesh_builder_cls()
        builder.add_shell(profile, half_width, side_windows,
                          body_material=body_paint,
                          facet_windows=facet_windows)

        mirror_arm_z = common_window_top_z + 0.035
        mirror_mount_front_x = x_front + 0.32
        mirror_depth_x = 0.09
        mirror_center_x = mirror_mount_front_x - mirror_depth_x * 0.5
        mirror_mount_width_y = 0.10
        mirror_mount_height_z = 0.05
        mirror_width_y = 0.22
        mirror_height = 0.55
        mirror_mount_center_y = half_width + mirror_mount_width_y * 0.5
        mirror_mount_inner_y = mirror_mount_center_y - mirror_mount_width_y * 0.5
        mirror_center_y = mirror_mount_inner_y + mirror_width_y * 0.5
        mirror_center_z = (mirror_arm_z - mirror_mount_height_z * 0.5
                           - mirror_height * 0.5)
        mirror_mount_start_x = (door_start + x_front) * 0.5 - 0.15
        for side in (-1.0, 1.0):
            mirror_arm_start = (mirror_mount_start_x,
                                side * mirror_mount_center_y, mirror_arm_z)
            mirror_arm_end = (mirror_mount_front_x,
                              side * mirror_mount_center_y, mirror_arm_z)
            builder.add_tube(
                mirror_arm_start, mirror_arm_end, mirror_mount_width_y * 0.5,
                dark_trim,
                height_scale=mirror_mount_height_z / mirror_mount_width_y)
            builder.add_box(
                (mirror_center_x, side * mirror_center_y, mirror_center_z),
                (mirror_depth_x, mirror_width_y, mirror_height), dark_trim)

        self.face_materials = builder.face_materials
        origin_x = config.get('origin_x', 0.0)
        vertices = [(x - origin_x, y, z) for x, y, z in builder.vertices]
        return vertices, builder.edges, builder.faces
