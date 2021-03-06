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

from . road_straight import DSC_OT_road_straight
from . road_arc import DSC_OT_road_arc
from . road_spiral import DSC_OT_road_spiral
from . road_parametric_polynomial import DSC_OT_road_parametric_polynomial
from . junction import DSC_OT_junction
from . export import DSC_OT_export
from . object_bicycle import DSC_OT_object_bicycle
from . object_car import DSC_OT_object_car
from . object_motorbike import DSC_OT_object_motorbike
from . object_pedestrian import DSC_OT_object_pedestrian
from . object_truck import DSC_OT_object_truck
from . trajectory_curve import DSC_OT_trajectory_curve
from . trajectory_waypoints import DSC_OT_trajectory_waypoints


bl_info = {
    "name" : "Driving Scenario Creator",
    "author" : "Johannes Schmitz",
    "description" : "Addon for creating OpenDRIVE and OpenSCENARIO based driving scenarios.",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Add Mesh"
}

# Global variables
custom_icons = None

class DSC_PT_panel_create(bpy.types.Panel):
    bl_idname = "DSC_PT_panel_create"
    bl_label = "Driving Scenario Creator"
    bl_category = "Create"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        global custom_icons

        layout = self.layout
        box = layout.box()
        box.label(text="Road primitives (OpenDRIVE)")
        row = box.row(align=True)
        row.operator("dsc.road_straight", icon_value=custom_icons["road_straight"].icon_id)
        row = box.row(align=True)
        row.operator("dsc.road_arc", icon_value=custom_icons["road_arc"].icon_id)
        row = box.row(align=True)
        row.operator("dsc.road_spiral", icon_value=custom_icons["road_spiral"].icon_id)
        row = box.row(align=True)
        row.operator("dsc.road_parametric_polynomial", icon_value=custom_icons["road_parametric_polynomial"].icon_id)
        row = box.row(align=True)
        row.operator("dsc.junction", icon_value=custom_icons["junction"].icon_id)

        box = layout.box()
        box.label(text="Objects (OpenSCENARIO)")
        row = box.row(align=True)
        row.operator("dsc.object_car")
        row = box.row(align=True)
        row.operator("dsc.object_truck")
        row = box.row(align=True)
        row.operator("dsc.object_motorbike")
        row = box.row(align=True)
        row.operator("dsc.object_bicycle")
        row = box.row(align=True)
        row.operator("dsc.object_pedestrian")

        box = layout.box()
        box.label(text="Trajectories (OpenSCENARIO)")
        row = box.row(align=True)
        row.operator("dsc.trajectory_curve", icon_value=custom_icons["trajectory_curve"].icon_id)
        row = box.row(align=True)
        row.operator("dsc.trajectory_waypoints", icon_value=custom_icons["trajectory_waypoints"].icon_id)


        box = layout.box()
        box.label(text="Export (Track, Scenario, Mesh)")
        row = box.row(align=True)
        row.operator("dsc.export_driving_scenario", icon="EXPORT")

def menu_func_export(self, context):
    self.layout.operator("dsc.export_driving_scenario", text="Driving Scenario (.xodr, .xodr, .fbx/.gltf)")

classes = (
    DSC_PT_panel_create,
    DSC_OT_road_straight,
    DSC_OT_road_arc,
    DSC_OT_road_spiral,
    DSC_OT_road_parametric_polynomial,
    DSC_OT_junction,
    DSC_OT_export,
    DSC_OT_object_bicycle,
    DSC_OT_object_car,
    DSC_OT_object_motorbike,
    DSC_OT_object_pedestrian,
    DSC_OT_object_truck,
    DSC_OT_trajectory_curve,
    DSC_OT_trajectory_waypoints
)

def register():
    global custom_icons
    # Load custom icons
    custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    custom_icons.load("road_straight", os.path.join(icons_dir, "road_straight.png"), 'IMAGE')
    custom_icons.load("road_arc", os.path.join(icons_dir, "road_arc.png"), 'IMAGE')
    custom_icons.load("road_spiral", os.path.join(icons_dir, "road_spiral.png"), 'IMAGE')
    custom_icons.load("road_parametric_polynomial", os.path.join(icons_dir, "road_parametric_polynomial.png"), 'IMAGE')
    custom_icons.load("junction", os.path.join(icons_dir, "junction.png"), 'IMAGE')
    custom_icons.load("trajectory_curve", os.path.join(icons_dir, "trajectory_curve.png"), 'IMAGE')
    custom_icons.load("trajectory_waypoints", os.path.join(icons_dir, "trajectory_waypoints.png"), 'IMAGE')

    # Register all addon classes
    for c in classes:
        bpy.utils.register_class(c)
    # Register export menu
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    global custom_icons
    # Unregister export menu
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    #  Unregister all addon classes
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    # Get rid of custom icons
    bpy.utils.previews.remove(custom_icons)

if __name__ == "__main__":
    register()
