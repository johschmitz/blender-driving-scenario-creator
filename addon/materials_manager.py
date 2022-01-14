# ******************************************************************************/
# coding=utf-8
# File Name     : materials_manager
# Description   : we neet extend it for custom materials, not only color
# 1.Date        : 2022/1/11 10:43
# Author        : lyfs
# ******************************************************************************/
import bpy
import os

# init road object's materials
def assign_road_materials(obj):
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
    obj.data.materials.append(bpy.data.materials.get(ASPHALT))
    obj.data.materials.append(bpy.data.materials.get(DOUBLE_YELLOW_LINE))


# get material by type
def get_material_index(obj, material_name):
    for idx, material in enumerate(obj.data.materials):
        if material.name == material_name:
            return idx
    return None
