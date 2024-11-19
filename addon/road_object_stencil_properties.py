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


def get_road_stencil_texture_dir_and_mapping():
    """Return directory and mapping from stencil type string to texture file names."""
    road_stencil_texture_mapping = {
        'fahrbahnmarkierung_pfeil_g': 'Fahrbahnmarkierung_Pfeil_G',
        'fahrbahnmarkierung_pfeil_gl': 'Fahrbahnmarkierung_Pfeil_GL',
        'fahrbahnmarkierung_pfeil_gr': 'Fahrbahnmarkierung_Pfeil_GR',
        'fahrbahnmarkierung_pfeil_l': 'Fahrbahnmarkierung_Pfeil_L',
        'fahrbahnmarkierung_pfeil_r': 'Fahrbahnmarkierung_Pfeil_R',
        'fahrbahnmarkierung_pfeil_lr': 'Fahrbahnmarkierung_Pfeil_LR',
        'fahrbahnmarkierung_pfeil_vl': 'Fahrbahnmarkierung_Pfeil_VL',
        'fahrbahnmarkierung_pfeil_vr': 'Fahrbahnmarkierung_Pfeil_VR',
    }

    return road_stencil_texture_mapping

def get_road_stencil_type_subtype_mapping():
    """Return OpenDRIVE/vzkat type and subtype of a stencil."""
    road_stencil_type_subtype_mapping = {
        'fahrbahnmarkierung_pfeil_g': {"type": "297", "subtype": "G"},
        'fahrbahnmarkierung_pfeil_gl': {"type": "297", "subtype": "GL"},
        'fahrbahnmarkierung_pfeil_gr': {"type": "297", "subtype": "GR"},
        'fahrbahnmarkierung_pfeil_l': {"type": "297", "subtype": "L"},
        'fahrbahnmarkierung_pfeil_r': {"type": "297", "subtype": "R"},
        'fahrbahnmarkierung_pfeil_lr': {"type": "297", "subtype": "LR"},
        'fahrbahnmarkierung_pfeil_vl': {"type": "297", "subtype": "VL"},
        'fahrbahnmarkierung_pfeil_vr': {"type": "297", "subtype": "VR"},
    }

    return road_stencil_type_subtype_mapping

def callback_selected(self, context):
    self.update_selected(context)

class DSC_road_object_stencil_property_item(bpy.types.PropertyGroup):
    idx: bpy.props.IntProperty(min=0)
    name: bpy.props.StringProperty(name='Name')
    texture_name: bpy.props.StringProperty(name='Texture name')
    type: bpy.props.StringProperty(name='Type')
    subtype: bpy.props.StringProperty(name='Subtype')
    selected: bpy.props.BoolProperty(default=False, update=callback_selected)
    selected_previously: bpy.props.BoolProperty(default=False)

    def update_selected(self, context):
        '''Callback that enables selection of a single road stencil item.'''
        # Avoid updating recursively
        if context.scene.dsc_properties.road_object_stencil_properties.lock_stencils:
            return
        context.scene.dsc_properties.road_object_stencil_properties.lock_stencils = True

        # Disable unselecting the selected item
        if self.selected_previously == True:
            self.selected = True
        else:
            self.selected_previously = True

        # Unselect all other items
        for stencil in context.scene.dsc_properties.road_object_stencil_properties.stencil_catalog:
            if self.idx != stencil.idx:
                stencil.selected = False
                stencil.selected_previously = False

        # Unlock updating
        context.scene.dsc_properties.road_object_stencil_properties.lock_stencils = False

class DSC_road_object_stencil_properties(bpy.types.PropertyGroup):

    width: bpy.props.FloatProperty(default=0.6, min=0.5, max=1.0, step=10)
    stencil_catalog: bpy.props.CollectionProperty(type=DSC_road_object_stencil_property_item)
    texture_directory: bpy.props.StringProperty(name='Texture directory')

    # A lock for deactivating callbacks
    lock_stencils: bpy.props.BoolProperty(default=False)

    def init(self):
        # Avoid updating callback
        self.lock_stencils = True
        self.stencil_catalog.clear()

        self.texture_directory =  os.path.join(os.path.dirname(__file__), 'stencils/de/')

        road_stencil_texture_mapping = get_road_stencil_texture_dir_and_mapping()
        road_stencil_type_subtype_mapping = get_road_stencil_type_subtype_mapping()

        idx = 0
        for stencil_name, stencil_texture_name in road_stencil_texture_mapping.items():
            stencil = self.stencil_catalog.add()
            stencil.name = stencil_name
            stencil.texture_name = stencil_texture_name
            stencil.type = road_stencil_type_subtype_mapping[stencil_name]["type"]
            stencil.subtype = road_stencil_type_subtype_mapping[stencil_name]["subtype"]
            stencil.selected = False
            stencil.idx = idx
            idx += 1

        # Select first item by default
        self.stencil_catalog[0].selected = True
        self.stencil_catalog[0].selected_previously = True

        # Re-enable updating callback
        self.lock_stencils = False