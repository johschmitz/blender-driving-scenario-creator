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
import addon_utils
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d
from mathutils.geometry import intersect_line_plane
from mathutils import Vector, Matrix

from math import pi, inf


def get_new_id_opendrive(context):
    '''
        Generate and return new ID for OpenDRIVE objects using a dummy object
        for storage.
    '''
    dummy_obj = context.scene.objects.get('id_odr_next')
    if dummy_obj is None:
        dummy_obj = bpy.data.objects.new('id_odr_next', None)
        # Do not render
        dummy_obj.hide_viewport = True
        dummy_obj.hide_render = True
        dummy_obj['id_odr_next'] = 1
        link_object_opendrive(context, dummy_obj)
    id_next = dummy_obj['id_odr_next']
    dummy_obj['id_odr_next'] += 1
    return id_next

def get_new_id_openscenario(context):
    '''
        Generate and return new ID for OpenSCENARIO objects using a dummy object
        for storage.
    '''
    dummy_obj = context.scene.objects.get('id_osc_next')
    if dummy_obj is None:
        dummy_obj = bpy.data.objects.new('id_osc_next',None)
        # Do not render
        dummy_obj.hide_viewport = True
        dummy_obj.hide_render = True
        dummy_obj['id_osc_next'] = 0
        link_object_openscenario(context, dummy_obj, subcategory=None)
    id_next = dummy_obj['id_osc_next']
    dummy_obj['id_osc_next'] += 1
    return id_next

def ensure_collection_dsc(context):
    if not 'Driving Scenario Creator' in bpy.data.collections:
        collection = bpy.data.collections.new('Driving Scenario Creator')
        context.scene.collection.children.link(collection)
        # Store addon version
        version = (0, 0, 0)
        for mod in addon_utils.modules():
            if mod.bl_info['name'] == 'Driving Scenario Creator':
                version = mod.bl_info['version']
        version_obj = bpy.data.objects.new('dsc_addon_version', None)
        # Do not render
        version_obj.hide_viewport = True
        version_obj.hide_render = True
        version_obj['dsc_addon_version'] = version
        link_object_opendrive(context, version_obj)
    else:
        collection = bpy.data.collections['Driving Scenario Creator']
    return collection

def ensure_collection_opendrive(context):
    collection_dsc = ensure_collection_dsc(context)
    if not 'OpenDRIVE' in collection_dsc.children:
        collection = bpy.data.collections.new('OpenDRIVE')
        collection_dsc.children.link(collection)
        return collection
    else:
        collection = bpy.data.collections['OpenDRIVE']
        return collection

def ensure_collection_openscenario(context):
    collection_dsc = ensure_collection_dsc(context)
    if not 'OpenSCENARIO' in collection_dsc.children:
        collection = bpy.data.collections.new('OpenSCENARIO')
        collection_dsc.children.link(collection)
        return collection
    else:
        collection = bpy.data.collections['OpenSCENARIO']
        return collection

def ensure_subcollection_openscenario(context, subcollection):
    collection_osc = ensure_collection_openscenario(context)
    if not subcollection in collection_osc.children:
        collection = bpy.data.collections.new(subcollection)
        collection_osc.children.link(collection)
        return collection
    else:
        collection = bpy.data.collections[subcollection]
        return collection

def collection_exists(collection_path):
    '''
        Check if a (sub)collection with path given as list exists.
    '''
    if not isinstance(collection_path, list):
        collection_path = [collection_path]
    root = collection_path.pop(0)
    if not root in bpy.data.collections:
        return False
    else:
        if len(collection_path) == 0:
            return True
        else:
            return collection_exists(collection_path)

def link_object_opendrive(context, obj):
    '''
        Link object to OpenDRIVE scene collection.
    '''
    ensure_collection_opendrive(context)
    collection = bpy.data.collections.get('OpenDRIVE')
    collection.objects.link(obj)

def link_object_openscenario(context, obj, subcategory=None):
    '''
        Link object to OpenSCENARIO scene collection.
    '''
    if subcategory is None:
        collection = ensure_collection_openscenario(context)
        collection.objects.link(obj)
    else:
        collection = ensure_subcollection_openscenario(context, subcategory)
        collection.objects.link(obj)

def get_object_xodr_by_id(id_odr):
    '''
        Get reference to OpenDRIVE object by ID, return None if not found.
    '''
    collection = bpy.data.collections.get('OpenDRIVE')
    for obj in collection.objects:
        if 'id_odr' in obj:
            if obj['id_odr'] == id_odr:
                return obj

def create_object_xodr_links(obj, link_type, cp_type_other, id_other, id_extra, id_lane):
    '''
        Create OpenDRIVE predecessor/successor linkage for current object with
        other object.
    '''

    # TODO try to refactor this whole method and better separate all cases:
    #   1. Road to road with all start and end combinations
    #   2. Junction to road and road to junction with start and end combinations
    #   3. Road to direct junction and direct junction to road

    # Case: road to junction or junction to junction
    obj_other = get_object_xodr_by_id(id_other)
    if id_extra != None:
        obj_extra = get_object_xodr_by_id(id_extra)
    else:
        obj_extra = None

    # 1. Set the link parameters of the object itself
    if 'road' in obj.name:
        if link_type == 'start':
            if obj['dsc_type'].startswith('road_'):
                if obj['road_split_type'] == 'none':
                    obj['link_predecessor_id_l'] = id_other
                else:
                    # Check connected to left or right side
                    if obj['lanes_left_num'] > obj['road_split_lane_idx']:
                        obj['link_predecessor_id_r'] = id_other
                        obj['link_predecessor_cp_r'] = cp_type_other
                    else:
                        obj['link_predecessor_id_l'] = id_other
                if id_extra == None:
                    # Case: road to road
                    obj['link_predecessor_cp_l'] = cp_type_other
                else:
                    if obj_extra != None and obj_extra['dsc_type'] == 'junction_direct':
                        # Case: road to direct junction
                        obj['link_predecessor_cp_l'] = cp_type_other
                        obj['id_direct_junction_start'] = id_extra
                    else:
                        # Case: connecting incoming road to junction
                        obj['link_predecessor_cp_l'] = 'junction_joint'
            elif obj['dsc_type'] == 'junction_connecting_road':
                # Case: connecting road (in junction) to incoming road
                obj['id_junction'] = id_other
                obj['id_joint_start'] = id_extra
                obj['id_lane_joint_start'] = id_lane
                if obj_other['joints'][id_extra]['id_incoming'] != None:
                    obj['link_predecessor_id_l'] = obj_other['joints'][id_extra]['id_incoming']
                    obj['link_predecessor_cp_l'] = obj_other['joints'][id_extra]['contact_point_type']
        else:
            if obj['dsc_type'].startswith('road_'):
                obj['link_successor_id_l'] = id_other
                if obj['road_split_type'] == 'none':
                    obj['link_successor_id_l'] = id_other
                else:
                    # Check connected to left or right side
                    if obj['lanes_left_num'] > obj['road_split_lane_idx']:
                        obj['link_successor_id_r'] = id_other
                        obj['link_successor_cp_r'] = cp_type_other
                    else:
                        obj['link_successor_id_l'] = id_other
                if id_extra == None:
                    # Case: road to road
                    obj['link_successor_cp_l'] = cp_type_other
                else:
                    if obj_extra != None and obj_extra['dsc_type'] == 'junction_direct':
                        # Case: road to direct junction
                        obj['link_successor_cp_l'] = cp_type_other
                        obj['id_direct_junction_end'] = id_extra
                    else:
                        # Case: connecting incoming road to junction
                        obj['link_successor_cp_l'] = 'junction_joint'
            elif obj['dsc_type'] == 'junction_connecting_road':
                # Case: connecting road (in junction) to incoming road
                obj['id_junction'] = id_other
                obj['id_joint_end'] = id_extra
                obj['id_lane_joint_end'] = id_lane
                if obj_other['joints'][id_extra]['id_incoming'] != None:
                    obj['link_successor_id_l'] = obj_other['joints'][id_extra]['id_incoming']
                    obj['link_successor_cp_l'] = obj_other['joints'][id_extra]['contact_point_type']
    elif 'junction' in obj.name:
        # Case: junction to road
        if link_type == 'start':
            id_joint = 0
        else:
            id_joint = 2
        obj['joints'][id_joint]['id_incoming'] = id_other
        obj['joints'][id_joint]['contact_point_type'] = cp_type_other
        # Connect connecting roads of this junction
        for obj_jcr in bpy.data.collections['OpenDRIVE'].objects:
            if obj_jcr.name.startswith('junction_connecting_road'):
                if obj_jcr['id_junction'] == obj['id_odr']:
                    if obj_jcr['id_joint_start'] == id_joint:
                        obj_jcr['link_predecessor_id_l'] = id_other
                        obj_jcr['link_predecessor_cp_l'] = cp_type_other
                    elif obj_jcr['id_joint_end'] == id_joint:
                        obj_jcr['link_successor_id_l'] = id_other
                        obj_jcr['link_successor_cp_l'] = cp_type_other


    # 2. Set the link parameters of the other object we are linking with
    if obj_other != None:
        if 'road' in obj_other.name:
            if 'road' in obj.name:
                # Case: road to road
                if link_type == 'start':
                    cp_type = 'cp_start_l'
                else:
                    cp_type = 'cp_end_l'
            if 'junction' in obj.name:
                # Case: junction to road
                cp_type = 'junction_joint'
            if cp_type_other == 'cp_start_l':
                obj_other['link_predecessor_id_l'] = obj['id_odr']
                obj_other['link_predecessor_cp_l'] = cp_type
                if id_extra != None:
                    obj_other['id_direct_junction_start'] = id_extra
                elif 'id_direct_junction_start' in obj_other:
                    # Clean up old direct junction link
                    del obj_other['id_direct_junction_start']
            elif cp_type_other == 'cp_start_r':
                obj_other['link_predecessor_id_r'] = obj['id_odr']
                obj_other['link_predecessor_cp_r'] = cp_type
                if id_extra != None:
                    obj_other['id_direct_junction_start'] = id_extra
                elif 'id_direct_junction_start' in obj_other:
                    # Clean up old direct junction link
                    del obj_other['id_direct_junction_start']
            elif cp_type_other == 'cp_end_l':
                obj_other['link_successor_id_l'] = obj['id_odr']
                obj_other['link_successor_cp_l'] = cp_type
                if id_extra != None:
                    obj_other['id_direct_junction_end'] = id_extra
                elif 'id_direct_junction_end' in obj_other:
                    # Clean up old direct junction link
                    del obj_other['id_direct_junction_end']
            elif cp_type_other == 'cp_end_r':
                obj_other['link_successor_id_r'] = obj['id_odr']
                obj_other['link_successor_cp_r'] = cp_type
                if id_extra != None:
                    obj_other['id_direct_junction_end'] = id_extra
                elif 'id_direct_junction_end' in obj_other:
                    # Clean up old direct junction link
                    del obj_other['id_direct_junction_end']
        elif obj_other.name.startswith('junction_area'):
            if obj['dsc_type'] == 'junction_connecting_road':
                obj_incoming = get_object_xodr_by_id(obj_other['joints'][id_extra]['id_incoming'])
                if obj_incoming != None:
                    cp_type_incoming = obj_other['joints'][id_extra]['contact_point_type']
                    if cp_type_incoming == 'cp_start_l':
                        obj_incoming['link_predecessor_id_l'] = obj_other['id_odr']
                        obj_incoming['link_predecessor_cp_l'] = 'junction_joint'
                    elif cp_type_incoming == 'cp_end_l':
                        obj_incoming['link_successor_id_l'] = obj_other['id_odr']
                        obj_incoming['link_successor_cp_l'] = 'junction_joint'
            else:
                # Case: incoming road to junction or junction to junction
                if link_type == 'start':
                    cp_type = 'cp_start_l'
                else:
                    cp_type = 'cp_end_l'
                obj_other['joints'][id_extra]['id_incoming'] = obj['id_odr']
                obj_other['joints'][id_extra]['contact_point_type'] = cp_type
                # Connect to all connecting roads of this joint
                for obj_jcr in bpy.data.collections['OpenDRIVE'].objects:
                    if obj_jcr.name.startswith('junction_connecting_road'):
                        if obj_jcr['id_junction'] == id_other:
                            if obj_jcr['id_joint_start'] == id_extra:
                                obj_jcr['link_predecessor_id_l'] = obj['id_odr']
                                obj_jcr['link_predecessor_cp_l'] = cp_type
                            elif obj_jcr['id_joint_end'] == id_extra:
                                obj_jcr['link_successor_id_l'] = obj['id_odr']
                                obj_jcr['link_successor_cp_l'] = cp_type

def create_reference_object_xodr_link(reference_object, id_object):
    '''
        Set the reference object ID for a road object
    '''
    reference_object['id_ref_object'] = id_object


def set_connecting_road_properties(context, joint_side_start, road_contact_point, width_lane_incoming):
    '''
        Set the properties for construction of a connecting road.
    '''
    context.scene.dsc_properties.connecting_road_properties.junction_connecting_road = True
    if joint_side_start == 'left':
        context.scene.dsc_properties.connecting_road_properties.num_lanes_left = 1
        context.scene.dsc_properties.connecting_road_properties.num_lanes_right = 0
        if road_contact_point == 'start':
            # We add lanes from left to right so first left has index 0, center lane index 1
            context.scene.dsc_properties.connecting_road_properties.lanes[0].width_start = width_lane_incoming
        else:
            context.scene.dsc_properties.connecting_road_properties.lanes[0].width_end = width_lane_incoming
    else:
        context.scene.dsc_properties.connecting_road_properties.num_lanes_left = 0
        context.scene.dsc_properties.connecting_road_properties.num_lanes_right = 1
        if road_contact_point == 'start':
            # We add lanes from left to right so center lane has index 0, first right index 1
            context.scene.dsc_properties.connecting_road_properties.lanes[1].width_start = width_lane_incoming
        else:
            context.scene.dsc_properties.connecting_road_properties.lanes[1].width_end = width_lane_incoming
    # Remove lane markings for connecting roads
    context.scene.dsc_properties.connecting_road_properties.lanes[0].road_mark_type = 'none'
    context.scene.dsc_properties.connecting_road_properties.lanes[1].road_mark_type = 'none'

def calculate_lane_offset(s, lane_offset_coefficients, total_length):
    '''
        Return lane offset in [m] for the given s value based on the
        pre-calculated polynomial coefficients. Note that 'b' is not
        required for the implemented solution.
    '''
    s_norm = s / total_length
    lane_offset = lane_offset_coefficients['a'] + \
        (lane_offset_coefficients['c'] * s_norm**2 + lane_offset_coefficients['d'] * s_norm**3)
    return lane_offset

def get_lane_widths_road_joint(obj, contact_point):
    '''
        Return the widths of the left and right road side of the road end
        touching a junction joint.
    '''
    lane_widths_left = []
    lane_widths_right = []
    if contact_point == 'start':
        lane_widths_left = obj['lanes_left_widths_start']
        lane_widths_right = obj['lanes_right_widths_start']
    else:
        lane_widths_left = obj['lanes_left_widths_end']
        lane_widths_right = obj['lanes_right_widths_end']
    return lane_widths_left, lane_widths_right

def select_object(context, obj):
    '''
        Select object.
    '''
    if obj is not None:
        obj.select_set(state=True)

def select_activate_object(context, obj):
    '''
        Select and activate object.
    '''
    if obj is not None:
        obj.select_set(state=True)
        context.view_layer.objects.active = obj

def remove_duplicate_vertices(context, obj):
    '''
        Remove duplicate vertices from a object's mesh
    '''
    context.view_layer.objects.active = obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001,
                use_unselected=True, use_sharp_edge_from_normals=False)
    bpy.ops.object.editmode_toggle()

def get_mouse_vectors(context, event):
    '''
        Return view vector and ray origin of mouse pointer position.
    '''
    region = context.region
    rv3d = context.region_data
    co2d = (event.mouse_region_x, event.mouse_region_y)
    view_vector_mouse = region_2d_to_vector_3d(region, rv3d, co2d)
    ray_origin_mouse = region_2d_to_origin_3d(region, rv3d, co2d)
    return view_vector_mouse, ray_origin_mouse

def mouse_to_xy_parallel_plane(context, event, z):
    '''
        Convert mouse pointer position to 3D point in plane parallel to xy-plane
        at height z.
    '''
    view_vector_mouse, ray_origin_mouse = get_mouse_vectors(context, event)
    point = intersect_line_plane(ray_origin_mouse, ray_origin_mouse + view_vector_mouse,
        (0, 0, z), (0, 0, 1), False)
    # Fix parallel plane issue
    if point is None:
        point = intersect_line_plane(ray_origin_mouse, ray_origin_mouse + view_vector_mouse,
            (0, 0, 0), view_vector_mouse, False)
    return point

def mouse_to_elevation(context, event, point):
    '''
        Convert mouse pointer position to elevation above point projected to xy plane.
    '''
    view_vector_mouse, ray_origin_mouse = get_mouse_vectors(context, event)
    point_elevation = intersect_line_plane(ray_origin_mouse, ray_origin_mouse + view_vector_mouse,
        point.to_2d().to_3d(), view_vector_mouse.to_2d().to_3d(), False)
    if point_elevation == None:
        return 0
    else:
        return point_elevation.z

def raycast_mouse_to_dsc_object(context, event):
    '''
        Convert mouse pointer position to hit obj of DSC type.
    '''
    view_vector_mouse, ray_origin_mouse = get_mouse_vectors(context, event)
    hit, point, normal, index_face, obj, matrix_world = context.scene.ray_cast(
        depsgraph=context.view_layer.depsgraph,
        origin=ray_origin_mouse,
        direction=view_vector_mouse)
    # Filter object type
    if hit:
        # Return hit only if not filtered out
        if 'dsc_category' in obj:
            return True, point, normal, obj
        else:
            return False, point, normal, None
    else:
        # No hit
        return False, point, normal, None

def point_to_road_connector(obj, point):
    '''
        Get a snapping point and heading from an existing road.
    '''
    dist_start_l = (Vector(obj['cp_start_l']) - point).length
    dist_start_r = (Vector(obj['cp_start_r']) - point).length
    dist_end_l = (Vector(obj['cp_end_l']) - point).length
    dist_end_r = (Vector(obj['cp_end_r']) - point).length
    distances = [dist_start_l, dist_start_r, dist_end_l, dist_end_r]
    arg_min_dist = distances.index(min(distances))
    widths_left_start, widths_right_start = get_lane_widths_road_joint(obj, contact_point='start')
    widths_left_end, widths_right_end = get_lane_widths_road_joint(obj, contact_point='end')
    if arg_min_dist == 0:
        lane_offset = calculate_lane_offset(0, obj['lane_offset_coefficients'], obj['geometry_total_length'])
        return 'cp_start_l', Vector(obj['cp_start_l']), obj['geometry'][0]['heading_start'] - pi, \
            -obj['geometry'][0]['curvature_start'], -obj['geometry'][0]['slope_start'], lane_offset, \
            widths_left_start, widths_right_start, obj['lanes_left_types'], obj['lanes_right_types']
    if arg_min_dist == 1:
        lane_offset = calculate_lane_offset(0, obj['lane_offset_coefficients'], obj['geometry_total_length'])
        return 'cp_start_r', Vector(obj['cp_start_r']), obj['geometry'][0]['heading_start'] - pi, \
            -obj['geometry'][0]['curvature_start'], -obj['geometry'][0]['slope_start'], lane_offset, \
            widths_left_start, widths_right_start, obj['lanes_left_types'], obj['lanes_right_types']
    elif arg_min_dist == 2:
        lane_offset = calculate_lane_offset(
            obj['geometry_total_length'], obj['lane_offset_coefficients'], obj['geometry_total_length'])
        return 'cp_end_l', Vector(obj['cp_end_l']), obj['geometry'][-1]['heading_end'], \
            obj['geometry'][-1]['curvature_end'], obj['geometry'][-1]['slope_end'], lane_offset, \
            widths_left_end, widths_right_end, obj['lanes_left_types'], obj['lanes_right_types']
    else:
        lane_offset = calculate_lane_offset(
            obj['geometry_total_length'], obj['lane_offset_coefficients'], obj['geometry_total_length'])
        return 'cp_end_r', Vector(obj['cp_end_r']), obj['geometry'][-1]['heading_end'], \
            obj['geometry'][-1]['curvature_end'], obj['geometry'][-1]['slope_end'], lane_offset, \
            widths_left_end, widths_right_end, obj['lanes_left_types'], obj['lanes_right_types']

def point_to_junction_joint_exterior(obj, point):
    '''
        Get joint parameters for the exterior side from closest joint including
        connecting road ID, contact point type, vector and heading from an
        existing junction.
    '''
    # Calculate which connecting point is closest to input point
    joints = obj['joints']
    distances = []
    cp_vectors = []
    for idx, joint in enumerate(joints):
        cp_vectors.append(Vector(joint['contact_point_vec']))
        distances.append((Vector(joint['contact_point_vec']) - point).length)
    arg_min_dist = distances.index(min(distances))
    return joints[arg_min_dist]['id_joint'], joints[arg_min_dist]['contact_point_type'], \
        cp_vectors[arg_min_dist], joints[arg_min_dist]['heading'] - pi, joints[arg_min_dist]['slope']

def get_closest_joint_lane_contact_point(joint, point, joint_side):
    '''
        Return the contact points for the closest lane of a junction joint.
    '''
    lane_center_points_left = []
    lane_center_points_right = []
    lane_contact_points_left = []
    lane_contact_points_right = []
    lane_ids_left = []
    lane_ids_right = []

    if joint_side == 'left' or joint_side == 'both':
        # Find all left side lane contact points
        t = 0
        lane_id = 0
        for width_left in list(joint['lane_widths_left']):
            lane_id += 1
            t_contact_point = t + joint['lane_offset']
            t_lane_center = t + width_left/2 + joint['lane_offset']
            t += width_left
            lane_ids_left.append(lane_id)
            vec_hdg = Vector((1.0, 0.0, 0.0))
            vec_hdg.rotate(Matrix.Rotation(joint['heading'] + pi/2, 4, 'Z'))
            lane_center_points_left.append(Vector(joint['contact_point_vec']) + t_lane_center * vec_hdg)
            lane_contact_points_left.append(Vector(joint['contact_point_vec']) + t_contact_point * vec_hdg)

    if joint_side == 'right' or joint_side == 'both':
        # Find all right side lane contact points
        t = 0
        lane_id = 0
        for width_right in joint['lane_widths_right']:
            lane_id -= 1
            t_contact_point = t + joint['lane_offset']
            t_lane_center = t - width_right/2 + joint['lane_offset']
            t -= width_right
            lane_ids_right.append(lane_id)
            vec_hdg = Vector((1.0, 0.0, 0.0))
            vec_hdg.rotate(Matrix.Rotation(joint['heading'] + pi/2, 4, 'Z'))
            lane_center_points_right.append(Vector(joint['contact_point_vec']) + t_lane_center * vec_hdg)
            lane_contact_points_right.append(Vector(joint['contact_point_vec']) + t_contact_point * vec_hdg)

    # Find the closest contact point, ignore all non-driving lanes
    d_min = inf
    id_lane_cp = None
    lane_width = None
    lane_type = None
    contact_point_vec = None
    lane_center_vec = None
    # Left lanes
    for idx_lane, lane_center_point in enumerate(lane_center_points_left):
        lane_type = list(joint['lane_types_left'])[idx_lane]
        if lane_type == 'driving' or lane_type == 'stop' or lane_type == 'onRamp' or lane_type == 'offRamp':
            distance = (lane_center_point - point).length
            # Take the contact point for the lane with the closest center point
            if distance < d_min:
                d_min = distance
                id_lane_cp = lane_ids_left[idx_lane]
                lane_width = list(joint['lane_widths_left'])[idx_lane]
                contact_point_vec = lane_contact_points_left[idx_lane]
                lane_center_vec = lane_center_point
    # Right lanes
    for idx_lane, lane_center_point in enumerate(lane_center_points_right):
        lane_type = joint['lane_types_right'][idx_lane]
        if lane_type == 'driving' or lane_type == 'stop' or lane_type == 'onRamp' or lane_type == 'offRamp':
            distance = (lane_center_point - point).length
            # Take the contact point for the lane with the closest center point
            if distance < d_min:
                d_min = distance
                id_lane_cp = lane_ids_right[idx_lane]
                lane_width = joint['lane_widths_right'][idx_lane]
                contact_point_vec = lane_contact_points_right[idx_lane]
                lane_center_vec = lane_center_point

    return [joint, id_lane_cp, lane_width, lane_type, contact_point_vec, lane_center_vec]

def get_closest_lane_contact_point(lane_contact_points, point):
    '''
        Return closest lane contact point from a list of lane contact points.
    '''
    if len(lane_contact_points) == 0:
        return None, None, None, None, None
    else:
        d_min = inf
        for lane_contact_point in lane_contact_points:
            # Find the closest lane center point
            lane_center_point = lane_contact_point[4]
            distance = (lane_center_point - point).length
            if distance < d_min:
                d_min = distance
                joint, id_lane_cp, lane_width, lane_type, contact_point_vec = lane_contact_point[:-1]

        return joint, id_lane_cp, lane_width, lane_type, contact_point_vec

def point_to_junction_joint_interior(obj, point, joint_side):
    '''
        Get joint parameters for the interior side from closest joint including
        connecting road ID, lane ID, contact point type, vector and heading from
        an existing junction.
    '''
    joints = obj['joints']
    lane_contact_points = []
    for joint in joints:
        closest_cp = get_closest_joint_lane_contact_point(joint, point, joint_side=joint_side)
        if closest_cp[1] != None:
            lane_contact_points.append(closest_cp)

    joint_cp, id_lane_cp, lane_width, lane_type, contact_point_vec = get_closest_lane_contact_point(
        lane_contact_points, point)

    if joint_cp != None:
        return joint_cp['id_joint'], joint_cp['contact_point_type'], \
            contact_point_vec, joint_cp['heading'] - pi, joint_cp['slope'], id_lane_cp, lane_width, lane_type
    else:
        return None, None, None, None, None, None, None, None

def point_to_object_connector(obj, point):
    '''
        Get a snapping point and heading from a scenario or road object.
    '''
    return 'cp_object', Vector(obj['position']), obj['hdg']

def project_point_vector_2d(point_start, heading_start, point_selected):
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

def mouse_to_road_joint_params(context, event, road_type, joint_side='both'):
    '''
        Check if a road is hit and return snapping parameters. The road side
        parameter determines which side to snap to (left|right|both) for
        junction connecting roads. Sides are determined based on incoming
        direction towards the junction interior.
    '''
    # Initialize with some defaults in case nothing is hit
    hit_type = None
    id_obj = None
    id_extra = None
    id_lane = None
    point_type = None
    hit_joint_side = None
    snapped_point = Vector((0.0,0.0,0.0))
    snapped_normal = Vector((0.0,0.0,1.0))
    heading = 0
    curvature = 0
    slope = 0
    lane_offset_coefficients = {'a': 0, 'b': 0, 'c': 0, 'd': 0}
    lane_widths_left = []
    lane_widths_right = []
    lane_types_left = []
    lane_types_right = []
    dsc_hit, raycast_point, raycast_normal, obj \
        = raycast_mouse_to_dsc_object(context, event)
    if dsc_hit:
        # DSC mesh hit
        if road_type == 'road':
            if obj['dsc_category'] == 'OpenDRIVE':
                if obj['dsc_type'].startswith('road_') and obj['dsc_type'] != 'road_object':
                    hit_type = 'road'
                    point_type, snapped_point, heading, curvature, slope, lane_offset_coefficients, \
                    lane_widths_left, lane_widths_right, lane_types_left, lane_types_right \
                        = point_to_road_connector(obj, raycast_point)
                    id_obj = obj['id_odr']
                    if obj['road_split_type'] == 'end':
                        if point_type == 'cp_end_l' or point_type == 'cp_end_r':
                            if 'id_direct_junction_end' in obj:
                                id_extra = obj['id_direct_junction_end']
                    elif obj['road_split_type'] == 'start':
                        if point_type == 'cp_start_l' or point_type == 'cp_start_r':
                            if 'id_direct_junction_start' in obj:
                                id_extra = obj['id_direct_junction_start']
            if obj.name.startswith('junction_area'):
                # This path is for incoming road to junction joint snapping
                hit_type = 'junction_joint'
                # Determine road side based on lane ID and reference line direction
                id_joint, point_type, snapped_point, heading, slope = \
                    point_to_junction_joint_exterior(obj, raycast_point)
                # Set both IDs to the junction ID
                id_obj = obj['id_odr']
                id_extra = id_joint
        if road_type == 'junction_connecting_road':
            if obj.name.startswith('junction_area'):
                # This path is for junction connecting roads
                id_joint, point_type, snapped_point, heading, slope, id_lane, lane_width, lane_type = \
                    point_to_junction_joint_interior(obj, raycast_point, joint_side=joint_side)
                if id_joint != None:
                    hit_type = 'junction_connecting_road'
                    heading = heading - pi
                    # Set both IDs to the junction ID
                    id_obj = obj['id_odr']
                    id_extra = id_joint
            if id_lane != None:
                # Determine road side based on lane ID and reference line direction
                if id_lane > 0:
                    hit_joint_side = 'left'
                    lane_widths_left = [lane_width]
                    lane_widths_right = []
                    lane_types_left = [lane_type]
                    lane_types_right = []
                elif id_lane < 0:
                    hit_joint_side = 'right'
                    lane_widths_left = []
                    lane_widths_right = [lane_width]
                    lane_types_left = []
                    lane_types_right = [lane_type]
    return {'hit_type': hit_type,
            'id_obj': id_obj,
            'id_extra': id_extra,
            'id_lane': id_lane,
            'joint_side': hit_joint_side,
            'point': snapped_point,
            'normal': snapped_normal,
            'point_type': point_type,
            'heading': heading,
            'curvature': curvature,
            'slope': slope,
            'lane_offset_coefficients': lane_offset_coefficients,
            'lane_widths_left': lane_widths_left,
            'lane_widths_right': lane_widths_right,
            'lane_types_left': lane_types_left,
            'lane_types_right': lane_types_right,
            }

def mouse_to_road_object_params(context, event, road_object_type):
    '''
        Check if an object is hit and return snapping parameters.
    '''
    # Initialize with some defaults in case nothing is hit
    hit_type = None
    id_obj = None
    id_extra = None
    point_type = None
    snapped_point = Vector((0.0,0.0,0.0))
    snapped_normal = Vector((0.0,0.0,1.0))
    heading = 0
    curvature = 0
    slope = 0
    # Do the raycasting
    dsc_hit, raycast_point, raycast_normal, obj \
        = raycast_mouse_to_dsc_object(context, event)
    if dsc_hit:
        # DSC mesh hit
        if obj['dsc_type'] == 'road_object' and obj['road_object_type'] == road_object_type:
            hit_type = 'object'
            point_type, snapped_point, heading = point_to_object_connector(obj, raycast_point)
            id_obj = obj['id_odr']
    return {'hit_type': hit_type,
            'id_obj': id_obj,
            'id_extra': id_extra,
            'point': snapped_point,
            'normal': snapped_normal,
            'point_type': point_type,
            'heading': heading,
            'curvature': curvature,
            'slope': slope,
            }

def mouse_to_entity_params(context, event):
    '''
        Check if an object is hit and return snapping parameters.
    '''
    # Initialize with some defaults in case nothing is hit
    hit_type = None
    id_obj = None
    id_extra = None
    point_type = None
    snapped_point = Vector((0.0,0.0,0.0))
    snapped_normal = Vector((0.0,0.0,1.0))
    heading = 0
    curvature = 0
    slope = 0
    # Do the raycasting
    dsc_hit, raycast_point, raycast_normal, obj \
        = raycast_mouse_to_dsc_object(context, event)
    if dsc_hit:
        # DSC mesh hit
        if obj['dsc_type'] == 'entity':
            hit_type = 'object'
            point_type, snapped_point, heading = point_to_object_connector(obj, raycast_point)
            id_obj = obj.name
    return {'hit_type': hit_type,
            'id_obj': id_obj,
            'id_extra': id_extra,
            'point': snapped_point,
            'normal': snapped_normal,
            'point_type': point_type,
            'heading': heading,
            'curvature': curvature,
            'slope': slope,
            }

def mouse_to_road_surface_params(context, event):
    '''
        Check if a road surface is hit and return a snapping parameters.
    '''
    # Initialize with some defaults in case nothing is hit
    hit_type = None
    id_obj = None
    id_extra = None
    id_lane = None
    point_type = None
    snapped_point = Vector((0.0,0.0,0.0))
    snapped_normal = Vector((0.0,0.0,1.0))
    heading = 0
    curvature = 0
    slope = 0
    # Do the raycasting
    dsc_hit, raycast_point, raycast_normal, obj \
        = raycast_mouse_to_dsc_object(context, event)
    if dsc_hit:
        # DSC mesh hit
        if obj['dsc_category'] == 'OpenDRIVE':
            hit_type = 'road_surface'
            point_type = 'surface'
            snapped_point = raycast_point
            snapped_normal = raycast_normal
            id_obj = obj.name
    return {'hit_type': hit_type,
            'id_obj': id_obj,
            'id_extra': id_extra,
            'id_lane': id_lane,
            'point': snapped_point,
            'normal': snapped_normal,
            'point_type': point_type,
            'heading': heading,
            'curvature': curvature,
            'slope': slope,
            }

def assign_materials(obj):
    '''
        Assign materials for asphalt and markings to object.
    '''
    default_materials = {
        'road_asphalt': [.3, .3, .3, 1.0],
        'road_mark_white': [.9, .9, .9, 1.0],
        'road_mark_yellow': [.85, .63, .0, 1.0],
        'grass': [.05, .6, .01, 1.0],
        'road_sign_pole': [.4, .4, .4, 1.0],
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

def assign_object_materials(obj, color):
    # Get road material
    material = bpy.data.materials.get(get_paint_material_name(color))
    if material is None:
        # Create material
        material = bpy.data.materials.new(name=get_paint_material_name(color))
        material.diffuse_color = color
    obj.data.materials.append(material)

def get_paint_material_name(color):
    '''
        Calculate material name from name string and Blender color
    '''
    return 'paint' + '_{:.2f}_{:.2f}_{:.2f}'.format(*color[0:4])

def get_material_index(obj, material_name):
    '''
        Return index of material slot based on material name.
    '''
    for idx, material in enumerate(obj.data.materials):
        if material.name == material_name:
            return idx
    return None

def replace_mesh(obj, mesh):
    '''
        Replace existing mesh
    '''
    # Delete old mesh data
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    verts = [v for v in bm.verts]
    bmesh.ops.delete(bm, geom=verts, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    # Set new mesh data
    obj.data = mesh

def triangulate_quad_mesh(obj):
    '''
        Triangulate then quadify the ngon mesh of an object.
    '''
    # Triangulate
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()
    # Tris to quads is missing in bmesh so use bpy.ops.mesh instead
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.tris_convert_to_quads(materials=True)
    bpy.ops.object.mode_set(mode='OBJECT')

def kmh_to_ms(speed):
    return speed / 3.6

def get_obj_custom_property(dsc_category, subcategory, obj_name, property):
    if collection_exists([dsc_category,subcategory]):
        for obj in bpy.data.collections[dsc_category].children[subcategory].objects:
            if obj.name == obj_name:
                if property in obj:
                    return obj[property]
                else:
                    return None
    else:
        return None
