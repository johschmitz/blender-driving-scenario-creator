"""
Legacy helper functions from the original helpers.py file.

These functions are maintained for backward compatibility while the codebase
is being refactored. New implementations should use the modular utility functions
in the utils package.
"""

import bpy
import bmesh
from typing import Optional, Union, List, Dict, Any
from mathutils import Vector

from ..core.constants import *
from ..core.exceptions import ValidationError
from .blender_utils import (
    get_new_id_opendrive,
    get_new_id_openscenario,
    ensure_collection_dsc,
    ensure_collection_opendrive,
    ensure_collection_openscenario,
    link_object_opendrive,
    link_object_openscenario,
    get_object_xodr_by_id
)
from .validation_utils import validate_not_none, validate_positive


def create_object_xodr_links(obj: bpy.types.Object, link_type: str, cp_type_other: str,
                           id_other: int, id_extra: Optional[int], id_lane: int) -> None:
    """
    Create OpenDRIVE predecessor/successor linkage for current object with other object.
    
    This is a legacy function maintained for compatibility.
    
    Args:
        obj: Object to create links for
        link_type: Type of link ('start' or 'end')
        cp_type_other: Contact point type of other object
        id_other: ID of other object
        id_extra: Extra ID for junction connections
        id_lane: Lane ID for connections
    """
    # Get other objects
    obj_other = get_object_xodr_by_id(id_other)
    obj_extra = get_object_xodr_by_id(id_extra) if id_extra is not None else None
    
    # Set link parameters based on object type and link type
    if 'road' in obj.name:
        if link_type == 'start':
            _set_road_start_links(obj, obj_other, obj_extra, cp_type_other, id_other, id_extra, id_lane)
        else:
            _set_road_end_links(obj, obj_other, obj_extra, cp_type_other, id_other, id_extra, id_lane)
    elif obj.get('dsc_type') == 'junction_connecting_road':
        _set_junction_connecting_road_links(obj, obj_other, obj_extra, cp_type_other, id_other, id_extra, id_lane)


def _set_road_start_links(obj: bpy.types.Object, obj_other: Optional[bpy.types.Object],
                         obj_extra: Optional[bpy.types.Object], cp_type_other: str,
                         id_other: int, id_extra: Optional[int], id_lane: int) -> None:
    """Set start links for road objects."""
    if obj.get('dsc_type', '').startswith('road_'):
        if obj.get('road_split_type') == 'none':
            obj['link_predecessor_id_l'] = id_other
        else:
            # Handle road splitting
            if obj.get('lanes_left_num', 0) > obj.get('road_split_lane_idx', 0):
                obj['link_predecessor_id_r'] = id_other
                obj['link_predecessor_cp_r'] = cp_type_other
            else:
                obj['link_predecessor_id_l'] = id_other
        
        if id_extra is None:
            obj['link_predecessor_cp_l'] = cp_type_other
        else:
            if obj_extra and obj_extra.get('dsc_type') == 'junction_direct':
                obj['link_predecessor_cp_l'] = cp_type_other
                obj['id_direct_junction_start'] = id_extra
            else:
                obj['link_predecessor_cp_l'] = 'junction_joint'


def _set_road_end_links(obj: bpy.types.Object, obj_other: Optional[bpy.types.Object],
                       obj_extra: Optional[bpy.types.Object], cp_type_other: str,
                       id_other: int, id_extra: Optional[int], id_lane: int) -> None:
    """Set end links for road objects."""
    if obj.get('dsc_type', '').startswith('road_'):
        if obj.get('road_split_type') == 'none':
            obj['link_successor_id_l'] = id_other
        else:
            # Handle road splitting
            if obj.get('lanes_left_num', 0) > obj.get('road_split_lane_idx', 0):
                obj['link_successor_id_r'] = id_other
                obj['link_successor_cp_r'] = cp_type_other
            else:
                obj['link_successor_id_l'] = id_other
        
        if id_extra is None:
            obj['link_successor_cp_l'] = cp_type_other
        else:
            if obj_extra and obj_extra.get('dsc_type') == 'junction_direct':
                obj['link_successor_cp_l'] = cp_type_other
                obj['id_direct_junction_end'] = id_extra
            else:
                obj['link_successor_cp_l'] = 'junction_joint'


def _set_junction_connecting_road_links(obj: bpy.types.Object, obj_other: Optional[bpy.types.Object],
                                      obj_extra: Optional[bpy.types.Object], cp_type_other: str,
                                      id_other: int, id_extra: Optional[int], id_lane: int) -> None:
    """Set links for junction connecting roads."""
    obj['id_junction'] = id_other
    obj['id_joint_start'] = id_extra
    obj['id_lane_joint_start'] = id_lane
    
    if obj_other and obj_other.get('joints') and id_extra is not None:
        joints = obj_other.get('joints', {})
        if id_extra in joints and joints[id_extra].get('id_incoming') is not None:
            obj['link_predecessor_id_l'] = joints[id_extra]['id_incoming']
            obj['link_predecessor_cp_l'] = joints[id_extra]['contact_point_type']


def mouse_to_road_joint_params(context: bpy.types.Context, event, road_type: str,
                             joint_side: str = 'both') -> Dict[str, Any]:
    """
    Get road joint parameters from mouse position.
    
    This is a legacy function maintained for compatibility.
    
    Args:
        context: Blender context
        event: Mouse event
        road_type: Type of road
        joint_side: Side of joint ('both', 'start', 'end')
        
    Returns:
        Dictionary with joint parameters
    """
    # This is a simplified version of the original function
    # The full implementation would be much more complex
    
    # Get mouse position in 3D
    mouse_pos = _get_mouse_3d_position(context, event)
    
    # Find closest road object
    closest_road = _find_closest_road_object(context, mouse_pos)
    
    if not closest_road:
        return {}
    
    # Calculate parameters
    params = {
        'point': mouse_pos,
        'road_id': closest_road.get('id_odr'),
        'heading': 0.0,
        'design_speed': DEFAULT_DESIGN_SPEED,
        'lane_widths': [DEFAULT_LANE_WIDTH] * 2
    }
    
    return params


def _get_mouse_3d_position(context: bpy.types.Context, event) -> Vector:
    """Get 3D position from mouse coordinates."""
    # This is a simplified implementation
    # The full version would use view3d_utils for proper 3D projection
    return Vector((0, 0, 0))


def _find_closest_road_object(context: bpy.types.Context, position: Vector) -> Optional[bpy.types.Object]:
    """Find the closest road object to the given position."""
    closest_obj = None
    min_distance = float('inf')
    
    # Search in OpenDRIVE collection
    collection = bpy.data.collections.get('OpenDRIVE')
    if not collection:
        return None
    
    for obj in collection.objects:
        if obj.name.startswith('road'):
            distance = (obj.location - position).length
            if distance < min_distance:
                min_distance = distance
                closest_obj = obj
    
    return closest_obj


def kmh_to_ms(speed_kmh: float) -> float:
    """
    Convert speed from km/h to m/s.
    
    Args:
        speed_kmh: Speed in km/h
        
    Returns:
        Speed in m/s
    """
    validate_positive(speed_kmh, "speed_kmh")
    return speed_kmh / 3.6


def ms_to_kmh(speed_ms: float) -> float:
    """
    Convert speed from m/s to km/h.
    
    Args:
        speed_ms: Speed in m/s
        
    Returns:
        Speed in km/h
    """
    validate_positive(speed_ms, "speed_ms")
    return speed_ms * 3.6


def calculate_lane_offset(s: float, lane_offset_coefficients: List[float], total_length: float) -> float:
    """
    Calculate lane offset at given s-coordinate.
    
    Args:
        s: S-coordinate along road
        lane_offset_coefficients: Polynomial coefficients for lane offset
        total_length: Total length of road segment
        
    Returns:
        Lane offset at position s
    """
    validate_positive(total_length, "total_length")
    
    if not lane_offset_coefficients:
        return 0.0
    
    # Normalize s to [0, 1] range
    s_normalized = s / total_length if total_length > 0 else 0.0
    
    # Calculate polynomial value
    offset = 0.0
    for i, coeff in enumerate(lane_offset_coefficients):
        offset += coeff * (s_normalized ** i)
    
    return offset


def get_lane_widths_road_joint(obj: bpy.types.Object, contact_point: str) -> List[float]:
    """
    Get lane widths at road joint.
    
    Args:
        obj: Road object
        contact_point: Contact point ('start' or 'end')
        
    Returns:
        List of lane widths
    """
    validate_not_none(obj, "obj")
    
    if contact_point == 'start':
        left_widths = obj.get('lanes_left_widths_start', [])
        right_widths = obj.get('lanes_right_widths_start', [])
    else:
        left_widths = obj.get('lanes_left_widths_end', [])
        right_widths = obj.get('lanes_right_widths_end', [])
    
    # Combine left and right widths
    all_widths = list(reversed(left_widths)) + right_widths
    
    return all_widths if all_widths else [DEFAULT_LANE_WIDTH]


def assign_object_materials(obj: bpy.types.Object, color: str) -> None:
    """
    Assign materials to object based on color.
    
    Args:
        obj: Object to assign materials to
        color: Color name ('red', 'blue', 'green', etc.)
    """
    validate_not_none(obj, "obj")
    
    # Color mapping
    color_mapping = {
        'red': (1.0, 0.0, 0.0, 1.0),
        'blue': (0.0, 0.0, 1.0, 1.0),
        'green': (0.0, 1.0, 0.0, 1.0),
        'yellow': (1.0, 1.0, 0.0, 1.0),
        'white': (1.0, 1.0, 1.0, 1.0),
        'black': (0.0, 0.0, 0.0, 1.0),
        'gray': (0.5, 0.5, 0.5, 1.0)
    }
    
    rgba = color_mapping.get(color.lower(), (0.5, 0.5, 0.5, 1.0))
    
    # Create or get material
    material_name = f"material_{color}"
    if material_name in bpy.data.materials:
        material = bpy.data.materials[material_name]
    else:
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        
        # Clear existing nodes
        material.node_tree.clear()
        
        # Add principled BSDF
        bsdf = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = rgba
        
        # Add output
        output = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # Assign to object
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material) 