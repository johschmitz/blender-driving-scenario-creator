"""
Entity package for the Driving Scenario Creator add-on.

This package contains all entity-related classes including vehicles, pedestrians,
and their properties.
"""

from .entity_base import EntityBase
from .entity_vehicle import VehicleEntity
from .entity_pedestrian import PedestrianEntity
from .entity_properties import (
    DSC_entity_properties_vehicle,
    DSC_entity_properties_pedestrian
)

__all__ = [
    'EntityBase',
    'VehicleEntity', 
    'PedestrianEntity',
    'DSC_entity_properties_vehicle',
    'DSC_entity_properties_pedestrian'
] 