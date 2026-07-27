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

import bpy
from math import pi, cos, sin

from . entity_base import DSC_OT_entity


VEHICLE_CATEGORY_ITEMS = (
    ('car', 'Car', 'Create a car entity'),
    ('motorcycle', 'Motorcycle', 'Create a motorcycle entity'),
    ('bicycle', 'Bicycle', 'Create a bicycle entity'),
    ('bus', 'Bus', 'Create a bus entity'),
    ('heavyTruck', 'Heavy Truck', 'Create a heavy truck entity'),
    ('van', 'Van', 'Create a van entity'),
)


VEHICLE_GEOMETRY_DIMENSIONS = {
    'motorcycle': {
        'length': 2.4,
        'half_width': 0.35,
        'height': 1.35,
        'clearance': 0.22,
        'nose_ratio': 0.12,
        'roof_ratio': 0.45,
        'wheel_radius': 0.33,
        'wheel_half_width': 0.07,
        'wheel_segments': 12,
        'wheel_positions': [
            ('wheel_f', 0.78, 0.0),
            ('wheel_r', -0.78, 0.0),
        ],
    },
    'bicycle': {
        'length': 2.0,
        'half_width': 0.30,
        'height': 1.70,
        'clearance': 0.28,
        'nose_ratio': 0.08,
        'roof_ratio': 0.40,
        'wheel_radius': 0.36,
        'wheel_half_width': 0.03,
        'wheel_segments': 12,
        'wheel_positions': [
            ('wheel_f', 0.82, 0.0),
            ('wheel_r', -0.82, 0.0),
        ],
    },
    'bus': {
        'length': 12.2,
        'half_width': 1.25,
        'height': 3.25,
        'clearance': 0.24,
        'nose_ratio': 0.04,
        'roof_ratio': 0.70,
        'wheel_radius': 0.50,
        'wheel_half_width': 0.16,
        'wheel_segments': 14,
        'wheel_positions': [
            ('wheel_fl', 2.9, 1.02),
            ('wheel_fr', 2.9, -1.02),
            ('wheel_ml', -1.0, 1.02),
            ('wheel_mr', -1.0, -1.02),
            ('wheel_rl', -3.1, 1.02),
            ('wheel_rr', -3.1, -1.02),
        ],
    },
    'heavyTruck': {
        'length': 13.8,
        'half_width': 1.25,
        'height': 3.6,
        'clearance': 0.26,
        'nose_ratio': 0.06,
        'roof_ratio': 0.62,
        'wheel_radius': 0.52,
        'wheel_half_width': 0.17,
        'wheel_segments': 14,
        'wheel_positions': [
            ('wheel_fl', 3.2, 1.02),
            ('wheel_fr', 3.2, -1.02),
            ('wheel_m1l', -1.8, 1.02),
            ('wheel_m1r', -1.8, -1.02),
            ('wheel_m2l', -3.6, 1.02),
            ('wheel_m2r', -3.6, -1.02),
            ('wheel_rl', -5.0, 1.02),
            ('wheel_rr', -5.0, -1.02),
        ],
    },
    'van': {
        'length': 5.5,
        'half_width': 1.0,
        'height': 2.35,
        'clearance': 0.20,
        'nose_ratio': 0.08,
        'roof_ratio': 0.68,
        'wheel_radius': 0.38,
        'wheel_half_width': 0.11,
        'wheel_segments': 12,
        'wheel_positions': [
            ('wheel_fl', 1.62, 0.88),
            ('wheel_fr', 1.62, -0.88),
            ('wheel_rl', -1.55, 0.88),
            ('wheel_rr', -1.55, -0.88),
        ],
    },
}


class DSC_OT_entity_vehicle(DSC_OT_entity):
    bl_idname = 'dsc.entity_vehicle'
    bl_label = 'Vehicle'
    bl_description = 'Place a vehicle entity object'
    bl_options = {'REGISTER', 'UNDO'}

    entity_type = 'vehicle'
    entity_subtype = 'car'

    vehicle_category: bpy.props.EnumProperty(
        name='Vehicle category',
        description='ASAM OpenSCENARIO vehicle category',
        items=VEHICLE_CATEGORY_ITEMS,
        default='car',
    )

    def invoke(self, context, event):
        self.entity_subtype = self.vehicle_category
        return super().invoke(context, event)

    def _make_arch_xz(self, wheel_center_x, arch_radius, wheel_center_z):
        arch_angles_deg = [210, 135, 90, 45, 330]
        points = []
        for deg in arch_angles_deg:
            angle = deg * pi / 180
            points.append((
                wheel_center_x + arch_radius * cos(angle),
                wheel_center_z + arch_radius * sin(angle),
            ))
        return points

    def _make_prismatic_mesh(self, profile_xz, half_width):
        y_left = -half_width
        y_right = half_width

        count = len(profile_xz)
        vertices = [(x, y_left, z) for (x, z) in profile_xz]
        vertices.extend((x, y_right, z) for (x, z) in profile_xz)

        edges = []
        for index in range(count):
            next_index = (index + 1) % count
            edges.append([index, next_index])
            edges.append([index + count, next_index + count])
            edges.append([index, index + count])

        left_face = list(range(count))
        right_face = list(range(2 * count - 1, count - 1, -1))
        faces = [left_face, right_face]
        for index in range(count):
            next_index = (index + 1) % count
            faces.append([next_index, index, index + count, next_index + count])

        return vertices, edges, faces

    def _get_legacy_car_vertices_edges_faces(self):
        wheel_radius = 0.35
        wheel_x_front = 1.5
        wheel_x_rear = -1.4

        # Keep the original car body profile to preserve existing look.
        clearance = 0.15
        arch_clearance = 0.05
        arch_radius = wheel_radius + arch_clearance
        wheel_center_z = wheel_radius

        rear_arch = self._make_arch_xz(wheel_x_rear, arch_radius, wheel_center_z)
        front_arch = self._make_arch_xz(wheel_x_front, arch_radius, wheel_center_z)

        profile_xz = [
            (-2.20, 0.05 + clearance),
        ]
        profile_xz += rear_arch
        profile_xz += front_arch
        profile_xz += [
            (2.20, 0.01 + clearance),
            (2.20, 0.50 + clearance),
            (1.90, 0.80 + clearance),
            (1.10, 0.85 + clearance),
            (0.10, 1.60 + clearance),
            (-1.60, 1.58 + clearance),
            (-2.20, 0.80 + clearance),
        ]

        return self._make_prismatic_mesh(profile_xz, half_width=1.0)

    def _get_non_car_vertices_edges_faces(self):
        config = VEHICLE_GEOMETRY_DIMENSIONS[self.entity_subtype]
        length = config['length']
        x_front = length * 0.5
        x_rear = -length * 0.5

        wheel_positions = config['wheel_positions']
        front_axle_x = max(wheel_positions, key=lambda item: item[1])[1]
        rear_axle_x = min(wheel_positions, key=lambda item: item[1])[1]

        wheel_radius = config['wheel_radius']
        wheel_center_z = wheel_radius
        arch_radius = wheel_radius + 0.06

        rear_arch = self._make_arch_xz(rear_axle_x, arch_radius, wheel_center_z)
        front_arch = self._make_arch_xz(front_axle_x, arch_radius, wheel_center_z)

        clearance = config['clearance']
        height = config['height']
        nose_x = x_front - config['nose_ratio'] * length
        roof_peak_x = x_rear + config['roof_ratio'] * length

        profile_xz = [
            (x_rear, 0.05 + clearance),
        ]
        profile_xz += rear_arch
        profile_xz += front_arch
        profile_xz += [
            (x_front, 0.03 + clearance),
            (x_front, 0.46 * height),
            (nose_x, 0.64 * height),
            (roof_peak_x, 0.93 * height),
            (x_rear + 0.10 * length, 0.92 * height),
            (x_rear, 0.62 * height),
        ]

        return self._make_prismatic_mesh(profile_xz, half_width=config['half_width'])

    def _build_wheel_mesh(self, radius, half_width, segments):
        verts = []
        for index in range(segments):
            angle = 2 * pi * index / segments
            verts.append((radius * cos(angle), -half_width, radius * sin(angle)))
        for index in range(segments):
            angle = 2 * pi * index / segments
            verts.append((radius * cos(angle), half_width, radius * sin(angle)))

        faces = []
        for index in range(segments):
            next_index = (index + 1) % segments
            faces.append([index, next_index, segments + next_index, segments + index])
        faces.append(list(range(segments)))
        faces.append(list(range(2 * segments - 1, segments - 1, -1)))

        return verts, [], faces

    def get_vertices_edges_faces(self):
        if self.entity_subtype == 'car':
            return self._get_legacy_car_vertices_edges_faces()
        return self._get_non_car_vertices_edges_faces()

    def get_wheel_configs(self):
        if self.entity_subtype == 'car':
            wheel_radius = 0.35
            wheel_half_width = 0.1125
            wheel_segments = 12
            wheel_positions = [
                ('wheel_fl', 1.5, 0.8775),
                ('wheel_fr', 1.5, -0.8775),
                ('wheel_rl', -1.4, 0.8775),
                ('wheel_rr', -1.4, -0.8775),
            ]
        else:
            config = VEHICLE_GEOMETRY_DIMENSIONS[self.entity_subtype]
            wheel_radius = config['wheel_radius']
            wheel_half_width = config['wheel_half_width']
            wheel_segments = config['wheel_segments']
            wheel_positions = config['wheel_positions']

        verts, edges, faces = self._build_wheel_mesh(
            wheel_radius,
            wheel_half_width,
            wheel_segments,
        )
        z_center = wheel_radius

        return [
            (name, (x_pos, y_pos, z_center), verts, edges, faces)
            for name, x_pos, y_pos in wheel_positions
        ]
