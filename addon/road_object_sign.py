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


class road_object_sign:

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
                if idx in materials['road_sign_pole']:
                    obj.data.polygons[idx].material_index = \
                        helpers.get_material_index(obj, 'road_sign_pole')

            # Assign texture
            material_name = self.assign_road_sign_texture(context, obj)
            if material_name != None:
                for idx in range(len(obj.data.polygons)):
                    if idx in materials['road_sign_plate']:
                        obj.data.polygons[idx].material_index = \
                            helpers.get_material_index(obj, material_name)
            # Set Shading to 'TEXTURE' to make the texture visible
            context.area.spaces.active.shading.color_type = 'TEXTURE'

            # Metadata
            obj['dsc_category'] = 'OpenDRIVE'
            obj['dsc_type'] = 'road_object'
            obj['road_object_type'] = self.road_object_type
            obj['id_odr'] = id_obj
            obj['id_road'] = road_id
            obj['position_s'] = params_input['point_s']
            obj['position_t'] = params_input['point_t']
            obj['width'] = context.scene.dsc_properties.road_object_sign_properties.width
            obj['height'] = context.scene.dsc_properties.road_object_sign_properties.width
            # TODO for now assume 2 mm steel for the signs
            obj['length'] = 0.002
            obj['zOffset'] = context.scene.dsc_properties.road_object_sign_properties.pole_height
            sign_info = self.get_sign_catalog_info(context)
            obj['catalog_type'] = sign_info['type']
            obj['catalog_subtype'] = sign_info['subtype']
            obj['value'] = sign_info['value']

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
        pole_height = context.scene.dsc_properties.road_object_sign_properties.pole_height
        sign_width = context.scene.dsc_properties.road_object_sign_properties.width
        vertices, edges, faces, materials = self.get_vertices_edges_faces_materials(pole_height, sign_width)
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

    def get_vertices_edges_faces_materials(self, pole_height, sign_width):
        vertices = [
            (0.016787, 0.015000, 0.000000),
            (0.016787, 0.015000, pole_height+sign_width),
            (0.029213, 0.015000, 0.000000),
            (0.029213, 0.015000, pole_height+sign_width),
            (0.038, 0.006213, 0.000000),
            (0.038, 0.006213, pole_height+sign_width),
            (0.038, -0.006213, 0.000000),
            (0.038, -0.006213, pole_height+sign_width),
            (0.029213, -0.015000, 0.000000),
            (0.029213, -0.015000, pole_height+sign_width),
            (0.016787, -0.015000, 0.000000),
            (0.016787, -0.015000, pole_height+sign_width),
            (0.008, -0.006213, 0.000000),
            (0.008, -0.006213, pole_height+sign_width),
            (0.008, 0.006213, 0.000000),
            (0.008, 0.006213, pole_height+sign_width),
            (0.004000, 0.5*sign_width, pole_height),
            (0.004000, 0.5*sign_width, pole_height+sign_width),
            (0.004000, -0.5*sign_width, pole_height),
            (0.004000, -0.5*sign_width, pole_height+sign_width),
            (0.000000, 0.5*sign_width, pole_height),
            (0.000000, 0.5*sign_width, pole_height+sign_width),
            (0.000000, -0.5*sign_width, pole_height),
            (0.000000, -0.5*sign_width, pole_height+sign_width),
        ]
        edges = [
            (0, 2),
            (3, 1),
            (0, 1),
            (3, 2),
            (2, 4),
            (5, 3),
            (5, 4),
            (4, 6),
            (7, 5),
            (7, 6),
            (6, 8),
            (9, 7),
            (9, 8),
            (8, 10),
            (11, 9),
            (11, 10),
            (10, 12),
            (13, 11),
            (13, 12),
            (12, 14),
            (15, 13),
            (15, 14),
            (14, 0),
            (1, 15),
            (18, 16),
            (16, 17),
            (17, 19),
            (19, 18),
            (22, 18),
            (19, 23),
            (23, 22),
            (20, 22),
            (23, 21),
            (21, 20),
            (16, 20),
            (21, 17),
        ]
        faces = [
            (0, 1, 3, 2),
            (2, 3, 5, 4),
            (4, 5, 7, 6),
            (6, 7, 9, 8),
            (8, 9, 11, 10),
            (10, 11, 13, 12),
            (3, 1, 15, 13, 11, 9, 7, 5),
            (12, 13, 15, 14),
            (14, 15, 1, 0),
            (0, 2, 4, 6, 8, 10, 12, 14),
            (16, 17, 19, 18),
            (18, 19, 23, 22),
            (22, 23, 21, 20),
            (20, 21, 17, 16),
            (18, 22, 20, 16),
            (23, 19, 17, 21),
        ]

        materials = {
            'road_sign_pole': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
            'road_sign_plate': (10, 11, 12, 13, 14, 15),
        }

        return vertices, edges, faces, materials


    def assign_road_sign_texture(self, context, obj):
        '''
            Assign material for road sign texture and return material name.
        '''
        # Get the file name for the selected road sign texture
        sign_name_selected = None
        for sign in context.scene.dsc_properties.road_object_sign_properties.sign_catalog:
            if sign.selected == True:
                sign_name_selected = sign.name
                texture_file_name = sign.texture_name + '_texture.png'
                break
        if sign_name_selected == None:
            return None
        material_name = 'sign_plate_' + sign_name_selected

        # Make sure we add this texture only once
        if helpers.get_material_index(obj, material_name) != None:
            return

        # Add texture
        img = bpy.data.images.load(os.path.join(
            context.scene.dsc_properties.road_object_sign_properties.texture_directory, texture_file_name))
        material = bpy.data.materials.get(material_name)
        if material is None:
            material = bpy.data.materials.new(name=material_name)
            material.diffuse_color = (.1, .1, .1, 1.0)
            material.use_nodes = True
            principled_BSDF = material.node_tree.nodes.get('Principled BSDF')
            tex_node = material.node_tree.nodes.new('ShaderNodeTexImage')
            tex_node.image = img

            material.node_tree.links.new(tex_node.outputs[0], principled_BSDF.inputs[0])
            material.use_backface_culling = True
            material.blend_method = 'CLIP'
            material.shadow_method = 'CLIP'
        obj.data.materials.append(material)
        # Make sure the textures are packed into the .blend file
        bpy.ops.file.pack_all()
        # Map UV coordinates to texture
        uv_coordinates = [
            (0.5,0.0), (0.5,1.0), (1.0,1.0), (1.0,0.0), # Front
            (0.0,0.0), (0.0,0.0), (0.0,0.0), (0.0,0.0), # Edge
            (0.5,0.0), (0.5,1.0), (0.0,1.0), (0.0,0.0), # Back
            (0.0,0.0), (0.0,0.0), (0.0,0.0), (0.0,0.0), # Edge
            (0.0,0.0), (0.0,0.0), (0.0,0.0), (0.0,0.0), # Edge
            (0.0,0.0), (0.0,0.0), (0.0,0.0), (0.0,0.0), # Edge
        ]
        obj.data.uv_layers.new(name="UVMapRoadSign")
        for idx, uv_entry in enumerate(obj.data.uv_layers[0].data[-len(uv_coordinates):]):
            uv_entry.uv = uv_coordinates[idx]

        return material_name

    def get_sign_catalog_info(self, context):
        '''
            Return sign OpenDRIVE type and subtype information.
        '''
        for sign in context.scene.dsc_properties.road_object_sign_properties.sign_catalog:
            if sign.selected == True:
                return {"type": sign.type, "subtype": sign.subtype, "value": sign.value}
        return {"type": None, "subtype": None, "value": 0}