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
from mathutils import Vector, Matrix

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
    # Wheel center positions relative to entity origin (x_front, x_rear, y_half_track)
    wheel_x_front = 1.5
    wheel_x_rear = -1.4
    wheel_y_half_track = 0.8775  # outer edge 10 mm inside body (y=1.0)

    def get_vertices_edges_faces(self):
        # Body raised slightly for ground clearance above the wheels
        clearance = 0.15    # body bottom z

        # Wheel arch parameters
        arch_clearance = 0.05
        arch_r = self.wheel_radius + arch_clearance
        wz = self.wheel_radius  # wheel center z (bottom of wheel at z=0)
        xf = self.wheel_x_front
        xr = self.wheel_x_rear

        # Compute arch points: 5 per arch (2 landings + 3 intermediate)
        # Angles go clockwise from left landing over top to right landing
        arch_angles_deg = [210, 135, 90, 45, 330]

        def make_arch_xz(wx):
            pts = []
            for deg in arch_angles_deg:
                a = deg * pi / 180
                pts.append((wx + arch_r * cos(a), wz + arch_r * sin(a)))
            return pts

        rear_arch = make_arch_xz(xr)
        front_arch = make_arch_xz(xf)

        # Build side profile (x, z) going CCW when viewed from left
        y_l = -1.0
        y_r = 1.0

        profile_xz = [
            (-2.20, 0.05 + clearance),                      # 0: bottom rear corner
        ]
        profile_xz += rear_arch               # 1-5: rear wheel arch
        profile_xz += front_arch              # 6-10: front wheel arch
        profile_xz += [
            ( 2.20, 0.01 + clearance),                      # 11: bottom front corner
            ( 2.20, 0.50 + clearance),        # 12: front lower
            ( 1.90, 0.80 + clearance),        # 13: front upper
            ( 1.10, 0.85 + clearance),        # 14: windshield
            ( 0.10, 1.60 + clearance),        # 15: roof
            (-1.60, 1.58 + clearance),        # 16: roof rear
            (-2.20, 0.80 + clearance),        # 17: rear upper
        ]

        n = len(profile_xz)  # 18

        # Vertices: left side then right side
        vertices = [(x, y_l, z) for (x, z) in profile_xz] + \
                   [(x, y_r, z) for (x, z) in profile_xz]

        # Edges: profile outlines + connecting edges between sides
        edges = []
        for i in range(n):
            ni = (i + 1) % n
            edges.append([i, ni])              # left profile
            edges.append([i + n, ni + n])      # right profile
            edges.append([i, i + n])           # connecting

        # Faces
        left_face = list(range(n))
        right_face = list(range(2 * n - 1, n - 1, -1))
        faces = [left_face, right_face]
        for i in range(n):
            j = (i + 1) % n
            faces.append([j, i, i + n, j + n])

        return vertices, edges, faces

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
            ('wheel_fl', (xf,  yt, z_center), verts, edges, faces),
            ('wheel_fr', (xf, -yt, z_center), verts, edges, faces),
            ('wheel_rl', (xr,  yt, z_center), verts, edges, faces),
            ('wheel_rr', (xr, -yt, z_center), verts, edges, faces),
        ]
        return configs