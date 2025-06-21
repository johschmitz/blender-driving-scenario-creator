"""
Base entity class for the Driving Scenario Creator add-on.
"""

import bpy
from typing import Optional, Dict, Any, Tuple
from mathutils import Vector
from abc import ABC, abstractmethod

from ..core.constants import *
from ..core.exceptions import ValidationError
from ..utils.validation_utils import validate_not_none, validate_positive
from ..utils.blender_utils import link_object_openscenario
from .. import helpers


class EntityBase(ABC):
    """
    Abstract base class for all entities in the driving scenario.
    
    This class provides common functionality for vehicles, pedestrians,
    and other dynamic objects in the scenario.
    """
    
    def __init__(self, context: bpy.types.Context, entity_type: str):
        """
        Initialize the entity.
        
        Args:
            context: Blender context
            entity_type: Type of entity (vehicle, pedestrian, etc.)
            
        Raises:
            ValidationError: If parameters are invalid
        """
        validate_not_none(context, "context")
        validate_not_none(entity_type, "entity_type")
        
        self.context = context
        self.entity_type = entity_type
        self.entity_id: Optional[int] = None
        self.properties: Dict[str, Any] = {}
        
    @abstractmethod
    def get_entity_subtype(self) -> str:
        """
        Get the specific subtype of this entity.
        
        Returns:
            String identifier for the entity subtype
        """
        pass
    
    @abstractmethod
    def get_default_dimensions(self) -> Tuple[float, float, float]:
        """
        Get default dimensions (length, width, height) for this entity type.
        
        Returns:
            Tuple of (length, width, height) in meters
        """
        pass
    
    @abstractmethod
    def get_default_speed(self) -> float:
        """
        Get default speed for this entity type.
        
        Returns:
            Default speed in km/h
        """
        pass
    
    @abstractmethod
    def create_mesh(self) -> bpy.types.Mesh:
        """
        Create the 3D mesh for this entity.
        
        Returns:
            Blender mesh object
        """
        pass
    
    def create_object_3d(self, location: Vector, rotation: float = 0.0, 
                        name: Optional[str] = None, color: Optional[Tuple[float, float, float, float]] = None) -> bpy.types.Object:
        """
        Create a 3D Blender object for this entity.
        
        Args:
            location: World position for the entity
            rotation: Rotation around Z-axis in radians
            name: Optional custom name for the object
            color: Optional RGBA color tuple
            
        Returns:
            Created Blender object
            
        Raises:
            ValidationError: If creation fails
        """
        try:
            # Generate ID and name
            if self.entity_id is None:
                self.entity_id = helpers.get_new_id_openscenario(self.context)
            
            if name is None:
                name = f"{self.entity_type}_{self.entity_id}"
            
            # Create mesh and object
            mesh = self.create_mesh()
            mesh.name = name + "_mesh"
            
            obj = bpy.data.objects.new(name, mesh)
            obj.location = location
            obj.rotation_euler.z = rotation
            
            # Link to scene
            link_object_openscenario(self.context, obj, subcategory='entities')
            
            # Set properties
            self._set_object_properties(obj)
            
            # Apply color if specified
            if color is not None:
                self._apply_color(obj, color)
            
            return obj
            
        except Exception as e:
            raise ValidationError(f"Failed to create entity object: {str(e)}") from e
    
    def _set_object_properties(self, obj: bpy.types.Object) -> None:
        """Set object custom properties for OpenSCENARIO export."""
        obj['id_osc'] = self.entity_id
        obj['dsc_category'] = 'OpenSCENARIO'
        obj['dsc_type'] = 'entity'
        obj['entity_type'] = self.entity_type
        obj['entity_subtype'] = self.get_entity_subtype()
        
        # Store entity dimensions
        length, width, height = self.get_default_dimensions()
        obj['length'] = length
        obj['width'] = width
        obj['height'] = height
        
        # Store default speed
        obj['speed_initial'] = self.get_default_speed()
        
        # Store additional properties
        for key, value in self.properties.items():
            obj[key] = value
    
    def _apply_color(self, obj: bpy.types.Object, color: Tuple[float, float, float, float]) -> None:
        """Apply color material to the object."""
        # Create or get material
        material_name = f"entity_{self.entity_type}_material"
        if material_name in bpy.data.materials:
            material = bpy.data.materials[material_name]
        else:
            material = bpy.data.materials.new(name=material_name)
            material.use_nodes = True
            material.node_tree.clear()
            
            # Create principled BSDF node
            bsdf = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
            bsdf.inputs['Base Color'].default_value = color
            
            # Create material output
            output = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
            material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        # Assign material to object
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
    
    def update_location(self, obj: bpy.types.Object, new_location: Vector) -> None:
        """
        Update entity location.
        
        Args:
            obj: Blender object to update
            new_location: New world position
        """
        validate_not_none(obj, "obj")
        validate_not_none(new_location, "new_location")
        
        obj.location = new_location
    
    def update_rotation(self, obj: bpy.types.Object, new_rotation: float) -> None:
        """
        Update entity rotation.
        
        Args:
            obj: Blender object to update  
            new_rotation: New rotation around Z-axis in radians
        """
        validate_not_none(obj, "obj")
        
        obj.rotation_euler.z = new_rotation
    
    def get_bounding_box(self) -> Dict[str, float]:
        """
        Get bounding box dimensions for OpenSCENARIO export.
        
        Returns:
            Dictionary with bounding box parameters
        """
        length, width, height = self.get_default_dimensions()
        
        return {
            'length': length,
            'width': width, 
            'height': height,
            'center_x': length / 2,
            'center_y': 0.0,
            'center_z': height / 2
        } 