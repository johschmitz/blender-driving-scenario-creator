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

from scenariogeneration import xosc
from scenariogeneration import xodr
from scenariogeneration import ScenarioGenerator

from math import pi

import pathlib
import subprocess

class DSC_OT_export(bpy.types.Operator):
    bl_idname = 'dsc.export_driving_scenario'
    bl_label = 'Export driving scenario'
    bl_description = 'Export driving scenario as OpenDRIVE, OpenSCENARIO and Mesh (e.g. OBJ, FBX, glTF 2.0)'

    directory: bpy.props.StringProperty(
        name='Export directory', description='Target directory for export.')
    
    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        self.export_scenegraph_file()
        s = Scenario(context, self.directory)
        s.generate_single(self.directory)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def export_scenegraph_file(self):
        # Export the scene mesh to file
        scenegraph_path = pathlib.Path(self.directory) / 'scenegraph' / 'export.obj'
        scenegraph_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.object.select_all(action='SELECT')
        if 'OpenSCENARIO' in bpy.data.collections:
            for obj in bpy.data.collections['OpenSCENARIO'].all_objects:
                obj.select_set(False)
        bpy.ops.export_scene.obj(filepath=str(scenegraph_path), check_existing=True,
                                 filter_glob='*.obj,*.mtl', use_selection=True, use_animation=False,
                                 use_mesh_modifiers=True, use_edges=True, use_smooth_groups=False,
                                 use_smooth_groups_bitflags=False, use_normals=True, use_uvs=True,
                                 use_materials=True, use_triangles=False, use_nurbs=False,
                                 use_vertex_groups=False, use_blen_objects=True, group_by_object=False,
                                 group_by_material=False, keep_vertex_order=False, global_scale=1.0,
                                     path_mode='RELATIVE', axis_forward='-Z', axis_up='Y')
        bpy.ops.object.select_all(action='DESELECT')
        try:
            subprocess.run(['osgconv', str(scenegraph_path), str(scenegraph_path.with_suffix('.osgb'))])
        except FileNotFoundError:
            self.report({'ERROR'}, 'Executable \"osgconv\" required to produce .osgb scenegraph file. '
                'Try installing openscenegraph.')

class Scenario(ScenarioGenerator):
    def __init__(self, context, directory):
        ScenarioGenerator.__init__(self)
        self.context = context
        self.directory = directory

    def road(self):
        odr = xodr.OpenDrive('blender_dsc')
        roads = []
        # Create OpenDRIVE roads from object collection
        for obj in bpy.data.collections['OpenDRIVE'].all_objects:
            if 'road' in obj.name:
                if obj['geometry'] == 'line':
                    planview = xodr.PlanView()
                    planview.set_start_point(obj['geometry_x'],
                        obj['geometry_y'],obj['geometry_hdg_start'])
                    line = xodr.Line(obj['geometry_length'])
                    planview.add_geometry(line)
                    # Create simple lanes
                    lanes = xodr.Lanes()
                    lanesection = xodr.LaneSection(0,xodr.standard_lane())
                    lanesection.add_left_lane(xodr.standard_lane(rm=xodr.STD_ROADMARK_SOLID))
                    lanesection.add_right_lane(xodr.standard_lane(rm=xodr.STD_ROADMARK_SOLID))
                    lanes.add_lanesection(lanesection)
                    road = xodr.Road(obj['id_xodr'],planview,lanes)
                if obj['geometry'] == 'arc':
                    planview = xodr.PlanView()
                    planview.set_start_point(obj['geometry_x'],
                        obj['geometry_y'],obj['geometry_hdg_start'])
                    arc = xodr.Arc(obj['geometry_curvature'],
                        angle=obj['geometry_angle'])
                    planview.add_geometry(arc)
                    # Create simple lanes
                    lanes = xodr.Lanes()
                    lanesection = xodr.LaneSection(0,xodr.standard_lane())
                    lanesection.add_left_lane(xodr.standard_lane(rm=xodr.STD_ROADMARK_SOLID))
                    lanesection.add_right_lane(xodr.standard_lane(rm=xodr.STD_ROADMARK_SOLID))
                    lanes.add_lanesection(lanesection)
                    road = xodr.Road(obj['id_xodr'],planview,lanes)
                # Add road level linking
                if 'link_predecessor' in obj:
                    element_type = self.get_element_type_by_id(obj['link_predecessor'])
                    if obj['link_predecessor_cp'] == 'cp_start':
                        cp_type = xodr.ContactPoint.start
                    elif obj['link_predecessor_cp'] == 'cp_end':
                        cp_type = xodr.ContactPoint.end
                    else:
                        cp_type = None
                    road.add_predecessor(element_type, obj['link_predecessor'], cp_type)
                if 'link_successor' in obj:
                    element_type = self.get_element_type_by_id(obj['link_successor'])
                    if obj['link_successor_cp'] == 'cp_start':
                        cp_type = xodr.ContactPoint.start
                    elif obj['link_successor_cp'] == 'cp_end':
                        cp_type = xodr.ContactPoint.end
                    else:
                        cp_type = None
                    road.add_successor(element_type, obj['link_successor'], cp_type)
                print('Add road with ID', obj['id_xodr'])
                odr.add_road(road)
                roads.append(road)
        # Add lane level linking for all roads
        # TODO: Improve performance by exploiting symmetry
        for road in roads:
            if road.predecessor:
                road_pre = self.get_road_by_id(roads, road.predecessor.element_id)
                if road_pre:
                    xodr.create_lane_links(road, road_pre)
            if road.successor:
                road_suc = self.get_road_by_id(roads, road.successor.element_id)
                if road_suc:
                    xodr.create_lane_links(road, road_suc)
        # Create OpenDRIVE junctions from object collection
        num_junctions = 0
        for obj in bpy.data.collections['OpenDRIVE'].all_objects:
            if 'junction' in obj.name:
                incoming_roads = []
                angles = []
                junction_id = obj['id_xodr']
                # Create junction roads based on incoming road angles (simple 4-way for now)
                for idx in range(4):
                    angles.append(idx * 2 * pi /len(obj['incoming_roads']))
                # 0 angle road must point in 'right' direction
                incoming_roads.append(xodr.get_road_by_id(roads, obj['incoming_roads']['cp_right']))
                incoming_roads.append(xodr.get_road_by_id(roads, obj['incoming_roads']['cp_up']))
                incoming_roads.append(xodr.get_road_by_id(roads, obj['incoming_roads']['cp_left']))
                incoming_roads.append(xodr.get_road_by_id(roads, obj['incoming_roads']['cp_down']))
                # Create connecting roads and link them to incoming roads
                junction_roads = xodr.create_junction_roads_standalone(angles, 3.4, junction_id,
                    spiral_part=0.1, arc_part=0.8, startnum=1000+6*num_junctions)
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
        return odr

    def scenario(self):
        init = xosc.Init()
        entities = xosc.Entities()
        if 'OpenSCENARIO' in bpy.data.collections:
            for obj in bpy.data.collections['OpenSCENARIO'].all_objects:
                if 'car' in obj.name:
                    car_name = obj.name
                    print('Add car with ID', obj['id_xosc'])
                    entities.add_scenario_object(car_name,xosc.CatalogReference('VehicleCatalog','car_white'))
                    init.add_init_action(car_name, xosc.TeleportAction(
                        xosc.WorldPosition(x=obj['x'], y=obj['y'], z=obj['z'], h=obj['hdg'])))
                    init.add_init_action(car_name, xosc.AbsoluteSpeedAction(
                        30, xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 1)))
                    init.add_init_action(car_name, xosc.RelativeLaneChangeAction(0, car_name,
                        xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.rate, 1)))

        road = xosc.RoadNetwork(self.road_file,'./scenegraph/export.osgb')
        catalog = xosc.Catalog()
        catalog.add_catalog('VehicleCatalog','../xosc/Catalogs/Vehicles')
        storyboard = xosc.StoryBoard(init,stoptrigger=xosc.ValueTrigger('start_trigger ', 3, xosc.ConditionEdge.none,xosc.SimulationTimeCondition(13,xosc.Rule.greaterThan),'stop'))
        scenario = xosc.Scenario('dsc_scenario','blender_dsc',xosc.ParameterDeclarations(),entities,storyboard,road,catalog)

        return scenario

    def get_element_type_by_id(self, id):
        '''
            Return element type of an OpenDRIVE element with given ID
        '''
        for obj in bpy.data.collections['OpenDRIVE'].all_objects:
            if 'road' in obj.name:
                if obj['id_xodr'] == id:
                    return xodr.ElementType.road
            elif 'junction' in obj.name:
                if obj['id_xodr'] == id:
                    return xodr.ElementType.junction

    def get_road_by_id(self, roads, id):
        '''
            Return road with given ID
        '''
        for road in roads:
            if road.id == id:
                return road
        print('ERROR: No road with ID {} found.'.format(id))
        return None