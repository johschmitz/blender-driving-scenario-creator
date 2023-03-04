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
import bpy.utils.previews

import os

from . export import DSC_OT_export
from . junction_four_way import DSC_OT_junction_four_way
from . modal_junction_generic import DSC_OT_junction_generic
from . junction_connecting_road import DSC_OT_junction_connecting_road
from . entity_bicycle import DSC_OT_entity_bicycle
from . entity_car import DSC_OT_entity_car
from . entity_motorbike import DSC_OT_entity_motorbike
from . entity_pedestrian import DSC_OT_entity_pedestrian
from . entity_truck import DSC_OT_entity_truck
from . road_arc import DSC_OT_road_arc
from . popup_road_properties import DSC_OT_popup_road_properties
from . road_parametric_polynomial import DSC_OT_road_parametric_polynomial
from . road_properties import DSC_road_properties, DSC_enum_lane
from . road_clothoid import DSC_OT_road_clothoid
from . road_straight import DSC_OT_road_straight
from . trajectory_nurbs import DSC_OT_trajectory_nurbs
from . trajectory_polyline import DSC_OT_trajectory_polyline
from . entity_properties import DSC_entity_properties_vehicle
from . entity_properties import DSC_entity_properties_pedestrian
from . popup_entity_properties import DSC_OT_popup_entity_properties


bl_info = {
    'name' : 'Driving Scenario Creator',
    'author' : 'Johannes Schmitz',
    'description' : 'Create OpenDRIVE and OpenSCENARIO based driving scenarios.',
    'blender' : (3, 3, 0),
    'version' : (0, 19, 1),
    'location' : 'View3D > Sidebar > Driving Scenario Creator',
    'warning' : '',
    'doc_url': '',
    'tracker_url': 'https://github.com/johschmitz/blender-driving-scenario-creator/issues',
    'link': 'https://github.com/johschmitz/blender-driving-scenario-creator',
    'support': 'COMMUNITY',
    'category' : 'Add Mesh'
}

# Global variables
custom_icons = None

class DSC_PT_panel_create(bpy.types.Panel):
    bl_idname = 'DSC_PT_panel_create'
    bl_label = 'Driving Scenario Creator'
    bl_category = 'Driving Scenario Creator'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'

    def draw(self, context):
        global custom_icons

        layout = self.layout
        layout.label(text='OpenDRIVE')
        box = layout.box()
        box.label(text='Roads')
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Straight',
            icon_value=custom_icons['road_straight'].icon_id).operator = 'road_straight'
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Arc',
            icon_value=custom_icons['road_arc'].icon_id).operator = 'road_arc'
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Clothoid (Hermite)',
            icon_value=custom_icons['road_clothoid'].icon_id).operator = 'road_clothoid_hermite'
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Clothoid (Forward)',
            icon_value=custom_icons['road_clothoid'].icon_id).operator = 'road_clothoid_forward'
        row = box.row(align=True)
        row.operator('dsc.road_parametric_polynomial', text='Parametric polynomial',
            icon_value=custom_icons['road_parametric_polynomial'].icon_id)
        row = box.row(align=True)
        row.label(text='Junctions')
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='4-way junction',
            icon_value=custom_icons['junction_4way'].icon_id).operator = 'junction_four_way'
        row = box.row(align=True)
        row.operator('dsc.junction_generic', text='Generic junction (area)',
            icon_value=custom_icons['junction_area'].icon_id)
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Junction connecting road',
            icon_value=custom_icons['junction_connecting_road'].icon_id).operator = 'junction_connecting_road'

        layout.label(text='OpenSCENARIO')
        box = layout.box()
        box.label(text='Objects')
        row = box.row(align=True)
        row.operator('dsc.popup_entity_properties', text='Car').operator = 'entity_vehicle_car'
        # TODO implement more vehicle types
        row = box.row(align=True)
        row.operator('dsc.popup_entity_properties', text='Pedestrian').operator = 'entity_pedestrian_pedestrian'
        # TODO implement more pedestrian types

        box.label(text='Trajectories')
        row = box.row(align=True)
        row.operator('dsc.trajectory_polyline', icon_value=custom_icons['trajectory_polyline'].icon_id)
        row = box.row(align=True)
        row.operator('dsc.trajectory_nurbs', icon_value=custom_icons['trajectory_nurbs'].icon_id)

        layout.label(text='Export (Track, Scenario, Mesh)')
        box = layout.box()
        row = box.row(align=True)
        row.operator('dsc.export_driving_scenario', icon='EXPORT')

def menu_func_export(self, context):
    self.layout.operator('dsc.export_driving_scenario', text='Driving Scenario (.xosc, .xodr, .fbx/.gltf/.osgb)')

classes = (
    DSC_enum_lane,
    DSC_OT_export,
    DSC_OT_junction_four_way,
    DSC_OT_junction_generic,
    DSC_OT_junction_connecting_road,
    DSC_OT_entity_bicycle,
    DSC_OT_entity_car,
    DSC_OT_entity_motorbike,
    DSC_OT_entity_pedestrian,
    DSC_OT_entity_truck,
    DSC_OT_road_arc,
    DSC_OT_popup_road_properties,
    DSC_OT_road_parametric_polynomial,
    DSC_OT_road_clothoid,
    DSC_OT_road_straight,
    DSC_OT_trajectory_nurbs,
    DSC_OT_trajectory_polyline,
    DSC_PT_panel_create,
    DSC_road_properties,
    DSC_entity_properties_vehicle,
    DSC_entity_properties_pedestrian,
    DSC_OT_popup_entity_properties,
)

def register():
    global custom_icons
    # Load custom icons
    custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    custom_icons.load('road_straight', os.path.join(icons_dir, 'road_straight.png'), 'IMAGE')
    custom_icons.load('road_arc', os.path.join(icons_dir, 'road_arc.png'), 'IMAGE')
    custom_icons.load('road_clothoid', os.path.join(icons_dir, 'road_clothoid.png'), 'IMAGE')
    custom_icons.load('road_parametric_polynomial', os.path.join(icons_dir, 'road_parametric_polynomial.png'), 'IMAGE')
    custom_icons.load('junction_4way', os.path.join(icons_dir, 'junction_4way.png'), 'IMAGE')
    custom_icons.load('junction_area', os.path.join(icons_dir, 'junction_area.png'), 'IMAGE')
    custom_icons.load('junction_connecting_road', os.path.join(icons_dir, 'junction_connecting_road.png'), 'IMAGE')
    custom_icons.load('trajectory_nurbs', os.path.join(icons_dir, 'trajectory_nurbs.png'), 'IMAGE')
    custom_icons.load('trajectory_polyline', os.path.join(icons_dir, 'trajectory_polyline.png'), 'IMAGE')

    # Register all addon classes
    for c in classes:
        bpy.utils.register_class(c)
    # Register export menu
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    # Register property groups
    bpy.types.Scene.road_properties = bpy.props.PointerProperty(type=DSC_road_properties)
    bpy.types.Scene.entity_properties_vehicle = bpy.props.PointerProperty(type=DSC_entity_properties_vehicle)
    bpy.types.Scene.entity_properties_pedestrian = bpy.props.PointerProperty(type=DSC_entity_properties_pedestrian)

def unregister():
    global custom_icons
    # Unregister export menu
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    #  Unregister all addon classes
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    # Get rid of custom icons
    bpy.utils.previews.remove(custom_icons)
    # Get rid of property groups
    del bpy.types.Scene.road_properties

if __name__ == '__main__':
    register()
