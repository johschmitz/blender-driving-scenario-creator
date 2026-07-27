"""Backward-compatible import for the generalized vehicle operator."""

from .entity_vehicle import DSC_OT_entity_vehicle


DSC_OT_entity_car = DSC_OT_entity_vehicle# This program is free software; you can redistribute it and/or modify
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
from mathutils import Vector, Matrix, geometry

from math import pi, cos, sin

from . entity_base import DSC_OT_entity
from . import helpers


class DSC_OT_entity_car(DSC_OT_entity):
    bl_idname = 'dsc.entity_car'
    bl_label = 'Car'
    bl_description = 'Place a car entity object'
    bl_options = {'REGISTER', 'UNDO'}

    entity_type = 'vehicle'
    entity_subtype = 'car'

    # Wheel parameters
    wheel_radius = 0.35
    wheel_half_width = 0.1125  # 225 mm total width
    wheel_segments = 12
    # Wheel center positions in the centered model coordinates.
    wheel_x_front = 1.5
    wheel_x_rear = -1.4
    wheel_y_half_track = 0.8775  # outer edge 10 mm inside body (y=1.0)
    # Local origin is on the ground directly below the rear axle center.
    origin_offset_x = -wheel_x_rear

    def get_vertices_edges_faces(self):
        # Authored LowPolyCar silhouette and smoothed twelve-vertex wheel arches.
        profile_xz = [
            (-2.20, 0.18), (-1.827, 0.18),
            (-1.827, 0.35), (-1.725, 0.675), (-1.40, 0.81),
            (-1.075, 0.675), (-0.973, 0.35), (-0.973, 0.18),
            (1.073, 0.18), (1.073, 0.35), (1.175, 0.675),
            (1.50, 0.81), (1.825, 0.675), (1.927, 0.35),
            (1.927, 0.18), (2.20, 0.18), (2.20, 0.66),
            (1.90, 1.0), (0.95, 1.72), (-0.65, 1.72),
            (-1.30, 1.10), (-2.20, 0.80),
        ]
        for indices, wheel_x in ((range(2, 7), self.wheel_x_rear),
                                 (range(9, 14), self.wheel_x_front)):
            for index in indices:
                x, z = profile_xz[index]
                dx, dz = x - wheel_x, z - self.wheel_radius
                radius = (dx * dx + dz * dz) ** 0.5
                target_radius = self.wheel_radius + (radius - self.wheel_radius) * 0.65
                if radius > 1e-8:
                    profile_xz[index] = (
                        wheel_x + dx * target_radius / radius,
                        self.wheel_radius + dz * target_radius / radius)
        glass = ('glass', (0.025, 0.11, 0.16, 1.0))
        headlamp = ('headlight', (1.0, 0.78, 0.35, 1.0))
        taillamp = ('taillight', (0.78, 0.025, 0.018, 1.0))
        indicator = ('indicator', (1.0, 0.22, 0.015, 1.0))
        side_windows = [
            [(x, z) for x, z in (
                (0.16, 1.12), (0.16, 1.56), (0.82, 1.56),
                (1.30, 1.146), (1.30, 1.12))],
            [(x, z) for x, z in (
                (0.0, 1.12), (0.0, 1.56), (-0.62, 1.56),
                (-1.0, 1.18), (-1.0, 1.12))],
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

        # Cut four window regions into each side face; the glass faces share
        # their boundary vertices and edges with the surrounding body faces.
        for side, reverse in ((-1.0, False), (1.0, True)):
            cut_surface([profile_xz] + side_windows,
                        lambda x, z: (x, side, z), [glass, glass], reverse)

        def rectangle(u0, u1, v0, v1):
            return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

        # Windshields and fascia lamps use the authored cutter proportions,
        # cut directly into the corresponding profile-extrusion faces.
        n = len(profile_xz)
        for i, (x0, z0) in enumerate(profile_xz):
            j = (i + 1) % n
            x1, z1 = profile_xz[j]
            holes, materials = [], []
            if i in (17, 19):
                # Edge parameter runs front-to-roof on one rake and roof-to-
                # rear on the other; trim the glazing inside its painted frame.
                holes.append(rectangle(0.14, 0.86, -0.88, 0.88))
                materials.append(glass)
            if i in (15, 21):
                front = i == 21
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

        # Match LowPolyCar's authored reflection. Its rear axle is at source
        # X=1.5, so this maps that axle to the entity origin while keeping the
        # vehicle front on +X to agree with the wheel configuration.
        vertices = [(-x + 1.5, y, z) for x, y, z in vertices]
        faces = [list(reversed(face)) for face in faces]
        self.face_materials = face_materials
        return vertices, edges, faces

    def get_face_materials(self):
        return self.face_materials

    def setup_entity_object(self, context, obj):
        """Narrow the roof and glass with one reusable lattice cage."""
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
        '''
            Return wheel definitions for esmini-compatible export.
            Each entry: (name, local_position_xyz, vertices, edges, faces).
            Wheel names follow the esmini convention: wheel_fl, wheel_fr, wheel_rl, wheel_rr.
        '''
        r = self.wheel_radius
        hw = self.wheel_half_width
        n = self.wheel_segments
        xf = self.wheel_x_front
        xr = self.wheel_x_rear
        yt = self.wheel_y_half_track

        # Generate cylinder mesh (axis along Y)
        verts = []
        for i in range(n):
            angle = 2 * pi * i / n
            vx = r * cos(angle)
            vz = r * sin(angle)
            verts.append((vx, -hw, vz))
        for i in range(n):
            angle = 2 * pi * i / n
            vx = r * cos(angle)
            vz = r * sin(angle)
            verts.append((vx, hw, vz))

        faces = []
        # Side quads
        for i in range(n):
            ni = (i + 1) % n
            faces.append([i, ni, n + ni, n + i])
        # Cap faces
        faces.append(list(range(n)))
        faces.append(list(range(2 * n - 1, n - 1, -1)))

        edges = []

        z_center = r  # wheel center at radius height (bottom touches ground)
        configs = [
            ('wheel_fl',
             (xf + self.origin_offset_x,  yt, z_center), verts, edges, faces),
            ('wheel_fr',
             (xf + self.origin_offset_x, -yt, z_center), verts, edges, faces),
            ('wheel_rl',
             (xr + self.origin_offset_x,  yt, z_center), verts, edges, faces),
            ('wheel_rr',
             (xr + self.origin_offset_x, -yt, z_center), verts, edges, faces),
        ]
        return configs