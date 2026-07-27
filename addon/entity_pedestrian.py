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
    entity_subtype = 'adult'

    pedestrian_category: bpy.props.EnumProperty(
        name='Pedestrian category',
        description='OpenSCENARIO pedestrian category',
        items=(
            ('adult', 'Adult', 'Create an adult pedestrian entity'),
            ('child', 'Child', 'Create a child pedestrian entity'),
        ),
        default='adult',
    )

    def invoke(self, context, event):
        self.entity_subtype = self.pedestrian_category
        return super().invoke(context, event)

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
        face_materials = []

        legs_material = ('pedestrian_legs', (0.08, 0.10, 0.14, 1.0))
        skin_material = ('pedestrian_skin', (0.72, 0.48, 0.32, 1.0))
        hair_material = ('pedestrian_hair', (0.075, 0.038, 0.022, 1.0))
        eye_material = ('pedestrian_eyes', (0.018, 0.012, 0.008, 1.0))
        shoe_material = ('pedestrian_shoes', (0.035, 0.04, 0.05, 1.0))

        def _add_box_edges(base):
            '''Add the twelve perimeter and corner edges for a box primitive.'''
            edges.extend([
                (base+0, base+1), (base+1, base+2),
                (base+2, base+3), (base+3, base+0),
                (base+4, base+5), (base+5, base+6),
                (base+6, base+7), (base+7, base+4),
                (base+0, base+4), (base+1, base+5),
                (base+2, base+6), (base+3, base+7),
            ])

        def _box(x0, x1, y0, y1, z0, z1, material=None):
            '''Axis-aligned box.'''
            b = len(verts)
            verts.extend([
                (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
            ])
            _add_box_edges(b)
            faces.extend([
                (b+0, b+1, b+5, b+4),
                (b+1, b+2, b+6, b+5),
                (b+2, b+3, b+7, b+6),
                (b+3, b+0, b+4, b+7),
                (b+4, b+5, b+6, b+7),
                (b+3, b+2, b+1, b+0),
            ])
            face_materials.extend([material] * 6)

        def _tbox(x0b, x1b, y0b, y1b, z0, x0t, x1t, y0t, y1t, z1,
                  material=None):
            '''Tapered box – different cross-section at top and bottom.'''
            b = len(verts)
            verts.extend([
                (x0b, y0b, z0), (x1b, y0b, z0), (x1b, y1b, z0), (x0b, y1b, z0),
                (x0t, y0t, z1), (x1t, y0t, z1), (x1t, y1t, z1), (x0t, y1t, z1),
            ])
            _add_box_edges(b)
            faces.extend([
                (b+0, b+1, b+5, b+4),
                (b+1, b+2, b+6, b+5),
                (b+2, b+3, b+7, b+6),
                (b+3, b+0, b+4, b+7),
                (b+4, b+5, b+6, b+7),
                (b+3, b+2, b+1, b+0),
            ])
            face_materials.extend([material] * 6)

        # ---- Legs (separated by a gap) ----
        # Right leg (y < 0)
        _box(-0.08, 0.10, -0.15, -0.02,  0.045, 0.82, legs_material)
        # Left leg  (y > 0)
        _box(-0.08, 0.10,  0.02,  0.15,  0.045, 0.82, legs_material)

        # Shoes overlap the lower legs and project forward in the +X direction.
        _box(-0.08, 0.14, -0.16, -0.01, 0.0, 0.045, shoe_material)
        _box(-0.08, 0.14,  0.01,  0.16, 0.0, 0.045, shoe_material)

        # ---- Pelvis / hips ----
        _box(-0.09, 0.11, -0.17, 0.17,  0.76, 0.95)

        # ---- Torso (narrow waist → broader chest) ----
        _tbox(-0.09, 0.11, -0.17, 0.17, 0.95,
              -0.11, 0.13, -0.21, 0.21, 1.35)

        # ---- Shoulders ----
        _box(-0.11, 0.13, -0.24, 0.24,  1.35, 1.45)

        # ---- Neck ----
        _box(-0.04, 0.06, -0.06, 0.06,  1.45, 1.55, skin_material)

        # ---- Head (slightly tapered towards crown) ----
        _tbox(-0.08, 0.10, -0.10, 0.10, 1.55,
              -0.07, 0.09, -0.09, 0.09, 1.75, skin_material)

        # A simple dark cap of hair, with two eyes on the forward-facing side.
        _box(-0.10, 0.12, -0.11, 0.11, 1.70, 1.77, hair_material)
        _box(0.092, 0.112, -0.052, -0.028, 1.655, 1.679, eye_material)
        _box(0.092, 0.112,  0.028,  0.052, 1.655, 1.679, eye_material)

        # ---- Arms (tapered from shoulder to hand) ----
        # Right arm
        _tbox(-0.05, 0.03, -0.32, -0.24, 0.72,
              -0.07, 0.05, -0.34, -0.24, 1.38)
        # Left arm
        _tbox(-0.05, 0.03,  0.24,  0.32, 0.72,
              -0.07, 0.05,  0.24,  0.34, 1.38)

        # Hands attach at the lower ends of the sleeves.
        _box(-0.02, 0.10, -0.325, -0.235, 0.66, 0.78, skin_material)
        _box(-0.02, 0.10,  0.235,  0.325, 0.66, 0.78, skin_material)

        # Keep adult as the reference model and scale child down.
        if self.entity_subtype == 'child':
            child_scale = 0.72
            verts = [(x * child_scale, y * child_scale, z * child_scale)
                     for x, y, z in verts]

        self.face_materials = face_materials
        return verts, edges, faces

    def get_face_materials(self):
        return getattr(self, 'face_materials', [])