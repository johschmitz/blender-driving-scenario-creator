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

from . import helpers


class entity:

    def __init__(self, context, entity_type, entity_subtype, get_vertices_edges_faces):
        self.context = context
        self.entity_type = entity_type
        self.entity_subtype = entity_subtype
        self.get_vertices_edges_faces = get_vertices_edges_faces
        self.params = {}

    def create_object_3d(self, context, params_input):
        '''
            Create a 3d entity object
        '''
        valid, mesh, matrix_world, materials = self.update_params_get_mesh(
            context, params_input, wireframe=False)
        if not valid:
            return None
        else:
            id_obj = helpers.get_new_id_openscenario(context)
            obj_name = self.params['name'] + '_' + str(id_obj)
            mesh.name = obj_name
            obj = bpy.data.objects.new(mesh.name, mesh)
            obj.matrix_world = matrix_world
            helpers.link_object_openscenario(context, obj, subcategory='entities')

            helpers.select_activate_object(context, obj)

            # Assign materials
            obj['color'] = self.params['color']
            helpers.assign_object_materials(obj, obj['color'])
            for idx in range(len(obj.data.polygons)):
                obj.data.polygons[idx].material_index = \
                    helpers.get_material_index(obj, helpers.get_paint_material_name(obj['color']))

            # Metadata
            obj['dsc_category'] = 'OpenSCENARIO'
            obj['dsc_type'] = 'entity'
            obj['entity_type'] = self.entity_type
            obj['entity_subtype'] = self.entity_subtype

            # Set OpenSCENARIO custom properties
            obj['position'] = self.params['position']
            obj['hdg'] = self.params['heading']
            obj['speed_initial'] = self.params['speed_initial']

        return obj

    def update_params_get_mesh(self, context, params_input, wireframe):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        if params_input['point_start'] == params_input['point_end']:
            if not wireframe:
                self.report({'WARNING'}, 'Start and end point can not be the same!')
            valid = False
            return valid, None, {}
        vector_start_end = params_input['point_end'] - params_input['point_start']
        heading = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        if self.entity_type == 'vehicle':
            entity_properties = context.scene.entity_properties_vehicle
        else:
            entity_properties = context.scene.entity_properties_pedestrian
        self.params = {'name': entity_properties.name,
                       'position': params_input['point_start'],
                       'heading': heading,
                       'speed_initial': entity_properties.speed_initial,
                       'color': entity_properties.color}
        vertices, edges, faces = self.get_vertices_edges_faces()
        mat_translation = Matrix.Translation(params_input['point_start'])
        vec_up = Vector((0.0, 0.0, 1.0))
        vec_normal = params_input['normal_start']
        mat_normal = vec_up.rotation_difference(vec_normal).to_matrix().to_4x4()
        mat_heading = Matrix.Rotation(heading, 4, 'Z')
        matrix_world = mat_translation @ mat_normal @ mat_heading
        # Create blender mesh
        if wireframe:
            faces = []
        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, edges, faces)
        valid = True
        materials = {}
        return valid, mesh, matrix_world, materials
