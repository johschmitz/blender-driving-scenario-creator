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
import os
from mathutils import Vector, Matrix

from math import pi

from . import helpers


class road_object_stop_line:

    def __init__(self, context, road_object_type):
        self.context = context
        self.road_object_type = road_object_type
        self.road_object_odr_info = {}
        self.params = {}

    def create_object_3d(self, context, params_input, id_road, id_reference_object):
        '''
            Create a 3d entity object
        '''
        valid, mesh, matrix_world, materials = self.update_params_get_mesh(
            context, params_input, wireframe=False)
        if not valid:
            return None
        else:
            id_obj = helpers.get_new_id_opendrive(context)
            obj_name = self.road_object_type + '_' + str(id_obj)
            mesh.name = obj_name
            obj = bpy.data.objects.new(mesh.name, mesh)
            obj.matrix_world = matrix_world
            helpers.link_object_opendrive(context, obj)

            helpers.select_activate_object(context, obj)

            # Assign materials
            helpers.assign_materials(obj)
            for idx in range(len(obj.data.polygons)):
                if idx in materials['road_mark_white']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'road_mark_white')

            # Set Shading to 'TEXTURE' to make the texture visible
            context.area.spaces.active.shading.color_type = 'TEXTURE'

            # Metadata
            obj['dsc_category'] = 'OpenDRIVE'
            obj['dsc_type'] = 'road_object'
            obj['road_object_type'] = self.road_object_type
            obj['id_odr'] = id_obj
            obj['id_road'] = id_road
            obj['id_ref_object'] = id_reference_object
            obj['position_s'] = params_input['point_s']
            obj['position_t'] = params_input['point_t']
            obj['width'] = 3.5
            # TODO for now assume 2 mm steel for the signs
            obj['length'] = 0.5
            obj['zOffset'] = 0.0
            obj['height'] = 0.01
            obj['catalog_type'] = 294
            obj['catalog_subtype'] = None
            obj['value'] = 0

        return obj

    def update_params_get_mesh(self, context, params_input, wireframe):
        '''
            Calculate and return the vertices, edges and faces to create a sign
            pole or plate mesh.
        '''
        origin_point = params_input['point']
        if params_input['point_t'] < 0:
            heading = params_input['heading']
        else:
            heading = params_input['heading'] + pi
        # Build sign plate
        length = 3.5
        vertices, edges, faces, materials = self.get_vertices_edges_faces_materials(length)
        # TODO make sign height configurable
        mat_translation = Matrix.Translation(origin_point)
        mat_rotation = Matrix.Rotation(heading, 4, 'Z')
        matrix_world = mat_translation @ mat_rotation
        # Create blender mesh
        if wireframe:
            mat_rotation_inverted = Matrix.Rotation(-heading, 4, 'Z')
            point_ref_line_rel = mat_rotation_inverted @ (params_input['point_ref_line'] - origin_point)
            vertices.append((0.0, 0.0, 0.0))
            vertices.append((point_ref_line_rel.x, point_ref_line_rel.y, 0.0))
            edges.append((len(vertices)-2, len(vertices)-1))
            point_ref_object_rel = mat_rotation_inverted @ (params_input['point_ref_object'] - origin_point)
            vertices.append((0.0, 0.0, 0.0))
            vertices.append((point_ref_object_rel.x, point_ref_object_rel.y, 0.0))
            edges.append((len(vertices)-2, len(vertices)-1))
            faces = []
        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, edges, faces)
        valid = True
        return valid, mesh, matrix_world, materials

    def get_vertices_edges_faces_materials(self, length):
        vertices = [
            (0.0, 0.0, 0.01),
            (0.0, -0.5*length, 0.01),
            (0.5, -0.5*length, 0.01),
            (0.5, 0.0, 0.01),
            (0.5, 0.5*length, 0.01),
            (0.0, 0.5*length, 0.01),
        ]
        edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),
            (4, 5),
            (5, 0),
        ]
        faces = [
            (0, 1, 2, 3, 4, 5),
        ]

        materials = {
            'road_mark_white': (0,),
        }

        return vertices, edges, faces, materials
