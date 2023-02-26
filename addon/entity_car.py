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


class DSC_OT_entity_car(DSC_OT_entity):
    bl_idname = 'dsc.entity_car'
    bl_label = 'Car'
    bl_description = 'Place a car entity object'
    bl_options = {'REGISTER', 'UNDO'}

    entity_type = 'vehicle'
    entity_subtype = 'car'

    def get_vertices_edges_faces(self):
        vertices = [(-2.2, -1.0, 0.0),
                    ( 2.2, -1.0, 0.0),
                    ( 2.2, -1.0, 0.5),
                    ( 1.9, -1.0, 0.8),
                    ( 1.1, -1.0, 0.85),
                    ( 0.1, -1.0, 1.6),
                    (-1.6, -1.0, 1.58),
                    (-2.2, -1.0, 0.9),
                    (-2.2, 1.0, 0.0),
                    ( 2.2, 1.0, 0.0),
                    ( 2.2, 1.0, 0.5),
                    ( 1.9, 1.0, 0.8),
                    ( 1.1, 1.0, 0.85),
                    ( 0.1, 1.0, 1.6),
                    (-1.6, 1.0, 1.58),
                    (-2.2, 1.0, 0.9),
                   ]
        edges = [[0, 1],[1, 2],[2, 3],[3, 4],[4 ,5],[5 ,6],[6 ,7],[7, 0],
                 [15 ,14],[14 ,13],[13 ,12],[12 ,11],[11 ,10],[10 ,9], [9 ,8], [8, 15],
                 [0, 8], [7 ,15], [6 ,14], [5 ,13], [4 ,12], [3 ,11], [2 ,10], [1 ,9],
                ]
        faces = [[0, 1, 2, 3, 4, 5, 6, 7],[15, 14, 13, 12, 11, 10, 9, 8],
                    [0, 7, 15, 8], [7, 6, 14, 15], [6, 5, 13, 14], [5, 4, 12, 13],
                    [4, 3, 11, 12], [3, 2, 10, 11], [2, 1, 9, 10], [8, 9, 1, 0]
                ]
        return vertices, edges, faces