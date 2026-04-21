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

from math import pi

from . entity_base import DSC_OT_entity
from . import helpers


class DSC_OT_entity_pedestrian(DSC_OT_entity):
    bl_idname = 'dsc.entity_pedestrian'
    bl_label = 'Pedestrian'
    bl_description = 'Place a pedestrian entity object'
    bl_options = {'REGISTER', 'UNDO'}

    entity_type = 'pedestrian'
    # There are multiple types of pedestrians, this is the default one
    entity_subtype = 'pedestrian'

    def get_vertices_edges_faces(self):
        '''Build a recognisable low-poly human figure.

        Body parts (all separate box / tapered-box primitives):
            head, neck, shoulders, torso, pelvis,
            left leg, right leg, left arm, right arm.
        Person faces the +X direction.
        '''
        verts = []
        edges = []
        faces = []

        def _box(x0, x1, y0, y1, z0, z1):
            '''Axis-aligned box.'''
            b = len(verts)
            verts.extend([
                (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
            ])
            faces.extend([
                (b+0, b+1, b+5, b+4),
                (b+1, b+2, b+6, b+5),
                (b+2, b+3, b+7, b+6),
                (b+3, b+0, b+4, b+7),
                (b+4, b+5, b+6, b+7),
                (b+3, b+2, b+1, b+0),
            ])

        def _tbox(x0b, x1b, y0b, y1b, z0, x0t, x1t, y0t, y1t, z1):
            '''Tapered box – different cross-section at top and bottom.'''
            b = len(verts)
            verts.extend([
                (x0b, y0b, z0), (x1b, y0b, z0), (x1b, y1b, z0), (x0b, y1b, z0),
                (x0t, y0t, z1), (x1t, y0t, z1), (x1t, y1t, z1), (x0t, y1t, z1),
            ])
            faces.extend([
                (b+0, b+1, b+5, b+4),
                (b+1, b+2, b+6, b+5),
                (b+2, b+3, b+7, b+6),
                (b+3, b+0, b+4, b+7),
                (b+4, b+5, b+6, b+7),
                (b+3, b+2, b+1, b+0),
            ])

        # ---- Legs (separated by a gap) ----
        # Right leg (y < 0)
        _box(-0.08, 0.10, -0.15, -0.02,  0.0,  0.82)
        # Left leg  (y > 0)
        _box(-0.08, 0.10,  0.02,  0.15,  0.0,  0.82)

        # ---- Pelvis / hips ----
        _box(-0.09, 0.11, -0.17, 0.17,  0.76, 0.95)

        # ---- Torso (narrow waist → broader chest) ----
        _tbox(-0.09, 0.11, -0.17, 0.17, 0.95,
              -0.11, 0.13, -0.21, 0.21, 1.35)

        # ---- Shoulders ----
        _box(-0.11, 0.13, -0.24, 0.24,  1.35, 1.45)

        # ---- Neck ----
        _box(-0.04, 0.06, -0.06, 0.06,  1.45, 1.55)

        # ---- Head (slightly tapered towards crown) ----
        _tbox(-0.08, 0.10, -0.10, 0.10, 1.55,
              -0.07, 0.09, -0.09, 0.09, 1.75)

        # ---- Arms (tapered from shoulder to hand) ----
        # Right arm
        _tbox(-0.05, 0.03, -0.32, -0.24, 0.72,
              -0.07, 0.05, -0.34, -0.24, 1.38)
        # Left arm
        _tbox(-0.05, 0.03,  0.24,  0.32, 0.72,
              -0.07, 0.05,  0.24,  0.34, 1.38)

        return verts, edges, faces