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
        # Use a simple box model
        vertices = [
            (0.225000, 0.300000, 1.550000),
            (0.225000, -0.300000, 1.550000),
            (-0.150000, -0.300000, 1.550000),
            (-0.150000, 0.300000, 1.550000),
            (0.200000, 0.300000, 0.000000),
            (0.200000, -0.300000, 0.000000),
            (-0.200000, -0.300000, 0.000000),
            (-0.200000, 0.300000, 0.000000),
            (0.225000, -0.300000, 1.350000),
            (0.225000, 0.300000, 1.350000),
            (0.150000, -0.300000, 1.200000),
            (0.150000, 0.300000, 1.200000),
            (0.025000, 0.300000, 1.700319),
            (0.025000, -0.300000, 1.698110),
            (-0.100000, 0.300000, 0.000000),
            (-0.100000, -0.300000, 0.000000),
            (0.000000, 0.300000, 0.600000),
            (0.000000, -0.300000, 0.600000),
            (0.100000, 0.300000, 0.000000),
            (0.100000, -0.300000, 0.000000),
            (-0.150000, -0.300000, 0.600000),
            (-0.150000, 0.300000, 0.600000),
            (0.150000, 0.300000, 0.600000),
            (0.150000, -0.300000, 0.600000),
            ]
        edges = [(0, 1), (3, 21), (2, 3), (4, 5), (6, 7), (1, 8), (0, 9),
                 (8, 10),(9, 11), (12, 0), (13, 2), (7, 14), (15, 6), (14, 16),
                 (17, 15), (18, 4), (19, 17), (20, 6), (21, 7), (22, 4), (23, 5),
                 (13, 12), (23, 22), (5, 19), (10, 11), (21, 20), (15, 14),
                 (10, 23), (11, 22), (1, 13), (3, 12), (17, 16), (16, 18),
                 (8, 9), (19, 18), (2, 20),]
        faces = [(0, 12, 13, 1), (4, 5, 19, 18),
                 (0, 9, 11, 22, 4, 18, 16, 14, 7, 21, 3, 12), (1, 8, 9, 0),
                 (2, 20, 6, 15, 17, 19, 5, 23, 10, 8, 1, 13), (3, 21, 20, 2),
                 (9, 8, 10, 11), (11, 10, 23, 22), (12, 3, 2, 13),
                 (14, 15, 6, 7), (16, 17, 15, 14), (18, 19, 17, 16),
                 (20, 21, 7, 6), (22, 23, 5, 4),
            ]

        return vertices, edges, faces