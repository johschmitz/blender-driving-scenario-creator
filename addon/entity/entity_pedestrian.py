"""
Pedestrian entity implementation for the Driving Scenario Creator add-on.
"""

import bpy
import bmesh
from typing import Tuple, Optional
from mathutils import Vector

from .entity_base import EntityBase
from ..core.constants import *
from ..utils.geometry_utils import create_cylinder_mesh


class PedestrianEntity(EntityBase):
    """
    Pedestrian entity class for creating human figures in driving scenarios.
    """
    
    # Pedestrian dimension constants (length, width, height in meters)
    PEDESTRIAN_DIMENSIONS = {
        'adult': (0.6, 0.4, 1.8),
        'child': (0.4, 0.3, 1.2),
        'elderly': (0.6, 0.4, 1.7),
        'wheelchair': (1.2, 0.7, 1.3)
    }
    
    # Default speeds in km/h
    PEDESTRIAN_SPEEDS = {
        'adult': 5.0,
        'child': 4.0,
        'elderly': 3.0,
        'wheelchair': 3.5
    }
    
    def __init__(self, context: bpy.types.Context, pedestrian_subtype: str = 'adult'):
        """
        Initialize pedestrian entity.
        
        Args:
            context: Blender context
            pedestrian_subtype: Type of pedestrian (adult, child, elderly, wheelchair)
        """
        super().__init__(context, 'pedestrian')
        
        if pedestrian_subtype not in self.PEDESTRIAN_DIMENSIONS:
            pedestrian_subtype = 'adult'  # Default fallback
            
        self.pedestrian_subtype = pedestrian_subtype
        
        # Set pedestrian-specific properties
        self.properties.update({
            'pedestrian_category': self._get_pedestrian_category(),
            'mass': self._get_default_mass(),
            'max_speed': self._get_max_speed()
        })
    
    def get_entity_subtype(self) -> str:
        """Get pedestrian subtype."""
        return self.pedestrian_subtype
    
    def get_default_dimensions(self) -> Tuple[float, float, float]:
        """Get default dimensions for this pedestrian type."""
        return self.PEDESTRIAN_DIMENSIONS[self.pedestrian_subtype]
    
    def get_default_speed(self) -> float:
        """Get default speed for this pedestrian type."""
        return self.PEDESTRIAN_SPEEDS[self.pedestrian_subtype]
    
    def create_mesh(self) -> bpy.types.Mesh:
        """
        Create 3D mesh for the pedestrian.
        
        Returns:
            Blender mesh representing the pedestrian
        """
        length, width, height = self.get_default_dimensions()
        
        # Create cylindrical mesh for basic human shape
        mesh = create_cylinder_mesh(
            name=f"pedestrian_{self.pedestrian_subtype}_mesh",
            radius=width / 2,
            height=height,
            segments=8  # Octagonal cross-section
        )
        
        # Add pedestrian-specific details
        self._add_pedestrian_details(mesh, length, width, height)
        
        return mesh
    
    def _add_pedestrian_details(self, mesh: bpy.types.Mesh, length: float, width: float, height: float) -> None:
        """Add pedestrian-specific mesh details."""
        # Enter edit mode for mesh modification
        bm = bmesh.new()
        bm.from_mesh(mesh)
        
        if self.pedestrian_subtype == 'adult':
            self._add_adult_details(bm, length, width, height)
        elif self.pedestrian_subtype == 'child':
            self._add_child_details(bm, length, width, height)
        elif self.pedestrian_subtype == 'elderly':
            self._add_elderly_details(bm, length, width, height)
        elif self.pedestrian_subtype == 'wheelchair':
            self._add_wheelchair_details(bm, length, width, height)
        
        # Update mesh
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
    
    def _add_adult_details(self, bm: bmesh.types.BMesh, length: float, width: float, height: float) -> None:
        """Add adult pedestrian details like head, shoulders."""
        for vert in bm.verts:
            # Create head (narrow the top section)
            if vert.co.z > height * 0.85:
                scale_factor = 0.6
                vert.co.x *= scale_factor
                vert.co.y *= scale_factor
            # Create shoulder area (wider middle section)
            elif vert.co.z > height * 0.65:
                scale_factor = 1.2
                vert.co.x *= scale_factor
                vert.co.y *= scale_factor
    
    def _add_child_details(self, bm: bmesh.types.BMesh, length: float, width: float, height: float) -> None:
        """Add child-specific details (proportionally larger head)."""
        for vert in bm.verts:
            # Larger head proportionally
            if vert.co.z > height * 0.75:
                scale_factor = 0.8
                vert.co.x *= scale_factor
                vert.co.y *= scale_factor
            # Smaller shoulders
            elif vert.co.z > height * 0.55:
                scale_factor = 0.9
                vert.co.x *= scale_factor
                vert.co.y *= scale_factor
    
    def _add_elderly_details(self, bm: bmesh.types.BMesh, length: float, width: float, height: float) -> None:
        """Add elderly-specific details (slightly hunched posture)."""
        for vert in bm.verts:
            # Slightly forward lean
            if vert.co.z > height * 0.3:
                vert.co.x += (vert.co.z / height) * 0.05
            
            # Standard adult proportions but slightly smaller
            if vert.co.z > height * 0.85:
                scale_factor = 0.65
                vert.co.x *= scale_factor
                vert.co.y *= scale_factor
    
    def _add_wheelchair_details(self, bm: bmesh.types.BMesh, length: float, width: float, height: float) -> None:
        """Add wheelchair-specific details."""
        for vert in bm.verts:
            # Seated position - compress lower body
            if vert.co.z < height * 0.4:
                vert.co.z *= 0.5
            
            # Wheelchair base - wider at bottom
            if vert.co.z < height * 0.2:
                scale_factor = 1.5
                vert.co.x *= scale_factor
                vert.co.y *= scale_factor
    
    def _get_pedestrian_category(self) -> str:
        """Get OpenSCENARIO pedestrian category."""
        return 'pedestrian'  # Standard category for all pedestrian types
    
    def _get_default_mass(self) -> float:
        """Get default mass in kg."""
        mass_mapping = {
            'adult': 70.0,
            'child': 30.0,
            'elderly': 65.0,
            'wheelchair': 90.0  # Includes wheelchair weight
        }
        return mass_mapping.get(self.pedestrian_subtype, 70.0)
    
    def _get_max_speed(self) -> float:
        """Get maximum speed in km/h."""
        max_speed_mapping = {
            'adult': 15.0,  # Running speed
            'child': 12.0,
            'elderly': 8.0,
            'wheelchair': 10.0
        }
        return max_speed_mapping.get(self.pedestrian_subtype, 15.0)
    
    def get_movement_profile(self) -> dict:
        """
        Get movement profile for this pedestrian type.
        
        Returns:
            Dictionary with movement characteristics
        """
        return {
            'walking_speed': self.get_default_speed(),
            'running_speed': self._get_max_speed(),
            'acceleration': self._get_acceleration(),
            'deceleration': self._get_deceleration(),
            'turning_radius': self._get_turning_radius(),
            'reaction_time': self._get_reaction_time()
        }
    
    def _get_acceleration(self) -> float:
        """Get acceleration in m/s²."""
        acceleration_mapping = {
            'adult': 2.0,
            'child': 1.5,
            'elderly': 1.0,
            'wheelchair': 1.2
        }
        return acceleration_mapping.get(self.pedestrian_subtype, 2.0)
    
    def _get_deceleration(self) -> float:
        """Get deceleration in m/s²."""
        deceleration_mapping = {
            'adult': 3.0,
            'child': 2.5,
            'elderly': 2.0,
            'wheelchair': 2.2
        }
        return deceleration_mapping.get(self.pedestrian_subtype, 3.0)
    
    def _get_turning_radius(self) -> float:
        """Get minimum turning radius in meters."""
        radius_mapping = {
            'adult': 0.5,
            'child': 0.4,
            'elderly': 0.6,
            'wheelchair': 1.0
        }
        return radius_mapping.get(self.pedestrian_subtype, 0.5)
    
    def _get_reaction_time(self) -> float:
        """Get reaction time in seconds."""
        reaction_mapping = {
            'adult': 1.5,
            'child': 2.0,
            'elderly': 2.5,
            'wheelchair': 1.8
        }
        return reaction_mapping.get(self.pedestrian_subtype, 1.5) 