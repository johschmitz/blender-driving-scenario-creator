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

from pathlib import Path

class DSC_OT_export(bpy.types.Operator):
    bl_idname = "dsc.export_driving_scenario"
    bl_label = "Export driving scenario"
    bl_description = "Export driving scenario as OpenDRIVE, OpenSCENARIO and Mesh (e.g. FBX, glTF 2.0)"

    filepath: bpy.props.StringProperty(
        name="File Path", description="Target filename for OpenDRIVE(.xosc) and OpenSCENARIO(.xodr)")
    
    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        s = Scenario(context)
        s.generate_single(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class Scenario(ScenarioGenerator):
    def __init__(self, context):
        ScenarioGenerator.__init__(self)
        self.context = context

    def road(self):
        odr = xodr.OpenDrive('blender_dsc')
        roads = []
        # Create OpenDRIVE roads from object collection
        for obj in bpy.data.collections['OpenDRIVE'].all_objects:
            if 'road_straight' in obj.name:
                planview = xodr.PlanView()
                planview.set_start_point(obj['t_road_planView_geometry_x'],obj['t_road_planView_geometry_y'],obj['t_road_planView_geometry_hdg'])
                line = xodr.Line(obj['t_road_planView_geometry_length'])
                planview.add_geometry(line)
                # Create simple lanes
                lanes = xodr.Lanes()
                lanesection = xodr.LaneSection(0,xodr.standard_lane())
                lanesection.add_left_lane(xodr.standard_lane(rm=xodr.STD_ROADMARK_SOLID))
                lanesection.add_right_lane(xodr.standard_lane(rm=xodr.STD_ROADMARK_SOLID))
                lanes.add_lanesection(lanesection)
                road = xodr.Road(obj['id_xodr'],planview,lanes)
                # Add road level linking
                if 't_road_link_predecessor' in obj:
                    element_type = self.get_element_type_by_id(obj['t_road_link_predecessor'])
                    if obj['t_road_link_predecessor_cp'] == 'cp_start':
                        cp_type = xodr.ContactPoint.start
                    elif obj['t_road_link_predecessor_cp'] == 'cp_end':
                        cp_type = xodr.ContactPoint.end
                    else:
                        cp_type = None
                    road.add_predecessor(element_type, obj['t_road_link_predecessor'], cp_type)
                if 't_road_link_successor' in obj:
                    element_type = self.get_element_type_by_id(obj['t_road_link_successor'])
                    if obj['t_road_link_successor_cp'] == 'cp_start':
                        cp_type = xodr.ContactPoint.start
                    elif obj['t_road_link_successor_cp'] == 'cp_end':
                        cp_type = xodr.ContactPoint.end
                    else:
                        cp_type = None
                    road.add_successor(element_type, obj['t_road_link_successor'], cp_type)
                print('Add road with ID', obj['id_xodr'])
                odr.add_road(road)
                roads.append(road)
        # Add lane level linking for all roads
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
                print(num_junctions)
                junction_roads = xodr.create_junction_roads_standalone(angles, 3.4, junction_id,
                    spiral_part=0.1, arc_part=0.8, startnum=1000+6*num_junctions)
                i = 0
                # Create connecting roads and link them to incoming roads
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
        # create a simple scenario
        road = xosc.RoadNetwork(self.road_file)
        egoname = 'Ego'
        entities = xosc.Entities()
        entities.add_scenario_object(egoname,xosc.CatalogReference('VehicleCatalog','car_white'))

        catalog = xosc.Catalog()
        catalog.add_catalog('VehicleCatalog','../xosc/Catalogs/Vehicles')

        init = xosc.Init()

        init.add_init_action(egoname,xosc.TeleportAction(xosc.LanePosition(50,0,-2,0)))
        init.add_init_action(egoname,xosc.AbsoluteSpeedAction(50,xosc.TransitionDynamics(xosc.DynamicsShapes.step,xosc.DynamicsDimension.time,1)))

        event = xosc.Event('my event',xosc.Priority.overwrite)
        event.add_action('lane change',xosc.AbsoluteLaneChangeAction(-1,xosc.TransitionDynamics(xosc.DynamicsShapes.sinusoidal,xosc.DynamicsDimension.time,4)))
        event.add_trigger(xosc.ValueTrigger('start_trigger ',0,xosc.ConditionEdge.none,xosc.SimulationTimeCondition(4,xosc.Rule.greaterThan)))

        man = xosc.Maneuver('maneuver')
        man.add_event(event)

        sb = xosc.StoryBoard(init,stoptrigger=xosc.ValueTrigger('start_trigger ',0,xosc.ConditionEdge.none,xosc.SimulationTimeCondition(13,xosc.Rule.greaterThan),'stop'))
        sb.add_maneuver(man,egoname)
        sce = xosc.Scenario('my scenario','Mandolin',xosc.ParameterDeclarations(),entities,sb,road,catalog)

        return sce

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
            else:
                return None