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
import bmesh
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
from mathutils.geometry import intersect_line_plane
from mathutils import Vector, Matrix
from idprop.types import IDPropertyArray

from math import pi


def get_new_id_opendrive(context):
    '''
        Generate and return new ID for OpenDRIVE objects using a dummy object
        for storage.
    '''
    dummy_obj = context.scene.objects.get('id_xodr_next')
    if dummy_obj is None:
        dummy_obj = bpy.data.objects.new('id_xodr_next',None)
        # Do not render
        dummy_obj.hide_viewport = True
        dummy_obj.hide_render = True
        dummy_obj['id_xodr_next'] = 0
        link_object_opendrive(context, dummy_obj)
    id_next = dummy_obj['id_xodr_next']
    dummy_obj['id_xodr_next'] += 1
    return id_next

def get_new_id_openscenario(context):
    '''
        Generate and return new ID for OpenSCENARIO objects using a dummy object
        for storage.
    '''
    dummy_obj = context.scene.objects.get('id_xosc_next')
    if dummy_obj is None:
        dummy_obj = bpy.data.objects.new('id_xosc_next',None)
        # Do not render
        dummy_obj.hide_viewport = True
        dummy_obj.hide_render = True
        dummy_obj['id_xosc_next'] = 0
        link_object_openscenario(context, dummy_obj)
    id_next = dummy_obj['id_xosc_next']
    dummy_obj['id_xosc_next'] += 1
    return id_next

def link_object_opendrive(context, obj):
    '''
        Link object to OpenDRIVE scene collection.
    '''
    if not 'OpenDRIVE' in bpy.data.collections:
        collection = bpy.data.collections.new('OpenDRIVE')
        context.scene.collection.children.link(collection)
    collection = bpy.data.collections.get('OpenDRIVE')
    collection.objects.link(obj)

def link_object_openscenario(context, obj):
    '''
        Link object to OpenSCENARIO scene collection.
    '''
    if not 'OpenSCENARIO' in bpy.data.collections:
        collection = bpy.data.collections.new('OpenSCENARIO')
        context.scene.collection.children.link(collection)
    collection = bpy.data.collections.get('OpenSCENARIO')
    collection.objects.link(obj)

def get_object_xodr_by_id(context, id_xodr):
    '''
        Get reference to OpenDRIVE object by ID.
    '''
    collection = bpy.data.collections.get('OpenDRIVE')
    for obj in collection.objects:
        if 'id_xodr' in obj:
            if obj['id_xodr'] == id_xodr:
                return obj

def create_object_xodr_links(context, obj, link_type, id_other, cp_type):
    '''
        Create OpenDRIVE predecessor/successor linkage for current object with
        other object.
    '''
    if 'road' in obj.name:
        if link_type == 'start':
            obj['link_predecessor'] =  id_other
            obj['link_predecessor_cp'] = cp_type
        else:
            obj['link_successor'] = id_other
            obj['link_successor_cp'] = cp_type
    elif 'junction' in obj.name:
        if link_type == 'start':
            obj['incoming_roads']['cp_down'] = id_other
        else:
            obj['incoming_roads']['cp_up'] = id_other
    obj_other = get_object_xodr_by_id(context, id_other)
    if 'road' in obj_other.name:
        if 'road' in obj.name:
            if link_type == 'start':
                cp_type_other = 'cp_start'
            else:
                cp_type_other = 'cp_end'
        if 'junction' in obj.name:
            if link_type == 'start':
                cp_type_other = 'cp_down'
            else:
                cp_type_other = 'cp_up'
        if cp_type == 'cp_start':
            obj_other['link_predecessor'] = obj['id_xodr']
            obj_other['link_predecessor_cp'] = cp_type_other
        else:
            obj_other['link_successor'] = obj['id_xodr']
            obj_other['link_successor_cp'] = cp_type_other
    elif 'junction' in obj_other.name:
        obj_other['incoming_roads'][cp_type] = obj['id_xodr']

def select_activate_object(context, obj):
    '''
        Select and activate object.
    '''
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    context.view_layer.objects.active = obj

def mouse_to_xy_plane(context, event):
    '''
        Convert mouse pointer position to 3D point in xy-plane.
    '''
    region = context.region
    rv3d = context.region_data
    co2d = (event.mouse_region_x, event.mouse_region_y)
    view_vector_mouse = region_2d_to_vector_3d(region, rv3d, co2d)
    ray_origin_mouse = region_2d_to_origin_3d(region, rv3d, co2d)
    point = intersect_line_plane(ray_origin_mouse, ray_origin_mouse + view_vector_mouse,
        (0, 0, 0), (0, 0, 1), False)
    # Fix parallel plane issue
    if point is None:
        point = intersect_line_plane(ray_origin_mouse, ray_origin_mouse + view_vector_mouse,
            (0, 0, 0), view_vector_mouse, False)
    return point

def raycast_mouse_to_odr_object(context, event, obj_type):
    '''
        Convert mouse pointer position to hit obj of OpenDRIVE type.
    '''
    region = context.region
    rv3d = context.region_data
    co2d = (event.mouse_region_x, event.mouse_region_y)
    view_vector_mouse = region_2d_to_vector_3d(region, rv3d, co2d)
    ray_origin_mouse = region_2d_to_origin_3d(region, rv3d, co2d)
    hit, point, normal, index_face, obj, matrix_world = context.scene.ray_cast(
        depsgraph=context.view_layer.depsgraph,
        origin=ray_origin_mouse,
        direction=view_vector_mouse)
    # Filter object type
    if hit:
        if 'geometry' or 't_junction_e_junction_type' in obj:
            return hit, point, obj
    else:
        return False, point, None

def point_to_road_connector(obj, point):
    '''
        Get a snapping point and heading from an existing road.
    '''
    dist_start = (Vector(obj['cp_start']) - point).length
    dist_end = (Vector(obj['cp_end']) - point).length
    if dist_start < dist_end:
        return 'cp_start', Vector(obj['cp_start']), obj['geometry_hdg_start'] - pi
    else:
        return 'cp_end', Vector(obj['cp_end']), obj['geometry_hdg_end']

def point_to_junction_connector(obj, point):
    '''
        Get a snapping point and heading from an existing junction.
    '''
    # Calculate which connecting point is closest to input point
    cps = ['cp_left', 'cp_down', 'cp_right', 'cp_up']
    distances = []
    cp_vectors = []
    for cp in cps:
        distances.append((Vector(obj[cp]) - point).length)
        cp_vectors.append(Vector(obj[cp]))
    headings = [obj['hdg_left'], obj['hdg_down'], obj['hdg_right'], obj['hdg_up']]
    arg_min_dist = distances.index(min(distances))
    return cps[arg_min_dist], cp_vectors[arg_min_dist], headings[arg_min_dist]

def project_point_vector(point_selected, point_start, heading_start):
    '''
        Project selected point to vector.
    '''
    vector_selected = point_selected - point_start
    if vector_selected.length > 0:
        vector_object = Vector((1.0, 0.0, 0.0))
        vector_object.rotate(Matrix.Rotation(heading_start, 4, 'Z'))
        return point_start + vector_selected.project(vector_object)
    else:
        return point_selected

def raycast_mouse_to_object_else_xy(context, event, snap):
    '''
        Get a snapping point and heading or just an xy-plane intersection point.
    '''
    hit, point_raycast, obj = raycast_mouse_to_odr_object(context, event, obj_type='line')
    if not hit or not snap:
        point_raycast = mouse_to_xy_plane(context, event)
        return False, -1, 'cp_none', point_raycast, 0
    else:
        if 'geometry' in obj:
            cp_type, cp, heading = point_to_road_connector(obj, point_raycast)
            id_xodr = obj['id_xodr']
            return True, id_xodr, cp_type, cp, heading
        if 't_junction_e_junction_type' in obj:
            cp_type, cp, heading = point_to_junction_connector(obj, point_raycast)
            id_xodr = obj['id_xodr']
            return True, id_xodr, cp_type, cp, heading

def assign_road_materials(obj):
    '''
        Assign materials for asphalt and markings to object.
    '''
    # Get road material
    material = bpy.data.materials.get("road_asphalt")
    if material is None:
        # Create material
        material = bpy.data.materials.new(name="road_asphalt")
        material.diffuse_color = [.3,.3,.3,1]
    obj.data.materials.append(material)
    # Get lane line material
    material = bpy.data.materials.get("road_surface_marking")
    if material is None:
        # Create material
        material = bpy.data.materials.new(name="road_surface_marking")
        material.diffuse_color = [.9,.9,.9,1]
    # Assign to object's 2nd material slot
    obj.data.materials.append(material)

def get_material_index(obj, material_name):
    '''
        Return index of material slot based on material name.
    '''
    for idx, material in enumerate(obj.data.materials):
        if material.name == material_name:
            return idx
    return None

def replace_mesh(obj, mesh):
    # Delete old mesh data
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    verts = [v for v in bm.verts]
    bmesh.ops.delete(bm, geom=verts, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    # Set new mesh data
    obj.data = mesh
