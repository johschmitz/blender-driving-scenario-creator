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
        odr = xodr.OpenDrive('blender_dsc_map')
        # Create OpenDRIVE road from object collection
        for obj in bpy.data.collections['OpenDRIVE'].all_objects:
            if 'road_straight' in obj.name:
                planview = xodr.PlanView()
                planview.set_start_point(obj['t_road_planView_geometry_x'],obj['t_road_planView_geometry_y'],obj['t_road_planView_geometry_hdg'])
                line = xodr.Line(obj['t_road_planView_geometry_length'])
                planview.add_geometry(line)
                marking = xodr.RoadMark(xodr.RoadMarkType.solid,0.2)
                centerlane = xodr.Lane(a=2)
                centerlane.add_roadmark(marking)
                lanesec = xodr.LaneSection(0,centerlane)
                lanes = xodr.Lanes()
                lanes.add_lanesection(lanesec)
                road = xodr.Road(obj['id_opendrive'],planview,lanes)
                print('Add road with ID', obj['id_opendrive'])
                odr.add_road(road)
        odr.adjust_roads_and_lanes()
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