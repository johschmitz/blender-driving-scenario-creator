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
from scenariogeneration import ScenarioGenerator

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

mapping_object_type = {
    'car': xosc.VehicleCategory.car,
}

class DSC_OT_export(bpy.types.Operator):
    bl_idname = 'dsc.export_driving_scenario'
    bl_label = 'Export driving scenario'
    bl_description = 'Export driving scenario as OpenDRIVE, OpenSCENARIO and Mesh (e.g. OSGB, FBX, glTF 2.0)'

    directory: bpy.props.StringProperty(
        name='Export directory', description='Target directory for export.')

    mesh_file_type : bpy.props.EnumProperty(
        items=(('fbx', '.fbx', '', 0),
               ('gltf', '.gltf', '', 1),
               ('osgb', '.osgb', '', 2),
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
        self.export_vehicle_models(context)
        self.export_scenegraph_file()
        self.export_openscenario()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def export_scenegraph_file(self):
        '''
            Export the scene mesh to file
        '''
        file_path = pathlib.Path(self.directory) / 'scenegraph' / 'export.suffix'
        file_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.object.select_all(action='SELECT')
        if helpers.collection_exists(['OpenSCENARIO']):
            for obj in bpy.data.collections['OpenSCENARIO'].objects:
                obj.select_set(False)
            for child in bpy.data.collections['OpenSCENARIO'].children:
                for obj in child.objects:
                    obj.select_set(False)
        self.export_mesh(file_path)
        bpy.ops.object.select_all(action='DESELECT')

    def export_vehicle_models(self, context):
        '''
            Export vehicle models to files.
        '''
        model_dir = pathlib.Path(self.directory) / 'models' / 'car.obj'
        model_dir.parent.mkdir(parents=True, exist_ok=True)
        catalog_path = pathlib.Path(self.directory) / 'catalogs' / 'vehicles' / 'VehicleCatalog.xosc'
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        # Select a car
        bpy.ops.object.select_all(action='DESELECT')
        if helpers.collection_exists(['OpenSCENARIO','dynamic_objects']):
            catalog_file_created = False
            for obj in bpy.data.collections['OpenSCENARIO'].children['dynamic_objects'].objects:
                print('Export object model for', obj.name)
                model_path = pathlib.Path(self.directory) / 'models' / str(obj.name + '.obj')
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
                # Add vehicle to vehicle catalog
                # TODO store in and read parameters from object
                bounding_box = xosc.BoundingBox(2,5,1.8,2.0,0,0.9)
                axle_front = xosc.Axle(0.523599,0.8,1.554,2.98,0.4)
                axle_rear = xosc.Axle(0,0.8,1.525,0,0.4)
                car = xosc.Vehicle(obj.name,mapping_object_type[obj['dsc_type']],
                    bounding_box,axle_front,axle_rear,69,10,10)
                car.add_property_file('../models/' + obj.name + '.' + self.mesh_file_type)
                car.add_property('control','internal')
                car.add_property('model_id','0')
                if not catalog_file_created:
                    # Create new catalog with first vehicle
                    car.dump_to_catalog(catalog_path,'VehicleCatalog',
                        'DSC vehicle catalog','Blender Driving Scenario Creator')
                    catalog_file_created = True
                else:
                    car.append_to_catalog(catalog_path)

    def export_mesh(self, file_path):
        '''
            Export a mesh to file
        '''
        if self.mesh_file_type == 'osgb':
            # Since Blender has no native .osgb support export .obj and then convert
            file_path = file_path.with_suffix('.obj')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            bpy.ops.export_scene.obj(filepath=str(file_path), check_existing=True,
                                     filter_glob='*.obj,*.mtl', use_selection=True, use_animation=False,
                                     use_mesh_modifiers=True, use_edges=True, use_smooth_groups=False,
                                     use_smooth_groups_bitflags=False, use_normals=True, use_uvs=True,
                                     use_materials=True, use_triangles=False, use_nurbs=False,
                                     use_vertex_groups=False, use_blen_objects=True, group_by_object=False,
                                     group_by_material=False, keep_vertex_order=False, global_scale=1.0,
                                     path_mode='RELATIVE', axis_forward='-Z', axis_up='Y')
            self.convert_to_osgb(file_path)
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
        elif self.mesh_file_type == 'gltf':
            file_path = file_path.with_suffix('.gltf')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            bpy.ops.export_scene.gltf(filepath=str(file_path), check_existing=True,
                                      export_format='GLTF_EMBEDDED', ui_tab='GENERAL', export_copyright='',
                                      export_image_format='AUTO', export_texture_dir='',
                                      export_texcoords=True, export_normals=True,
                                      export_draco_mesh_compression_enable=False,
                                      export_draco_mesh_compression_level=6,
                                      export_draco_position_quantization=14,
                                      export_draco_normal_quantization=10,
                                      export_draco_texcoord_quantization=12,
                                      export_draco_color_quantization=10,
                                      export_draco_generic_quantization=12, export_tangents=False,
                                      export_materials='EXPORT', export_colors=True, use_mesh_edges=False,
                                      use_mesh_vertices=False, export_cameras=False, export_selected=False,
                                      use_selection=True, use_visible=False, use_renderable=False,
                                      use_active_collection=False, export_extras=False, export_yup=True,
                                      export_apply=False, export_animations=True, export_frame_range=True,
                                      export_frame_step=1, export_force_sampling=True,
                                      export_nla_strips=True, export_def_bones=False,
                                      export_current_frame=False, export_skins=True,
                                      export_all_influences=False, export_morph=True,
                                      export_morph_normal=True, export_morph_tangent=False,
                                      export_lights=False, export_displacement=False,
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
                    road = xodr.Road(obj['id_xodr'],planview,lanes)
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
                        if 'id_xodr_direct_junction_start' in obj:
                            # Connect to direction junction attached to the other (split) road
                            lane_offset = self.get_lane_offset(obj,obj['link_predecessor_id_l'])
                            road.add_predecessor(xodr.ElementType.junction, obj['id_xodr_direct_junction_start'],
                                cp_type, lane_offset, direct_junction=[obj['link_predecessor_id_l']])
                        else:
                            road.add_predecessor(element_type, obj['link_predecessor_id_l'], cp_type)
                    if 'link_successor_id_l' in obj:
                        if obj['road_split_type'] != 'none':
                            # Attach to direct junction from the split road
                            road.add_successor(xodr.ElementType.junction, obj['id_xodr_direct_junction_end'],
                                direct_junction=[obj['link_successor_id_l'], obj['link_successor_id_r']])
                        else:
                            # TODO also make it work for predecessors
                            element_type = self.get_element_type_by_id(obj['link_successor_id_l'])
                            if obj['link_successor_cp_l'] == 'cp_start_l' or \
                                obj['link_successor_cp_l'] == 'cp_start_r':
                                cp_type = xodr.ContactPoint.start
                            elif obj['link_successor_cp_l'] == 'cp_end_l' or \
                                    obj['link_successor_cp_l'] == 'cp_end_r':
                                cp_type = xodr.ContactPoint.end
                            else:
                                cp_type = None
                            if 'id_xodr_direct_junction_end' in obj:
                                # Connect to direction junction attached to the other (split) road
                                lane_offset = self.get_lane_offset(obj,obj['link_successor_id_l'])
                                road.add_successor(xodr.ElementType.junction, obj['id_xodr_direct_junction_end'],
                                    cp_type, lane_offset, direct_junction=[obj['link_successor_id_l']])
                            else:
                                road.add_successor(element_type, obj['link_successor_id_l'], cp_type)
                    print('Add road with ID', obj['id_xodr'])
                    odr.add_road(road)
                    roads.append(road)
            # Now that all roads exist create direct junctions
            for obj in bpy.data.collections['OpenDRIVE'].objects:
                if obj.name.startswith('road'):
                    if obj['road_split_type'] != 'none':
                        if 'link_successor_id_l' in obj and 'link_successor_id_r' in obj:
                            road_in = self.get_road_by_id(roads, obj['id_xodr'])
                            road_out_l = self.get_road_by_id(roads, obj['link_successor_id_l'])
                            road_out_r = self.get_road_by_id(roads, obj['link_successor_id_r'])
                            direct_junction = xodr.create_direct_junction(
                                [road_in, road_out_l, road_out_r],
                                id=obj['id_xodr_direct_junction_end'],
                                name='direct_junction_'+str(obj['id_xodr_direct_junction_end']))
                            odr.add_junction(direct_junction)
                        else:
                            print('WARNING: Direct junction of road with ID {} not fully connected.'.format(obj['id_xodr']))
        # Add lane level linking for all roads
        self.link_lanes(roads)
        # Create OpenDRIVE junctions from object collection
        num_junctions = 0
        if helpers.collection_exists(['OpenDRIVE']):
            for obj in bpy.data.collections['OpenDRIVE'].objects:
                if obj.name.startswith('junction'):
                    if not len(obj['incoming_roads']) == 4:
                        self.report({'ERROR'}, 'Junction must have 4 connected roads.')
                        break
                    incoming_roads = []
                    angles = []
                    junction_id = obj['id_xodr']
                    # Create junction roads based on incoming road angles (simple 4-way for now)
                    for idx in range(4):
                        angles.append(idx * 2 * pi / len(obj['incoming_roads']))
                    # 0 angle road must point in 'right' direction
                    incoming_roads.append(xodr.get_road_by_id(roads, obj['incoming_roads']['cp_right']))
                    incoming_roads.append(xodr.get_road_by_id(roads, obj['incoming_roads']['cp_up']))
                    incoming_roads.append(xodr.get_road_by_id(roads, obj['incoming_roads']['cp_left']))
                    incoming_roads.append(xodr.get_road_by_id(roads, obj['incoming_roads']['cp_down']))
                    # Create connecting roads and link them to incoming roads
                    junction_roads = xodr.create_junction_roads_standalone(angles, 3.75, junction_id,
                        spiral_part=0.01, arc_part=0.99, startnum=1000+6*num_junctions, lane_width=3.75)
                    self.add_junction_roads_elevation(junction_roads, obj['elevation_level'])
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
                    # Finally create the junction
                    junction = xodr.create_junction(
                        junction_roads, junction_id, incoming_roads, 'junction_' + str(junction_id))
                    num_junctions += 1
                    print('Add junction with ID', junction_id)
                    odr.add_junction(junction)
                    for road in junction_roads:
                        odr.add_road(road)
        odr.adjust_startpoints()
        odr.write_xml(str(xodr_path))

        # OpenSCENARIO
        xosc_path = pathlib.Path(self.directory) / 'xosc' / (self.dsc_export_filename + '.xosc')
        xosc_path.parent.mkdir(parents=True, exist_ok=True)
        init = xosc.Init()
        entities = xosc.Entities()
        if helpers.collection_exists(['OpenSCENARIO','dynamic_objects']):
            for obj in bpy.data.collections['OpenSCENARIO'].children['dynamic_objects'].objects:
                if 'dsc_type' in obj and obj['dsc_type'] == 'car':
                    car_name = obj.name
                    print('Add car with name', obj.name)
                    entities.add_scenario_object(car_name,xosc.CatalogReference('VehicleCatalog', car_name))
                    # Teleport to initial position
                    init.add_init_action(car_name,
                        xosc.TeleportAction(
                            xosc.WorldPosition(
                                x=obj['position'][0], y=obj['position'][1], z=obj['position'][2], h=obj['hdg'])))
                    # Get pitch and roll from road
                    init.add_init_action(car_name,
                        xosc.TeleportAction(
                            xosc.RelativeRoadPosition(0, 0, car_name,
                                xosc.Orientation(h=obj['hdg'], p=0, r=0, reference=xosc.ReferenceContext.absolute))))
                    # Begin driving
                    init.add_init_action(car_name,
                        xosc.AbsoluteSpeedAction(helpers.kmh_to_ms(obj['speed_initial']),
                            xosc.TransitionDynamics(xosc.DynamicsShapes.step,
                                                    xosc.DynamicsDimension.time, 1)))
                    # Center on closest lane
                    init.add_init_action(car_name,
                        xosc.RelativeLaneChangeAction(0, car_name,
                            xosc.TransitionDynamics(xosc.DynamicsShapes.cubic,
                                                    xosc.DynamicsDimension.rate, 2.0)))
        if helpers.collection_exists(['OpenSCENARIO','trajectories']):
            for obj in bpy.data.collections['OpenSCENARIO'].children['trajectories'].objects:
                if 'dsc_type' in obj and obj['dsc_type'] == 'trajectory':
                    if obj['dsc_subtype'] == 'polyline':
                        speed_kmh = helpers.get_obj_custom_property('OpenSCENARIO', 'dynamic_objects',
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
                    action = xosc.FollowTrajectoryAction(trajectory,xosc.FollowMode.follow,
                        None,None,None,None)
                    init.add_init_action(obj['owner_name'], action)
                    # FIXME the following does not seem to work with esmini in
                    # init, we need a separate maneuver group/act
                    # # After trajectory following get pitch and roll from road
                    # init.add_init_action(car_name,
                    #     xosc.TeleportAction(
                    #         xosc.RelativeRoadPosition(0, 0, car_name,
                    #             xosc.Orientation(p=0, r=0, reference=xosc.ReferenceContext.relative))))
                    # # Finally center on closest lane
                    # init.add_init_action(car_name,
                    #     xosc.RelativeLaneChangeAction(0, car_name,
                    #         xosc.TransitionDynamics(xosc.DynamicsShapes.cubic,
                    #                                 xosc.DynamicsDimension.rate, 2.0)))

        # Link .xodr to .xosc with relative path
        dotdot = pathlib.Path('..')
        xodr_path_relative = dotdot / xodr_path.relative_to(pathlib.Path(self.directory))
        if helpers.collection_exists(['OpenDRIVE']):
            road = xosc.RoadNetwork(str(xodr_path_relative),'./scenegraph/export.' + self.mesh_file_type)
        else:
            road = xosc.RoadNetwork(str(xodr_path_relative))

        storyboard = xosc.StoryBoard(init)
        catalog_vehicles = xosc.Catalog()
        catalog_vehicles.add_catalog('VehicleCatalog','../catalogs/vehicles')
        scenario = xosc.Scenario('dsc_scenario','blender_dsc',xosc.ParameterDeclarations(),
            entities,storyboard,road,catalog_vehicles)
        scenario.write_xml(str(xosc_path))

    def get_element_type_by_id(self, id):
        '''
            Return element type of an OpenDRIVE element with given ID
        '''
        for obj in bpy.data.collections['OpenDRIVE'].objects:
            if obj.name.startswith('road'):
                if obj['id_xodr'] == id:
                    return xodr.ElementType.road
            elif obj.name.startswith('junction'):
                if obj['id_xodr'] == id:
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
                    lane_ids_road = self.get_lanes_ids_to_link(road_obj, 'predecessor')
                    # Check if we are connected to beginning or end of the other road
                    if road_obj['link_predecessor_cp_l'] == 'cp_start_l':
                        lanes_ids_road_pre = self.get_lanes_ids_to_link(road_obj_pre, 'predecessor')
                    elif road_obj['link_predecessor_cp_l'] == 'cp_end_l':
                        lanes_ids_road_pre = self.get_lanes_ids_to_link(road_obj_pre, 'successor')
                    xodr.create_lane_links_from_ids(road, road_pre, lane_ids_road, lanes_ids_road_pre)
            if road.successor:
                road_suc = self.get_road_by_id(roads, road.successor.element_id)
                if road_suc:
                    road_obj_suc = helpers.get_object_xodr_by_id(road.successor.element_id)
                    lane_ids_road = self.get_lanes_ids_to_link(road_obj, 'successor')
                    # Check if we are connected to beginning or end of the other road
                    if road_obj['link_successor_cp_l'] == 'cp_start_l':
                        lanes_ids_road_suc = self.get_lanes_ids_to_link(road_obj_suc, 'predecessor')
                    elif road_obj['link_successor_cp_l'] == 'cp_end_l':
                        lanes_ids_road_suc = self.get_lanes_ids_to_link(road_obj_suc, 'successor')
                    xodr.create_lane_links_from_ids(road, road_suc, lane_ids_road, lanes_ids_road_suc)

    def get_lanes_ids_to_link(self, road_obj, link_type):
        '''
            Get the lane IDs with non-zero lane width which should be linked.
        '''
        lane_ids_to_link = []
        if link_type == 'predecessor':
            for lane_idx in range(road_obj['lanes_left_num']):
                if road_obj['lanes_left_widths_change'][lane_idx] != 'open':
                    lane_ids_to_link.append(road_obj['lanes_left_num']-lane_idx)
            for lane_idx in range(road_obj['lanes_right_num']):
                if road_obj['lanes_right_widths_change'][lane_idx] != 'open':
                    lane_ids_to_link.append(-lane_idx-1)
        if link_type == 'successor':
            for lane_idx in range(road_obj['lanes_left_num']):
                if road_obj['lanes_left_widths_change'][lane_idx] != 'close':
                    lane_ids_to_link.append(road_obj['lanes_left_num']-lane_idx)
            for lane_idx in range(road_obj['lanes_right_num']):
                if road_obj['lanes_right_widths_change'][lane_idx] != 'close':
                    lane_ids_to_link.append(-lane_idx-1)
        return lane_ids_to_link

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
        print("z_global:", z_global)
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

    def get_lane_offset(self, road_obj, id_split_road):
        '''
            Return lane offset of road connected to the split road via direct
            junction.
        '''
        for obj_split in bpy.data.collections['OpenDRIVE'].objects:
            if obj_split.name.startswith('road'):
                if obj_split['id_xodr'] == id_split_road:
                    if obj_split['link_successor_id_l'] == road_obj['id_xodr']:
                        if obj_split['road_split_lane_idx'] < obj_split['lanes_left_num'] + 1:
                            lane_offset = obj_split['lanes_left_num'] - obj_split['road_split_lane_idx'] + 1
                        else:
                            lane_offset = obj_split['lanes_left_num'] - obj_split['road_split_lane_idx']
                    elif obj_split['link_successor_id_r'] == road_obj['id_xodr']:
                        # Remove center lane if necessary
                        if obj_split['road_split_lane_idx'] > obj_split['lanes_left_num'] + 1:
                            lane_offset = obj_split['lanes_left_num'] - obj_split['road_split_lane_idx']
                        else:
                            lane_offset = obj_split['lanes_left_num'] - obj_split['road_split_lane_idx'] - 1
                    return lane_offset
