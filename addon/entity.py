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

    def __init__(self, context, entity_type, entity_subtype, get_vertices_edges_faces,
                 get_wheel_configs=None, get_face_materials=None,
                 setup_entity_object=None, get_additional_meshes=None):
        self.context = context
        self.entity_type = entity_type
        self.entity_subtype = entity_subtype
        self.get_vertices_edges_faces = get_vertices_edges_faces
        self.get_wheel_configs = get_wheel_configs
        self.get_face_materials = get_face_materials
        self.setup_entity_object = setup_entity_object
        self.get_additional_meshes = get_additional_meshes
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
            obj['speed_initial'] = self.params['speed_initial']

            # Create wheel child objects if provided by the entity subclass
            if self.get_wheel_configs is not None:
                wheel_configs = self.get_wheel_configs()
                # Wheels are parented directly to the body mesh.
                # The esmini-compatible hierarchy (empty -> body + wheels)
                # is created at export time only.
                wheel_color = (0.15, 0.15, 0.15, 1.0)
                for w_name, w_pos, w_verts, w_edges, w_faces in wheel_configs:
                    w_mesh = bpy.data.meshes.new(w_name)
                    w_mesh.from_pydata(w_verts, w_edges, w_faces)
                    w_obj = bpy.data.objects.new(w_name, w_mesh)
                    w_obj.parent = obj
                    w_obj.location = w_pos
                    helpers.link_object_openscenario(context, w_obj,
                        subcategory='entities')
                    helpers.assign_object_materials(w_obj, wheel_color)
                    for poly_idx in range(len(w_obj.data.polygons)):
                        w_obj.data.polygons[poly_idx].material_index = \
                            helpers.get_material_index(w_obj,
                                helpers.get_paint_material_name(wheel_color))

            if self.get_face_materials is not None:
                material_indices = {}
                for index, assignment in enumerate(self.get_face_materials()):
                    if assignment is None:
                        continue
                    name, color = assignment
                    material_name = 'entity_detail_' + name
                    if material_name not in material_indices:
                        material = bpy.data.materials.get(material_name)
                        if material is None:
                            material = bpy.data.materials.new(name=material_name)
                        material.diffuse_color = color
                        material.use_nodes = True
                        shader = material.node_tree.nodes.get('Principled BSDF')
                        if shader:
                            shader.inputs['Base Color'].default_value = color
                            shader.inputs['Roughness'].default_value = 0.28
                        obj.data.materials.append(material)
                        material_indices[material_name] = len(obj.data.materials) - 1
                    obj.data.polygons[index].material_index = material_indices[material_name]

            if self.get_additional_meshes is not None:
                for component in self.get_additional_meshes() or ():
                    if component is None:
                        continue
                    component_name, component_data = component
                    component_vertices, component_edges, component_faces, component_materials = component_data
                    component_mesh = bpy.data.meshes.new(component_name)
                    component_mesh.from_pydata(
                        component_vertices, component_edges, component_faces)
                    component_obj = bpy.data.objects.new(component_name, component_mesh)
                    component_obj.parent = obj
                    component_obj.location = (0.0, 0.0, 0.0)
                    helpers.link_object_openscenario(
                        context, component_obj, subcategory='entities')
                    component_obj['dsc_component'] = component_name
                    helpers.assign_object_materials(component_obj, obj['color'])
                    for polygon in component_obj.data.polygons:
                        polygon.material_index = helpers.get_material_index(
                            component_obj,
                            helpers.get_paint_material_name(obj['color']))
                    material_indices = {}
                    for index, assignment in enumerate(component_materials):
                        if assignment is None:
                            continue
                        name, color = assignment
                        material_name = 'entity_detail_' + name
                        if material_name not in material_indices:
                            material = bpy.data.materials.get(material_name)
                            if material is None:
                                material = bpy.data.materials.new(name=material_name)
                            material.diffuse_color = color
                            material.use_nodes = True
                            shader = material.node_tree.nodes.get('Principled BSDF')
                            if shader:
                                shader.inputs['Base Color'].default_value = color
                                shader.inputs['Roughness'].default_value = 0.28
                            component_mesh.materials.append(material)
                            material_indices[material_name] = len(component_mesh.materials) - 1
                        component_mesh.polygons[index].material_index = \
                            material_indices[material_name]

            if self.setup_entity_object is not None:
                self.setup_entity_object(context, obj)

        return obj

    def update_params_get_mesh(self, context, params_input, wireframe):
        '''
            Calculate and return the vertices, edges and faces to create a road mesh.
        '''
        heading_override = params_input.get('heading_override')
        if params_input['point_start'] == params_input['point_end'] and heading_override is None:
            if not wireframe:
                self.report({'WARNING'}, 'Start and end point can not be the same!')
            valid = False
            return valid, None, {}
        if heading_override is None:
            vector_start_end = params_input['point_end'] - params_input['point_start']
            heading = vector_start_end.to_2d().angle_signed(Vector((1.0, 0.0)))
        else:
            heading = heading_override
        if self.entity_type == 'vehicle':
            entity_properties = context.scene.dsc_properties.entity_properties_vehicle
        else:
            entity_properties = context.scene.dsc_properties.entity_properties_pedestrian
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
