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

from math import pi


def get_new_id_opendrive(context):
    '''
        Generate and return new ID for OpenDRIVE objects using a dummy object
        for storage.
    '''
    dummy_obj = context.scene.objects.get('id_odr_next')
    if dummy_obj is None:
        dummy_obj = bpy.data.objects.new('id_odr_next',None)
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
        version_obj = bpy.data.objects.new('dsc_addon_version',None)
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

def create_object_xodr_links(obj, link_type, cp_type_other, id_other, id_extra):
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
            if obj['dsc_type'] == 'road':
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
                if obj_other['joints'][id_extra]['id_incoming'] != None:
                    obj['link_predecessor_id_l'] = obj_other['joints'][id_extra]['id_incoming']
                    obj['link_predecessor_cp_l'] = obj_other['joints'][id_extra]['contact_point_type']
        else:
            if obj['dsc_type'] == 'road':
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
                cp_type = None
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


def get_width_road_sides(obj):
    '''
        Return the width of the left and right road sid e calculated by suming up
        all lane widths.
    '''
    # TODO take edge lines and opening/closing lanes into account
    width_left = 0
    width_right = 0
    for width_lane_left in obj['lanes_left_widths']:
        width_left += width_lane_left
    for width_lane_right in obj['lanes_right_widths']:
        width_right += width_lane_right
    return width_left, width_right

def select_activate_object(context, obj):
    '''
        Select and activate object.
    '''
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(state=True)
    context.view_layer.objects.active = obj

def remove_duplicate_vertices(context, obj):
    '''
        Remove duplicate vertices from a object's mesh
    '''
    context.view_layer.objects.active = obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001,
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

def raycast_mouse_to_object(context, event, filter=None):
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
        if filter is not None:
            # Return hit only if not filtered out
            if filter in obj:
                return True, point, normal, obj
            else:
                return False, point, normal, None
        else:
            # No filter, return any hit
            return True, point, normal, obj
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
    width_left, width_right = get_width_road_sides(obj)
    if arg_min_dist == 0:
        return 'cp_start_l', Vector(obj['cp_start_l']), obj['geometry']['heading_start'] - pi, \
            obj['geometry']['curvature_start'], obj['geometry']['slope_start'], \
            width_left, width_right
    if arg_min_dist == 1:
        return 'cp_start_r', Vector(obj['cp_start_r']), obj['geometry']['heading_start'] - pi, \
            obj['geometry']['curvature_start'], obj['geometry']['slope_start'], \
            width_left, width_right
    elif arg_min_dist == 2:
        return 'cp_end_l', Vector(obj['cp_end_l']), obj['geometry']['heading_end'], \
            obj['geometry']['curvature_end'], obj['geometry']['slope_end'], \
            width_left, width_right
    else:
        return 'cp_end_r', Vector(obj['cp_end_r']), obj['geometry']['heading_end'], \
            obj['geometry']['curvature_end'], obj['geometry']['slope_end'], \
            width_left, width_right

def point_to_junction_joint(obj, point):
    '''
        Get joint parameters from closest joint including connecting road ID,
        contact point type, vector and heading from an existing junction.
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

def point_to_object_connector(obj, point):
    '''
        Get a snapping point and heading from a dynamic object.
    '''
    return 'cp_axle_rear', Vector(obj['position']), obj['hdg']

def project_point_vector(point_start, heading_start, point_selected):
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

def mouse_to_object_params(context, event, filter):
    '''
        Check if an object is hit and return a connection (snapping) point. In
        case of OpenDRIVE objects including heading, curvature and slope. Filter
        may be used to distinguish between OpenDRIVE, OpenSCENARIO and any
        object (set filter to None).
    '''
    # Initialize with some defaults in case nothing is hit
    hit = False
    id_obj = None
    id_extra = None
    point_type = None
    snapped_point = Vector((0.0,0.0,0.0))
    snapped_normal = Vector((0.0,0.0,1.0))
    heading = 0
    curvature = 0
    slope = 0
    width_left = 0
    width_right = 0
    # Do the raycasting
    if filter is None:
        dsc_hit, raycast_point, raycast_normal, obj \
            = raycast_mouse_to_object(context, event, filter=None)
    else:
        dsc_hit, raycast_point, raycast_normal, obj \
        = raycast_mouse_to_object(context, event, filter='dsc_category')
    if dsc_hit:
        # DSC mesh hit
        if filter == 'OpenDRIVE':
            if obj['dsc_category'] == 'OpenDRIVE':
                if obj['dsc_type'] == 'road':
                    hit = True
                    point_type, snapped_point, heading, curvature, \
                    slope, width_left, width_right = point_to_road_connector(obj, raycast_point)
                    id_obj = obj['id_odr']
                    if obj['road_split_type'] == 'end':
                        if point_type == 'cp_end_l' or point_type == 'cp_end_r':
                            if 'id_direct_junction_end' in obj:
                                id_extra = obj['id_direct_junction_end']
                    elif obj['road_split_type'] == 'start':
                        if point_type == 'cp_start_l' or point_type == 'cp_start_r':
                            if 'id_direct_junction_start' in obj:
                                id_extra = obj['id_direct_junction_start']
        if filter == 'OpenDRIVE' or filter == 'OpenDRIVE_junction':
            if obj.name.startswith('junction_area'):
                # This path is for incoming road to junction joint snapping
                hit = True
                id_joint, point_type, snapped_point, heading, slope = point_to_junction_joint(obj, raycast_point)
                if filter == 'OpenDRIVE_junction':
                    heading = heading - pi
                # For incoming junction connection set both IDs to the junction ID
                id_obj = obj['id_odr']
                id_extra = id_joint
        elif filter == 'OpenSCENARIO':
            if obj['dsc_category'] == 'OpenSCENARIO':
                hit = True
                point_type, snapped_point, heading = point_to_object_connector(obj, raycast_point)
                id_obj = obj.name
        elif filter == 'surface':
            hit = True
            point_type = 'surface'
            snapped_point = raycast_point
            snapped_normal = raycast_normal
            id_obj = obj.name
    return hit ,{'id_obj': id_obj,
                 'id_extra': id_extra,
                 'point': snapped_point,
                 'normal': snapped_normal,
                 'type': point_type,
                 'heading': heading,
                 'curvature': curvature,
                 'slope': slope,
                 'width_left': width_left,
                 'width_right': width_right,}

def assign_road_materials(obj):
    '''
        Assign materials for asphalt and markings to object.
    '''
    default_materials = {
        'road_asphalt': [.3, .3, .3, 1],
        'road_mark_white': [.9, .9, .9, 1],
        'road_mark_yellow': [.85, .63, .0, 1],
        'grass': [.05, .6, .01, 1],
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
    return 'vehicle_paint' + '_{:.2f}_{:.2f}_{:.2f}'.format(*color[0:4])

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
