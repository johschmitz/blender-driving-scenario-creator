"""
Blender-specific utility functions for the Driving Scenario Creator add-on.
"""

import bpy
import bmesh
import addon_utils
from typing import Optional, List, Tuple, Dict, Any, Union
from mathutils import Vector, Matrix
from bpy.types import Object, Collection, Scene, Context

from ..core.constants import *
from ..core.exceptions import BlenderAPIError, ValidationError


def get_new_id_opendrive(context: Context) -> int:
    """
    Generate and return new ID for OpenDRIVE objects using a dummy object for storage.
    
    Args:
        context: Blender context
        
    Returns:
        New unique ID for OpenDRIVE objects
        
    Raises:
        BlenderAPIError: If ID generation fails
    """
    try:
        dummy_obj = context.scene.objects.get('id_odr_next')
        if dummy_obj is None:
            dummy_obj = bpy.data.objects.new('id_odr_next', None)
            dummy_obj.hide_viewport = True
            dummy_obj.hide_render = True
            dummy_obj['id_odr_next'] = 1
            link_object_opendrive(context, dummy_obj)
        
        id_next = dummy_obj['id_odr_next']
        dummy_obj['id_odr_next'] += 1
        return id_next
    except Exception as e:
        raise BlenderAPIError(f"Failed to generate OpenDRIVE ID: {str(e)}")


def get_new_id_openscenario(context: Context) -> int:
    """
    Generate and return new ID for OpenSCENARIO objects using a dummy object for storage.
    
    Args:
        context: Blender context
        
    Returns:
        New unique ID for OpenSCENARIO objects
        
    Raises:
        BlenderAPIError: If ID generation fails
    """
    try:
        dummy_obj = context.scene.objects.get('id_osc_next')
        if dummy_obj is None:
            dummy_obj = bpy.data.objects.new('id_osc_next', None)
            dummy_obj.hide_viewport = True
            dummy_obj.hide_render = True
            dummy_obj['id_osc_next'] = 0
            link_object_openscenario(context, dummy_obj, subcategory=None)
        
        id_next = dummy_obj['id_osc_next']
        dummy_obj['id_osc_next'] += 1
        return id_next
    except Exception as e:
        raise BlenderAPIError(f"Failed to generate OpenSCENARIO ID: {str(e)}")


def ensure_collection_dsc(context: Context) -> Collection:
    """
    Ensure the main DSC collection exists and return it.
    
    Args:
        context: Blender context
        
    Returns:
        The DSC collection
        
    Raises:
        BlenderAPIError: If collection creation fails
    """
    try:
        if COLLECTION_DSC not in bpy.data.collections:
            collection = bpy.data.collections.new(COLLECTION_DSC)
            context.scene.collection.children.link(collection)
            
            # Store addon version
            version = ADDON_VERSION
            for mod in addon_utils.modules():
                if mod.bl_info['name'] == ADDON_NAME:
                    version = mod.bl_info['version']
                    break
            
            version_obj = bpy.data.objects.new('dsc_addon_version', None)
            version_obj.hide_viewport = True
            version_obj.hide_render = True
            version_obj['dsc_addon_version'] = version
            link_object_opendrive(context, version_obj)
        else:
            collection = bpy.data.collections[COLLECTION_DSC]
        
        return collection
    except Exception as e:
        raise BlenderAPIError(f"Failed to ensure DSC collection: {str(e)}")


def ensure_collection_opendrive(context: Context) -> Collection:
    """
    Ensure the OpenDRIVE collection exists and return it.
    
    Args:
        context: Blender context
        
    Returns:
        The OpenDRIVE collection
        
    Raises:
        BlenderAPIError: If collection creation fails
    """
    try:
        collection_dsc = ensure_collection_dsc(context)
        if COLLECTION_OPENDRIVE not in collection_dsc.children:
            collection = bpy.data.collections.new(COLLECTION_OPENDRIVE)
            collection_dsc.children.link(collection)
            return collection
        else:
            collection = bpy.data.collections[COLLECTION_OPENDRIVE]
            return collection
    except Exception as e:
        raise BlenderAPIError(f"Failed to ensure OpenDRIVE collection: {str(e)}")


def ensure_collection_openscenario(context: Context) -> Collection:
    """
    Ensure the OpenSCENARIO collection exists and return it.
    
    Args:
        context: Blender context
        
    Returns:
        The OpenSCENARIO collection
        
    Raises:
        BlenderAPIError: If collection creation fails
    """
    try:
        collection_dsc = ensure_collection_dsc(context)
        if COLLECTION_OPENSCENARIO not in collection_dsc.children:
            collection = bpy.data.collections.new(COLLECTION_OPENSCENARIO)
            collection_dsc.children.link(collection)
            return collection
        else:
            collection = bpy.data.collections[COLLECTION_OPENSCENARIO]
            return collection
    except Exception as e:
        raise BlenderAPIError(f"Failed to ensure OpenSCENARIO collection: {str(e)}")


def ensure_subcollection_openscenario(context: Context, subcollection: str) -> Collection:
    """
    Ensure a subcollection within OpenSCENARIO exists and return it.
    
    Args:
        context: Blender context
        subcollection: Name of the subcollection
        
    Returns:
        The requested subcollection
        
    Raises:
        BlenderAPIError: If collection creation fails
    """
    try:
        collection_osc = ensure_collection_openscenario(context)
        if subcollection not in collection_osc.children:
            collection = bpy.data.collections.new(subcollection)
            collection_osc.children.link(collection)
            return collection
        else:
            collection = bpy.data.collections[subcollection]
            return collection
    except Exception as e:
        raise BlenderAPIError(f"Failed to ensure OpenSCENARIO subcollection '{subcollection}': {str(e)}")


def collection_exists(collection_path: Union[str, List[str]]) -> bool:
    """
    Check if a (sub)collection with path given as list exists.
    
    Args:
        collection_path: Path to the collection as string or list
        
    Returns:
        True if collection exists, False otherwise
    """
    try:
        if not isinstance(collection_path, list):
            collection_path = [collection_path]
        
        root = collection_path.pop(0)
        if root not in bpy.data.collections:
            return False
        else:
            if len(collection_path) == 0:
                return True
            else:
                return collection_exists(collection_path)
    except Exception:
        return False


def link_object_opendrive(context: Context, obj: Object) -> None:
    """
    Link object to OpenDRIVE scene collection.
    
    Args:
        context: Blender context
        obj: Object to link
        
    Raises:
        BlenderAPIError: If linking fails
    """
    try:
        collection = ensure_collection_opendrive(context)
        collection.objects.link(obj)
    except Exception as e:
        raise BlenderAPIError(f"Failed to link object to OpenDRIVE collection: {str(e)}")


def link_object_openscenario(context: Context, obj: Object, subcategory: Optional[str] = None) -> None:
    """
    Link object to OpenSCENARIO scene collection.
    
    Args:
        context: Blender context
        obj: Object to link
        subcategory: Optional subcategory name
        
    Raises:
        BlenderAPIError: If linking fails
    """
    try:
        if subcategory is None:
            collection = ensure_collection_openscenario(context)
            collection.objects.link(obj)
        else:
            collection = ensure_subcollection_openscenario(context, subcategory)
            collection.objects.link(obj)
    except Exception as e:
        raise BlenderAPIError(f"Failed to link object to OpenSCENARIO collection: {str(e)}")


def get_object_xodr_by_id(id_odr: int) -> Optional[Object]:
    """
    Get reference to OpenDRIVE object by ID.
    
    Args:
        id_odr: OpenDRIVE object ID
        
    Returns:
        Object if found, None otherwise
    """
    try:
        collection = bpy.data.collections.get(COLLECTION_OPENDRIVE)
        if collection:
            for obj in collection.objects:
                if 'id_odr' in obj and obj['id_odr'] == id_odr:
                    return obj
        return None
    except Exception:
        return None


def select_object(context: Context, obj: Object) -> None:
    """
    Select an object in Blender.
    
    Args:
        context: Blender context
        obj: Object to select
        
    Raises:
        BlenderAPIError: If selection fails
    """
    try:
        obj.select_set(True)
    except Exception as e:
        raise BlenderAPIError(f"Failed to select object: {str(e)}")


def select_activate_object(context: Context, obj: Object) -> None:
    """
    Select and activate an object in Blender.
    
    Args:
        context: Blender context
        obj: Object to select and activate
        
    Raises:
        BlenderAPIError: If selection/activation fails
    """
    try:
        select_object(context, obj)
        context.view_layer.objects.active = obj
    except Exception as e:
        raise BlenderAPIError(f"Failed to select and activate object: {str(e)}")


def remove_duplicate_vertices(context: Context, obj: Object) -> None:
    """
    Remove duplicate vertices from an object's mesh.
    
    Args:
        context: Blender context
        obj: Object to process
        
    Raises:
        BlenderAPIError: If operation fails
    """
    try:
        if obj.type != 'MESH':
            raise ValidationError("Object is not a mesh")
        
        # Create bmesh representation
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        
        # Remove duplicates
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        
        # Update mesh
        bm.to_mesh(obj.data)
        bm.free()
        
        # Update object
        obj.data.update()
    except Exception as e:
        raise BlenderAPIError(f"Failed to remove duplicate vertices: {str(e)}")


def replace_mesh(obj: Object, mesh: bpy.types.Mesh) -> None:
    """
    Replace an object's mesh with a new one.
    
    Args:
        obj: Object whose mesh to replace
        mesh: New mesh to assign
        
    Raises:
        BlenderAPIError: If replacement fails
    """
    try:
        old_mesh = obj.data
        obj.data = mesh
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    except Exception as e:
        raise BlenderAPIError(f"Failed to replace mesh: {str(e)}")


def triangulate_quad_mesh(obj: Object) -> None:
    """
    Convert ngons to triangles and quads for a mesh object.
    
    Args:
        obj: Object to triangulate
        
    Raises:
        BlenderAPIError: If triangulation fails
    """
    try:
        if obj.type != 'MESH':
            raise ValidationError("Object is not a mesh")
        
        # Create bmesh representation
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        
        # Triangulate
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
        
        # Update mesh
        bm.to_mesh(obj.data)
        bm.free()
        
        # Update object
        obj.data.update()
    except Exception as e:
        raise BlenderAPIError(f"Failed to triangulate mesh: {str(e)}")


def assign_materials(obj: Object) -> None:
    """
    Assign default materials to an object.
    
    Args:
        obj: Object to assign materials to
        
    Raises:
        BlenderAPIError: If material assignment fails
    """
    try:
        # Get or create materials
        materials = {
            MATERIAL_ROAD_ASPHALT: _get_or_create_material(MATERIAL_ROAD_ASPHALT, (0.2, 0.2, 0.2, 1.0)),
            MATERIAL_ROAD_MARK_WHITE: _get_or_create_material(MATERIAL_ROAD_MARK_WHITE, (1.0, 1.0, 1.0, 1.0)),
            MATERIAL_ROAD_MARK_YELLOW: _get_or_create_material(MATERIAL_ROAD_MARK_YELLOW, (1.0, 1.0, 0.0, 1.0)),
            MATERIAL_GRASS: _get_or_create_material(MATERIAL_GRASS, (0.1, 0.4, 0.1, 1.0)),
        }
        
        # Assign materials to object
        for material in materials.values():
            obj.data.materials.append(material)
    except Exception as e:
        raise BlenderAPIError(f"Failed to assign materials: {str(e)}")


def get_material_index(obj: Object, material_name: str) -> int:
    """
    Get the index of a material in an object's material list.
    
    Args:
        obj: Object to search
        material_name: Name of material to find
        
    Returns:
        Material index, or 0 if not found
    """
    try:
        for idx, material in enumerate(obj.data.materials):
            if material and material.name == material_name:
                return idx
        return 0
    except Exception:
        return 0


def _get_or_create_material(name: str, color: Tuple[float, float, float, float]) -> bpy.types.Material:
    """
    Get existing material or create a new one.
    
    Args:
        name: Material name
        color: RGBA color tuple
        
    Returns:
        Material object
        
    Raises:
        BlenderAPIError: If material creation fails
    """
    try:
        material = bpy.data.materials.get(name)
        if material is None:
            material = bpy.data.materials.new(name=name)
            material.diffuse_color = color
        return material
    except Exception as e:
        raise BlenderAPIError(f"Failed to get or create material '{name}': {str(e)}")


def kmh_to_ms(speed_kmh: float) -> float:
    """
    Convert speed from km/h to m/s.
    
    Args:
        speed_kmh: Speed in km/h
        
    Returns:
        Speed in m/s
    """
    return speed_kmh / 3.6


def ms_to_kmh(speed_ms: float) -> float:
    """
    Convert speed from m/s to km/h.
    
    Args:
        speed_ms: Speed in m/s
        
    Returns:
        Speed in km/h
    """
    return speed_ms * 3.6


def get_objects_by_type(object_type: str) -> List[Object]:
    """
    Get all objects of a specific type from the scene.
    
    Args:
        object_type: Type of objects to find (e.g., 'road', 'junction', 'entity', 'trajectory')
        
    Returns:
        List of objects matching the specified type
    """
    matching_objects = []
    
    # Search in all collections
    for collection in bpy.data.collections:
        for obj in collection.objects:
            # Check object type in custom properties
            obj_type = obj.get('dsc_type', obj.get('object_type', ''))
            if obj_type and object_type in obj_type:
                matching_objects.append(obj)
    
    return matching_objects