"""
Custom exceptions for the Blender Driving Scenario Creator add-on.
"""

from typing import Optional, Any


class DSCError(Exception):
    """Base exception for all DSC-related errors."""
    
    def __init__(self, message: str, context: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.context = context


class GeometryError(DSCError):
    """Raised when geometry calculations fail."""
    pass


class RoadCreationError(DSCError):
    """Raised when road creation fails."""
    pass


class JunctionCreationError(DSCError):
    """Raised when junction creation fails."""
    pass


class EntityCreationError(DSCError):
    """Raised when entity creation fails."""
    pass


class ExportError(DSCError):
    """Raised when export operations fail."""
    pass


class ImportError(DSCError):
    """Raised when import operations fail."""
    pass


class ValidationError(DSCError):
    """Raised when parameter validation fails."""
    pass


class ConfigurationError(DSCError):
    """Raised when configuration is invalid."""
    pass


class BlenderAPIError(DSCError):
    """Raised when Blender API operations fail."""
    pass


class UnsupportedVersionError(DSCError):
    """Raised when Blender version is not supported."""
    pass


class FileOperationError(DSCError):
    """Raised when file operations fail."""
    pass


class NetworkError(DSCError):
    """Raised when network operations fail."""
    pass 