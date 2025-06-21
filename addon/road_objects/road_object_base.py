"""
Base road object class for the Driving Scenario Creator add-on.
"""

import bpy
from typing import Optional, Dict, Any, Tuple, List
from mathutils import Vector, Matrix
from abc import ABC, abstractmethod

from ..core.constants import *
from ..core.exceptions import ValidationError
from ..utils.validation_utils import validate_not_none, validate_positive, validate_range
from ..utils.blender_utils import link_object_opendrive
from .. import helpers


class RoadObjectBase(ABC):
    """
    Abstract base class for all road objects (signs, traffic lights, stop lines, stencils).
    
    This class provides common functionality for positioning, creating, and exporting
    road objects in the driving scenario.
    """
    
    def __init__(self, context: bpy.types.Context, road_object_type: str):
        """
        Initialize the road object.
        
        Args:
            context: Blender context
            road_object_type: Type of road object
            
        Raises:
            ValidationError: If parameters are invalid
        """
        validate_not_none(context, "context")
        validate_not_none(road_object_type, "road_object_type")
        
        self.context = context
        self.road_object_type = road_object_type
        self.object_id: Optional[int] = None
        self.properties: Dict[str, Any] = {}
        
    @abstractmethod
    def get_default_dimensions(self) -> Tuple[float, float, float]:
        """
        Get default dimensions (width, height, length) for this road object type.
        
        Returns:
            Tuple of (width, height, length) in meters
        """
        pass
    
    @abstractmethod
    def create_mesh(self, wireframe: bool = False) -> Tuple[bpy.types.Mesh, List[int]]:
        """
        Create the 3D mesh for this road object.
        
        Args:
            wireframe: Whether to create wireframe mesh
            
        Returns:
            Tuple of (mesh, materials) where materials is a list of material indices
        """
        pass
    
    @abstractmethod
    def get_catalog_info(self) -> Dict[str, Any]:
        """
        Get catalog information for OpenDRIVE export.
        
        Returns:
            Dictionary with catalog type, subtype, and value information
        """
        pass
    
    def create_object_3d(self, road_id: int, position_s: float, position_t: float,
                        rotation: float = 0.0, z_offset: float = 0.0) -> bpy.types.Object:
        """
        Create a 3D Blender object for this road object.
        
        Args:
            road_id: ID of the road this object is attached to
            position_s: Position along road (s-coordinate)
            position_t: Position across road (t-coordinate) 
            rotation: Rotation around Z-axis in radians
            z_offset: Vertical offset in meters
            
        Returns:
            Created Blender object
            
        Raises:
            ValidationError: If creation fails
        """
        try:
            # Get road object to attach to
            road_obj = helpers.get_object_xodr_by_id(road_id)
            if not road_obj:
                raise ValidationError(f"Road with ID {road_id} not found")
            
            # Calculate world position from road coordinates
            world_position, heading = self._calculate_world_position(
                road_obj, position_s, position_t, z_offset
            )
            
            # Generate ID and name
            if self.object_id is None:
                self.object_id = helpers.get_new_id_opendrive(self.context)
            
            name = f"{self.road_object_type}_{self.object_id}"
            
            # Create mesh and object
            mesh, materials = self.create_mesh()
            mesh.name = name + "_mesh"
            
            obj = bpy.data.objects.new(name, mesh)
            
            # Set transformation
            mat_translation = Matrix.Translation(world_position)
            mat_rotation = Matrix.Rotation(heading + rotation, 4, 'Z')
            obj.matrix_world = mat_translation @ mat_rotation
            
            # Link to scene
            link_object_opendrive(self.context, obj)
            
            # Set properties
            self._set_object_properties(obj, road_id, position_s, position_t, z_offset)
            
            # Assign materials
            self._assign_materials(obj, materials)
            
            return obj
            
        except Exception as e:
            raise ValidationError(f"Failed to create road object: {str(e)}") from e
    
    def _calculate_world_position(self, road_obj: bpy.types.Object, position_s: float,
                                position_t: float, z_offset: float) -> Tuple[Vector, float]:
        """
        Calculate world position and heading from road coordinates.
        
        Args:
            road_obj: Road object to attach to
            position_s: S-coordinate along road
            position_t: T-coordinate across road  
            z_offset: Vertical offset
            
        Returns:
            Tuple of (world_position, heading_angle)
        """
        # This is a simplified implementation
        # In a full implementation, this would use the road geometry to
        # properly transform from road coordinates to world coordinates
        
        # For now, use a basic approximation
        road_start = road_obj.get('cp_start_l', Vector((0, 0, 0)))
        road_end = road_obj.get('cp_end_l', Vector((1, 0, 0)))
        
        # Calculate position along road
        if hasattr(road_start, '__len__') and len(road_start) >= 3:
            road_start = Vector(road_start)
        if hasattr(road_end, '__len__') and len(road_end) >= 3:
            road_end = Vector(road_end)
            
        road_length = road_obj.get('geometry_total_length', 1.0)
        t_factor = position_s / road_length if road_length > 0 else 0.0
        
        # Interpolate along road
        road_position = road_start.lerp(road_end, t_factor)
        
        # Add lateral offset
        road_direction = (road_end - road_start).normalized()
        lateral_direction = Vector((-road_direction.y, road_direction.x, 0))
        lateral_offset = lateral_direction * position_t
        
        world_position = road_position + lateral_offset + Vector((0, 0, z_offset))
        
        # Calculate heading
        heading = road_direction.to_track_quat('Y', 'Z').to_euler().z
        
        return world_position, heading
    
    def _set_object_properties(self, obj: bpy.types.Object, road_id: int, 
                             position_s: float, position_t: float, z_offset: float) -> None:
        """Set object custom properties for OpenDRIVE export."""
        obj['id_odr'] = self.object_id
        obj['dsc_category'] = 'OpenDRIVE'
        obj['dsc_type'] = self.road_object_type
        obj['id_road'] = road_id
        obj['position_s'] = position_s
        obj['position_t'] = position_t
        obj['zOffset'] = z_offset
        
        # Set dimensions
        width, height, length = self.get_default_dimensions()
        obj['width'] = width
        obj['height'] = height
        obj['length'] = length
        
        # Set catalog information
        catalog_info = self.get_catalog_info()
        obj['catalog_type'] = catalog_info.get('type', '')
        obj['catalog_subtype'] = catalog_info.get('subtype', None)
        obj['value'] = catalog_info.get('value', None)
        
        # Store additional properties
        for key, value in self.properties.items():
            obj[key] = value
    
    def _assign_materials(self, obj: bpy.types.Object, materials: List[int]) -> None:
        """Assign materials to the object based on material indices."""
        # Apply standard materials assignment
        helpers.assign_materials(obj)
        
        # Apply specific materials if provided
        if materials and hasattr(obj.data, 'polygons'):
            for idx, polygon in enumerate(obj.data.polygons):
                if idx < len(materials):
                    material_index = materials[idx]
                    if material_index < len(obj.data.materials):
                        polygon.material_index = material_index
    
    def update_position(self, obj: bpy.types.Object, position_s: float, 
                       position_t: float, z_offset: float) -> None:
        """
        Update road object position.
        
        Args:
            obj: Blender object to update
            position_s: New S-coordinate
            position_t: New T-coordinate  
            z_offset: New vertical offset
        """
        validate_not_none(obj, "obj")
        
        # Get road object
        road_id = obj.get('id_road')
        if road_id is None:
            return
            
        road_obj = helpers.get_object_xodr_by_id(road_id)
        if not road_obj:
            return
        
        # Calculate new world position
        world_position, heading = self._calculate_world_position(
            road_obj, position_s, position_t, z_offset
        )
        
        # Update object transform
        mat_translation = Matrix.Translation(world_position)
        mat_rotation = Matrix.Rotation(heading, 4, 'Z')
        obj.matrix_world = mat_translation @ mat_rotation
        
        # Update properties
        obj['position_s'] = position_s
        obj['position_t'] = position_t
        obj['zOffset'] = z_offset
    
    def get_export_data(self, obj: bpy.types.Object) -> Dict[str, Any]:
        """
        Get data for OpenDRIVE export.
        
        Args:
            obj: Blender object
            
        Returns:
            Dictionary with export data
        """
        return {
            'id': obj.get('id_odr'),
            'type': obj.get('catalog_type'),
            'subtype': obj.get('catalog_subtype'),
            'value': obj.get('value'),
            's': obj.get('position_s'),
            't': obj.get('position_t'),
            'zOffset': obj.get('zOffset'),
            'width': obj.get('width'),
            'height': obj.get('height'),
            'length': obj.get('length'),
            'name': obj.name
        }
    
    def validate_position(self, road_obj: bpy.types.Object, position_s: float, 
                         position_t: float) -> bool:
        """
        Validate if the given position is valid for the road.
        
        Args:
            road_obj: Road object
            position_s: S-coordinate to validate
            position_t: T-coordinate to validate
            
        Returns:
            True if position is valid, False otherwise
        """
        try:
            # Check s-coordinate bounds
            road_length = road_obj.get('geometry_total_length', 0.0)
            if not (0.0 <= position_s <= road_length):
                return False
            
            # Check t-coordinate bounds (simplified check)
            # In a full implementation, this would check actual lane boundaries
            max_t = 20.0  # Assume maximum road width of 40m (±20m)
            if not (-max_t <= position_t <= max_t):
                return False
                
            return True
            
        except Exception:
            return False 