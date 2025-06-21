"""
Vehicle entity implementation for the Driving Scenario Creator add-on.
"""

import bpy
import bmesh
from typing import Tuple, Optional
from mathutils import Vector

from .entity_base import EntityBase
from ..core.constants import *
from ..utils.geometry_utils import create_box_mesh


class VehicleEntity(EntityBase):
    """
    Vehicle entity class for creating car, truck, motorcycle, and bicycle objects.
    """
    
    # Vehicle dimension constants (length, width, height in meters)
    VEHICLE_DIMENSIONS = {
        'car': (4.5, 1.8, 1.5),
        'truck': (12.0, 2.5, 3.0), 
        'motorcycle': (2.0, 0.8, 1.2),
        'bicycle': (1.8, 0.6, 1.1)
    }
    
    # Default speeds in km/h
    VEHICLE_SPEEDS = {
        'car': 50.0,
        'truck': 80.0,
        'motorcycle': 60.0,
        'bicycle': 20.0
    }
    
    def __init__(self, context: bpy.types.Context, vehicle_subtype: str = 'car'):
        """
        Initialize vehicle entity.
        
        Args:
            context: Blender context
            vehicle_subtype: Type of vehicle (car, truck, motorcycle, bicycle)
        """
        super().__init__(context, 'vehicle')
        
        if vehicle_subtype not in self.VEHICLE_DIMENSIONS:
            vehicle_subtype = 'car'  # Default fallback
            
        self.vehicle_subtype = vehicle_subtype
        
        # Set vehicle-specific properties
        self.properties.update({
            'vehicle_category': self._get_vehicle_category(),
            'mass': self._get_default_mass(),
            'max_speed': self._get_max_speed(),
            'max_acceleration': self._get_max_acceleration(),
            'max_deceleration': self._get_max_deceleration()
        })
    
    def get_entity_subtype(self) -> str:
        """Get vehicle subtype."""
        return self.vehicle_subtype
    
    def get_default_dimensions(self) -> Tuple[float, float, float]:
        """Get default dimensions for this vehicle type."""
        return self.VEHICLE_DIMENSIONS[self.vehicle_subtype]
    
    def get_default_speed(self) -> float:
        """Get default speed for this vehicle type."""
        return self.VEHICLE_SPEEDS[self.vehicle_subtype]
    
    def create_mesh(self) -> bpy.types.Mesh:
        """
        Create 3D mesh for the vehicle.
        
        Returns:
            Blender mesh representing the vehicle
        """
        length, width, height = self.get_default_dimensions()
        
        # Create basic box mesh for the vehicle body
        mesh = create_box_mesh(
            name=f"vehicle_{self.vehicle_subtype}_mesh",
            size=(length, width, height)
        )
        
        # Add vehicle-specific details
        self._add_vehicle_details(mesh, length, width, height)
        
        return mesh
    
    def _add_vehicle_details(self, mesh: bpy.types.Mesh, length: float, width: float, height: float) -> None:
        """Add vehicle-specific mesh details."""
        # Enter edit mode for mesh modification
        bm = bmesh.new()
        bm.from_mesh(mesh)
        
        if self.vehicle_subtype == 'car':
            self._add_car_details(bm, length, width, height)
        elif self.vehicle_subtype == 'truck':
            self._add_truck_details(bm, length, width, height)
        elif self.vehicle_subtype == 'motorcycle':
            self._add_motorcycle_details(bm, length, width, height)
        elif self.vehicle_subtype == 'bicycle':
            self._add_bicycle_details(bm, length, width, height)
        
        # Update mesh
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
    
    def _add_car_details(self, bm: bmesh.types.BMesh, length: float, width: float, height: float) -> None:
        """Add car-specific details like windshield, wheels.""" 
        # Add a simple windshield slope by moving front-top vertices
        for vert in bm.verts:
            # Move front vertices slightly back and down for windshield effect
            if vert.co.x > length * 0.3 and vert.co.z > height * 0.5:
                vert.co.x -= length * 0.1
                vert.co.z -= height * 0.1
    
    def _add_truck_details(self, bm: bmesh.types.BMesh, length: float, width: float, height: float) -> None:
        """Add truck-specific details like cab separation."""
        # Create cab/trailer separation by adding loop cuts
        # This is a simplified implementation - could be expanded
        pass
    
    def _add_motorcycle_details(self, bm: bmesh.types.BMesh, length: float, width: float, height: float) -> None:
        """Add motorcycle-specific details."""
        # Make the body narrower and add some basic shaping
        for vert in bm.verts:
            # Narrow the middle section
            if abs(vert.co.x) < length * 0.3:
                vert.co.y *= 0.7
    
    def _add_bicycle_details(self, bm: bmesh.types.BMesh, length: float, width: float, height: float) -> None:
        """Add bicycle-specific details."""
        # Make it even narrower than motorcycle
        for vert in bm.verts:
            vert.co.y *= 0.5
            # Lower the center of mass
            vert.co.z -= height * 0.2
    
    def _get_vehicle_category(self) -> str:
        """Get OpenSCENARIO vehicle category."""
        category_mapping = {
            'car': 'car',
            'truck': 'truck',
            'motorcycle': 'motorbike', 
            'bicycle': 'bicycle'
        }
        return category_mapping.get(self.vehicle_subtype, 'car')
    
    def _get_default_mass(self) -> float:
        """Get default mass in kg."""
        mass_mapping = {
            'car': 1500.0,
            'truck': 12000.0,
            'motorcycle': 200.0,
            'bicycle': 15.0
        }
        return mass_mapping.get(self.vehicle_subtype, 1500.0)
    
    def _get_max_speed(self) -> float:
        """Get maximum speed in km/h."""
        max_speed_mapping = {
            'car': 200.0,
            'truck': 120.0,
            'motorcycle': 180.0,
            'bicycle': 40.0
        }
        return max_speed_mapping.get(self.vehicle_subtype, 200.0)
    
    def _get_max_acceleration(self) -> float:
        """Get maximum acceleration in m/s²."""
        acceleration_mapping = {
            'car': 5.0,
            'truck': 2.0,
            'motorcycle': 6.0,
            'bicycle': 2.0
        }
        return acceleration_mapping.get(self.vehicle_subtype, 5.0)
    
    def _get_max_deceleration(self) -> float:
        """Get maximum deceleration in m/s²."""
        deceleration_mapping = {
            'car': 8.0,
            'truck': 6.0,
            'motorcycle': 9.0,
            'bicycle': 4.0
        }
        return deceleration_mapping.get(self.vehicle_subtype, 8.0)
    
    def get_axle_data(self) -> dict:
        """
        Get axle data for OpenSCENARIO export.
        
        Returns:
            Dictionary with front and rear axle specifications
        """
        if self.vehicle_subtype == 'car':
            return {
                'front': {
                    'max_steering': 0.523599,  # 30 degrees in radians
                    'wheel_diameter': 0.8,
                    'track_width': 1.554,
                    'position_x': self.get_default_dimensions()[0] * 0.3,
                    'position_z': 0.4
                },
                'rear': {
                    'max_steering': 0.0,
                    'wheel_diameter': 0.8, 
                    'track_width': 1.525,
                    'position_x': -self.get_default_dimensions()[0] * 0.3,
                    'position_z': 0.4
                }
            }
        elif self.vehicle_subtype == 'truck':
            return {
                'front': {
                    'max_steering': 0.436332,  # 25 degrees
                    'wheel_diameter': 1.0,
                    'track_width': 2.0,
                    'position_x': self.get_default_dimensions()[0] * 0.4,
                    'position_z': 0.5
                },
                'rear': {
                    'max_steering': 0.0,
                    'wheel_diameter': 1.0,
                    'track_width': 2.0,
                    'position_x': -self.get_default_dimensions()[0] * 0.2,
                    'position_z': 0.5
                }
            }
        else:
            # Default for motorcycle/bicycle
            return {
                'front': {
                    'max_steering': 0.785398,  # 45 degrees
                    'wheel_diameter': 0.6,
                    'track_width': 0.1,
                    'position_x': self.get_default_dimensions()[0] * 0.4,
                    'position_z': 0.3
                },
                'rear': {
                    'max_steering': 0.0,
                    'wheel_diameter': 0.6,
                    'track_width': 0.1,
                    'position_x': -self.get_default_dimensions()[0] * 0.4,
                    'position_z': 0.3
                }
            } 