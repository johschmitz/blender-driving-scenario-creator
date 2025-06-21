"""
Configuration management for the Blender Driving Scenario Creator add-on.
"""

import bpy
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from .constants import *
from .exceptions import ConfigurationError


@dataclass
class RoadConfig:
    """Configuration for road creation."""
    default_lane_width: float = DEFAULT_LANE_WIDTH
    default_border_width: float = DEFAULT_BORDER_WIDTH
    default_shoulder_width: float = DEFAULT_SHOULDER_WIDTH
    default_median_width: float = DEFAULT_MEDIAN_WIDTH
    default_stop_width: float = DEFAULT_STOP_WIDTH
    default_none_width: float = DEFAULT_NONE_WIDTH
    default_line_width_standard: float = DEFAULT_LINE_WIDTH_STANDARD
    default_line_width_bold: float = DEFAULT_LINE_WIDTH_BOLD
    default_design_speed: float = DEFAULT_DESIGN_SPEED
    max_lanes_per_side: int = MAX_LANES_PER_SIDE


@dataclass
class EntityConfig:
    """Configuration for entity creation."""
    default_speed: float = DEFAULT_ENTITY_SPEED
    default_vehicle_category: str = VehicleCategory.CAR.value
    default_pedestrian_category: str = PedestrianCategory.PEDESTRIAN.value


@dataclass
class ExportConfig:
    """Configuration for export operations."""
    default_filename: str = DEFAULT_EXPORT_FILENAME
    supported_formats: list = field(default_factory=lambda: SUPPORTED_MESH_FORMATS.copy())
    default_format: str = "fbx"
    subdirectories: Dict[str, str] = field(default_factory=lambda: EXPORT_SUBDIRS.copy())


@dataclass
class UIConfig:
    """Configuration for user interface."""
    panel_width: int = 700
    show_advanced_options: bool = False
    default_cross_section: str = "two_lanes_default"


@dataclass
class DSCConfig:
    """Main configuration class for the add-on."""
    road: RoadConfig = field(default_factory=RoadConfig)
    entity: EntityConfig = field(default_factory=EntityConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        try:
            # Validate road config
            if self.road.default_lane_width < MIN_LANE_WIDTH or self.road.default_lane_width > MAX_LANE_WIDTH:
                raise ConfigurationError(f"Invalid lane width: {self.road.default_lane_width}")
            
            if self.road.default_design_speed < MIN_DESIGN_SPEED or self.road.default_design_speed > MAX_DESIGN_SPEED:
                raise ConfigurationError(f"Invalid design speed: {self.road.default_design_speed}")
            
            if self.road.max_lanes_per_side > MAX_LANES_PER_SIDE:
                raise ConfigurationError(f"Too many lanes: {self.road.max_lanes_per_side}")
            
            # Validate export config
            if self.export.default_format not in [fmt.lstrip('.') for fmt in self.export.supported_formats]:
                raise ConfigurationError(f"Unsupported export format: {self.export.default_format}")
            
            return True
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")


class ConfigManager:
    """Manages configuration for the add-on."""
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[DSCConfig] = None
    
    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = DSCConfig()
    
    @property
    def config(self) -> DSCConfig:
        """Get the current configuration."""
        if self._config is None:
            self._config = DSCConfig()
        return self._config
    
    def update_config(self, new_config: DSCConfig) -> None:
        """Update the configuration."""
        new_config.validate()
        self._config = new_config
    
    def save_to_blend_file(self) -> None:
        """Save configuration to the current blend file."""
        try:
            # Store config in scene custom properties
            if bpy.context.scene:
                scene = bpy.context.scene
                scene["dsc_config_road_lane_width"] = self._config.road.default_lane_width
                scene["dsc_config_road_design_speed"] = self._config.road.default_design_speed
                scene["dsc_config_export_format"] = self._config.export.default_format
                scene["dsc_config_ui_cross_section"] = self._config.ui.default_cross_section
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")
    
    def load_from_blend_file(self) -> None:
        """Load configuration from the current blend file."""
        try:
            if bpy.context.scene:
                scene = bpy.context.scene
                
                # Load saved config values
                if "dsc_config_road_lane_width" in scene:
                    self._config.road.default_lane_width = scene["dsc_config_road_lane_width"]
                
                if "dsc_config_road_design_speed" in scene:
                    self._config.road.default_design_speed = scene["dsc_config_road_design_speed"]
                
                if "dsc_config_export_format" in scene:
                    self._config.export.default_format = scene["dsc_config_export_format"]
                
                if "dsc_config_ui_cross_section" in scene:
                    self._config.ui.default_cross_section = scene["dsc_config_ui_cross_section"]
                
                self._config.validate()
        except Exception as e:
            # If loading fails, use defaults
            self._config = DSCConfig()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = DSCConfig()


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> DSCConfig:
    """Get the current configuration."""
    return config_manager.config


def update_config(new_config: DSCConfig) -> None:
    """Update the configuration."""
    config_manager.update_config(new_config)


def save_config() -> None:
    """Save configuration to blend file."""
    config_manager.save_to_blend_file()


def load_config() -> None:
    """Load configuration from blend file."""
    config_manager.load_from_blend_file()


def reset_config() -> None:
    """Reset configuration to defaults."""
    config_manager.reset_to_defaults() 