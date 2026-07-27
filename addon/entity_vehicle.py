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
from math import pi, cos, sin, sqrt, asin, atan2
from mathutils import Vector, geometry

from . entity_base import DSC_OT_entity
from . import helpers


VEHICLE_CATEGORY_ITEMS = (
    ('car', 'Car', 'Create a car entity'),
    ('motorcycle', 'Motorbike', 'Create a motorbike entity'),
    ('bicycle', 'Bicycle', 'Create a bicycle entity'),
    ('van', 'Van', 'Create a van entity'),
    ('bus', 'Bus', 'Create a bus entity'),
    ('heavyTruck', 'Truck', 'Create a truck entity'),
)


VEHICLE_GEOMETRY_DIMENSIONS = {
    'motorcycle': {
        'length': 2.2,
        'half_width': 0.42,
        'height': 1.62,
        'clearance': 0.19,
        'nose_ratio': 0.12,
        'roof_ratio': 0.45,
        'wheel_radius': 0.33,
        'wheel_half_width': 0.07,
        'front_wheel_half_width': 0.055,
        'rear_wheel_half_width': 0.085,
        'wheel_segments': 12,
        'origin_x': -0.73,
        'wheel_positions': [
            ('wheel_f', 0.73, 0.0),
            ('wheel_r', -0.73, 0.0),
        ],
    },
    'bicycle': {
        'length': 1.80,
        'half_width': 0.34,
        'height': 1.70,
        'clearance': 0.30,
        'nose_ratio': 0.08,
        'roof_ratio': 0.40,
        # 28-inch (700C) nominal wheel outside diameter: 28 * 0.0254 m.
        'wheel_radius': 28 * 0.0254 / 2,
        'wheel_half_width': 0.02,
        'wheel_segments': 12,
        'origin_x': -0.64,
        'wheel_positions': [
            ('wheel_f', 0.4528, 0.0),
            ('wheel_r', -0.64, 0.0),
        ],
    },
    'bus': {
        # Segment dimensions sum to 13.115 m: 2.890 + 6.090 + 1.350 + 2.785.
        'length': 13.115,
        'half_width': 1.25,
        'height': 3.25,
        'clearance': 0.24,
        'nose_ratio': 0.04,
        'roof_ratio': 0.70,
        'front_overhang': 2.890,
        'wheelbase': 6.090,
        'rear_axle_spacing': 1.350,
        'rear_overhang': 2.785,
        # Place the object origin on the ground below the first rear axle.
        'origin_x': -2.4225,
        'wheel_radius': 0.50,
        'wheel_half_width': 0.16,
        'wheel_segments': 14,
        'wheel_positions': [
            ('wheel_fl', 3.6675, 1.02),
            ('wheel_fr', 3.6675, -1.02),
            ('wheel_ml', -2.4225, 1.02),
            ('wheel_mr', -2.4225, -1.02),
            ('wheel_rl', -3.7725, 1.02),
            ('wheel_rr', -3.7725, -1.02),
        ],
    },
    'heavyTruck': {
        # Actros 1845 LS 4x2 tractor with a three-axle semitrailer.
        # Combination envelope is 16.5 m; tractor dimensions are modeled separately.
        'length': 16.5,
        'half_width': 1.25,
        'height': 4.0,
        'tractor_rear_x': 1.90,
        # The truck object's origin is the tractor's rear axle center.
        'origin_x': 2.60,
        'tractor_length': 6.00,
        'tractor_front_x': 7.90,
        'wheelbase': 3.85,
        'tractor_deck_z': 1.03,
        'cab_rear_x': 5.15,
        'cab_roof_z': 4.00,
        'trailer_front_x': 4.75,
        'trailer_half_width': 1.25,
        'trailer_floor_z': 1.15,
        'trailer_roof_z': 4.00,
        'trailer_interior_height': 2.68,
        'trailer_side_loading_height': 2.60,
        'fifth_wheel_x': 3.15,
        'fifth_wheel_radius': 0.50,
        'fifth_wheel_center_cutout_radius': 0.0508,
        'fifth_wheel_bottom_z': 1.03,
        'clearance': 0.30,
        'nose_ratio': 0.06,
        'roof_ratio': 0.62,
        'wheel_radius': 0.50,
        # 385/65 R22.5 tyre: rim diameter plus two 65% sidewalls.
        'trailer_rim_diameter': 22.5 * 0.0254,
        'trailer_tire_width': 0.385,
        'trailer_tire_aspect_ratio': 0.65,
        'trailer_wheel_radius': (22.5 * 0.0254 + 2 * 0.385 * 0.65) / 2,
        'trailer_wheel_half_width': 0.385 / 2,
        'wheel_half_width': 0.17,
        # Rear tire spans the side-box width between the chassis rail and body edge.
        'rear_wheel_half_width': (1.25 - (0.48 + 0.17 / 2)) / 2,
        'rear_wheel_center_y': (1.25 + (0.48 + 0.17 / 2)) / 2,
        'wheel_segments': 16,
        'wheel_positions': [
            ('wheel_fl', 6.45, 1.02),
            ('wheel_fr', 6.45, -1.02),
            ('wheel_rl', 2.60, 0.9075),
            ('wheel_rr', 2.60, -0.9075),
            ('wheel_t1l', -5.25, 1.02),
            ('wheel_t1r', -5.25, -1.02),
            ('wheel_t2l', -6.35, 1.02),
            ('wheel_t2r', -6.35, -1.02),
            ('wheel_t3l', -7.45, 1.02),
            ('wheel_t3r', -7.45, -1.02),
        ],
    },
    'van': {
        # Mercedes Sprinter L2H2-style panel van (approximate exterior body dimensions).
        'length': 5.93,
        'half_width': 1.01,
        'height': 2.62,
        'clearance': 0.24,
        'nose_ratio': 0.08,
        'roof_ratio': 0.68,
        'wheel_radius': 0.36,
        'wheel_half_width': 0.12,
        'wheel_segments': 12,
        'origin_x': -1.735,
        'wheel_positions': [
            ('wheel_fl', 1.93, 0.88),
            ('wheel_fr', 1.93, -0.88),
            ('wheel_rl', -1.735, 0.88),
            ('wheel_rr', -1.735, -0.88),
        ],
    },
}


class _VehicleMeshBuilder:
    """Accumulate vehicle body parts and keep face material data in sync."""

    def __init__(self):
        self.vertices = []
        self.edges = []
        self.faces = []
        self.face_materials = []
        self.vertex_lookup = {}
        self.edge_lookup = set()

    def add_face(self, points, material=None, reverse=False):
        points = [Vector(point) for point in points]
        if len(points) < 3:
            return
        normal = (points[1] - points[0]).cross(points[2] - points[0])
        if normal.length < 1e-9:
            return
        indices = []
        for point in points:
            key = tuple(round(value, 7) for value in point)
            if key not in self.vertex_lookup:
                self.vertex_lookup[key] = len(self.vertices)
                self.vertices.append(tuple(point))
            indices.append(self.vertex_lookup[key])
        if len(set(indices)) < 3:
            return
        if reverse:
            indices.reverse()
        self.faces.append(indices)
        self.face_materials.append(material)
        for a, b in zip(indices, indices[1:] + indices[:1]):
            edge = (min(a, b), max(a, b))
            if edge not in self.edge_lookup:
                self.edge_lookup.add(edge)
                self.edges.append(edge)

    @staticmethod
    def _area(loop):
        return sum(a[0] * b[1] - b[0] * a[1]
                   for a, b in zip(loop, loop[1:] + loop[:1]))

    @staticmethod
    def _point_in_loop(point, loop):
        x, y = point
        inside = False
        for first, second in zip(loop, loop[1:] + loop[:1]):
            if ((first[1] > y) != (second[1] > y)
                    and x < (second[0] - first[0]) * (y - first[1])
                    / (second[1] - first[1]) + first[0]):
                inside = not inside
        return inside

    def _add_planar_region(self, loops, to_3d, hole_materials, reverse=False,
                           excluded_regions=()):
        outer_positive = self._area(loops[0]) > 0
        contours = [loops[0]]
        for hole in loops[1:]:
            if (self._area(hole) > 0) == outer_positive:
                hole = list(reversed(hole))
            contours.append(hole)
        flat = [point for contour in contours for point in contour]
        projected = [[Vector((u, v, 0.0)) for u, v in contour]
                     for contour in contours]
        for triangle in geometry.tessellate_polygon(projected):
            center = tuple(sum(flat[index][axis] for index in triangle) / 3
                           for axis in (0, 1))
            if any(self._point_in_loop(center, region)
                   for region in excluded_regions):
                continue
            self.add_face([to_3d(*flat[index]) for index in triangle],
                          reverse=reverse)
        for hole, material in zip(contours[1:], hole_materials):
            if material is not None:
                self.add_face([to_3d(*point) for point in reversed(hole)],
                              material, reverse)

    def add_shell(self, profile_xz, half_width, windows=(), body_material=None,
                  facet_windows=None, facet_cutouts=None, side_cutouts=(),
                  y_center=0.0, open_facets=(), side_exclusions=()):
        """Create a closed extruded shell with inset, separately colored glazing."""
        face_start = len(self.face_materials)
        side_windows = [window for window, _material in windows] + list(side_cutouts)
        window_materials = ([material for _window, material in windows]
                            + [None] * len(side_cutouts))
        for side, reverse in ((-half_width, False), (half_width, True)):
            self._add_planar_region(
                [profile_xz] + side_windows,
                lambda x, z, side=side: (x, side + y_center, z),
                window_materials,
                reverse,
                excluded_regions=side_exclusions,
            )

        facet_windows = facet_windows or {}
        facet_cutouts = facet_cutouts or {}
        for index, (x0, z0) in enumerate(profile_xz):
            if index in open_facets:
                continue
            x1, z1 = profile_xz[(index + 1) % len(profile_xz)]
            windows_on_facet = facet_windows.get(index)
            cutouts_on_facet = facet_cutouts.get(index, ())
            if windows_on_facet or cutouts_on_facet:
                loops = [[(0.0, -half_width), (1.0, -half_width),
                          (1.0, half_width), (0.0, half_width)]]
                loops.extend(loop for loop, _material in (windows_on_facet or ()))
                loops.extend(cutouts_on_facet)
                materials = [material for _loop, material
                             in (windows_on_facet or ())]
                materials.extend([None] * len(cutouts_on_facet))

                def facet_to_3d(u, y, x0=x0, z0=z0, x1=x1, z1=z1):
                    return (x0 + (x1 - x0) * u, y + y_center,
                            z0 + (z1 - z0) * u)

                self._add_planar_region(loops, facet_to_3d, materials)
            else:
                self.add_face([
                    (x0, -half_width + y_center, z0),
                    (x1, -half_width + y_center, z1),
                    (x1, half_width + y_center, z1),
                    (x0, half_width + y_center, z0),
                ])

        if body_material is not None:
            for index in range(face_start, len(self.face_materials)):
                if self.face_materials[index] is None:
                    self.face_materials[index] = body_material

    def add_prism(self, profile_xz, half_width, material=None):
        start = len(self.face_materials)
        self.add_shell(profile_xz, half_width, body_material=material)
        if material is not None:
            for index in range(start, len(self.face_materials)):
                self.face_materials[index] = material

    def add_box(self, center, size, material=None, rotation_y=0.0):
        cx, cy, cz = center
        sx, sy, sz = (value * 0.5 for value in size)
        x0, x1 = cx - sx, cx + sx
        y0, y1 = cy - sy, cy + sy
        z0, z1 = cz - sz, cz + sz
        faces = (
            ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)),
            ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)),
            ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)),
            ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)),
            ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)),
            ((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)),
        )
        for face in faces:
            if rotation_y:
                face = tuple((cx + cos(rotation_y) * (x - cx)
                              + sin(rotation_y) * (z - cz), y,
                              cz - sin(rotation_y) * (x - cx)
                              + cos(rotation_y) * (z - cz))
                             for x, y, z in face)
            self.add_face(face, material)

    def add_lamp_housing_x(self, center, size, lens_size, outward_sign,
                           housing_material, lens_material):
        """Build a connected box housing with a flush, separately-materialed lens."""
        cx, cy, cz = center
        sx, sy, sz = (value * 0.5 for value in size)
        lens_y, lens_z = (value * 0.5 for value in lens_size)
        front_x = cx + outward_sign * sx
        back_x = cx - outward_sign * sx
        yz = ((-sy, -sz), (sy, -sz), (sy, sz), (-sy, sz))
        outer_front = [(front_x, cy + y, cz + z) for y, z in yz]
        outer_back = [(back_x, cy + y, cz + z) for y, z in yz]
        inner_front = [
            (front_x, cy + y * (lens_y / sy), cz + z * (lens_z / sz))
            for y, z in yz
        ]
        for index in range(4):
            following = (index + 1) % 4
            front_frame = (outer_front[index], outer_front[following],
                           inner_front[following], inner_front[index])
            if len(set(front_frame)) >= 3:
                self.add_face(front_frame, housing_material)
            self.add_face((outer_front[index], outer_front[following],
                           outer_back[following], outer_back[index]),
                          housing_material)
        self.add_face(outer_back, housing_material)
        self.add_face(inner_front, lens_material)

    def add_profile_band(self, centerline, center_y, width, thickness, material):
        """Extrude a constant-thickness 2D profile band across the vehicle width."""
        half_thickness = thickness * 0.5
        normals = []
        for first, second in zip(centerline, centerline[1:]):
            dx, dz = second[0] - first[0], second[1] - first[1]
            length = sqrt(dx * dx + dz * dz)
            if length < 1e-9:
                raise ValueError('Profile band centerline contains duplicate points')
            normals.append((-dz / length, dx / length))

        outer, inner = [], []
        for index, point in enumerate(centerline):
            if index == 0:
                nx, nz = normals[0]
                scale = half_thickness
            elif index == len(centerline) - 1:
                nx, nz = normals[-1]
                scale = half_thickness
            else:
                previous, following = normals[index - 1], normals[index]
                nx, nz = previous[0] + following[0], previous[1] + following[1]
                length = sqrt(nx * nx + nz * nz)
                if length < 1e-9:
                    raise ValueError('Profile band centerline reverses direction')
                nx, nz = nx / length, nz / length
                scale = half_thickness / (nx * following[0] + nz * following[1])
            outer.append((point[0] + nx * scale, point[1] + nz * scale))
            inner.append((point[0] - nx * scale, point[1] - nz * scale))

        profile = outer + list(reversed(inner))
        y_values = (center_y - width * 0.5, center_y + width * 0.5)
        vertices = [(x, y, z) for y in y_values for x, z in profile]
        count = len(profile)
        self.add_face(vertices[:count], material)
        self.add_face(vertices[count:], material, reverse=True)
        for index in range(count):
            following = (index + 1) % count
            self.add_face((vertices[index], vertices[following],
                           vertices[count + following], vertices[count + index]),
                          material)

    def add_tube(self, start, end, radius, material,
                 cap_start=True, cap_end=True, roll=0.0, height_scale=1.0):
        """Add a simple four-sided low-poly tube between 3D points."""
        start, end = Vector(start), Vector(end)
        axis = end - start
        if axis.length < 1e-8:
            return
        axis.normalize()
        reference = Vector((0.0, 1.0, 0.0))
        if abs(axis.dot(reference)) > 0.9:
            reference = Vector((0.0, 0.0, 1.0))
        first = axis.cross(reference).normalized()
        second = axis.cross(first).normalized()
        rolled_first = first * cos(roll) + second * sin(roll)
        rolled_second = second * cos(roll) - first * sin(roll)
        first = rolled_first * radius * height_scale
        second = rolled_second * radius
        if height_scale == 1.0:
            start_offsets = (first, second, -first, -second)
            end_offsets = start_offsets
        else:
            start_offsets = (first + second, -first + second,
                             -first - second, first - second)
            end_offsets = start_offsets
        start_ring = [start + offset for offset in start_offsets]
        end_ring = [end + offset for offset in end_offsets]
        if cap_start:
            self.add_face(start_ring, material, reverse=True)
        if cap_end:
            self.add_face(end_ring, material)
        for index in range(4):
            next_index = (index + 1) % 4
            self.add_face((start_ring[index], start_ring[next_index],
                           end_ring[next_index], end_ring[index]), material)

    def add_end_lamps(self, front_x, rear_x, half_width, z, height, width):
        headlamp = ('headlight', (1.0, 0.78, 0.35, 1.0))
        taillamp = ('taillight', (0.78, 0.025, 0.018, 1.0))
        for side in (-1.0, 1.0):
            self.add_box((front_x, side * half_width * 0.72, z),
                         (0.06, width, height), headlamp)
            self.add_box((rear_x, side * half_width * 0.72, z),
                         (0.06, width, height), taillamp)


class DSC_OT_entity_vehicle(DSC_OT_entity):
    bl_idname = 'dsc.entity_vehicle'
    bl_label = 'Vehicle'
    bl_description = 'Place a vehicle entity object'
    bl_options = {'REGISTER', 'UNDO'}

    entity_type = 'vehicle'
    entity_subtype = 'car'

    # Car axle and wheel dimensions, in the authored model coordinates.
    wheel_radius = 0.35
    wheel_half_width = 0.1125
    wheel_segments = 12
    wheel_x_front = 1.5
    wheel_x_rear = -1.4
    wheel_y_half_track = 0.8775
    origin_offset_x = -wheel_x_rear

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
            for a, b in zip(indices, indices[1:] + indices[:1]):
                edge = (min(a, b), max(a, b))
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

        n = len(profile_xz)
        for i, (x0, z0) in enumerate(profile_xz):
            j = (i + 1) % n
            x1, z1 = profile_xz[j]
            holes, materials = [], []
            if i in (upper_profile_start + 1, upper_profile_start + 3):
                holes.append(rectangle(0.14, 0.86, -0.88, 0.88))
                materials.append(glass)
            if i in (upper_profile_start - 1, n - 1):
                front = i == n - 1
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

        mirror_builder = _VehicleMeshBuilder()
        mirror_trim = self._material('trim', (0.055, 0.065, 0.075, 1.0))
        # The authored profile has its nose at -X; the final transform below
        # reflects it so the placed car faces +X. The front side-window A-pillar
        # is the sloped profile edge immediately ahead of that window, from the
        # windshield corner to the roof corner.
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
        # In authored coordinates -X is forward. Moving the mount endpoint
        # toward +X therefore angles it backward in the final +X-forward car.
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
        mirror_center_y = (
            mirror_pillar_y + mount_lateral_offset + mirror_width_y * 0.5
        )
        projected_radius = (
            mirror_stem_radius * mount_lateral_offset
            / sqrt(mount_backward_offset ** 2 + mount_lateral_offset ** 2)
        )
        # The housing's authored low-X edge becomes its forward edge after
        # reflection. Keep the stem's forward-facing edge flush with this face.
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
                 side * (mirror_pillar_y - mount_embed_depth),
                 mirror_center_z),
                (mirror_stem_end_x + mount_x_per_y * mount_embed_depth,
                 side * (mirror_center_y - mirror_width_y * 0.5
                         + mount_embed_depth), mirror_center_z),
                mirror_stem_radius,
                mirror_trim,
            )
            mirror_builder.add_box(
                (mirror_center_x, side * mirror_center_y, mirror_center_z),
                (mirror_length_x, mirror_width_y, 0.09),
                mirror_trim,
            )
        vertex_offset = len(vertices)
        vertices.extend(mirror_builder.vertices)
        edges.extend((first + vertex_offset, second + vertex_offset)
                     for first, second in mirror_builder.edges)
        faces.extend([index + vertex_offset for index in face]
                     for face in mirror_builder.faces)
        face_materials.extend(mirror_builder.face_materials)

        # Reflect the authored -X-forward profile into +X-forward object space;
        # the translation places the rear axle at the object origin.
        vertices = [(-x + 1.5, y, z) for x, y, z in vertices]
        faces = [list(reversed(face)) for face in faces]
        self.face_materials = face_materials
        return vertices, edges, faces

    def _get_non_car_vertices_edges_faces(self):
        if self.entity_subtype in {'bicycle', 'motorcycle'}:
            return self._get_two_wheeler_vertices_edges_faces()
        if self.entity_subtype == 'heavyTruck':
            return self._get_heavy_truck_vertices_edges_faces()
        if self.entity_subtype == 'bus':
            return self._get_bus_vertices_edges_faces()
        return self._get_road_vehicle_vertices_edges_faces()

    def _wheel_arch_profile(self, rear_x, front_x, axle_positions, radius,
                            clearance, arch_clearance=0.10):
        profile = [(rear_x, clearance)]
        for axle_x in sorted(set(axle_positions)):
            arch_radius = radius + arch_clearance
            profile.extend([
                (axle_x - arch_radius, clearance),
                (axle_x - arch_radius, radius),
            ])
            for degrees in (150, 120, 90, 60, 30):
                angle = degrees * pi / 180.0
                profile.append((axle_x + arch_radius * cos(angle),
                                radius + arch_radius * sin(angle)))
            profile.extend([
                (axle_x + arch_radius, radius),
                (axle_x + arch_radius, clearance),
            ])
        profile.append((front_x, clearance))
        return profile

    @staticmethod
    def _window_rect(x0, x1, z0, z1, chamfer=0.0):
        chamfer = min(chamfer, (x1 - x0) * 0.2, (z1 - z0) * 0.2)
        return [
            (x0 + chamfer, z0), (x1 - chamfer, z0),
            (x1, z0 + chamfer), (x1, z1 - chamfer),
            (x1 - chamfer, z1), (x0 + chamfer, z1),
            (x0, z1 - chamfer), (x0, z0 + chamfer),
        ]

    @staticmethod
    def _material(name, color):
        return (name, color)

    def _get_road_vehicle_vertices_edges_faces(self):
        if self.entity_subtype == 'van':
            return self._get_van_vertices_edges_faces()

        config = VEHICLE_GEOMETRY_DIMENSIONS[self.entity_subtype]
        length, height = config['length'], config['height']
        x_rear, x_front = -length * 0.5, length * 0.5
        clearance = config['clearance']
        half_width = config['half_width']
        wheel_radius = config['wheel_radius']
        axle_positions = [item[1] for item in config['wheel_positions']]
        profile = self._wheel_arch_profile(
            x_rear, x_front, axle_positions, wheel_radius, clearance)

        if self.entity_subtype == 'bus':
            roof_rear, roof_front = x_rear + 0.55, x_front - 0.70
            shoulder_z = height * 0.72
            roof_z = height * 0.97
            profile.extend([
                (x_front, shoulder_z), (x_front - 0.18, height * 0.82),
                (roof_front, roof_z), (roof_rear, roof_z),
                (x_rear, height * 0.92), (x_rear, shoulder_z),
            ])
            glass = self._material('glass', (0.025, 0.11, 0.16, 1.0))
            windows = []
            window_start = x_rear + 0.72
            window_end = x_front - 1.05
            window_count = 6
            gap = 0.16
            pane_width = ((window_end - window_start) - gap * (window_count - 1)) / window_count
            for index in range(window_count):
                x0 = window_start + index * (pane_width + gap)
                windows.append((self._window_rect(
                    x0, x0 + pane_width, height * 0.61, height * 0.86, 0.10), glass))
            windows.append(([
                (x_front - 0.82, height * 0.66),
                (x_front - 0.26, height * 0.76),
                (x_front - 0.48, height * 0.92),
                (x_front - 0.90, height * 0.92),
            ], glass))
        else:
            roof_rear, roof_front = x_rear + length * 0.12, x_front - length * 0.14
            roof_z = height * 0.96
            profile.extend([
                (x_front, height * 0.49),
                (x_front - length * config['nose_ratio'], height * 0.66),
                (roof_front, roof_z), (roof_rear, roof_z),
                (x_rear + length * 0.04, height * 0.88),
                (x_rear, height * 0.68),
            ])
            glass = self._material('glass', (0.025, 0.11, 0.16, 1.0))
            windows = []
            window_ranges = (
                (x_rear + 0.52, x_rear + 1.55),
                (x_rear + 1.70, x_rear + 2.85),
                (x_rear + 3.00, roof_front - 0.18),
            )
            for x0, x1 in window_ranges:
                if x1 > x0 + 0.2:
                    windows.append((self._window_rect(
                        x0, x1, height * 0.61, height * 0.84, 0.10), glass))
            windows.append(([
                (x_front - 0.82, height * 0.57),
                (x_front - 0.32, height * 0.69),
                (roof_front - 0.10, roof_z - 0.12),
                (roof_front - 0.40, roof_z - 0.12),
            ], glass))

        builder = _VehicleMeshBuilder()
        builder.add_shell(profile, half_width, windows)
        body_paint = self._material('body_highlight', (0.18, 0.34, 0.48, 1.0))
        dark_trim = self._material('trim', (0.055, 0.065, 0.075, 1.0))
        roof_paint = self._material('roof', (0.12, 0.22, 0.32, 1.0))

        if self.entity_subtype == 'bus':
            # Keep the bus roof clear; retain only its low bumper rails.
            builder.add_box((0.0, 0.0, clearance + 0.16),
                            (length * 0.91, half_width * 2.08, 0.12), dark_trim)
            for x in (x_rear + 1.0, x_rear + 1.18):
                builder.add_box((x, -half_width - 0.012, height * 0.42),
                                (0.035, 0.025, height * 0.40), dark_trim)
        else:
            # Side sill, sliding-door track, and mirrors give the van a distinct utility body.
            builder.add_box((0.0, 0.0, clearance + 0.16),
                            (length * 0.84, half_width * 2.04, 0.11), dark_trim)
            for side in (-1.0, 1.0):
                builder.add_box((x_rear + 2.8, side * (half_width + 0.015), height * 0.58),
                                (0.035, 0.035, height * 0.42), roof_paint)
                builder.add_box((x_front - 0.38, side * (half_width + 0.12), height * 0.70),
                                (0.20, 0.28, 0.10), dark_trim)

        builder.add_end_lamps(x_front + 0.025, x_rear - 0.025,
                              half_width, height * 0.39, 0.18, 0.16)
        self.face_materials = builder.face_materials
        origin_x = config.get('origin_x', 0.0)
        vertices = [(x - origin_x, y, z) for x, y, z in builder.vertices]
        return vertices, builder.edges, builder.faces

    def _get_van_vertices_edges_faces(self):
        config = VEHICLE_GEOMETRY_DIMENSIONS['van']
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

        # Restrict side glazing to the cab; the rear cargo body is a solid panel.
        pillar_lower = (x_front, height * 0.48)
        pillar_upper = (x_front - 0.88, height * 0.94)
        window_edge_lower_z = height * 0.50
        lower_pillar_fraction = (
            (window_edge_lower_z - pillar_lower[1])
            / (pillar_upper[1] - pillar_lower[1])
        )
        window_edge_lower = (
            pillar_lower[0]
            + lower_pillar_fraction * (pillar_upper[0] - pillar_lower[0])
            - 0.21,
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

        def transverse_window(u0, u1, y0, y1):
            return [(u0, y0), (u1, y0), (u1, y1), (u0, y1)]

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

        builder = _VehicleMeshBuilder()
        builder.add_shell(profile, half_width, side_windows,
                          body_material=body_paint,
                          facet_windows=facet_windows)

        # Mount shortened, backward-angled mirrors low on the A-pillar. The
        # profile and side-window edge define the center of the pillar band.
        mirror_center_z = height * 0.60
        pillar_fraction = (
            (mirror_center_z - pillar_lower[1])
            / (pillar_upper[1] - pillar_lower[1])
        )
        pillar_outer_x = (
            pillar_lower[0]
            + pillar_fraction * (pillar_upper[0] - pillar_lower[0])
        )
        window_fraction = (
            (mirror_center_z - window_edge_lower[1])
            / (window_edge_upper[1] - window_edge_lower[1])
        )
        window_edge_x = (
            window_edge_lower[0]
            + window_fraction * (window_edge_upper[0] - window_edge_lower[0])
        )
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
                / sqrt(mount_backward_offset ** 2 + mount_lateral_offset ** 2)
            )
            mount_backward_offset = 0.03 + projected_radius
        mirror_center_y = (
            mirror_pillar_y + mount_lateral_offset
            + mirror_width_y * 0.5 - mirror_embed_depth
        )
        projected_radius = (
            mirror_stem_radius * mount_lateral_offset
            / sqrt(mount_backward_offset ** 2 + mount_lateral_offset ** 2)
        )
        mirror_front_edge_x = (
            pillar_center_x - mount_backward_offset + projected_radius
        )
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

    def _get_bus_vertices_edges_faces(self):
        config = VEHICLE_GEOMETRY_DIMENSIONS['bus']
        length, height = config['length'], config['height']
        x_rear, x_front = -length * 0.5, length * 0.5
        half_width, clearance = config['half_width'], config['clearance']
        axle_positions = [position[1] for position in config['wheel_positions']]

        profile = self._wheel_arch_profile(
            x_rear, x_front, axle_positions, config['wheel_radius'], clearance)
        # Avoid a zero-area tessellation triangle through the three exactly
        # collinear arch crowns; the 2 mm offsets are visually imperceptible.
        arch_crown_z = config['wheel_radius'] * 2 + 0.10
        for index, axle_x in enumerate(sorted(set(axle_positions))):
            crown_index = profile.index((axle_x, arch_crown_z))
            crown_x, crown_z = profile[crown_index]
            profile[crown_index] = (crown_x, crown_z + (0.002 if index != 1 else -0.002))
        front_facet_index = profile.index((x_front, clearance))
        roof_front = x_front - 0.35
        roof_rear = x_rear + 0.55
        shoulder_z = height * 0.45 - 0.50
        roof_z = height * 0.97
        common_window_top_z = height * 0.87
        windshield_bottom_z = shoulder_z + (roof_z - shoulder_z) * 0.01
        windshield_top_fraction = (
            (common_window_top_z - shoulder_z) / (roof_z - shoulder_z)
        )
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

        # One connected side window extends into a taller front-door section.
        passenger_start = x_rear + 0.72
        door_start = x_front - 2.05
        pillar_x_per_z = (roof_front - x_front) / (roof_z - shoulder_z)
        window_front_edge_lower_x = (
            x_front + pillar_x_per_z * (windshield_bottom_z - shoulder_z) - 0.21
        )
        window_front_edge_upper_x = (
            x_front + pillar_x_per_z * (common_window_top_z - shoulder_z) - 0.21
        )
        side_window = [
            (passenger_start, height * 0.61),
            (door_start, height * 0.61),
            (door_start, windshield_bottom_z),
            (window_front_edge_lower_x, windshield_bottom_z),
            (window_front_edge_upper_x, common_window_top_z),
            (passenger_start, common_window_top_z),
        ]
        side_windows = [(side_window, glass)]

        def transverse_window(u0, u1, y0, y1):
            return [(u0, y0), (u1, y0), (u1, y1), (u0, y1)]

        rear_edge_height = height * 0.92 - clearance
        rear_window_top_fraction = (height * 0.92 - height * 0.87) / rear_edge_height
        rear_window_bottom_fraction = (height * 0.92 - height * 0.61) / rear_edge_height
        # The front windscreen reaches the same height as the tall door pane.
        # The rear pane is lifted to align with the passenger windows.
        facet_windows = {
            front_facet_index: [
                (transverse_window(0.16, 0.31, -0.90, -0.68), headlamp),
                (transverse_window(0.16, 0.31, 0.68, 0.90), headlamp),
                (transverse_window(0.16, 0.31, -1.19, -0.98), indicator),
                (transverse_window(0.16, 0.31, 0.98, 1.19), indicator),
            ],
            windshield_facet: [
                (transverse_window(0.01, windshield_top_fraction,
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

        builder = _VehicleMeshBuilder()
        builder.add_shell(profile, half_width, side_windows,
                          body_material=body_paint,
                          facet_windows=facet_windows)

        # Two large mirrors mounted around the A-pillar midpoint.
        mirror_x = x_front - 0.35
        mirror_z = height * 0.84
        for side in (-1.0, 1.0):
            builder.add_tube((mirror_x, side * half_width * 0.96, mirror_z - 0.02),
                             (mirror_x - 0.03, side * (half_width + 0.25), mirror_z),
                             0.045, dark_trim)
            builder.add_box((mirror_x - 0.03, side * (half_width + 0.32), mirror_z),
                            (0.22, 0.16, 0.16), dark_trim)

        self.face_materials = builder.face_materials
        origin_x = config.get('origin_x', 0.0)
        vertices = [(x - origin_x, y, z) for x, y, z in builder.vertices]
        return vertices, builder.edges, builder.faces

    @staticmethod
    def _get_heavy_truck_fifth_wheel_outline(config, segments=32):
        center_x = config['fifth_wheel_x']
        radius = config['fifth_wheel_radius']
        throat_half_width = radius * 0.38
        angle = asin(throat_half_width / radius)
        lower_angle = pi + angle
        upper_angle = 3 * pi - angle
        arc_segments = max(segments - 2, 8)
        outline = [
            (center_x + radius * cos(lower_angle
                                     + (upper_angle - lower_angle) * index / arc_segments),
             radius * sin(lower_angle
                          + (upper_angle - lower_angle) * index / arc_segments))
            for index in range(arc_segments + 1)
        ]
        # The V throat joins a 2-inch kingpin punch at the plate center.
        throat_apex_x = radius * 0.12
        throat_lip_x = -sqrt(radius ** 2 - throat_half_width ** 2)
        throat_slope = throat_half_width / (throat_apex_x - throat_lip_x)
        cutout_radius = config['fifth_wheel_center_cutout_radius']
        intersection_radicand = (
            (1 + throat_slope ** 2) * cutout_radius ** 2
            - throat_slope ** 2 * throat_apex_x ** 2
        )
        intersection_x = (
            throat_slope ** 2 * throat_apex_x - sqrt(intersection_radicand)
        ) / (1 + throat_slope ** 2)
        intersection_angle = asin(
            throat_slope * (throat_apex_x - intersection_x) / cutout_radius
        )
        cutout_segments = max(16, segments // 2)
        outline.extend((
            (center_x + cutout_radius * cos(intersection_angle
                                             - 2 * intersection_angle * index
                                             / cutout_segments),
             cutout_radius * sin(intersection_angle
                                 - 2 * intersection_angle * index
                                 / cutout_segments))
            for index in range(cutout_segments + 1)
        ))
        return outline

    def _get_heavy_truck_vertices_edges_faces(self):
        config = VEHICLE_GEOMETRY_DIMENSIONS['heavyTruck']
        x_front = config['tractor_front_x']
        half_width, clearance = config['half_width'], config['clearance']
        tractor_rear = config['tractor_rear_x']
        cab_rear = config['cab_rear_x']
        cab_roof = config['cab_roof_z']
        pillar_kink_z = 1.98
        upper_pillar_kink_z = 3.20
        lower_pillar_x_offset = 0.12
        upper_pillar_x_offset = 0.35
        pillar_width = 0.10
        window_bottom_z = 2.10
        window_top_z = 3.10
        deck_z = config['tractor_deck_z']
        wheel_arch_top_z = 2 * config['wheel_radius'] + 0.10
        bed_cut_top_z = wheel_arch_top_z + 0.15
        front_axle_x = next(position[1] for position in config['wheel_positions']
                    if position[0] == 'wheel_fl')
        rear_axle_x = next(position[1] for position in config['wheel_positions']
                   if position[0] == 'wheel_rl')
        rear_fender_radius = config['wheel_radius'] + 0.10
        body_rear_x = rear_axle_x + rear_fender_radius + 0.10
        rear_guard_bottom_z = clearance + 0.02
        rear_guard_top_z = 2 * config['wheel_radius'] + 0.025
        rear_guard_clearance = 0.04
        rear_guard_end_offset = 0.10
        rear_guard_front_x = (rear_axle_x + config['wheel_radius']
                              + rear_guard_clearance)
        rear_guard_rear_x = (rear_axle_x - config['wheel_radius']
                             - rear_guard_clearance)
        side_box_fender_gap = 0.05
        side_box_front_top_x = rear_guard_front_x + side_box_fender_gap
        side_box_front_bottom_x = (rear_guard_front_x + rear_guard_end_offset
                                   + side_box_fender_gap)
        frame_rear_overhang = 0.75
        frame_front_overhang = 0.50
        frame_rear_x = rear_axle_x - frame_rear_overhang
        frame_front_x = front_axle_x + frame_front_overhang
        bed_cutout_x_rear = max(tractor_rear, frame_rear_x) + 0.002
        bed_cutout_x_front = min(x_front, frame_front_x) - 0.002
        bed_deck_cutout_x_rear = body_rear_x + 0.002
        bed_deck_cutout_x_front = cab_rear - 0.002
        window_rear_x = front_axle_x
        body_wheel_arch_positions = [front_axle_x]
        glass = self._material('glass', (0.025, 0.11, 0.16, 1.0))
        headlamp = self._material('headlight', (1.0, 0.78, 0.35, 1.0))
        taillamp = self._material('taillight', (0.78, 0.025, 0.018, 1.0))
        indicator = self._material('indicator', (1.0, 0.22, 0.015, 1.0))
        cab_paint = self._material('cab_paint', (0.15, 0.31, 0.46, 1.0))
        dark_trim = self._material('trim', (0.055, 0.065, 0.075, 1.0))
        builder = _VehicleMeshBuilder()

        profile = self._wheel_arch_profile(
            body_rear_x, x_front, body_wheel_arch_positions,
            config['wheel_radius'], clearance)
        front_facet_index = profile.index((x_front, clearance))
        profile.extend([
            (x_front, pillar_kink_z),
            (x_front - lower_pillar_x_offset, upper_pillar_kink_z),
            (x_front - upper_pillar_x_offset, cab_roof),
            (cab_rear, cab_roof),
            (cab_rear, deck_z),
            (body_rear_x, deck_z),
        ])
        windshield_facet = front_facet_index + 1

        # Actros-style single large driver window follows the sloped A-pillar.
        cab_windows = [(
            [
                (window_rear_x, window_bottom_z),
                (x_front - lower_pillar_x_offset
                 * (window_bottom_z - pillar_kink_z)
                 / (upper_pillar_kink_z - pillar_kink_z) - pillar_width,
                 window_bottom_z),
                (x_front - lower_pillar_x_offset
                 * (window_top_z - pillar_kink_z)
                 / (upper_pillar_kink_z - pillar_kink_z) - pillar_width,
                 window_top_z),
                (window_rear_x, window_top_z),
            ],
            glass,
        )]

        def transverse_window(u0, u1, y0, y1):
            return [(u0, y0), (u1, y0), (u1, y1), (u0, y1)]

        facet_windows = {
            front_facet_index: [
                (transverse_window(0.32, 0.48, -0.91, -0.55), headlamp),
                (transverse_window(0.32, 0.48, 0.55, 0.91), headlamp),
                (transverse_window(0.32, 0.48, -half_width + 0.04, -0.98), indicator),
                (transverse_window(0.32, 0.48, 0.98, half_width - 0.04), indicator),
            ],
            windshield_facet: [
                (transverse_window(
                    (window_bottom_z - pillar_kink_z)
                    / (upper_pillar_kink_z - pillar_kink_z),
                    (window_top_z - pillar_kink_z)
                    / (upper_pillar_kink_z - pillar_kink_z),
                    -half_width + 0.10,
                        half_width - 0.10), glass),
                    ],
        }

        # A box-shaped cut removes the painted bed around the chassis before
        # the frame and fifth wheel are added. The side cuts reach the rail base;
        # the deck cut is wider than both frame rails.
        frame_outer_half_width = 0.50
        frame_rail_width = 0.17
        bed_cutout_half_width = frame_outer_half_width + 0.005
        bed_deck_facet = front_facet_index + 5
        bed_cutout_u_start = ((cab_rear - bed_deck_cutout_x_front)
                      / (cab_rear - body_rear_x))
        bed_cutout_u_end = ((cab_rear - bed_deck_cutout_x_rear)
                    / (cab_rear - body_rear_x))
        bed_deck_cutout = [[
            (bed_cutout_u_start, -bed_cutout_half_width),
            (bed_cutout_u_end, -bed_cutout_half_width),
            (bed_cutout_u_end, bed_cutout_half_width),
            (bed_cutout_u_start, bed_cutout_half_width),
        ]]

        def facet_channel_cutout(index):
            x0, z0 = profile[index]
            x1, z1 = profile[(index + 1) % len(profile)]
            u_min, u_max = 0.0, 1.0
            for value0, value1, lower, upper in (
                (x0, x1, bed_cutout_x_rear, bed_cutout_x_front),
                (z0, z1, clearance, bed_cut_top_z),
            ):
                delta = value1 - value0
                if abs(delta) < 1e-9:
                    if not lower <= value0 <= upper:
                        return None
                    continue
                first = (lower - value0) / delta
                second = (upper - value0) / delta
                u_min = max(u_min, min(first, second))
                u_max = min(u_max, max(first, second))
                if u_min >= u_max:
                    return None

            return [[
                (u_min, -bed_cutout_half_width),
                (u_max, -bed_cutout_half_width),
                (u_max, bed_cutout_half_width),
                (u_min, bed_cutout_half_width),
            ]]

        center_gap_facets = {}
        for index in range(front_facet_index):
            cutout = facet_channel_cutout(index)
            if cutout:
                center_gap_facets[index] = cutout
        center_gap_facets[bed_deck_facet] = bed_deck_cutout
        lower_profile = profile[:front_facet_index + 1]

        def lower_profile_height(x_position):
            for first, second in zip(lower_profile, lower_profile[1:]):
                if first[0] <= x_position <= second[0] and second[0] > first[0]:
                    fraction = ((x_position - first[0])
                                / (second[0] - first[0]))
                    return first[1] + (second[1] - first[1]) * fraction
            raise ValueError(f'Cut x={x_position} is outside the wheelhouse profile')

        side_cutout_profile = [
                        (body_rear_x, lower_profile_height(body_rear_x)),
            *[(x, z) for x, z in lower_profile
                            if body_rear_x < x < bed_cutout_x_front],
            (bed_cutout_x_front, lower_profile_height(bed_cutout_x_front)),
        ]
        bed_side_cutout = [
            (body_rear_x, deck_z - 0.002),
            (cab_rear - 0.002, deck_z - 0.002),
            (cab_rear + 0.002, bed_cut_top_z),
            (bed_cutout_x_front, bed_cut_top_z),
            *[(x, z + 0.002)
              for x, z in reversed(side_cutout_profile)],
        ]
        side_box_profile = list(bed_side_cutout)
        side_box_profile[0] = (side_box_front_top_x, deck_z - 0.002)
        side_box_front_bottom_z = (
            clearance if side_box_front_bottom_x < body_rear_x
            else lower_profile_height(side_box_front_bottom_x)
        )
        side_box_profile[-1] = (
            side_box_front_bottom_x,
            side_box_front_bottom_z + 0.002,
        )

        cab_rear_facet = front_facet_index + 4
        builder.add_shell(profile, half_width, cab_windows,
                          body_material=cab_paint,
                          facet_windows=facet_windows,
                          facet_cutouts=center_gap_facets,
                          open_facets={cab_rear_facet, len(profile) - 1},
                          side_cutouts=[bed_side_cutout])
        builder.add_face((
            (cab_rear, -half_width, bed_cut_top_z),
            (cab_rear, half_width, bed_cut_top_z),
            (cab_rear, half_width, cab_roof),
            (cab_rear, -half_width, cab_roof),
        ), cab_paint)
        for side in (-1.0, 1.0):
            side_y = (side * bed_cutout_half_width,
                      side * half_width)
            builder.add_face((
                (cab_rear, side_y[0], deck_z),
                (cab_rear, side_y[1], deck_z),
                (cab_rear, side_y[1], bed_cut_top_z),
                (cab_rear, side_y[0], bed_cut_top_z),
            ), cab_paint)

        # Build the lower cab/body sections as separate left and right shells.
        # Their inner edges leave a clear channel for the chassis frame.
        side_piece_half_width = (half_width - bed_cutout_half_width) * 0.5
        side_piece_center_y = (half_width + bed_cutout_half_width) * 0.5
        for side in (1.0, -1.0):
            builder.add_shell(
                side_box_profile,
                side_piece_half_width,
                body_material=cab_paint,
                y_center=side * side_piece_center_y,
            )

        # Match the trailer's flat fenders: two sloped end pieces and a
        # horizontal top piece, with no circular wheel-arch profile.
        rear_guard_width = config['rear_wheel_half_width'] * 2 + 0.02
        rear_guard_center_y = config['rear_wheel_center_y']
        flap_rise = rear_guard_top_z - rear_guard_bottom_z
        end_raise = (0.02 * rear_guard_end_offset
                     / sqrt(rear_guard_end_offset ** 2 + flap_rise ** 2))
        rear_guard_centerline = [
            (rear_guard_front_x + rear_guard_end_offset,
             rear_guard_bottom_z + end_raise),
            (rear_guard_front_x, rear_guard_top_z),
            (rear_guard_rear_x, rear_guard_top_z),
            (rear_guard_rear_x - rear_guard_end_offset,
             rear_guard_bottom_z + end_raise),
        ]
        for side in (-1.0, 1.0):
            builder.add_profile_band(
                rear_guard_centerline,
                side * rear_guard_center_y,
                rear_guard_width,
                0.04,
                dark_trim,
            )

        # A thin painted cover closes only the forward hood section; the
        # longer bed channel behind the cab remains open above the frame.
        hood_x_start = cab_rear + 0.002
        hood_x_end = frame_front_x - 0.002
        hood_thickness = 0.04
        builder.add_box(
            ((hood_x_start + hood_x_end) * 0.5, 0.0,
             bed_cut_top_z - hood_thickness * 0.5),
            (hood_x_end - hood_x_start, bed_cutout_half_width * 2,
             hood_thickness),
            cab_paint,
        )


        # Tilt the mirror housing parallel to the lower A-pillar segment.
        # The housing is 800 mm long along the pillar, with its lower end at 2.2 m.
        pillar_dx_dz = -lower_pillar_x_offset / (upper_pillar_kink_z - pillar_kink_z)
        mirror_z = 2.60
        axis_length = sqrt(1.0 + pillar_dx_dz ** 2)
        axis_x, axis_z = pillar_dx_dz / axis_length, 1.0 / axis_length
        normal_x, normal_z = axis_z, -axis_x
        mirror_x = (x_front + pillar_dx_dz * (mirror_z - pillar_kink_z)
                - pillar_width * 0.5 - 0.10 / axis_z)
        mirror_half_height = (0.40 - abs(normal_z) * 0.10) / axis_z
        mirror_outer_y = 1.475
        mirror_depth = 0.16
        mirror_corners = []
        for along, across in ((-mirror_half_height, -0.10),
                      (mirror_half_height, -0.10),
                      (mirror_half_height, 0.10),
                      (-mirror_half_height, 0.10)):
            mirror_corners.append((mirror_x + axis_x * along + normal_x * across,
                                   mirror_z + axis_z * along + normal_z * across))
        mount_height = 0.05
        mount_contact_depth = mirror_depth / 3
        for side in (-1.0, 1.0):
            y_inner = side * (mirror_outer_y - mirror_depth)
            y_outer = side * mirror_outer_y
            y_mount_contact = side * (mirror_outer_y - mirror_depth
                                      + mount_contact_depth)
            mirror_points = [(x, y, z) for y in (y_inner, y_outer)
                             for x, z in mirror_corners]
            for face in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                builder.add_face([mirror_points[index] for index in face], dark_trim)
            # Each support is 50 mm high and reaches only one-third of the
            # mirror depth. Its inner edge aligns with the mirror's top/bottom.
            for corner_index, (along_start, along_end) in (
                    (2, (0.0, mount_height / axis_z)),
                    (3, (-mount_height / axis_z, 0.0))):
                mount_x, mount_z = mirror_corners[corner_index]
                mount_points = []
                for y in (side * half_width, y_mount_contact):
                    for along, across in ((along_start, 0.0),
                                          (along_end, 0.0),
                                          (along_end, -0.05),
                                          (along_start, -0.05)):
                        mount_points.append((
                            mount_x + axis_x * along + normal_x * across,
                            y,
                            mount_z + axis_z * along + normal_z * across,
                        ))
                for face in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                    builder.add_face([mount_points[index] for index in face], dark_trim)

        # The chassis is 1 m wide and supports the fifth wheel on a level deck.
        front_axle_x = next(x for name, x, _y in config['wheel_positions']
                    if name == 'wheel_fl')
        rear_axle_x = next(x for name, x, _y in config['wheel_positions']
                   if name == 'wheel_rl')
        frame_length = frame_front_x - frame_rear_x
        frame_center_x = (frame_front_x + frame_rear_x) * 0.5
        frame_rail_center_y = frame_outer_half_width - frame_rail_width * 0.5
        rail_height = 0.16
        deck_plate_thickness = 0.10
        for side in (-1.0, 1.0):
            builder.add_box(
                (frame_center_x, side * frame_rail_center_y,
                 deck_z - deck_plate_thickness - rail_height * 0.5),
                (frame_length, frame_rail_width, rail_height), dark_trim)
        builder.add_box(
            (frame_center_x, 0.0, deck_z - deck_plate_thickness * 0.5),
            (frame_length, 2 * frame_outer_half_width, deck_plate_thickness), dark_trim)
        frame_inner_half_width = frame_rail_center_y - frame_rail_width * 0.5
        builder.add_box(
            (frame_front_x - 0.01,
             0.0,
             deck_z - deck_plate_thickness - rail_height * 0.5),
            (0.02, frame_inner_half_width * 2, rail_height), dark_trim)

        self.trailer_mesh_data = self._get_heavy_truck_trailer_mesh()
        self.fifth_wheel_mesh_data = self._get_fifth_wheel_mesh()

        origin_x = config['origin_x']
        vertices = [(x - origin_x, y, z) for x, y, z in builder.vertices]
        self.face_materials = builder.face_materials
        return vertices, builder.edges, builder.faces

    def _get_heavy_truck_trailer_mesh(self):
        config = VEHICLE_GEOMETRY_DIMENSIONS['heavyTruck']
        rear_x = config['tractor_front_x'] - config['length']
        front_x = config['trailer_front_x']
        half_width = config['trailer_half_width']
        floor_z = config['trailer_floor_z']
        roof_z = config['trailer_roof_z']
        trailer_paint = self._material('trailer_paint', (0.56, 0.59, 0.61, 1.0))
        trailer_door = self._material('trailer_door', (0.48, 0.51, 0.53, 1.0))
        taillamp = self._material('taillight', (0.78, 0.025, 0.018, 1.0))
        indicator = self._material('indicator', (1.0, 0.22, 0.015, 1.0))
        profile = [
            (rear_x, floor_z),
            (front_x, floor_z),
            (front_x, roof_z),
            (rear_x, roof_z),
        ]

        def rear_region(u0, u1, y0, y1):
            return [(u0, y0), (u1, y0), (u1, y1), (u0, y1)]

        trailer_facet_windows = {
            3: [
                (rear_region(0.03, 0.96, -1.20, -0.025), trailer_door),
                (rear_region(0.03, 0.96, 0.025, 1.20), trailer_door),
            ],
        }
        builder = _VehicleMeshBuilder()
        builder.add_shell(profile, half_width,
                          body_material=trailer_paint,
                          facet_windows=trailer_facet_windows)

        # A lower rear panel connects the trailer body to its underrun crash bar.
        dark_trim = self._material('trailer_trim', (0.055, 0.065, 0.075, 1.0))
        rear_panel_material = self._material('trailer_rear_panel', trailer_door[1])
        bumper_x = rear_x + 0.10
        panel_bottom = 0.622
        panel_height = floor_z - panel_bottom
        crash_bar_front_x = bumper_x + 0.08
        panel_front_face_x = crash_bar_front_x
        panel_rear_face_x = panel_front_face_x - 0.07
        panel_x = (panel_front_face_x + panel_rear_face_x) * 0.5
        builder.add_box((panel_x, 0.0, (floor_z + panel_bottom) * 0.5),
                        (0.07, 2.38, panel_height), rear_panel_material)
        builder.add_box((bumper_x, 0.0, 0.54), (0.16, 2.38, 0.16), dark_trim)

        # Rear lamps are mounted on the new lower panel rather than the trailer body.
        rear_panel_x = panel_rear_face_x - 0.0075
        for side in (-1.0, 1.0):
            builder.add_box((rear_panel_x, side * 0.88, 0.91),
                            (0.015, 0.18, 0.16), taillamp)
            builder.add_box((rear_panel_x, side * 1.09, 0.91),
                            (0.015, 0.12, 0.16), indicator)

        # Side guards attach directly to the trailer body's lower edge.
        side_bar_bottom_z = config['clearance']
        side_bar_top_z = floor_z
        side_bar_height = side_bar_top_z - side_bar_bottom_z
        side_bar_center_z = (side_bar_top_z + side_bar_bottom_z) * 0.5
        for side in (-1.0, 1.0):
            builder.add_box((-2.50, side * (half_width - 0.03), side_bar_center_z),
                            (4.00, 0.06, side_bar_height), dark_trim)

        # Fender strips start at the side-bar rear end and run over the trailer
        # tires. Both drop pieces have matching outward slopes; the front slope
        # shortens the flat fender section at its front-facing end.
        trailer_wheel_x_positions = [
            position[1] for position in config['wheel_positions']
            if position[0].startswith('wheel_t')
        ]
        wheel_clearance = 0.04
        wheel_guard_width = config['trailer_tire_width'] + 0.05
        wheel_guard_thickness = 0.04
        wheel_guard_bottom_z = (2 * config['trailer_wheel_radius']
                    + 0.025)
        mud_flap_half_thickness = wheel_guard_thickness * 0.5
        mud_flap_angle_offset = 0.10
        wheel_guard_front_x = (trailer_wheel_x_positions[0]
                               + config['trailer_wheel_radius']
                               + wheel_clearance)
        wheel_guard_front_lower_x = wheel_guard_front_x + mud_flap_angle_offset
        wheel_guard_rear_x = (trailer_wheel_x_positions[-1]
                              - config['trailer_wheel_radius']
                              - wheel_clearance)
        wheel_guard_rear_lower_x = wheel_guard_rear_x - mud_flap_angle_offset
        wheel_guard_center_z = wheel_guard_bottom_z + mud_flap_half_thickness
        flap_rise = wheel_guard_center_z - side_bar_bottom_z
        end_raise = (mud_flap_half_thickness * mud_flap_angle_offset
                     / sqrt(mud_flap_angle_offset ** 2 + flap_rise ** 2))
        guard_centerline = [
            (wheel_guard_front_lower_x, side_bar_bottom_z + end_raise),
            (wheel_guard_front_x, wheel_guard_center_z),
            (wheel_guard_rear_x, wheel_guard_center_z),
            (wheel_guard_rear_lower_x, side_bar_bottom_z + end_raise),
        ]
        segment_normals = []
        for first, second in zip(guard_centerline, guard_centerline[1:]):
            dx, dz = second[0] - first[0], second[1] - first[1]
            segment_length = sqrt(dx * dx + dz * dz)
            segment_normals.append((-dz / segment_length, dx / segment_length))

        guard_profile_outer = []
        guard_profile_inner = []
        for index, point in enumerate(guard_centerline):
            if index == 0:
                offset_x, offset_z = segment_normals[0]
                scale = mud_flap_half_thickness
            elif index == len(guard_centerline) - 1:
                offset_x, offset_z = segment_normals[-1]
                scale = mud_flap_half_thickness
            else:
                previous_normal = segment_normals[index - 1]
                next_normal = segment_normals[index]
                offset_x = previous_normal[0] + next_normal[0]
                offset_z = previous_normal[1] + next_normal[1]
                offset_length = sqrt(offset_x * offset_x + offset_z * offset_z)
                offset_x /= offset_length
                offset_z /= offset_length
                normal_dot = (offset_x * next_normal[0]
                              + offset_z * next_normal[1])
                scale = mud_flap_half_thickness / normal_dot
            guard_profile_outer.append((point[0] + offset_x * scale,
                                        point[1] + offset_z * scale))
            guard_profile_inner.append((point[0] - offset_x * scale,
                                        point[1] - offset_z * scale))
        guard_profile = guard_profile_outer + list(reversed(guard_profile_inner))
        for side in (-1.0, 1.0):
            y_values = (side * (1.02 - wheel_guard_width * 0.5),
                        side * (1.02 + wheel_guard_width * 0.5))
            guard_vertices = [
                (x, y, z) for y in y_values for x, z in guard_profile
            ]
            profile_count = len(guard_profile)
            builder.add_face(guard_vertices[:profile_count], dark_trim)
            builder.add_face(guard_vertices[profile_count:], dark_trim,
                             reverse=True)
            for index in range(profile_count):
                next_index = (index + 1) % profile_count
                builder.add_face((guard_vertices[index],
                                  guard_vertices[next_index],
                                  guard_vertices[profile_count + next_index],
                                  guard_vertices[profile_count + index]),
                                 dark_trim)
        origin_x = config['origin_x']
        vertices = [(x - origin_x, y, z) for x, y, z in builder.vertices]
        return ('trailer', (vertices, builder.edges, builder.faces,
                    builder.face_materials))

    def _get_fifth_wheel_mesh(self):
        config = VEHICLE_GEOMETRY_DIMENSIONS['heavyTruck']
        outline = self._get_heavy_truck_fifth_wheel_outline(config)
        segments = len(outline)
        z_bottom = config['fifth_wheel_bottom_z']
        z_top = config['trailer_floor_z']
        vertices = []
        for z in (z_bottom, z_top):
            vertices.extend((x, y, z) for x, y in outline)
        faces = []
        for index in range(segments):
            next_index = (index + 1) % segments
            faces.append([index, next_index, segments + next_index,
                          segments + index])
        faces.append(list(range(segments - 1, -1, -1)))
        faces.append(list(range(segments, 2 * segments)))
        material = self._material('fifth_wheel', (0.16, 0.17, 0.18, 1.0))
        origin_x = config['origin_x']
        vertices = [(x - origin_x, y, z) for x, y, z in vertices]
        return ('fifth_wheel', (vertices, [], faces,
                                [material] * len(faces)))

    def _get_two_wheeler_vertices_edges_faces(self):
        builder = _VehicleMeshBuilder()
        frame = self._material('frame', (0.12, 0.20, 0.26, 1.0))
        metal = self._material('metal', (0.38, 0.42, 0.45, 1.0))
        rubber = self._material('rubber', (0.055, 0.065, 0.075, 1.0))
        paint = self._material('body_highlight', (0.18, 0.34, 0.48, 1.0))

        if self.entity_subtype == 'bicycle':
            bicycle_config = VEHICLE_GEOMETRY_DIMENSIONS['bicycle']
            wheel_radius = bicycle_config['wheel_radius']
            rear = (bicycle_config['wheel_positions'][1][1], 0.0, wheel_radius)
            front = (bicycle_config['wheel_positions'][0][1], 0.0, wheel_radius)
            crank = (-0.197058823529, 0.0, 0.34)
            seat = (-0.31, 0.0, 0.82)
            head = (0.22, 0.0, 0.86)
            fork_top = (0.28, 0.0, 0.73)
            for a, b, radius in (
                (rear, seat, 0.035), (rear, crank, 0.035),
                (crank, seat, 0.035), (seat, head, 0.035),
                (head, crank, 0.035), (head, fork_top, 0.040),
                (fork_top, front, 0.030),
            ):
                builder.add_tube(a, b, radius, frame)
            builder.add_tube((seat[0], 0.0, seat[2]),
                             (seat[0] - 0.0247058823529, 0.0, 0.925),
                             0.024, metal)
            builder.add_box((seat[0] - 0.03, 0.0, 0.94), (0.26, 0.16, 0.055), rubber)
            stem_end = (0.295, 0.0, 0.95)
            handlebar_x, handlebar_z = 0.275, 0.95
            builder.add_tube(head, stem_end, 0.028, metal)
            builder.add_tube((handlebar_x, -0.29, handlebar_z),
                             (handlebar_x, 0.29, handlebar_z), 0.022, metal)
            pedal_positions = {}
            for side, crank_dx, crank_dz in (
                (1.0, 0.13, -0.12), (-1.0, -0.13, 0.12),
            ):
                pedal = (crank[0] + crank_dx, side * 0.16,
                         crank[2] + crank_dz)
                pedal_positions[side] = pedal
                builder.add_tube((crank[0], side * 0.035, crank[2]),
                                 (pedal[0], side * 0.08, pedal[2]),
                                 0.025, metal, cap_start=False)
                builder.add_box(pedal, (0.14, 0.14, 0.04), rubber)
        else:
            wheel_radius = VEHICLE_GEOMETRY_DIMENSIONS['motorcycle']['wheel_radius']
            rear = (-0.73, 0.0, wheel_radius)
            front = (0.73, 0.0, wheel_radius)
            swing = (-0.10, 0.0, 0.42)
            rear_split = (-0.32, 0.0, 0.3885714285714)
            builder.add_tube(swing, rear_split, 0.025, frame, roll=0.0,
                             height_scale=2.0)
            for side in (-1.0, 1.0):
                builder.add_tube(
                    (rear[0], side * 0.13, rear[2]),
                    (rear_split[0], side * 0.13, rear_split[2]),
                    0.025, frame, roll=0.0, height_scale=2.0)
            builder.add_tube((rear[0], -0.16, rear[2]),
                             (rear[0], 0.16, rear[2]), 0.025, metal)
            rear_fork_angle = atan2(rear_split[2] - rear[2],
                                    rear_split[0] - rear[0])
            rear_splitter_roll = pi / 2 - rear_fork_angle
            builder.add_tube((rear_split[0], -0.155, rear_split[2]),
                             (rear_split[0], 0.155, rear_split[2]),
                             0.025, frame, roll=rear_splitter_roll,
                             height_scale=2.0)
            tank_front = (0.43, 0.0, 0.90)
            front_fork_start = (0.4510526315789, 0.0, 0.86)
            front_split = (0.5163157894737, 0.0, 0.736)
            builder.add_tube(front_fork_start, front_split, 0.035, metal)
            for side in (-1.0, 1.0):
                builder.add_tube(
                    (front_split[0], side * 0.095, front_split[2]),
                    (front[0], side * 0.095, front[2]), 0.025, metal)
            front_fork_angle = atan2(front[2] - front_split[2],
                                     front[0] - front_split[0])
            front_splitter_roll = pi / 2 - front_fork_angle
            builder.add_tube((front[0], -0.12, front[2]),
                             (front[0], 0.12, front[2]), 0.025, metal,
                             roll=front_splitter_roll)
            builder.add_tube((front_split[0], -0.125, front_split[2]),
                             (front_split[0], 0.125, front_split[2]),
                             0.018, metal, roll=front_splitter_roll,
                             height_scale=2.0)
            stem_end = (0.3352631578947, 0.0, 1.08)
            builder.add_tube(tank_front, stem_end, 0.035, metal)
            builder.add_tube((stem_end[0], -0.39, stem_end[2]),
                             (stem_end[0], 0.39, stem_end[2]), 0.026, metal)
            saddle_profile = [
                (-0.73, 0.71), (-0.73, 0.79), (-0.18, 0.79),
                (0.24, 0.79), (0.18, 0.71),
            ]
            builder.add_prism(saddle_profile, 0.13, rubber)
            engine_profile = [
                (-0.24, 0.34), (0.12, 0.34),
                (0.18, 0.71), (-0.12, 0.71),
            ]
            builder.add_prism(engine_profile, 0.13, metal)
            tank_profile = [
                (-0.18, 0.79), (-0.02, 0.98), (0.30, 1.03),
                (0.43, 0.90), (0.24, 0.79),
            ]
            builder.add_prism(tank_profile, 0.17, paint)
            # The tank and engine meet directly; the steering bridge is the headlight housing.
            headlight_material = self._material(
                'headlight', (1.0, 0.78, 0.35, 1.0))
            builder.add_lamp_housing_x(
                (0.435, 0.0, 0.91), (0.14, 0.25, 0.10), (0.23, 0.08),
                1.0, frame, headlight_material)
            taillight_material = self._material(
                'taillight', (0.78, 0.025, 0.018, 1.0))
            builder.add_lamp_housing_x(
                (-0.7675, 0.0, 0.75), (0.075, 0.24, 0.12), (0.21, 0.09),
                -1.0, frame, taillight_material)
            indicator = self._material('indicator', (1.0, 0.28, 0.025, 1.0))
            for x, z, lateral_offset, size in (
                (0.47, 0.91, 0.155, (0.07, 0.06, 0.07)),
                (-0.77, 0.75, 0.15, (0.07, 0.06, 0.07)),
            ):
                for side in (-1.0, 1.0):
                    builder.add_box((x, side * lateral_offset, z),
                                    size, indicator)
            for side in (-1.0, 1.0):
                builder.add_tube((0.085, side * 0.12, 0.40),
                                 (0.085, side * 0.27, 0.40), 0.025, metal,
                                 roll=-side * pi / 18, height_scale=2.5)

        self._add_two_wheeler_rider(builder)
        self.face_materials = builder.face_materials
        origin_x = VEHICLE_GEOMETRY_DIMENSIONS[self.entity_subtype]['origin_x']
        vertices = [(x - origin_x, y, z) for x, y, z in builder.vertices]
        return vertices, builder.edges, builder.faces

    def _add_two_wheeler_rider(self, builder):
        """Add a simple seated rider using the pedestrian's low-poly body-part style."""
        skin = self._material('rider_skin', (0.72, 0.48, 0.32, 1.0))
        clothing = self._material('rider_clothing', (0.12, 0.24, 0.42, 1.0))
        trousers = self._material('rider_trousers', (0.08, 0.10, 0.14, 1.0))
        shoes = self._material('rider_shoes', (0.035, 0.04, 0.05, 1.0))
        helmet = self._material('rider_helmet', (1.0, 1.0, 1.0, 1.0))
        visor = self._material('rider_visor', (0.025, 0.11, 0.16, 1.0))
        hair = self._material('rider_hair', (0.075, 0.038, 0.022, 1.0))
        eyes = self._material('rider_eyes', (0.018, 0.012, 0.008, 1.0))

        if self.entity_subtype == 'bicycle':
            hip_x, hip_z = -0.31, 1.05
            shoulder_x, shoulder_z = -0.015, 1.26
            head_x, head_z = 0.015, 1.46
            elbow_x, elbow_z = 0.10, 1.12
            hand_x, hand_z = 0.275, 0.95
            knee_x, knee_z = -0.015, 0.70
            foot_x, foot_z = -0.04, 0.39
        else:
            hip_x, hip_z = -0.38, 0.86
            shoulder_x, shoulder_z = -0.08, 1.22
            head_x, head_z = -0.06, 1.48
            elbow_x, elbow_z = 0.065, 1.165
            hand_x, hand_z = 0.3352631578947, 1.08
            knee_x, knee_z = 0.0, 0.75
            foot_x, foot_z = 0.12, 0.46

        # Seated hips and a forward-leaning torso.
        torso_profile = [
            (hip_x - 0.13, hip_z - 0.08),
            (hip_x + 0.14, hip_z - 0.08),
            (shoulder_x + 0.10, shoulder_z + 0.03),
            (shoulder_x - 0.09, shoulder_z + 0.03),
        ]
        builder.add_prism(torso_profile, 0.17, clothing)

        # Short neck and head; only the motorcycle rider wears a helmet.
        builder.add_tube((shoulder_x - 0.015, 0.0, shoulder_z),
                         (head_x, 0.0, head_z - 0.06), 0.052, skin)
        if self.entity_subtype == 'bicycle':
            builder.add_box((head_x, 0.0, head_z),
                            (0.19, 0.19, 0.23), skin)
            builder.add_box((head_x, 0.0, head_z + 0.09),
                            (0.23, 0.23, 0.075), hair)
            for side in (-1.0, 1.0):
                builder.add_box((head_x + 0.101, side * 0.04,
                                 head_z + 0.025),
                                (0.012, 0.026, 0.018), eyes)
        else:
            builder.add_box((head_x - 0.015, 0.0, head_z + 0.01),
                    (0.23, 0.22, 0.24), helmet)
            builder.add_box((head_x + 0.095, 0.0, head_z + 0.005),
                    (0.035, 0.16, 0.09), visor)

        # Bent arms reach the handlebars; both legs fold down to pedals/foot pegs.
        for side in (-1.0, 1.0):
            shoulder = (shoulder_x, side * 0.15, shoulder_z - 0.015)
            hand_y = 0.27 if self.entity_subtype == 'bicycle' else 0.36
            elbow_y = 0.32 if self.entity_subtype == 'bicycle' else 0.38
            elbow = (elbow_x, side * elbow_y, elbow_z)
            hand = (hand_x, side * hand_y, hand_z)
            arm_cross_section_roll = pi / 4
            builder.add_tube(shoulder, elbow, 0.052, clothing,
                             roll=arm_cross_section_roll)
            arm_dx = hand[0] - elbow[0]
            arm_dy = hand[1] - elbow[1]
            arm_dz = hand[2] - elbow[2]
            arm_length = sqrt(arm_dx * arm_dx + arm_dy * arm_dy
                              + arm_dz * arm_dz)
            elbow_overlap = 0.018
            arm_direction = (arm_dx / arm_length,
                             arm_dy / arm_length,
                             arm_dz / arm_length)
            lower_arm_start = (
                elbow[0] - arm_direction[0] * elbow_overlap,
                elbow[1] - arm_direction[1] * elbow_overlap,
                elbow[2] - arm_direction[2] * elbow_overlap,
            )
            hand_size = (0.11, 0.09, 0.075)
            hand_surface_distance = sum(
                size * 0.5 * abs(direction)
                for size, direction in zip(hand_size, arm_direction)
            )
            wrist_embed = 0.012
            wrist = tuple(
                hand[index] - arm_direction[index]
                * (hand_surface_distance - wrist_embed)
                for index in range(3)
            )
            builder.add_tube(lower_arm_start, wrist, 0.043, clothing,
                             roll=arm_cross_section_roll)
            hand_rotation = atan2(-arm_dz, arm_dx) * 0.12
            if self.entity_subtype == 'bicycle':
                hand_rotation += pi / 9
            builder.add_box(hand, hand_size, skin,
                            rotation_y=hand_rotation)

            hip = (hip_x, side * 0.12, hip_z - 0.03)
            knee = (knee_x, side * 0.19, knee_z)
            if self.entity_subtype == 'bicycle':
                pedal_x = -0.197058823529 + side * 0.13
                pedal_z = 0.34 - side * 0.12
                foot_x = pedal_x + 0.015
                foot_z = pedal_z + 0.055
                knee = ((-0.04, side * 0.19, 0.65) if side > 0.0
                    else (-0.15, side * 0.19, 0.75))
            foot_side_y = 0.21 if self.entity_subtype == 'motorcycle' else 0.16
            ankle = (foot_x - 0.08, side * foot_side_y, foot_z)
            thigh_end = (hip[0] + (knee[0] - hip[0]) * 0.04,
                         hip[1] + (knee[1] - hip[1]) * 0.04,
                         hip[2] + (knee[2] - hip[2]) * 0.04)
            builder.add_tube(thigh_end, knee, 0.075, trousers,
                             roll=pi / 4)
            builder.add_tube(knee, ankle, 0.052, trousers,
                             roll=pi / 4)
            builder.add_box((foot_x - 0.035, side * foot_side_y, foot_z - 0.0125),
                            (0.22, 0.12, 0.045), shoes,
                            rotation_y=(-pi / 18
                                        if self.entity_subtype == 'motorcycle'
                                        else 0.0))

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

    def _build_bicycle_wheel_mesh(self, radius, half_width, segments):
        """Build an open bicycle wheel with a tire, rim, spokes, hub, and axle."""
        builder = _VehicleMeshBuilder()
        tire_inner_radius = radius - 0.035
        rim_outer_radius = radius - 0.045
        rim_inner_radius = radius - 0.052
        rim_half_width = 0.006
        hub_radius = 0.03
        tire_rings = {}
        for name, ring_radius, y in (
            ('outer_minus', radius, -half_width),
            ('outer_plus', radius, half_width),
            ('inner_minus', tire_inner_radius, -half_width),
            ('inner_plus', tire_inner_radius, half_width),
        ):
            tire_rings[name] = [
                (ring_radius * cos(2 * pi * index / segments), y,
                 ring_radius * sin(2 * pi * index / segments))
                for index in range(segments)
            ]

        for index in range(segments):
            following = (index + 1) % segments
            outer_minus = tire_rings['outer_minus']
            outer_plus = tire_rings['outer_plus']
            inner_minus = tire_rings['inner_minus']
            inner_plus = tire_rings['inner_plus']
            builder.add_face((outer_minus[index], outer_minus[following],
                              outer_plus[following], outer_plus[index]))
            builder.add_face((inner_minus[following], inner_minus[index],
                              inner_plus[index], inner_plus[following]))
            builder.add_face((outer_plus[index], outer_plus[following],
                              inner_plus[following], inner_plus[index]))
            builder.add_face((outer_minus[following], outer_minus[index],
                              inner_minus[index], inner_minus[following]))

        rim_rings = {}
        for name, ring_radius, y in (
            ('outer_minus', rim_outer_radius, -rim_half_width),
            ('outer_plus', rim_outer_radius, rim_half_width),
            ('inner_minus', rim_inner_radius, -rim_half_width),
            ('inner_plus', rim_inner_radius, rim_half_width),
        ):
            rim_rings[name] = [
                (ring_radius * cos(2 * pi * index / segments), y,
                 ring_radius * sin(2 * pi * index / segments))
                for index in range(segments)
            ]
        for index in range(segments):
            following = (index + 1) % segments
            outer_minus = rim_rings['outer_minus']
            outer_plus = rim_rings['outer_plus']
            inner_minus = rim_rings['inner_minus']
            inner_plus = rim_rings['inner_plus']
            builder.add_face((outer_minus[index], outer_minus[following],
                              outer_plus[following], outer_plus[index]))
            builder.add_face((inner_minus[following], inner_minus[index],
                              inner_plus[index], inner_plus[following]))
            builder.add_face((outer_plus[index], outer_plus[following],
                              inner_plus[following], inner_plus[index]))
            builder.add_face((outer_minus[following], outer_minus[index],
                              inner_minus[index], inner_minus[following]))

        def add_y_cylinder(cylinder_radius, half_length, cylinder_segments):
            rings = []
            for y in (-half_length, half_length):
                rings.append([
                    (cylinder_radius * cos(2 * pi * index / cylinder_segments),
                     y,
                     cylinder_radius * sin(2 * pi * index / cylinder_segments))
                    for index in range(cylinder_segments)
                ])
            for index in range(cylinder_segments):
                following = (index + 1) % cylinder_segments
                builder.add_face((rings[0][index], rings[0][following],
                                  rings[1][following], rings[1][index]))
            builder.add_face(rings[0], reverse=True)
            builder.add_face(rings[1])

        axle_half_length = half_width + 0.035
        hub_half_length = max(half_width * 1.25, 0.025)
        add_y_cylinder(0.008, axle_half_length, 12)
        add_y_cylinder(hub_radius, hub_half_length, 16)
        spoke_end_radius = rim_outer_radius - 0.002
        for index in range(16):
            angle = 2 * pi * index / 16
            spoke_start = (hub_radius * 0.85 * cos(angle), 0.0,
                           hub_radius * 0.85 * sin(angle))
            spoke_end = (spoke_end_radius * cos(angle), 0.0,
                         spoke_end_radius * sin(angle))
            builder.add_tube(spoke_start, spoke_end, 0.0025, None)

        return builder.vertices, builder.edges, builder.faces

    def get_vertices_edges_faces(self):
        if self.entity_subtype == 'car':
            return self._get_car_vertices_edges_faces()
        return self._get_non_car_vertices_edges_faces()

    def get_face_materials(self):
        return getattr(self, 'face_materials', [])

    def get_additional_meshes(self):
        """Return independently authored mesh children for composite vehicles."""
        if self.entity_subtype == 'heavyTruck':
            component = getattr(self, 'trailer_mesh_data', None)
            fifth_wheel = getattr(self, 'fifth_wheel_mesh_data', None)
            return [item for item in (component, fifth_wheel) if item]
        return []

    def setup_entity_object(self, context, obj):
        if self.entity_subtype != 'car':
            return
        data = bpy.data.lattices.new('Car_RoofLattice')
        data.points_u, data.points_v, data.points_w = 2, 2, 4
        data.interpolation_type_u = 'KEY_BSPLINE'
        data.interpolation_type_v = 'KEY_BSPLINE'
        data.interpolation_type_w = 'KEY_BSPLINE'
        cage = bpy.data.objects.new('Car_RoofLattice', data)
        helpers.link_object_openscenario(context, cage, subcategory='entities')
        cage.parent = obj
        cage.location = (1.5, 0.0, 0.95)
        cage.scale = (4.8, 2.4, 2.0 / 3.0)
        layer_scale = (1.0, 1.0, 0.98, 0.60)
        points_per_layer = data.points_u * data.points_v
        for index, point in enumerate(data.points):
            point.co_deform = (point.co_deform.x,
                               point.co_deform.y * layer_scale[index // points_per_layer],
                               point.co_deform.z)
        cage.hide_render = True
        cage.hide_set(True)
        modifier = obj.modifiers.new('Roof_Lattice', 'LATTICE')
        modifier.object = cage

    def get_wheel_configs(self):
        if self.entity_subtype == 'car':
            r = self.wheel_radius
            hw = self.wheel_half_width
            n = self.wheel_segments
            verts = []
            for y in (-hw, hw):
                verts.extend((r * cos(2 * pi * i / n), y,
                              r * sin(2 * pi * i / n)) for i in range(n))
            faces = []
            for i in range(n):
                ni = (i + 1) % n
                faces.append([i, ni, n + ni, n + i])
            faces.extend([list(range(n)), list(range(2 * n - 1, n - 1, -1))])
            positions = [
                ('wheel_fl', self.wheel_x_front + self.origin_offset_x,
                 self.wheel_y_half_track),
                ('wheel_fr', self.wheel_x_front + self.origin_offset_x,
                 -self.wheel_y_half_track),
                ('wheel_rl', self.wheel_x_rear + self.origin_offset_x,
                 self.wheel_y_half_track),
                ('wheel_rr', self.wheel_x_rear + self.origin_offset_x,
                 -self.wheel_y_half_track),
            ]
            return [(name, (x, y, r), verts, [], faces)
                    for name, x, y in positions]

        config = VEHICLE_GEOMETRY_DIMENSIONS[self.entity_subtype]
        wheel_radius = config['wheel_radius']
        wheel_half_width = config['wheel_half_width']
        wheel_segments = config['wheel_segments']
        wheel_positions = config['wheel_positions']

        if self.entity_subtype == 'bicycle':
            return [
                (name,
                 (x_pos - config.get('origin_x', 0.0), y_pos, wheel_radius),
                 *self._build_bicycle_wheel_mesh(
                     wheel_radius, wheel_half_width, max(wheel_segments, 32)))
                for name, x_pos, y_pos in wheel_positions
            ]

        mesh_by_dimensions = {}
        wheel_configs = []
        for name, x_pos, y_pos in wheel_positions:
            x_pos -= config.get('origin_x', 0.0)
            is_trailer_wheel = name.startswith('wheel_t')
            radius = (config.get('trailer_wheel_radius', wheel_radius)
                      if is_trailer_wheel else wheel_radius)
            if is_trailer_wheel:
                half_width = config.get('trailer_wheel_half_width', wheel_half_width)
            elif name in {'wheel_rl', 'wheel_rr', 'wheel_r'}:
                half_width = config.get('rear_wheel_half_width', wheel_half_width)
            elif name in {'wheel_fl', 'wheel_fr', 'wheel_f'}:
                half_width = config.get('front_wheel_half_width', wheel_half_width)
            else:
                half_width = wheel_half_width
            dimensions = (radius, half_width)
            if dimensions not in mesh_by_dimensions:
                mesh_by_dimensions[dimensions] = self._build_wheel_mesh(
                    radius, half_width, wheel_segments)
            verts, edges, faces = mesh_by_dimensions[dimensions]
            wheel_configs.append(
                (name, (x_pos, y_pos, radius), verts, edges, faces))

        return wheel_configs
