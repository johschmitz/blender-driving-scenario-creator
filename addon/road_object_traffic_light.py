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


class road_object_traffic_light:

    def __init__(self, context, road_object_type):
        self.context = context
        self.road_object_type = road_object_type
        self.road_object_odr_info = {}
        self.params = {}

    def create_object_3d(self, context, params_input, road_id):
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
                if idx in materials['traffic_light_housing']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'traffic_light_housing')
                if idx in materials['traffic_light_red']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'traffic_light_red')
                if idx in materials['traffic_light_yellow']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'traffic_light_yellow')
                if idx in materials['traffic_light_green']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'traffic_light_green')

            # Metadata
            obj['dsc_category'] = 'OpenDRIVE'
            obj['dsc_type'] = 'road_object'
            obj['road_object_type'] = self.road_object_type
            obj['id_odr'] = id_obj
            obj['id_road'] = road_id
            obj['position_s'] = params_input['point_s']
            obj['position_t'] = params_input['point_t']
            obj['position'] = params_input['point']
            obj['hdg'] = params_input['heading']
            obj['width'] = context.scene.dsc_properties.road_object_traffic_light_properties.height
            obj['height'] = context.scene.dsc_properties.road_object_traffic_light_properties.height/2
            obj['length'] = context.scene.dsc_properties.road_object_traffic_light_properties.height/2
            # TODO for now assume 2 mm steel for the signs
            obj['length'] = 0.002
            obj['zOffset'] = context.scene.dsc_properties.road_object_traffic_light_properties.pole_height
            # See https://publications.pages.asam.net/standards/ASAM_OpenDRIVE/ASAM_OpenDRIVE_Signal_reference/latest/signal-catalog/01_road_signals/road_signals.html#_traffic_signals_for_all_traffic_participants
            obj['catalog_type'] = "1000001"
            obj['catalog_subtype'] = None
            obj['value'] = None

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
        pole_height = context.scene.dsc_properties.road_object_traffic_light_properties.pole_height
        housing_height = context.scene.dsc_properties.road_object_traffic_light_properties.height
        vertices, edges, faces, materials = self.get_vertices_edges_faces_materials(pole_height, housing_height)
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
            faces = []
        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, edges, faces)
        valid = True
        return valid, mesh, matrix_world, materials

    def get_vertices_edges_faces_materials(self, pole_height, housing_height):
        vertices = [
            (0.000000, -1.5/13.0*housing_height, pole_height+1.0/13.0*housing_height),
            (0.000000, -1.5/13.0*housing_height, pole_height+12.0/13.0*housing_height),
            (-0.000000, 1.5/13.0*housing_height, pole_height+1.0/13.0*housing_height),
            (-0.000000, 1.5/13.0*housing_height, pole_height+12.0/13.0*housing_height),
            (housing_height/5.0, -2.5/13.0*housing_height, pole_height),
            (housing_height/5.0, -2.5/13.0*housing_height, pole_height+housing_height),
            (housing_height/5.0, 2.5/13.0*housing_height, pole_height),
            (housing_height/5.0, 2.5/13.0*housing_height, pole_height+housing_height),
            (-0.000000, 2.5/13.0*housing_height, pole_height+housing_height),
            (-0.000000, 2.5/13.0*housing_height, pole_height),
            (0.000000, -2.5/13.0*housing_height, pole_height),
            (0.000000, -2.5/13.0*housing_height, pole_height+housing_height),
            (-0.000000, 1.5/13.0*housing_height, pole_height+9.0/13.0*housing_height),
            (0.000000, -1.5/13.0*housing_height, pole_height+9.0/13.0*housing_height),
            (-0.000000, 1.5/13.0*housing_height, pole_height+8.0/13.0*housing_height),
            (0.000000, -1.5/13.0*housing_height, pole_height+8.0/13.0*housing_height),
            (-0.000000, 1.5/13.0*housing_height, pole_height+5.0/13.0*housing_height),
            (0.000000, -1.5/13.0*housing_height, pole_height+5.0/13.0*housing_height),
            (-0.000000, 1.5/13.0*housing_height, pole_height+4.0/13.0*housing_height),
            (0.000000, -1.5/13.0*housing_height, pole_height+4.0/13.0*housing_height),
            (-housing_height/5.0, 1.5/13.0*housing_height, pole_height+8.0/13.0*housing_height),
            (-housing_height/5.0, -1.5/13.0*housing_height, pole_height+8.0/13.0*housing_height),
            (-housing_height/10.0, 1.5/13.0*housing_height, pole_height+5.0/13.0*housing_height),
            (-housing_height/10.0, -1.5/13.0*housing_height, pole_height+5.0/13.0*housing_height),
            (-housing_height/5.0, -1.5/13.0*housing_height, pole_height+12.0/13.0*housing_height),
            (-housing_height/5.0, 1.5/13.0*housing_height, pole_height+12.0/13.0*housing_height),
            (-housing_height/10.0, 1.5/13.0*housing_height, pole_height+9.0/13.0*housing_height),
            (-housing_height/10.0, -1.5/13.0*housing_height, pole_height+9.0/13.0*housing_height),
            (-housing_height/10.0, -1.5/13.0*housing_height, pole_height+1.0/13.0*housing_height),
            (-housing_height/10.0, 1.5/13.0*housing_height, pole_height+1.0/13.0*housing_height),
            (-housing_height/5.0, 1.5/13.0*housing_height, pole_height+4.0/13.0*housing_height),
            (-housing_height/5.0, -1.5/13.0*housing_height, pole_height+4.0/13.0*housing_height),
        ]
        edges = [
            (8, 9),
            (10, 11),
            (9, 10),
            (11, 8),
            (10, 4),
            (5, 4),
            (6, 9),
            (8, 7),
            (5, 11),
            (7, 5),
            (7, 6),
            (4, 6),
            (18, 2),
            (13, 1),
            (2, 0),
            (1, 3),
            (9, 2),
            (3, 8),
            (11, 1),
            (0, 10),
            (3, 12),
            (15, 13),
            (13, 12),
            (12, 14),
            (17, 15),
            (15, 14),
            (14, 16),
            (19, 17),
            (17, 16),
            (16, 18),
            (0, 19),
            (19, 18),
            (23, 21),
            (21, 20),
            (20, 22),
            (22, 16),
            (14, 20),
            (15, 21),
            (17, 23),
            (27, 24),
            (24, 25),
            (25, 26),
            (25, 3),
            (12, 26),
            (24, 1),
            (27, 13),
            (30, 29),
            (28, 31),
            (31, 30),
            (30, 18),
            (19, 31),
            (0, 28),
            (29, 2),
        ]
        faces = [
            (13, 1, 3, 12),
            (9, 8, 7, 6),
            (6, 7, 5, 4),
            (4, 5, 11, 10),
            (9, 6, 4, 10),
            (7, 8, 11, 5),
            (2, 18, 16, 14, 12, 3, 8, 9),
            (1, 13, 15, 17, 19, 0, 10, 11),
            (0, 2, 9, 10),
            (3, 1, 11, 8),
            (15, 13, 12, 14),
            (17, 15, 14, 16),
            (19, 17, 16, 18),
            (0, 19, 18, 2),
            (16, 22, 20, 14),
            (14, 20, 21, 15),
            (15, 21, 23, 17),
            (3, 12, 26, 25),
            (1, 3, 25, 24),
            (13, 1, 24, 27),
            (18, 30, 31, 19),
            (19, 31, 28, 0),
            (2, 29, 30, 18),
        ]

        materials = {
            'traffic_light_housing': (1, 2, 3, 4, 5, 6,7, 8,9, 10, 12, 14, 15, 16, 17, 18,
                                      19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31),
            'traffic_light_red': (0,),
            'traffic_light_yellow': (11,),
            'traffic_light_green': (13,),
        }

        return vertices, edges, faces, materials
