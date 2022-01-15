
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

def assign_road_materials(obj):
    '''
       init road object's materials
    '''
    default_materials = {
        'road_asphalt': [.3, .3, .3, 1],
        'road_mark': [.9, .9, .9, 1],
        'grass': [.05, .6, .01, 1],
        'double_yellow_line': [.6, .356, .022, 1]
    }
    for key in default_materials.keys():
        material = bpy.data.materials.get(key)
        if material is None:
            material = bpy.data.materials.new(name=key)
            material.diffuse_color = (default_materials[key][0],
                                      default_materials[key][1],
                                      default_materials[key][2],
                                      default_materials[key][3])
        obj.data.materials.append(material)


def get_material_index(obj, material_name):
    '''
       get material by type
    '''
    for idx, material in enumerate(obj.data.materials):
        if material.name == material_name:
            return idx
    return None
