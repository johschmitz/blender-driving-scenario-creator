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

import json
import os
import pathlib

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
from . popup_road_properties import (DSC_OT_popup_road_properties, DSC_OT_save_cross_section_preset,
    DSC_OT_delete_cross_section_preset, DSC_OT_copy_cross_section_preset_name)
from . road_parametric_polynomial import DSC_OT_road_parametric_polynomial
from . road_properties import DSC_road_properties, DSC_enum_lane
from . road_clothoid import DSC_OT_road_clothoid
from . road_clothoid_triple import DSC_OT_road_clothoid_triple
from . road_straight import DSC_OT_road_straight
from . trajectory_nurbs import DSC_OT_trajectory_nurbs
from . trajectory_polyline import DSC_OT_trajectory_polyline
from . scenario_object_move import DSC_OT_scenario_object_move
from . entity_properties import DSC_entity_properties_vehicle
from . entity_properties import DSC_entity_properties_pedestrian
from . popup_entity_properties import DSC_OT_popup_entity_properties
from . road_object_sign_properties import DSC_road_object_sign_property_item
from . road_object_sign_properties import DSC_road_object_sign_properties
from . road_object_stencil_properties import DSC_road_object_stencil_property_item
from . road_object_stencil_properties import DSC_road_object_stencil_properties
from . road_object_traffic_light_properties import DSC_road_object_traffic_light_properties
from . road_object_sign_operator import DSC_OT_road_object_sign
from . road_object_stencil_operator import DSC_OT_road_object_stencil
from . road_object_traffic_light_operator import DSC_OT_road_object_traffic_light
from . popup_road_object_sign_properties import DSC_OT_popup_road_object_sign_properties
from . popup_road_object_stencil_properties import DSC_OT_popup_road_object_stencil_properties
from . popup_road_object_traffic_light_properties import DSC_OT_popup_road_object_traffic_light_properties
from . road_object_stop_line_operator import DSC_OT_road_object_stop_line
from . esmini_preview_operators import DSC_OT_esmini_preview_start
from . esmini_preview_operators import DSC_OT_esmini_preview_stop
from . esmini_preview_operators import DSC_OT_esmini_preview_step
from . esmini_preview_operators import DSC_OT_esmini_open_preferences
from . import esmini_preview


bl_info = {
    'name' : 'Driving Scenario Creator',
    'author' : 'Johannes Schmitz',
    'description' : 'Create OpenDRIVE and OpenSCENARIO based driving scenarios.',
    'blender' : (3, 6, 0),
    'version' : (0, 31, 0),
    'location' : 'View3D > Sidebar > Driving Scenario Creator',
    'warning' : '',
    'doc_url': '',
    'tracker_url': 'https://github.com/johschmitz/blender-driving-scenario-creator/issues',
    'link': 'https://github.com/johschmitz/blender-driving-scenario-creator',
    'support': 'COMMUNITY',
    'category' : 'Add Mesh'
}

# Global variables
dsc_custom_icons = None
dsc_road_sign_previews = None

_CONFIG_DIR_NAME = 'driving_scenario_creator'
_CONFIG_FILE_NAME = 'config.json'


def _get_config_file_path():
    config_root = bpy.utils.user_resource('CONFIG', path=_CONFIG_DIR_NAME, create=True)
    if not config_root:
        return None
    return pathlib.Path(config_root) / _CONFIG_FILE_NAME


def _save_esmini_library_path_to_config(path):
    config_file = _get_config_file_path()
    if config_file is None:
        return

    payload = {'esmini_library_path': path or ''}
    try:
        with config_file.open('w', encoding='utf-8') as handle:
            json.dump(payload, handle, indent=2)
    except OSError:
        pass


def _load_esmini_library_path_from_config():
    config_file = _get_config_file_path()
    if config_file is None or not config_file.exists():
        return ''

    try:
        with config_file.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return ''

    value = data.get('esmini_library_path', '') if isinstance(data, dict) else ''
    return value if isinstance(value, str) else ''


def _on_esmini_library_path_update(self, context):
    del context
    _save_esmini_library_path_to_config(self.esmini_library_path)


def _resolve_addon_preferences(context=None):
    prefs = context.preferences if context is not None else bpy.context.preferences
    if prefs is None:
        return None

    addons = prefs.addons
    module_candidates = []
    for candidate in (__package__, __name__.split('.')[0], 'addon'):
        if candidate and candidate not in module_candidates:
            module_candidates.append(candidate)

    for module_name in module_candidates:
        addon_cfg = addons.get(module_name)
        if addon_cfg is not None and addon_cfg.preferences is not None:
            return addon_cfg.preferences

    for addon_cfg in addons.values():
        addon_prefs = getattr(addon_cfg, 'preferences', None)
        if addon_prefs is not None and hasattr(addon_prefs, 'esmini_library_path'):
            return addon_prefs

    return None


class DSC_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    esmini_library_path: bpy.props.StringProperty(
        name='esmini_library_path',
        description='Path to esmini shared library file (.dll/.so/.dylib) for esmini preview feature',
        subtype='FILE_PATH',
        default='',
        update=_on_esmini_library_path_update)

    def draw(self, context):
        del context
        layout = self.layout
        layout.prop(self, 'esmini_library_path', text='esmini library path (.dll/.so/.dylib)')

class DSC_PT_panel_create(bpy.types.Panel):
    bl_idname = 'DSC_PT_panel_create'
    bl_label = 'Driving Scenario Creator'
    bl_category = 'Driving Scenario Creator'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'

    def draw(self, context):
        global dsc_custom_icons

        layout = self.layout
        layout.label(text='OpenDRIVE')
        box = layout.box()
        box.label(text='Roads')
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Straight',
            icon_value=dsc_custom_icons['road_straight'].icon_id).operator = 'road_straight'
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Arc',
            icon_value=dsc_custom_icons['road_arc'].icon_id).operator = 'road_arc'
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Clothoid (Forward)',
            icon_value=dsc_custom_icons['road_clothoid'].icon_id).operator = 'road_clothoid_forward'
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Clothoid (Hermite)',
            icon_value=dsc_custom_icons['road_clothoid'].icon_id).operator = 'road_clothoid_hermite'
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Clothoid triple (G2)',
            icon_value=dsc_custom_icons['road_clothoid'].icon_id).operator = 'road_clothoid_triple'
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='Parametric polynomial',
            icon_value=dsc_custom_icons['road_parametric_polynomial'].icon_id).operator = 'road_parametric_polynomial'
        row = box.row(align=True)
        row.label(text='Junctions')
        row = box.row(align=True)
        row.operator('dsc.popup_road_properties', text='4-way junction',
            icon_value=dsc_custom_icons['junction_4way'].icon_id).operator = 'junction_four_way'
        row = box.row(align=True)
        row.operator('dsc.junction_generic', text='Generic junction (area)',
            icon_value=dsc_custom_icons['junction_area'].icon_id)
        row = box.row(align=True)
        row.operator('dsc.junction_connecting_road', text='Junction connecting road',
            icon_value=dsc_custom_icons['junction_connecting_road'].icon_id)
        row = box.row(align=True)
        row.label(text='Road objects')
        row = box.row(align=True)
        row.operator('dsc.popup_road_object_sign_properties', text='Sign',
            icon_value=dsc_custom_icons['road_object_sign'].icon_id).operator = 'road_object_sign'
        row = box.row(align=True)
        row.operator('dsc.popup_road_object_traffic_light_properties', text='Traffic light',
            icon_value=dsc_custom_icons['road_object_traffic_light'].icon_id).operator = 'road_object_traffic_light'
        row = box.row(align=True)
        row.operator('dsc.road_object_stop_line', text='Stop line',
            icon_value=dsc_custom_icons['road_object_stop_line'].icon_id)
        row = box.row(align=True)
        row.operator('dsc.popup_road_object_stencil_properties', text='Stencil',
            icon_value=dsc_custom_icons['road_object_stencil'].icon_id).operator = 'road_object_stencil'

        layout.label(text='OpenSCENARIO')
        box = layout.box()
        box.label(text='Objects')
        row = box.row(align=True)
        row.operator('dsc.popup_entity_properties', text='Car').operator = 'entity_vehicle_car'
        # TODO implement more vehicle types
        row = box.row(align=True)
        row.operator('dsc.popup_entity_properties', text='Pedestrian').operator = 'entity_pedestrian_pedestrian'
        # TODO implement more pedestrian types
        row = box.row(align=True)
        row.operator('dsc.scenario_object_move', text='Move object', icon='ORIENTATION_GIMBAL')

        box.label(text='Trajectories')
        row = box.row(align=True)
        row.operator('dsc.trajectory_polyline', icon_value=dsc_custom_icons['trajectory_polyline'].icon_id)
        row = box.row(align=True)
        row.operator('dsc.trajectory_nurbs', icon_value=dsc_custom_icons['trajectory_nurbs'].icon_id)

        layout.label(text='esmini Preview')
        box = layout.box()
        row = box.row(align=True)
        row.operator('dsc.esmini_open_preferences', icon='PREFERENCES')
        row = box.row(align=True)
        if esmini_preview.is_preview_running():
            row.operator('dsc.esmini_preview_start', text='Pause', icon='PAUSE')
        else:
            row.operator('dsc.esmini_preview_start', text='Start', icon='PLAY')
        row.operator('dsc.esmini_preview_step', icon='FRAME_NEXT')
        row.operator('dsc.esmini_preview_stop', text='■\u00A0\u00A0\u00A0\u00A0\u00A0Stop')
        row = box.row(align=True)
        row.label(text='Status: {}'.format(esmini_preview.get_preview_status_text()))

        layout.label(text='Export (Track, Scenario, Mesh)')
        box = layout.box()
        row = box.row(align=True)
        row.operator('dsc.export_driving_scenario', icon='EXPORT')

def menu_func_export(self, context):
    self.layout.operator('dsc.export_driving_scenario', text='Driving Scenario (.xosc, .xodr, .fbx/.gltf/.osgb)')

class DSC_Properties(bpy.types.PropertyGroup):
    road_properties: bpy.props.PointerProperty(
        name='road_properties', type=DSC_road_properties)
    connecting_road_properties: bpy.props.PointerProperty(
        name='connecting_road_properties', type=DSC_road_properties)
    road_object_sign_properties: bpy.props.PointerProperty(
        name='road_object_sign_properties', type=DSC_road_object_sign_properties)
    road_object_traffic_light_properties: bpy.props.PointerProperty(
        name='road_object_traffic light_properties', type=DSC_road_object_traffic_light_properties)
    road_object_stencil_properties: bpy.props.PointerProperty(
        name='road_object_stencil_properties', type=DSC_road_object_stencil_properties)
    entity_properties_vehicle: bpy.props.PointerProperty(
        name='entity_properties_vehicle', type=DSC_entity_properties_vehicle)
    entity_properties_pedestrian: bpy.props.PointerProperty(
        name='entity_properties_pedestrian', type=DSC_entity_properties_pedestrian)

classes = (
    DSC_AddonPreferences,
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
    DSC_OT_save_cross_section_preset,
    DSC_OT_delete_cross_section_preset,
    DSC_OT_copy_cross_section_preset_name,
    DSC_OT_road_parametric_polynomial,
    DSC_OT_road_clothoid,
    DSC_OT_road_clothoid_triple,
    DSC_OT_road_straight,
    DSC_OT_trajectory_nurbs,
    DSC_OT_trajectory_polyline,
    DSC_OT_scenario_object_move,
    DSC_PT_panel_create,
    DSC_road_properties,
    DSC_entity_properties_vehicle,
    DSC_entity_properties_pedestrian,
    DSC_OT_popup_entity_properties,
    DSC_road_object_sign_property_item,
    DSC_road_object_sign_properties,
    DSC_road_object_stencil_property_item,
    DSC_road_object_stencil_properties,
    DSC_road_object_traffic_light_properties,
    DSC_OT_road_object_sign,
    DSC_OT_road_object_stencil,
    DSC_OT_road_object_traffic_light,
    DSC_OT_popup_road_object_sign_properties,
    DSC_OT_popup_road_object_stencil_properties,
    DSC_OT_popup_road_object_traffic_light_properties,
    DSC_OT_road_object_stop_line,
    DSC_OT_esmini_preview_start,
    DSC_OT_esmini_preview_step,
    DSC_OT_esmini_open_preferences,
    DSC_OT_esmini_preview_stop,
    DSC_Properties,
)

def register():
    global dsc_custom_icons
    global dsc_road_sign_previews

    # Load custom button icons
    dsc_custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    dsc_custom_icons.load('road_straight', os.path.join(icons_dir, 'road_straight.png'), 'IMAGE')
    dsc_custom_icons.load('road_arc', os.path.join(icons_dir, 'road_arc.png'), 'IMAGE')
    dsc_custom_icons.load('road_clothoid', os.path.join(icons_dir, 'road_clothoid.png'), 'IMAGE')
    dsc_custom_icons.load('road_parametric_polynomial', os.path.join(icons_dir, 'road_parametric_polynomial.png'), 'IMAGE')
    dsc_custom_icons.load('junction_4way', os.path.join(icons_dir, 'junction_4way.png'), 'IMAGE')
    dsc_custom_icons.load('junction_area', os.path.join(icons_dir, 'junction_area.png'), 'IMAGE')
    dsc_custom_icons.load('junction_connecting_road', os.path.join(icons_dir, 'junction_connecting_road.png'), 'IMAGE')
    dsc_custom_icons.load('road_object_sign', os.path.join(icons_dir, 'road_object_sign.png'), 'IMAGE')
    dsc_custom_icons.load('road_object_traffic_light', os.path.join(icons_dir, 'road_object_traffic_light.png'), 'IMAGE')
    dsc_custom_icons.load('road_object_stop_line', os.path.join(icons_dir, 'road_object_stop_line.png'), 'IMAGE')
    dsc_custom_icons.load('road_object_stencil', os.path.join(icons_dir, 'road_object_stencil.png'), 'IMAGE')
    dsc_custom_icons.load('trajectory_nurbs', os.path.join(icons_dir, 'trajectory_nurbs.png'), 'IMAGE')
    dsc_custom_icons.load('trajectory_polyline', os.path.join(icons_dir, 'trajectory_polyline.png'), 'IMAGE')

    # Create a new preview collection to use in other modules
    dsc_road_sign_previews = bpy.utils.previews.new()

    # Register all addon classes
    for c in classes:
        bpy.utils.register_class(c)
    # Register export menu
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    # Register addon property group
    bpy.types.Scene.dsc_properties = bpy.props.PointerProperty(type=DSC_Properties)

    # Restore persisted esmini path for current runtime even if preferences were not explicitly saved.
    addon_prefs = _resolve_addon_preferences(bpy.context)
    if addon_prefs is not None and not addon_prefs.esmini_library_path:
        persisted_path = _load_esmini_library_path_from_config()
        if persisted_path:
            addon_prefs.esmini_library_path = persisted_path

def unregister():
    global dsc_custom_icons
    esmini_preview.ensure_preview_stopped_on_unregister()
    # Unregister export menu
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    #  Unregister all addon classes
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    # Get rid of icon collections
    bpy.utils.previews.remove(dsc_custom_icons)
    bpy.utils.previews.remove(dsc_road_sign_previews)
    # Get rid of addon property group
    del bpy.types.Scene.dsc_properties

if __name__ == '__main__':
    register()

