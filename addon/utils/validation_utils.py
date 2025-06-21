"""
Validation utility functions for the Driving Scenario Creator add-on.
"""

import re
from typing import Any, Union, List, Optional, Dict, Callable
from mathutils import Vector
from ..core.constants import *
from ..core.exceptions import ValidationError


def validate_not_none(value: Any, param_name: str = "value") -> Any:
    """
    Validate that a value is not None.
    
    Args:
        value: Value to validate
        param_name: Name of the parameter for error messages
        
    Returns:
        The validated value
        
    Raises:
        ValidationError: If value is None
    """
    if value is None:
        raise ValidationError(f"{param_name} cannot be None")
    return value


def validate_positive(value: Union[int, float], param_name: str = "value") -> Union[int, float]:
    """
    Validate that a numeric value is positive (> 0).
    
    Args:
        value: Numeric value to validate
        param_name: Name of the parameter for error messages
        
    Returns:
        The validated value
        
    Raises:
        ValidationError: If value is not positive
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{param_name} must be a number, got {type(value).__name__}")
    
    if value <= 0:
        raise ValidationError(f"{param_name} must be positive, got {value}")
    
    return value


def validate_lane_width(width: float, param_name: str = "lane_width") -> float:
    """
    Validate lane width parameter.
    
    Args:
        width: Lane width to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated lane width
        
    Raises:
        ValidationError: If width is invalid
    """
    if not isinstance(width, (int, float)):
        raise ValidationError(f"{param_name} must be a number, got {type(width)}")
    
    if width < MIN_LANE_WIDTH or width > MAX_LANE_WIDTH:
        raise ValidationError(f"{param_name} must be between {MIN_LANE_WIDTH} and {MAX_LANE_WIDTH} meters")
    
    return float(width)


def validate_design_speed(speed: float, param_name: str = "design_speed") -> float:
    """
    Validate design speed parameter.
    
    Args:
        speed: Design speed to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated design speed
        
    Raises:
        ValidationError: If speed is invalid
    """
    if not isinstance(speed, (int, float)):
        raise ValidationError(f"{param_name} must be a number, got {type(speed)}")
    
    if speed < MIN_DESIGN_SPEED or speed > MAX_DESIGN_SPEED:
        raise ValidationError(f"{param_name} must be between {MIN_DESIGN_SPEED} and {MAX_DESIGN_SPEED} km/h")
    
    return float(speed)


def validate_lane_count(count: int, param_name: str = "lane_count") -> int:
    """
    Validate lane count parameter.
    
    Args:
        count: Lane count to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated lane count
        
    Raises:
        ValidationError: If count is invalid
    """
    if not isinstance(count, int):
        raise ValidationError(f"{param_name} must be an integer, got {type(count)}")
    
    if count < 0 or count > MAX_LANES_PER_SIDE:
        raise ValidationError(f"{param_name} must be between 0 and {MAX_LANES_PER_SIDE}")
    
    return count


def validate_cross_section_preset(preset: str, param_name: str = "cross_section") -> str:
    """
    Validate cross section preset.
    
    Args:
        preset: Cross section preset to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated cross section preset
        
    Raises:
        ValidationError: If preset is invalid
    """
    if not isinstance(preset, str):
        raise ValidationError(f"{param_name} must be a string, got {type(preset)}")
    
    if preset not in CROSS_SECTION_PRESETS:
        raise ValidationError(f"{param_name} '{preset}' is not a valid cross section preset")
    
    return preset


def validate_object_type(obj_type: str, param_name: str = "object_type") -> str:
    """
    Validate object type.
    
    Args:
        obj_type: Object type to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated object type
        
    Raises:
        ValidationError: If object type is invalid
    """
    if not isinstance(obj_type, str):
        raise ValidationError(f"{param_name} must be a string, got {type(obj_type)}")
    
    valid_types = [t.value for t in ObjectType]
    if obj_type not in valid_types:
        raise ValidationError(f"{param_name} '{obj_type}' is not a valid object type")
    
    return obj_type


def validate_geometry_solver(solver: str, param_name: str = "geometry_solver") -> str:
    """
    Validate geometry solver type.
    
    Args:
        solver: Geometry solver to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated geometry solver
        
    Raises:
        ValidationError: If solver is invalid
    """
    if not isinstance(solver, str):
        raise ValidationError(f"{param_name} must be a string, got {type(solver)}")
    
    valid_solvers = [s.value for s in GeometrySolver]
    if solver not in valid_solvers:
        raise ValidationError(f"{param_name} '{solver}' is not a valid geometry solver")
    
    return solver


def validate_filename(filename: str, param_name: str = "filename") -> str:
    """
    Validate filename for file operations.
    
    Args:
        filename: Filename to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated filename
        
    Raises:
        ValidationError: If filename is invalid
    """
    if not isinstance(filename, str):
        raise ValidationError(f"{param_name} must be a string, got {type(filename)}")
    
    if not filename.strip():
        raise ValidationError(f"{param_name} cannot be empty")
    
    # Check for invalid characters
    invalid_chars = r'<>:"/\|?*'
    if any(char in filename for char in invalid_chars):
        raise ValidationError(f"{param_name} contains invalid characters: {invalid_chars}")
    
    # Check length
    if len(filename) > 255:
        raise ValidationError(f"{param_name} is too long (max 255 characters)")
    
    return filename.strip()


def validate_export_format(format_name: str, param_name: str = "export_format") -> str:
    """
    Validate export format.
    
    Args:
        format_name: Export format to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated export format
        
    Raises:
        ValidationError: If format is invalid
    """
    if not isinstance(format_name, str):
        raise ValidationError(f"{param_name} must be a string, got {type(format_name)}")
    
    format_name = format_name.lower().strip()
    
    # Remove leading dot if present
    if format_name.startswith('.'):
        format_name = format_name[1:]
    
    supported_formats = [fmt.lstrip('.') for fmt in SUPPORTED_MESH_FORMATS]
    if format_name not in supported_formats:
        raise ValidationError(f"{param_name} '{format_name}' is not supported. Supported formats: {supported_formats}")
    
    return format_name


def validate_vector(vector: Vector, dimensions: int = 3, param_name: str = "vector") -> Vector:
    """
    Validate Vector object.
    
    Args:
        vector: Vector to validate
        dimensions: Expected number of dimensions (2 or 3)
        param_name: Parameter name for error messages
        
    Returns:
        Validated vector
        
    Raises:
        ValidationError: If vector is invalid
    """
    if not isinstance(vector, Vector):
        raise ValidationError(f"{param_name} must be a Vector, got {type(vector)}")
    
    if dimensions == 2 and len(vector) < 2:
        raise ValidationError(f"{param_name} must have at least 2 dimensions")
    elif dimensions == 3 and len(vector) < 3:
        raise ValidationError(f"{param_name} must have at least 3 dimensions")
    
    # Check for NaN or infinite values
    for i, component in enumerate(vector):
        if not isinstance(component, (int, float)):
            raise ValidationError(f"{param_name}[{i}] must be a number")
        
        if not (-1e10 < component < 1e10):  # Reasonable bounds
            raise ValidationError(f"{param_name}[{i}] value {component} is out of reasonable bounds")
    
    return vector


def validate_positive_number(value: Union[int, float], param_name: str = "value") -> Union[int, float]:
    """
    Validate that a number is positive.
    
    Args:
        value: Number to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated number
        
    Raises:
        ValidationError: If number is not positive
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{param_name} must be a number, got {type(value)}")
    
    if value <= 0:
        raise ValidationError(f"{param_name} must be positive, got {value}")
    
    return value


def validate_non_negative_number(value: Union[int, float], param_name: str = "value") -> Union[int, float]:
    """
    Validate that a number is non-negative.
    
    Args:
        value: Number to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated number
        
    Raises:
        ValidationError: If number is negative
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{param_name} must be a number, got {type(value)}")
    
    if value < 0:
        raise ValidationError(f"{param_name} must be non-negative, got {value}")
    
    return value


def validate_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float], 
                  param_name: str = "value") -> Union[int, float]:
    """
    Validate that a number is within a specified range.
    
    Args:
        value: Number to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        param_name: Parameter name for error messages
        
    Returns:
        Validated number
        
    Raises:
        ValidationError: If number is out of range
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{param_name} must be a number, got {type(value)}")
    
    if value < min_val or value > max_val:
        raise ValidationError(f"{param_name} must be between {min_val} and {max_val}, got {value}")
    
    return value


def validate_enum_value(value: str, enum_class: type, param_name: str = "value") -> str:
    """
    Validate that a string is a valid enum value.
    
    Args:
        value: String to validate
        enum_class: Enum class to validate against
        param_name: Parameter name for error messages
        
    Returns:
        Validated enum value
        
    Raises:
        ValidationError: If value is not a valid enum value
    """
    if not isinstance(value, str):
        raise ValidationError(f"{param_name} must be a string, got {type(value)}")
    
    valid_values = [item.value for item in enum_class]
    if value not in valid_values:
        raise ValidationError(f"{param_name} '{value}' is not valid. Valid values: {valid_values}")
    
    return value


def validate_list_of_type(lst: List[Any], expected_type: type, param_name: str = "list") -> List[Any]:
    """
    Validate that all items in a list are of the expected type.
    
    Args:
        lst: List to validate
        expected_type: Expected type for all items
        param_name: Parameter name for error messages
        
    Returns:
        Validated list
        
    Raises:
        ValidationError: If list or items are invalid
    """
    if not isinstance(lst, list):
        raise ValidationError(f"{param_name} must be a list, got {type(lst)}")
    
    for i, item in enumerate(lst):
        if not isinstance(item, expected_type):
            raise ValidationError(f"{param_name}[{i}] must be {expected_type.__name__}, got {type(item)}")
    
    return lst


def validate_dict_keys(dct: Dict[str, Any], required_keys: List[str], 
                      param_name: str = "dictionary") -> Dict[str, Any]:
    """
    Validate that a dictionary contains all required keys.
    
    Args:
        dct: Dictionary to validate
        required_keys: List of required keys
        param_name: Parameter name for error messages
        
    Returns:
        Validated dictionary
        
    Raises:
        ValidationError: If dictionary or keys are invalid
    """
    if not isinstance(dct, dict):
        raise ValidationError(f"{param_name} must be a dictionary, got {type(dct)}")
    
    missing_keys = [key for key in required_keys if key not in dct]
    if missing_keys:
        raise ValidationError(f"{param_name} is missing required keys: {missing_keys}")
    
    return dct


def validate_custom(value: Any, validator_func: Callable[[Any], bool], 
                   error_message: str, param_name: str = "value") -> Any:
    """
    Validate using a custom validation function.
    
    Args:
        value: Value to validate
        validator_func: Function that returns True if value is valid
        error_message: Error message if validation fails
        param_name: Parameter name for error messages
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        if not validator_func(value):
            raise ValidationError(f"{param_name}: {error_message}")
    except Exception as e:
        raise ValidationError(f"{param_name} validation failed: {str(e)}")
    
    return value


class ParameterValidator:
    """
    Utility class for validating multiple parameters at once.
    """
    
    def __init__(self):
        self.errors: List[str] = []
    
    def validate_parameter(self, param_name: str, value: Any, validator_func: Callable) -> Any:
        """
        Validate a parameter and collect any errors.
        
        Args:
            param_name: Parameter name
            value: Parameter value
            validator_func: Validation function
            
        Returns:
            Validated value or original value if validation failed
        """
        try:
            return validator_func(value)
        except ValidationError as e:
            self.errors.append(f"{param_name}: {str(e)}")
            return value
    
    def has_errors(self) -> bool:
        """Check if any validation errors occurred."""
        return len(self.errors) > 0
    
    def get_error_summary(self) -> str:
        """Get a summary of all validation errors."""
        if not self.errors:
            return "No validation errors"
        
        return "Validation errors:\n" + "\n".join(f"- {error}" for error in self.errors)
    
    def raise_if_errors(self) -> None:
        """Raise ValidationError if any errors occurred."""
        if self.errors:
            raise ValidationError(self.get_error_summary())
    
    def clear_errors(self) -> None:
        """Clear all validation errors."""
        self.errors.clear()


# Aliases for backward compatibility
validate_in_range = validate_range