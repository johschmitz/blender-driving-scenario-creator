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
from . import helpers

from scenariogeneration import xosc
from scenariogeneration import xodr

from mathutils import Vector
from math import pi

import pathlib
import subprocess

mapping_lane_type = {
    'driving': xodr.LaneType.driving,
    #'bidirectional': xodr.LaneType.bidirectional,
    #'bus': xodr.LaneType.bus,
    'stop': xodr.LaneType.stop,
    #'parking': xodr.LaneType.parking,
    #'biking': xodr.LaneType.biking,
    #'restricted': xodr.LaneType.restricted,
    #'roadWorks': xodr.LaneType.roadWorks,
    'border': xodr.LaneType.border,
    # TODO (missing) 'curb': xodr.LaneType.curb,
    #'sidewalk': xodr.LaneType.sidewalk,
    'shoulder': xodr.LaneType.shoulder,
    'median': xodr.LaneType.median,
    'entry': xodr.LaneType.entry,
    'exit': xodr.LaneType.exit,
    'onRamp': xodr.LaneType.onRamp,
    'offRamp': xodr.LaneType.offRamp,
    #'connectingRamp': xodr.LaneType.connectingRamp,
    'none': xodr.LaneType.none,
}

mapping_road_mark_type = {
    'none': xodr.RoadMarkType.none,
    'solid': xodr.RoadMarkType.solid,
    'broken': xodr.RoadMarkType.broken,
    'solid_solid': xodr.RoadMarkType.solid_solid,
    #'solid_broken': xodr.RoadMarkType.solid_broken,
    #'broken_solid': xodr.RoadMarkType.broken_solid,
}

mapping_road_mark_weight = {
    'standard': xodr.RoadMarkWeight.standard,
    'bold': xodr.RoadMarkWeight.bold,
}

mapping_road_mark_color = {
    'white': xodr.RoadMarkColor.white,
    'yellow': xodr.RoadMarkColor.yellow,
}

mapping_vehicle_type = {
    'car': xosc.VehicleCategory.car,
}

mapping_pedestrian_type = {
    'pedestrian': xosc.PedestrianCategory.pedestrian,
}

mapping_contact_point = {
    'cp_start_l': xodr.ContactPoint.start,
    'cp_start_r': xodr.ContactPoint.start,
    'cp_end_l': xodr.ContactPoint.end,
    'cp_end_r': xodr.ContactPoint.end,
}

class DSC_OT_export(bpy.types.Operator):
    bl_idname = 'dsc.export_driving_scenario'
    bl_label = 'Export driving scenario'
    bl_description = 'Export driving scenario as OpenDRIVE, OpenSCENARIO and Mesh (e.g. OSGB, FBX, glTF 2.0)'

    directory: bpy.props.StringProperty(
        name='Export directory', description='Target directory for export.')

    mesh_file_type : bpy.props.EnumProperty(
        items=(('fbx', '.fbx', '', 0),
               ('glb', '.glb', '', 1),
               ('gltf', '.gltf', '', 2),
               ('osgb', '.osgb', '', 3),
              ),
        default='osgb',
    )

    dsc_export_filename = 'bdsc_export'

    @classmethod
    def poll(cls, context):
        # if helpers.collection_exists(['OpenDRIVE']):
        #     return True
        # else:
        #     return False
        return True

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Mesh file:")
        row.prop(self, "mesh_file_type", expand=True)

    def execute(self, context):
        self.export_entity_models(context)
        self.export_static_scene_model()
        self.export_openscenario()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def export_static_scene_model(self):
        '''
            Export the scene mesh to file
        '''
        file_path = pathlib.Path(self.directory) / 'models'/ 'static_scene' / 'bdsc_export.suffix'
        file_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.object.select_all(action='SELECT')
        if helpers.collection_exists(['OpenSCENARIO']):
            for obj in bpy.data.collections['OpenSCENARIO'].objects:
                obj.select_set(False)
            for child in bpy.data.collections['OpenSCENARIO'].children:
                for obj in child.objects:
                    obj.select_set(False)
            for obj in bpy.data.collections['OpenDRIVE'].objects:
                if 'dsc_type' in obj and obj['dsc_type'] == 'junction_connecting_road':
                        obj.select_set(False)
        self.export_mesh(file_path)
        bpy.ops.object.select_all(action='DESELECT')

    def export_entity_models(self, context):
        '''
            Export vehicle models to files.
        '''
        model_dir = pathlib.Path(self.directory) / 'models' / 'entities' / 'vehicle.obj'
        model_dir.parent.mkdir(parents=True, exist_ok=True)
        vehicle_catalog_path = pathlib.Path(self.directory) / 'catalogs' / 'vehicles' / 'VehicleCatalog.xosc'
        vehicle_catalog_path.parent.mkdir(parents=True, exist_ok=True)
        pedestrian_catalog_path = pathlib.Path(self.directory) / 'catalogs' / 'pedestrians' / 'PedestrianCatalog.xosc'
        pedestrian_catalog_path.parent.mkdir(parents=True, exist_ok=True)
        # Select a vehicle
        bpy.ops.object.select_all(action='DESELECT')
        if helpers.collection_exists(['OpenSCENARIO','entities']):
            vehicle_catalog_file_created = False
            pedestrian_catalog_file_created = False
            for obj in bpy.data.collections['OpenSCENARIO'].children['entities'].objects:
                print('Export entity object model for', obj.name)
                model_path = pathlib.Path(self.directory) / 'models' / 'entities' / str(obj.name)
                # Create a temporary copy without transform
                obj_export = obj.copy()
                helpers.link_object_openscenario(context, obj_export, subcategory=None)
                obj_export.select_set(True)
                bpy.ops.object.location_clear()
                bpy.ops.object.rotation_clear()
                # Export then delete copy
                self.export_mesh(model_path)
                bpy.ops.object.delete()
                self.convert_to_osgb(model_path)
                if obj['entity_type'] == 'vehicle':
                    # Add vehicle to vehicle catalog
                    # TODO store in and read vehicle parameters from object
                    bounding_box = xosc.BoundingBox(2,5,1.8,2.0,0,0.9)
                    axle_front = xosc.Axle(0.523599,0.8,1.554,2.98,0.4)
                    axle_rear = xosc.Axle(0,0.8,1.525,0,0.4)
                    vehicle = xosc.Vehicle(obj.name,mapping_vehicle_type[obj['entity_subtype']],
                        bounding_box,axle_front,axle_rear,69,10,10)
                    vehicle.add_property_file('../models/entities/' + obj.name + '.' + self.mesh_file_type)
                    vehicle.add_property('control','internal')
                    vehicle.add_property('model_id','0')
                    if not vehicle_catalog_file_created:
                        # Create new catalog with first vehicle
                        vehicle.dump_to_catalog(vehicle_catalog_path,'VehicleCatalog',
                            'DSC vehicle catalog','Blender Driving Scenario Creator')
                        vehicle_catalog_file_created = True
                    else:
                        vehicle.append_to_catalog(vehicle_catalog_path)
                elif obj['entity_type'] == 'pedestrian':
                    # Add pedestrian to pedestrian catalog
                    # TODO store in and read pedestrian bounding box from object
                    bounding_box = xosc.BoundingBox(0.4,0.6,1.8,0,0,0.6)
                    pedestrian = xosc.Pedestrian(obj.name,80,mapping_pedestrian_type[obj['entity_subtype']],
                        bounding_box)
                    pedestrian.add_property_file('../models/entities/' + obj.name + '.' + self.mesh_file_type)
                    pedestrian.add_property('model_id','0')
                    if not pedestrian_catalog_file_created:
                        # Create new catalog with first pedestrian
                        pedestrian.dump_to_catalog(pedestrian_catalog_path,'PedestrianCatalog',
                            'DSC pedestrian catalog','Blender Driving Scenario Creator')
                        pedestrian_catalog_file_created = True
                    else:
                        pedestrian.append_to_catalog(pedestrian_catalog_path)
                else:
                    print('Unknown entity type:', obj['entity_type'])
                    self.report({'ERROR'}, 'Unknown entity type: {}'.format(obj['entity_type']))

    def export_mesh(self, file_path):
        '''
            Export a mesh to file
        '''
        if self.mesh_file_type == 'osgb':
            # Since Blender has no native .osgb support export .obj and then convert
            file_path_obj = file_path.with_suffix('.obj')
            file_path_mtl = file_path.with_suffix('.mtl')
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            bpy.ops.export_scene.obj(filepath=str(file_path_obj), check_existing=True,
                                     filter_glob='*.obj,*.mtl', use_selection=True, use_animation=False,
                                     use_mesh_modifiers=True, use_edges=True, use_smooth_groups=False,
                                     use_smooth_groups_bitflags=False, use_normals=True, use_uvs=True,
                                     use_materials=True, use_triangles=False, use_nurbs=False,
                                     use_vertex_groups=False, use_blen_objects=True, group_by_object=False,
                                     group_by_material=False, keep_vertex_order=False, global_scale=1.0,
                                     path_mode='RELATIVE', axis_forward='-Z', axis_up='Y')
            self.convert_to_osgb(file_path_obj)
            # Remove mtl and obj files
            file_path_obj.unlink()
            file_path_mtl.unlink()
        elif self.mesh_file_type == 'fbx':
            file_path = file_path.with_suffix('.fbx')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            bpy.ops.export_scene.fbx(filepath=str(file_path), check_existing=True, filter_glob='*.fbx',
                                     use_selection=True, use_active_collection=False, global_scale=1.0,
                                     apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                                     use_space_transform=True, bake_space_transform=False,
                                     object_types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'},
                                     use_mesh_modifiers=True, use_mesh_modifiers_render=True,
                                     mesh_smooth_type='OFF', use_subsurf=False, use_mesh_edges=False,
                                     use_tspace=False, use_custom_props=False, add_leaf_bones=True,
                                     primary_bone_axis='Y', secondary_bone_axis='X',
                                     use_armature_deform_only=False, armature_nodetype='NULL',
                                     bake_anim=True, bake_anim_use_all_bones=True,
                                     bake_anim_use_nla_strips=True, bake_anim_use_all_actions=True,
                                     bake_anim_force_startend_keying=True, bake_anim_step=1.0,
                                     bake_anim_simplify_factor=1.0, path_mode='AUTO',
                                     embed_textures=False, batch_mode='OFF', use_batch_own_dir=True,
                                     use_metadata=True, axis_forward='-Z', axis_up='Y')
        elif self.mesh_file_type == 'gltf' or self.mesh_file_type == 'glb':
            if self.mesh_file_type == 'glb':
                export_format = 'GLB'
                file_path = file_path.with_suffix('.glb')
            elif self.mesh_file_type == 'gltf':
                export_format = 'GLTF_EMBEDDED'
                file_path = file_path.with_suffix('.gltf')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            bpy.ops.export_scene.gltf(filepath=str(file_path), check_existing=True,
                                      export_format=export_format, ui_tab='GENERAL',
                                      export_copyright='Blender Driving Scenario Creator',
                                      export_image_format='AUTO', export_texture_dir='',
                                      export_keep_originals=False, export_texcoords=True,
                                      export_normals=True,
                                      export_draco_mesh_compression_enable=False,
                                      export_draco_mesh_compression_level=6,
                                      export_draco_position_quantization=14,
                                      export_draco_normal_quantization=10,
                                      export_draco_texcoord_quantization=12,
                                      export_draco_color_quantization=10,
                                      export_draco_generic_quantization=12,
                                      export_tangents=False, export_materials='EXPORT',
                                      export_original_specular=False, export_colors=True,
                                      use_mesh_edges=False, use_mesh_vertices=False,
                                      export_cameras=False, use_selection=True, use_visible=False,
                                      use_renderable=False, use_active_collection=False,
                                      use_active_scene=False, export_extras=False, export_yup=True,
                                      export_apply=False, export_animations=True,
                                      export_frame_range=True, export_frame_step=1,
                                      export_force_sampling=True, export_nla_strips=True,
                                      export_nla_strips_merged_animation_name='Animation',
                                      export_def_bones=False, export_optimize_animation_size=False,
                                      export_anim_single_armature=True, export_current_frame=False,
                                      export_skins=True, export_all_influences=False,
                                      export_morph=True, export_morph_normal=True,
                                      export_morph_tangent=False, export_lights=False,
                                      will_save_settings=False, filter_glob='*.glb;*.gltf')

    def convert_to_osgb(self, input_file_path):
        try:
            subprocess.run(['osgconv', str(input_file_path), str(input_file_path.with_suffix('.osgb'))])
        except FileNotFoundError:
            self.report({'ERROR'}, 'Executable \"osgconv\" required to produce .osgb scenegraph file. '
                'Try installing openscenegraph.')

    def export_openscenario(self):
        # OpenDRIVE (referenced by OpenSCENARIO)
        xodr_path = pathlib.Path(self.directory) / 'xodr' / (self.dsc_export_filename + '.xodr')
        xodr_path.parent.mkdir(parents=True, exist_ok=True)
        odr = xodr.OpenDrive('blender_dsc')
        roads = []
        # Create OpenDRIVE roads from object collection
        if helpers.collection_exists(['OpenDRIVE']):
            for obj in bpy.data.collections['OpenDRIVE'].objects:
                if obj.name.startswith('road'):
                    planview = xodr.PlanView()
                    planview.set_start_point(obj['geometry']['point_start'][0],
                        obj['geometry']['point_start'][1],obj['geometry']['heading_start'])
                    if obj['geometry']['curve'] == 'line':
                        geometry = xodr.Line(obj['geometry']['length'])
                    if obj['geometry']['curve'] == 'arc':
                        geometry = xodr.Arc(obj['geometry']['curvature_start'],
                            length=obj['geometry']['length'])
                    if obj['geometry']['curve'] == 'spiral':
                        geometry = xodr.Spiral(obj['geometry']['curvature_start'],
                            obj['geometry']['curvature_end'], length=obj['geometry']['length'])
                    planview.add_geometry(geometry)
                    lanes = self.create_lanes(obj)
                    road = xodr.Road(obj['id_odr'],planview,lanes)
                    self.add_elevation_profiles(obj, road)
                    # Add road level linking
                    if 'link_predecessor_id_l' in obj:
                        element_type = self.get_element_type_by_id(obj['link_predecessor_id_l'])
                        if obj['link_predecessor_cp_l'] == 'cp_start_l' or \
                            obj['link_predecessor_cp_l'] == 'cp_start_r':
                            cp_type = xodr.ContactPoint.start
                        elif obj['link_predecessor_cp_l'] == 'cp_end_l' or \
                                obj['link_predecessor_cp_l'] == 'cp_end_r':
                            cp_type = xodr.ContactPoint.end
                        else:
                            cp_type = None
                        if not 'id_direct_junction_start' in obj:
                            road.add_predecessor(element_type, obj['link_predecessor_id_l'], cp_type)
                    if 'link_predecessor_id_r' in obj:
                        element_type = self.get_element_type_by_id(obj['link_predecessor_id_r'])
                        if obj['link_predecessor_cp_r'] == 'cp_start_l' or \
                            obj['link_predecessor_cp_r'] == 'cp_start_r':
                            cp_type = xodr.ContactPoint.start
                        elif obj['link_predecessor_cp_r'] == 'cp_end_l' or \
                                obj['link_predecessor_cp_r'] == 'cp_end_r':
                            cp_type = xodr.ContactPoint.end
                        else:
                            cp_type = None
                        if not 'id_direct_junction_start' in obj:
                            road.add_predecessor(element_type, obj['link_predecessor_id_r'], cp_type)
                    if 'link_successor_id_l' in obj:
                        element_type = self.get_element_type_by_id(obj['link_successor_id_l'])
                        if obj['link_successor_cp_l'] == 'cp_start_l' or \
                            obj['link_successor_cp_l'] == 'cp_start_r':
                            cp_type = xodr.ContactPoint.start
                        elif obj['link_successor_cp_l'] == 'cp_end_l' or \
                                obj['link_successor_cp_l'] == 'cp_end_r':
                            cp_type = xodr.ContactPoint.end
                        else:
                            cp_type = None
                        if not 'id_direct_junction_end' in obj:
                            road.add_successor(element_type, obj['link_successor_id_l'], cp_type)
                    if 'link_successor_id_r' in obj:
                        element_type = self.get_element_type_by_id(obj['link_successor_id_r'])
                        if obj['link_successor_cp_r'] == 'cp_start_l' or \
                            obj['link_successor_cp_r'] == 'cp_start_r':
                            cp_type = xodr.ContactPoint.start
                        elif obj['link_successor_cp_r'] == 'cp_end_l' or \
                                obj['link_successor_cp_r'] == 'cp_end_r':
                            cp_type = xodr.ContactPoint.end
                        else:
                            cp_type = None
                        if not 'id_direct_junction_end' in obj:
                            road.add_successor(element_type, obj['link_successor_id_r'], cp_type)
                    if 'id_direct_junction_start' in obj:
                        # Connect to direction junction attached to the other (split) road
                        road.add_predecessor(xodr.ElementType.junction, obj['id_direct_junction_start'])
                    if 'id_direct_junction_end' in obj:
                        # Connect to direction junction attached to the other (split) road
                        road.add_successor(xodr.ElementType.junction, obj['id_direct_junction_end'])
                    print('Add road with ID', obj['id_odr'])
                    odr.add_road(road)
                    roads.append(road)
            # Now that all roads exist create direct junctions
            for obj in bpy.data.collections['OpenDRIVE'].objects:
                if obj.name.startswith('road'):
                    if obj['road_split_type'] != 'none':
                        if ('link_predecessor_id_l' in obj and 'link_predecessor_id_r' in obj) \
                                or ('link_successor_id_l' in obj and 'link_successor_id_r' in obj):
                            if obj['road_split_type'] == 'end':
                                junction_id = obj['id_direct_junction_end']
                                road_out_id_l = obj['link_successor_id_l']
                                road_out_cp_l = obj['link_successor_cp_l']
                                road_out_id_r = obj['link_successor_id_r']
                                road_out_cp_r = obj['link_successor_cp_r']
                                road_in_cp_l = 'cp_end_l'
                                road_in_cp_r = 'cp_end_r'
                            elif obj['road_split_type'] == 'start':
                                junction_id = obj['id_direct_junction_start']
                                road_out_id_l = obj['link_predecessor_id_l']
                                road_out_cp_l = obj['link_predecessor_cp_l']
                                road_out_id_r = obj['link_predecessor_id_r']
                                road_out_cp_r = obj['link_predecessor_cp_r']
                                road_in_cp_l = 'cp_start_l'
                                road_in_cp_r = 'cp_start_r'
                            dj_creator = xodr.DirectJunctionCreator(id=junction_id,
                                name='direct_junction_' + str(junction_id))
                            road_obj_in = helpers.get_object_xodr_by_id(obj['id_odr'])
                            road_obj_out_l = helpers.get_object_xodr_by_id(road_out_id_l)
                            road_obj_out_r = helpers.get_object_xodr_by_id(road_out_id_r)
                            lane_ids_road_in_l, lane_ids_road_out_l = \
                                self.get_lanes_ids_to_link(road_obj_in, road_in_cp_l, road_obj_out_l, road_out_cp_l)
                            lane_ids_road_in_r, lane_ids_road_out_r = \
                                self.get_lanes_ids_to_link(road_obj_in, road_in_cp_r, road_obj_out_r, road_out_cp_r)
                            road_in = self.get_road_by_id(roads, obj['id_odr'])
                            road_out_l = self.get_road_by_id(roads, road_out_id_l)
                            road_out_r = self.get_road_by_id(roads, road_out_id_r)
                            dj_creator.add_connection(road_in, road_out_l, lane_ids_road_in_l, lane_ids_road_out_l)
                            dj_creator.add_connection(road_in, road_out_r, lane_ids_road_in_r, lane_ids_road_out_r)
                            odr.add_junction(dj_creator.junction)
                        else:
                            self.report({'ERROR'}, 'Export of direct junction connected to road with ID {}'
                                ' failed due to missing connection.'.format(obj['id_odr']))
        # Add lane level linking for all roads
        self.link_lanes(roads)
        # Create OpenDRIVE junctions from object collection
        num_junctions = 0
        if helpers.collection_exists(['OpenDRIVE']):
            for obj in bpy.data.collections['OpenDRIVE'].objects:
                # Export generic junctions
                if obj.name.startswith('junction_area'):
                    incoming_roads = []
                    junction_id = obj['id_odr']
                    for joint in obj['joints']:
                        inc_road = xodr.get_road_by_id(roads, joint['id_incoming'])
                        if(inc_road != None):
                            incoming_roads.append(inc_road)
                        else:
                            self.report({'WARNING'}, 'Junction with ID {}'
                            ' is missing a connection.'.format(obj['id_odr']))
                    # Find and export connecting roads of this junction
                    junction_roads = []
                    for obj_jcr in bpy.data.collections['OpenDRIVE'].objects:
                        if obj_jcr.name.startswith('junction_connecting_road'):
                            if obj_jcr['id_junction'] == junction_id:
                                if 'link_predecessor_id_l' in obj_jcr and 'link_successor_id_l' in obj_jcr:
                                    # Create a junction connecting road
                                    # TODO for now we use a single spiral, later we should use arc - spiral - arc
                                    planview = xodr.PlanView()
                                    planview.set_start_point(obj_jcr['geometry']['point_start'][0],
                                        obj_jcr['geometry']['point_start'][1],obj_jcr['geometry']['heading_start'])
                                    geometry = xodr.Spiral(obj_jcr['geometry']['curvature_start'],
                                        obj_jcr['geometry']['curvature_end'], length=obj_jcr['geometry']['length'])
                                    planview.add_geometry(geometry)
                                    lanes = self.create_lanes(obj_jcr)
                                    road = xodr.Road(obj_jcr['id_odr'],planview,lanes, road_type=junction_id)
                                    self.add_elevation_profiles(obj_jcr, road)
                                    # Connect the junction connecting road to incoming and connecting roads
                                    incoming_road = self.get_road_by_id(roads, obj_jcr['link_predecessor_id_l'])
                                    contact_point = mapping_contact_point[obj_jcr['link_predecessor_cp_l']]
                                    road.add_predecessor(xodr.ElementType.road, incoming_road.id, contact_point)
                                    xodr.create_lane_links(road, incoming_road)
                                    incoming_road = self.get_road_by_id(roads, obj_jcr['link_successor_id_l'])
                                    contact_point = mapping_contact_point[obj_jcr['link_successor_cp_l']]
                                    road.add_successor(xodr.ElementType.road, incoming_road.id, contact_point)
                                    xodr.create_lane_links(road, incoming_road)
                                    junction_roads.append(road)
                                    # Create lane links with incoming roads
                    # Finally create the junction
                    junction = xodr.create_junction(
                        junction_roads, junction_id, incoming_roads, 'junction_' + str(junction_id))
                    num_junctions += 1
                    print('Add junction with ID', junction_id)
                    odr.add_junction(junction)
                    # Junction connecting roads also need to be registered as "normal" roads
                    for road in junction_roads:
                        odr.add_road(road)
        odr.adjust_startpoints()
        odr.write_xml(str(xodr_path))

        # OpenSCENARIO
        xosc_path = pathlib.Path(self.directory) / 'xosc' / (self.dsc_export_filename + '.xosc')
        xosc_path.parent.mkdir(parents=True, exist_ok=True)
        init = xosc.Init()
        entities = xosc.Entities()
        if helpers.collection_exists(['OpenSCENARIO','entities']):
            for obj in bpy.data.collections['OpenSCENARIO'].children['entities'].objects:
                if 'dsc_type' in obj and obj['dsc_type'] == 'entity':
                    entity_name = obj.name
                    print('Add entity with name', obj.name)
                    if obj['entity_type'] == 'vehicle':
                        catalog = 'VehicleCatalog'
                    elif obj['entity_type'] == 'pedestrian':
                        catalog = 'PedestrianCatalog'
                    else:
                        self.report({'ERROR'}, 'Unknown entity type {}'.format(obj['dsc_type']))
                    entities.add_scenario_object(entity_name,xosc.CatalogReference(catalog, entity_name))
                    # Teleport to initial position
                    init.add_init_action(entity_name,
                        xosc.TeleportAction(
                            xosc.WorldPosition(
                                x=obj['position'][0], y=obj['position'][1], z=obj['position'][2], h=obj['hdg'])))
                    # Get pitch and roll from road
                    init.add_init_action(entity_name,
                        xosc.TeleportAction(
                            xosc.RelativeRoadPosition(0, 0, entity_name,
                                xosc.Orientation(h=obj['hdg'], p=0, r=0, reference=xosc.ReferenceContext.absolute))))
                    # Begin driving/walking
                    init.add_init_action(entity_name,
                        xosc.AbsoluteSpeedAction(helpers.kmh_to_ms(obj['speed_initial']),
                            xosc.TransitionDynamics(xosc.DynamicsShapes.step,
                                                    xosc.DynamicsDimension.time, 1)))
                    # Center on closest lane
                    init.add_init_action(entity_name,
                        xosc.RelativeLaneChangeAction(0, entity_name,
                            xosc.TransitionDynamics(xosc.DynamicsShapes.cubic,
                                                    xosc.DynamicsDimension.rate, 2.0)))
        if helpers.collection_exists(['OpenSCENARIO','trajectories']):
            for obj in bpy.data.collections['OpenSCENARIO'].children['trajectories'].objects:
                if 'dsc_type' in obj and obj['dsc_type'] == 'trajectory':
                    if obj['dsc_subtype'] == 'polyline':
                        speed_kmh = helpers.get_obj_custom_property('OpenSCENARIO', 'entities',
                            obj['owner_name'], 'speed_initial')
                        if speed_kmh == None:
                            self.report({'ERROR'}, 'Trajectory ' + obj.name + ' owner not found!')
                            break
                        times, positions = self.calculate_trajectory_values(obj, helpers.kmh_to_ms(speed_kmh))
                        shape = xosc.Polyline(times, positions)
                    if obj['dsc_subtype'] == 'nurbs':
                        order = obj.data.splines[0].order_u
                        num_control_points = len(obj.data.splines[0].points)
                        shape = xosc.Nurbs(order)
                        for point in obj.data.splines[0].points:
                            point_global = obj.matrix_world @ point.co
                            control_point = xosc.ControlPoint(
                                xosc.WorldPosition(point_global.x, point_global.y, point_global.z))
                            shape.add_control_point(control_point)
                        knots = []
                        u = 0
                        for idx in range(order + num_control_points):
                            if idx >= order and idx <= num_control_points:
                                u += 1
                            knots.append(u)
                        shape.add_knots(knots)
                    trajectory = xosc.Trajectory(obj.name,False)
                    trajectory.add_shape(shape)
                    action = xosc.FollowTrajectoryAction(trajectory,xosc.FollowingMode.follow,
                        None,None,None,None)
                    init.add_init_action(obj['owner_name'], action)
                    # FIXME the following does not seem to work with esmini in
                    # init, we need a separate maneuver group/act
                    # # After trajectory following get pitch and roll from road
                    # init.add_init_action(entity_name,
                    #     xosc.TeleportAction(
                    #         xosc.RelativeRoadPosition(0, 0, entity_name,
                    #             xosc.Orientation(p=0, r=0, reference=xosc.ReferenceContext.relative))))
                    # # Finally center on closest lane
                    # init.add_init_action(entity_name,
                    #     xosc.RelativeLaneChangeAction(0, entity_name,
                    #         xosc.TransitionDynamics(xosc.DynamicsShapes.cubic,
                    #                                 xosc.DynamicsDimension.rate, 2.0)))

        # Link .xodr to .xosc with relative path
        dotdot = pathlib.Path('..')
        xodr_path_relative = dotdot / xodr_path.relative_to(pathlib.Path(self.directory))
        static_scene_model_path_relative = dotdot / 'models' / 'static_scene' \
            / str('bdsc_export.' + self.mesh_file_type)
        # static_scene_model_path_relative.with_suffix(self.mesh_file_type)
        if helpers.collection_exists(['OpenDRIVE']):
            road_network = xosc.RoadNetwork(str(xodr_path_relative), str(static_scene_model_path_relative))
        else:
            road_network = xosc.RoadNetwork(str(xodr_path_relative))

        storyboard = xosc.StoryBoard(init)
        catalogs = xosc.Catalog()
        catalogs.add_catalog('VehicleCatalog','../catalogs/vehicles')
        catalogs.add_catalog('PedestrianCatalog','../catalogs/pedestrians')
        scenario = xosc.Scenario('dsc_scenario','blender_dsc',xosc.ParameterDeclarations(),
            entities,storyboard,road_network,catalogs)
        scenario.write_xml(str(xosc_path))

    def get_element_type_by_id(self, id):
        '''
            Return element type of an OpenDRIVE element with given ID
        '''
        for obj in bpy.data.collections['OpenDRIVE'].objects:
            if obj.name.startswith('road'):
                if obj['id_odr'] == id:
                    return xodr.ElementType.road
            elif obj.name.startswith('junction'):
                if obj['id_odr'] == id:
                    return xodr.ElementType.junction
            elif obj.name.startswith('direct_junction'):
                if obj['id_odr'] == id:
                    return xodr.ElementType.junction

    def get_road_by_id(self, roads, id):
        '''
            Return road with given ID
        '''
        for road in roads:
            if road.id == id:
                return road
        print('WARNING: No road with ID {} found. Maybe a junction?'.format(id))
        return None

    def get_road_mark(self, marking_type, weight, color):
        '''
            Return road mark based on object lane parameters.
        '''
        if marking_type == 'none':
            # Make sure to not set a 'none' weight or color
            return xodr.RoadMark(mapping_road_mark_type['none'])
        else:
            return xodr.RoadMark(marking_type=mapping_road_mark_type[marking_type],
                                 color=mapping_road_mark_color[color],
                                 marking_weight=mapping_road_mark_weight[weight])

    def create_lanes(self, obj):
        lanes = xodr.Lanes()
        road_mark = self.get_road_mark(obj['lane_center_road_mark_type'],
                                       obj['lane_center_road_mark_weight'],
                                       obj['lane_center_road_mark_color'])
        lane_center = xodr.standard_lane(rm=road_mark)
        lane_center.add_roadmark
        lanesection = xodr.LaneSection(0,lane_center)
        for idx in range(obj['lanes_left_num']):
            a,b,c,d = self.get_lane_width_coefficients(obj['lanes_left_widths'][idx],
                obj['lanes_left_widths_change'][idx], obj['geometry']['length'])
            lane = xodr.Lane(lane_type=mapping_lane_type[obj['lanes_left_types'][idx]],
                a=a, b=b, c=c, d=d)
            road_mark = self.get_road_mark(obj['lanes_left_road_mark_types'][idx],
                                           obj['lanes_left_road_mark_weights'][idx],
                                           obj['lanes_left_road_mark_colors'][idx])
            lane.add_roadmark(road_mark)
            lanesection.add_left_lane(lane)
        for idx in range(obj['lanes_right_num']):
            a,b,c,d = self.get_lane_width_coefficients(obj['lanes_right_widths'][idx],
                obj['lanes_right_widths_change'][idx], obj['geometry']['length'])
            lane = xodr.Lane(lane_type=mapping_lane_type[obj['lanes_right_types'][idx]],
                a=a, b=b, c=c, d=d)
            road_mark = self.get_road_mark(obj['lanes_right_road_mark_types'][idx],
                                           obj['lanes_right_road_mark_weights'][idx],
                                           obj['lanes_right_road_mark_colors'][idx])
            lane.add_roadmark(road_mark)
            lanesection.add_right_lane(lane)
        lanes.add_lanesection(lanesection)

        return lanes

    def get_lane_width_coefficients(self, lane_width, width_change, length_road):
        '''
            Return coefficients a, b, c, d for lane width polynomial
        '''
        if width_change == 'open':
            a=0.0
            b=0.0
            c=3.0 / length_road**2 * lane_width
            d=-2.0 / length_road**3 * lane_width
        elif width_change == 'close':
            a=lane_width
            b=0.0
            c=-3.0 / length_road**2 * lane_width
            d=2.0 / length_road**3 * lane_width
        else:
            a=lane_width
            b=0.0
            c=0.0
            d=0.0
        return a, b, c, d

    def link_lanes(self, roads):
        '''
            Create lane links for all roads.
        '''
        # TODO: Improve performance by exploiting symmetry, e.g., check for existing links
        for road in roads:
            road_obj = helpers.get_object_xodr_by_id(road.id)
            if road.predecessor:
                road_pre = self.get_road_by_id(roads, road.predecessor.element_id)
                if road_pre:
                    road_obj_pre = helpers.get_object_xodr_by_id(road.predecessor.element_id)
                    # Check if we are connected to beginning or end of the other road
                    if road_obj['link_predecessor_cp_l'] == 'cp_start_l':
                        lane_ids_road, lanes_ids_road_pre = \
                            self.get_lanes_ids_to_link(road_obj, 'cp_start_l', road_obj_pre, 'cp_start_l')
                    elif road_obj['link_predecessor_cp_l'] == 'cp_end_l':
                        lane_ids_road, lanes_ids_road_pre = \
                            self.get_lanes_ids_to_link(road_obj, 'cp_start_l', road_obj_pre, 'cp_end_l')
                    xodr.create_lane_links_from_ids(road, road_pre, lane_ids_road, lanes_ids_road_pre)
            if road.successor:
                road_suc = self.get_road_by_id(roads, road.successor.element_id)
                if road_suc:
                    road_obj_suc = helpers.get_object_xodr_by_id(road.successor.element_id)
                    # Check if we are connected to beginning or end of the other road
                    if road_obj['link_successor_cp_l'] == 'cp_start_l':
                        lane_ids_road, lanes_ids_road_suc = \
                            self.get_lanes_ids_to_link(road_obj, 'cp_end_l', road_obj_suc, 'cp_start_l')
                    elif road_obj['link_successor_cp_l'] == 'cp_end_l':
                        lane_ids_road, lanes_ids_road_suc = \
                            self.get_lanes_ids_to_link(road_obj, 'cp_end_l', road_obj_suc, 'cp_end_l')
                    xodr.create_lane_links_from_ids(road, road_suc, lane_ids_road, lanes_ids_road_suc)

    def get_non_zero_lane_ids(self, road_obj, cp_type):
        '''
            Return the non zero width lane ids for a road's end.
        '''
        non_zero_lane_idxs = []
        # Go through left lanes
        for lane_idx in range(road_obj['lanes_left_num']):
            if cp_type == 'cp_end_l' or cp_type == 'cp_end_r':
                if road_obj['lanes_left_widths_change'][lane_idx] != 'close':
                    non_zero_lane_idxs.append(road_obj['lanes_left_num']-lane_idx)
            if cp_type == 'cp_start_l' or cp_type == 'cp_start_r':
                if road_obj['lanes_left_widths_change'][lane_idx] != 'open':
                    non_zero_lane_idxs.append(road_obj['lanes_left_num']-lane_idx)
        # Go through right lanes
        for lane_idx in range(road_obj['lanes_right_num']):
            if cp_type == 'cp_end_l' or cp_type == 'cp_end_r':
                if road_obj['lanes_right_widths_change'][lane_idx] != 'close':
                    non_zero_lane_idxs.append(-lane_idx-1)
            if cp_type == 'cp_start_l' or cp_type == 'cp_start_r':
                if road_obj['lanes_right_widths_change'][lane_idx] != 'open':
                    non_zero_lane_idxs.append(-lane_idx-1)
        return non_zero_lane_idxs

    def match_lane_ids(self, non_zero_lane_ids_in, pair_id, non_zero_lane_ids_out, heads_on):
        '''
            Match lane ids between two roads with potentially unequal number of
            lane IDs, based on a known pair. The pair_id can not be a lane with
            non-zero width except for the center lane (ID=0).
        '''
        # Find index of pair elements
        if pair_id == 0:
            if -1 in non_zero_lane_ids_in:
                pair_idx_in = non_zero_lane_ids_in.index(-1)
            else:
                pair_idx_in = non_zero_lane_ids_in.index(1)
            if heads_on:
                # Take reverse lane links into account
                if -1 in non_zero_lane_ids_out:
                    pair_idx_out = non_zero_lane_ids_out.index(1)
                else:
                    pair_idx_out = non_zero_lane_ids_out.index(-1)
            else:
                if -1 in non_zero_lane_ids_out:
                    pair_idx_out = non_zero_lane_ids_out.index(-1)
                else:
                    pair_idx_out = non_zero_lane_ids_out.index(1)
        else:
            pair_idx_in = non_zero_lane_ids_in.index(pair_id)
            # For the out road use the left most 1 or -1 lane
            if -1 in non_zero_lane_ids_out:
                idx_minus_one = non_zero_lane_ids_out.index(-1)
                if 1 in non_zero_lane_ids_out:
                    idx_one = non_zero_lane_ids_out.index(1)
                    if idx_minus_one < idx_one:
                        pair_idx_out = idx_minus_one
                    else:
                        pair_idx_out = idx_one
                else:
                    pair_idx_out = idx_minus_one
            else:
                pair_idx_out = non_zero_lane_ids_out.index(1)
        # Calculate how many IDs to pair on each side
        if (pair_idx_in - pair_idx_out) > 0:
            pair_num_left = pair_idx_out
        else:
            pair_num_left = pair_idx_in
        num_right_ids_in = len(non_zero_lane_ids_in) - pair_idx_in
        num_right_ids_out = len(non_zero_lane_ids_out) - pair_idx_out
        if num_right_ids_in > num_right_ids_out:
            pair_num_right = num_right_ids_out
        else:
            pair_num_right = num_right_ids_in
        # Pair lanes
        lane_ids_in = non_zero_lane_ids_in[pair_idx_in-pair_num_left:pair_idx_in]
        lane_ids_out = non_zero_lane_ids_out[pair_idx_out-pair_num_left:pair_idx_out]
        lane_ids_in.extend(non_zero_lane_ids_in[pair_idx_in:pair_idx_in+pair_num_right])
        lane_ids_out.extend(non_zero_lane_ids_out[pair_idx_out:pair_idx_out+pair_num_right])
        return lane_ids_in, lane_ids_out

    def get_lanes_ids_to_link(self, road_obj_in, cp_type_in, road_obj_out, cp_type_out):
        '''
            Get the lane IDs with non-zero lane width which should be linked.
            Pair non-split roads based on center lane. If a split road is given
            assume it is the "in" road. Split roads are either paired based on
            center lane or based on split lane index. Split to split connections
            are currently not supported.
        '''
        non_zero_lane_ids_in = self.get_non_zero_lane_ids(road_obj_in, cp_type_in)
        non_zero_lane_ids_out = self.get_non_zero_lane_ids(road_obj_out, cp_type_out)

        # If roads are connected heads on flip road out lanes
        if (cp_type_in.startswith('cp_start') and cp_type_out.startswith('cp_start')) or \
           (cp_type_in.startswith('cp_end') and cp_type_out.startswith('cp_end')):
            non_zero_lane_ids_out.reverse()
            heads_on = True
        else:
            heads_on = False

        # Set pair ID for non split roads (center lane matching)
        pair_id = 0
        # Check if road is split and pairing is not with center lane
        if road_obj_in['road_split_type'] == 'start' and cp_type_in.startswith('cp_start') \
            or road_obj_in['road_split_type'] == 'end' and cp_type_in.startswith('cp_end'):
            # Check if pair lane is the center lane or towards the right
            if cp_type_in == 'cp_end_l' or cp_type_in == 'cp_start_l':
                if road_obj_in['lanes_left_num'] >= road_obj_in['road_split_lane_idx']:
                    pair_id = road_obj_in['lanes_right_num'] - road_obj_in['road_split_lane_idx']
            elif cp_type_in == 'cp_end_r' or cp_type_in == 'cp_start_r':
                if road_obj_in['lanes_left_num'] < road_obj_in['road_split_lane_idx']:
                    pair_id = -(road_obj_in['road_split_lane_idx']-road_obj_in['lanes_left_num'])
        ids_in, ids_out = self.match_lane_ids(non_zero_lane_ids_in, pair_id,
            non_zero_lane_ids_out, heads_on)
        return [ids_in, ids_out]

    def calculate_trajectory_values(self, obj, speed):
        times = [0]
        for idx in range(len(obj.data.vertices)-1):
            distance = (obj.data.vertices[idx].co - obj.data.vertices[idx+1].co).length
            times.append(times[idx] + distance/speed)
        positions = []
        for idx, vert in enumerate(obj.data.vertices):
            vert_global = obj.matrix_world @ vert.co
            if idx == 0:
                vert_global_next = obj.matrix_world @ obj.data.vertices[idx+1].co
                vec_hdg_after = Vector(vert_global_next - vert_global)
                heading = vec_hdg_after.to_2d().angle_signed(Vector((1.0, 0.0)))
            elif idx < len(obj.data.vertices)-1:
                vert_global_next = obj.matrix_world @ obj.data.vertices[idx+1].co
                vert_global_last = obj.matrix_world @ obj.data.vertices[idx-1].co
                vec_hdg_before = Vector(vert_global - vert_global_last)
                vec_hdg_after = Vector(vert_global_next - vert_global)
                vec_avg = vec_hdg_before + vec_hdg_after
                if vec_avg.length == 0:
                    heading = vec_hdg_after.to_2d().angle_signed(Vector((1.0, 0.0)))
                else:
                    heading = (vec_hdg_before + vec_hdg_after).to_2d().angle_signed(Vector((1.0, 0.0)))
            else:
                vert_global_last = obj.matrix_world @ obj.data.vertices[idx-1].co
                vec_hdg_before = Vector(vert_global - vert_global_last)
                heading = vec_hdg_before.to_2d().angle_signed(Vector((1.0, 0.0)))
            positions.append(xosc.WorldPosition(vert_global.x, vert_global.y, vert_global.z, heading))
        return times, positions

    def add_elevation_profiles(self, obj, road):
        '''
            Add elevation profiles to road
        '''
        z_global = obj['geometry']['point_start'][2]
        for profile in obj['geometry']['elevation']:
            # Shift each elevation profile to start at s=0 (use substitution)
            # SageMath code:
            #   sage: s, a, b, c, d, h, shift = var('s, a, b, c, d, h, shift');
            #   sage: eq = (a + b * s + c * s^2 + d * s^3 == h);
            #   sage: eq.substitute(s=s+shift).expand()
            shift = profile['s']
            a = profile['a'] + z_global
            b = profile['b']
            c = profile['c']
            d = profile['d']
            a_shifted = a + b * shift + c * shift**2 + d * shift**3
            b_shifted = b + 2 * c * shift + 3 * d * shift**2
            c_shifted = c + 3 * d * shift
            d_shifted = d
            road.add_elevation(profile['s'], a_shifted, b_shifted, c_shifted, d_shifted)

    def add_junction_roads_elevation(self, junction_roads, elevation_level):
        for road in junction_roads:
            road.add_elevation(s=0, a=elevation_level, b=0, c=0, d=0)

    def add_junction_roads_connections_4way(self, incoming_roads, junction_roads, junction_id):
        '''
            Connectin all incoming roads with each other
        '''
        i = 0
        for j in range(len(incoming_roads) - 1):
            for k in range(j + 1, len(incoming_roads)):
                # FIXME this will create problems when a single road is
                # connected to a junction twice
                if incoming_roads[j].predecessor:
                    if incoming_roads[j].predecessor.element_id == junction_id:
                        cp_type_j = xodr.ContactPoint.start
                if incoming_roads[j].successor:
                    if incoming_roads[j].successor.element_id == junction_id:
                        cp_type_j = xodr.ContactPoint.end
                if incoming_roads[k].predecessor:
                    if incoming_roads[k].predecessor.element_id == junction_id:
                        cp_type_k = xodr.ContactPoint.start
                if incoming_roads[k].successor:
                    if incoming_roads[k].successor.element_id == junction_id:
                        cp_type_k = xodr.ContactPoint.end
                # Link incoming with connecting road
                junction_roads[i].add_predecessor(
                    xodr.ElementType.road, incoming_roads[j].id, cp_type_j)
                # FIXME is redundant lane linking needed?
                xodr.create_lane_links(junction_roads[i], incoming_roads[j])
                junction_roads[i].add_successor(
                    xodr.ElementType.road, incoming_roads[k].id, cp_type_k)
                # FIXME is redundant lane linking needed?
                xodr.create_lane_links(junction_roads[i], incoming_roads[k])
                i += 1

    def get_lane_offset(self, road_obj, id_split_road):
        '''
            Return lane offset of road connected to the split road via direct
            junction.
        '''
        for obj_split in bpy.data.collections['OpenDRIVE'].objects:
            if obj_split.name.startswith('road'):
                if obj_split['id_odr'] == id_split_road:
                    if obj_split['link_successor_id_l'] == road_obj['id_odr']:
                        if obj_split['road_split_lane_idx'] < obj_split['lanes_left_num'] + 1:
                            lane_offset = obj_split['lanes_left_num'] - obj_split['road_split_lane_idx'] + 1
                        else:
                            lane_offset = obj_split['lanes_left_num'] - obj_split['road_split_lane_idx']
                    elif obj_split['link_successor_id_r'] == road_obj['id_odr']:
                        # Remove center lane if necessary
                        if obj_split['road_split_lane_idx'] > obj_split['lanes_left_num'] + 1:
                            lane_offset = obj_split['lanes_left_num'] - obj_split['road_split_lane_idx']
                        else:
                            lane_offset = obj_split['lanes_left_num'] - obj_split['road_split_lane_idx'] - 1
                    return lane_offset
