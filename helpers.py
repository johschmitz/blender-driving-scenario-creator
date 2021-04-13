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
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
from mathutils.geometry import intersect_line_plane
from mathutils import Vector

from math import pi


def get_new_id_opendrive(context):
    '''
        Generate and return new ID for OpenDRIVE objects using a dummy object
        for storage.
    '''
    dummy_obj = context.scene.objects.get('id_next')
    if dummy_obj is None:
        dummy_obj = bpy.data.objects.new('id_next',None)
        # Do not render
        dummy_obj.hide_viewport = True
        dummy_obj.hide_render = True
        dummy_obj['id_next'] = 0
        link_object_opendrive(context, dummy_obj)
    id_next = dummy_obj['id_next']
    dummy_obj['id_next'] += 1
    return id_next

def link_object_opendrive(context, obj):
    if not 'OpenDRIVE' in bpy.data.collections:
        collection = bpy.data.collections.new('OpenDRIVE')
        context.scene.collection.children.link(collection)
    collection = bpy.data.collections.get('OpenDRIVE')
    collection.objects.link(obj)

def link_object_openscenario(context, obj):
    if not 'OpenSCENARIO' in bpy.data.collections:
        collection = bpy.data.collections.new('OpenSCENARIO')
        context.scene.collection.children.link(collection)
    collection = bpy.data.collections.get('OpenSCENARIO')
    collection.objects.link(obj)

def select_activate_object(context, obj):
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
        if 't_road_planView_geometry' or 't_junction_e_junction_type' in obj:
            return hit, point, obj
    else:
        return False, point, None

def point_to_road_connector(obj, point):
    '''
        Get a snapping point and heading from an existing road.
    '''
    dist_start = (Vector(obj['point_start']) - point).length
    dist_end = (Vector(obj['point_end']) - point).length
    if dist_start < dist_end:
        return Vector(obj['point_start']), obj['t_road_planView_geometry_hdg'] - pi
    else:
        return Vector(obj['point_end']), obj['t_road_planView_geometry_hdg']

def point_to_junction_connector(obj, point):
    '''
        Get a snapping point and heading from an existing junction.
    '''
    # Calculate which connector point is closest to input point
    dist_down = (Vector(obj['point_down']) - point).length
    dist_left = (Vector(obj['point_left']) - point).length
    dist_up = (Vector(obj['point_up']) - point).length
    dist_right = (Vector(obj['point_right']) - point).length
    dist_lst = [dist_down, dist_left, dist_up, dist_right]
    arg_min_dist = dist_lst.index(min(dist_lst))
    vec_connector_lst = [Vector(obj['point_down']), Vector(obj['point_left']),
               Vector(obj['point_up']), Vector(obj['point_right'])]
    vec_hdg_lst = [obj['hdg_down'], obj['hdg_left'], obj['hdg_up'], obj['hdg_right']]
    return vec_connector_lst[arg_min_dist], vec_hdg_lst[arg_min_dist]

def raycast_mouse_to_object_else_xy(context, event):
    '''
        Get a snapping point and heading or just an xy-plane intersection point.
    '''
    hit, point_raycast, obj = raycast_mouse_to_odr_object(context, event, obj_type='line')
    if not hit:
        point_raycast = mouse_to_xy_plane(context, event)
        return False, point_raycast, 0
    else:
        if 't_road_planView_geometry' in obj:
            point, heading = point_to_road_connector(obj, point_raycast)
            return True, point, heading
        if 't_junction_e_junction_type' in obj:
            point, heading = point_to_junction_connector(obj, point_raycast)
            return True, point, heading