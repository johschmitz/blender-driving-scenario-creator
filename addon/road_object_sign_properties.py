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


def get_road_sign_texture_dir_and_mapping():
    """Return directory and mapping from sign type string to texture file names."""
    road_sign_texture_mapping = {
        'halt_vorfahrt_gewaehren': 'Zeichen_206_-_Halt_Vorfahrt_gewaehren',
        'vorfahrt_gewaehren': 'Zeichen_205_-_Vorfahrt_gewaehren',
        'vorfahrt': 'Zeichen_301_-_Vorfahrt',
        'vorfahrtstrasse': 'Zeichen_306_-_Vorfahrtstrasse',
        'zulaessige_hoechstgeschwindigkeit_5': 'Zeichen_274-5_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_10': 'Zeichen_274-10_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_20': 'Zeichen_274-20_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_30': 'Zeichen_274-30_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_40': 'Zeichen_274-40_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_50': 'Zeichen_274-50_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_60': 'Zeichen_274-60_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_70': 'Zeichen_274-70_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_80': 'Zeichen_274-80_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_90': 'Zeichen_274-90_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_100': 'Zeichen_274-100_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_110': 'Zeichen_274-110_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_120': 'Zeichen_274-120_-_Zulaessige_Hoechstgeschwindigkeit',
        'zulaessige_hoechstgeschwindigkeit_130': 'Zeichen_274-130_-_Zulaessige_Hoechstgeschwindigkeit',
        'ende_saemtlicher_streckenverbote': 'Zeichen_282_-_Ende_saemtlicher_Streckenverbote',
    }

    return road_sign_texture_mapping

def get_road_sign_type_subtype_mapping():
    """Return OpenDRIVE/vzkat type and subtype of a sign."""
    road_sign_type_subtype_mapping = {
        'halt_vorfahrt_gewaehren': {"type": "206", "subtype": ""},
        'vorfahrt_gewaehren': {"type": "205", "subtype": ""},
        'vorfahrt': {"type": "306", "subtype": ""},
        'vorfahrtstrasse': {"type": "301", "subtype": ""},
        'zulaessige_hoechstgeschwindigkeit_5': {"type": "274", "subtype": "5"},
        'zulaessige_hoechstgeschwindigkeit_10': {"type": "274", "subtype": "10"},
        'zulaessige_hoechstgeschwindigkeit_20': {"type": "274", "subtype": "20"},
        'zulaessige_hoechstgeschwindigkeit_30': {"type": "274", "subtype": "30"},
        'zulaessige_hoechstgeschwindigkeit_40': {"type": "274", "subtype": "40"},
        'zulaessige_hoechstgeschwindigkeit_50': {"type": "274", "subtype": "50"},
        'zulaessige_hoechstgeschwindigkeit_60': {"type": "274", "subtype": "60"},
        'zulaessige_hoechstgeschwindigkeit_70': {"type": "274", "subtype": "70"},
        'zulaessige_hoechstgeschwindigkeit_80': {"type": "274", "subtype": "80"},
        'zulaessige_hoechstgeschwindigkeit_90': {"type": "274", "subtype": "90"},
        'zulaessige_hoechstgeschwindigkeit_100': {"type": "274", "subtype": "100"},
        'zulaessige_hoechstgeschwindigkeit_110': {"type": "274", "subtype": "110"},
        'zulaessige_hoechstgeschwindigkeit_120': {"type": "274", "subtype": "120"},
        'zulaessige_hoechstgeschwindigkeit_130': {"type": "274", "subtype": "130"},
        'ende_saemtlicher_streckenverbote': {"type": "282", "subtype": ""},
    }

    return road_sign_type_subtype_mapping

def get_road_sign_value_mapping():
    """Return OpenDRIVE/vzkat type and subtype of a sign."""
    road_sign_value_mapping = {
        'halt_vorfahrt_gewaehren': 0,
        'vorfahrt_gewaehren': 0,
        'vorfahrt': 0,
        'vorfahrtstrasse': 0,
        'zulaessige_hoechstgeschwindigkeit_5': 5,
        'zulaessige_hoechstgeschwindigkeit_10': 10,
        'zulaessige_hoechstgeschwindigkeit_20': 20,
        'zulaessige_hoechstgeschwindigkeit_30': 30,
        'zulaessige_hoechstgeschwindigkeit_40': 40,
        'zulaessige_hoechstgeschwindigkeit_50': 50,
        'zulaessige_hoechstgeschwindigkeit_60': 60,
        'zulaessige_hoechstgeschwindigkeit_70': 70,
        'zulaessige_hoechstgeschwindigkeit_80': 80,
        'zulaessige_hoechstgeschwindigkeit_90': 90,
        'zulaessige_hoechstgeschwindigkeit_100': 100,
        'zulaessige_hoechstgeschwindigkeit_110': 110,
        'zulaessige_hoechstgeschwindigkeit_120': 120,
        'zulaessige_hoechstgeschwindigkeit_130': 130,
        'ende_saemtlicher_streckenverbote': 0,
    }

    return road_sign_value_mapping

def callback_selected(self, context):
    self.update_selected(context)

class DSC_road_object_sign_property_item(bpy.types.PropertyGroup):
    idx: bpy.props.IntProperty(min=0)
    name: bpy.props.StringProperty(name='Name')
    texture_name: bpy.props.StringProperty(name='Texture name')
    type: bpy.props.StringProperty(name='Type')
    subtype: bpy.props.StringProperty(name='Subtype')
    value: bpy.props.IntProperty(name='Value', min=0, max=500, step=1)
    selected: bpy.props.BoolProperty(default=False, update=callback_selected)

    def update_selected(self, context):
        '''Callback that enables selection of a single road sign item.'''
        # Avoid updating recursively
        if context.scene.dsc_properties.road_object_sign_properties.lock_signs:
            return
        context.scene.dsc_properties.road_object_sign_properties.lock_signs = True

        # Unselect all other items
        for sign in context.scene.dsc_properties.road_object_sign_properties.sign_catalog:
            if self.idx != sign.idx:
                sign.selected = False

        # Unlock updating
        context.scene.dsc_properties.road_object_sign_properties.lock_signs = False

class DSC_road_object_sign_properties(bpy.types.PropertyGroup):

    pole_height: bpy.props.FloatProperty(default=2.20, min=1.0, max=10.0, step=10)
    width: bpy.props.FloatProperty(default=0.6, min=0.5, max=1.0, step=10)
    sign_catalog: bpy.props.CollectionProperty(type=DSC_road_object_sign_property_item)
    texture_directory: bpy.props.StringProperty(name='Texture directory')

    # A lock for deactivating callbacks
    lock_signs: bpy.props.BoolProperty(default=False)

    def init(self):
        # Avoid updating callback
        self.lock_signs = True
        self.sign_catalog.clear()

        self.texture_directory =  os.path.join(os.path.dirname(__file__), 'signs/vzkat')

        road_sign_texture_mapping = get_road_sign_texture_dir_and_mapping()
        road_sign_type_subtype_mapping = get_road_sign_type_subtype_mapping()
        road_sign_value_mapping = get_road_sign_value_mapping()

        idx = 0
        for sign_name, sign_texture_name in road_sign_texture_mapping.items():
            sign = self.sign_catalog.add()
            sign.name = sign_name
            sign.texture_name = sign_texture_name
            sign.type = road_sign_type_subtype_mapping[sign_name]["type"]
            sign.subtype = road_sign_type_subtype_mapping[sign_name]["subtype"]
            sign.value = road_sign_value_mapping[sign_name]
            sign.selected = False
            sign.idx = idx
            idx += 1

        # Re-enable updating callback
        self.lock_signs = False