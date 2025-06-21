"""
Logging utility functions for the Driving Scenario Creator add-on.
Provides structured, clean, and informative logging output.
"""

import time
import sys
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from ..core.constants import ADDON_NAME


class LogLevel(Enum):
    """Log levels for different types of messages."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


@dataclass
class LogEntry:
    """Represents a single log entry."""
    level: LogLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DSCLogger:
    """
    Enhanced logger for the Driving Scenario Creator add-on.
    Provides structured, clean, and informative logging.
    """
    
    def __init__(self, name: str = ADDON_NAME):
        """
        Initialize the logger.
        
        Args:
            name: Name of the logger (usually the add-on name)
        """
        self.name = name
        self.log_entries: List[LogEntry] = []
        self.start_time = time.time()
        self.operation_stack: List[str] = []
        self.indent_level = 0
        
        # Statistics tracking
        self.stats = {
            'objects_created': 0,
            'objects_deleted': 0,
            'vertices_removed': 0,
            'roads_created': 0,
            'entities_created': 0,
            'exports_completed': 0,
            'warnings': 0,
            'errors': 0
        }
        
        # Colors for terminal output
        self.colors = {
            LogLevel.DEBUG: '\033[90m',    # Gray
            LogLevel.INFO: '\033[94m',     # Blue
            LogLevel.WARNING: '\033[93m',  # Yellow
            LogLevel.ERROR: '\033[91m',    # Red
            LogLevel.SUCCESS: '\033[92m',  # Green
            'RESET': '\033[0m',
            'BOLD': '\033[1m',
            'DIM': '\033[2m'
        }
    
    def _format_message(self, level: LogLevel, message: str, category: Optional[str] = None) -> str:
        """
        Format a log message with proper styling.
        
        Args:
            level: Log level
            message: Message content
            category: Optional category for grouping
            
        Returns:
            Formatted message string
        """
        # Get color codes
        color = self.colors.get(level, '')
        reset = self.colors['RESET']
        bold = self.colors['BOLD']
        dim = self.colors['DIM']
        
        # Create indent
        indent = "  " * self.indent_level
        
        # Create timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Create level indicator
        level_indicators = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "ℹ️ ",
            LogLevel.WARNING: "⚠️ ",
            LogLevel.ERROR: "❌",
            LogLevel.SUCCESS: "✅"
        }
        indicator = level_indicators.get(level, "  ")
        
        # Format category if provided
        category_str = f"[{category}] " if category else ""
        
        # Combine everything
        formatted = f"{dim}{timestamp}{reset} {color}{indicator} {bold}{category_str}{reset}{color}{indent}{message}{reset}"
        
        return formatted
    
    def _log(self, level: LogLevel, message: str, category: Optional[str] = None, 
             details: Optional[Dict[str, Any]] = None) -> None:
        """
        Internal logging method.
        
        Args:
            level: Log level
            message: Message content
            category: Optional category
            details: Optional additional details
        """
        # Create log entry
        entry = LogEntry(level=level, message=message, category=category, details=details)
        self.log_entries.append(entry)
        
        # Update statistics
        if level == LogLevel.WARNING:
            self.stats['warnings'] += 1
        elif level == LogLevel.ERROR:
            self.stats['errors'] += 1
        
        # Print to console
        formatted_message = self._format_message(level, message, category)
        print(formatted_message)
        
        # Print details if provided
        if details:
            for key, value in details.items():
                detail_msg = f"  {key}: {value}"
                detail_formatted = self._format_message(LogLevel.DEBUG, detail_msg)
                print(detail_formatted)
    
    def debug(self, message: str, category: Optional[str] = None, **kwargs) -> None:
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message, category, kwargs if kwargs else None)
    
    def info(self, message: str, category: Optional[str] = None, **kwargs) -> None:
        """Log an info message."""
        self._log(LogLevel.INFO, message, category, kwargs if kwargs else None)
    
    def warning(self, message: str, category: Optional[str] = None, **kwargs) -> None:
        """Log a warning message."""
        self._log(LogLevel.WARNING, message, category, kwargs if kwargs else None)
    
    def error(self, message: str, category: Optional[str] = None, **kwargs) -> None:
        """Log an error message."""
        self._log(LogLevel.ERROR, message, category, kwargs if kwargs else None)
    
    def success(self, message: str, category: Optional[str] = None, **kwargs) -> None:
        """Log a success message."""
        self._log(LogLevel.SUCCESS, message, category, kwargs if kwargs else None)
    
    def start_operation(self, operation_name: str, category: Optional[str] = None) -> None:
        """
        Start a new operation (increases indent level).
        
        Args:
            operation_name: Name of the operation
            category: Optional category
        """
        self.operation_stack.append(operation_name)
        self.info(f"Starting {operation_name}...", category)
        self.indent_level += 1
    
    def end_operation(self, operation_name: Optional[str] = None, success: bool = True, 
                     duration: Optional[float] = None, **stats) -> None:
        """
        End the current operation (decreases indent level).
        
        Args:
            operation_name: Name of the operation (for verification)
            success: Whether the operation was successful
            duration: Duration in seconds
            **stats: Additional statistics to log
        """
        if self.indent_level > 0:
            self.indent_level -= 1
        
        if self.operation_stack:
            current_op = self.operation_stack.pop()
            
            # Create completion message
            if duration is not None:
                duration_str = f" in {duration:.3f}s"
            else:
                duration_str = ""
            
            # Format statistics
            stats_str = ""
            if stats:
                stats_parts = [f"{k}={v}" for k, v in stats.items()]
                stats_str = f" ({', '.join(stats_parts)})"
            
            message = f"Completed {current_op}{duration_str}{stats_str}"
            
            if success:
                self.success(message)
            else:
                self.error(f"Failed {current_op}{duration_str}")
    
    def log_object_creation(self, obj_type: str, obj_name: str, obj_id: Optional[int] = None) -> None:
        """
        Log object creation with proper formatting.
        
        Args:
            obj_type: Type of object (road, entity, etc.)
            obj_name: Name of the object
            obj_id: Optional object ID
        """
        self.stats['objects_created'] += 1
        
        if obj_type.lower() == 'road':
            self.stats['roads_created'] += 1
        elif obj_type.lower() in ['entity', 'vehicle', 'pedestrian']:
            self.stats['entities_created'] += 1
        
        id_str = f" (ID: {obj_id})" if obj_id is not None else ""
        self.info(f"Created {obj_type}: {obj_name}{id_str}", "Creation")
    
    def log_object_deletion(self, count: int, obj_type: Optional[str] = None) -> None:
        """
        Log object deletion with proper formatting.
        
        Args:
            count: Number of objects deleted
            obj_type: Optional type of objects deleted
        """
        self.stats['objects_deleted'] += count
        
        obj_type_str = f" {obj_type}" if obj_type else ""
        plural = "s" if count != 1 else ""
        self.info(f"Deleted {count}{obj_type_str} object{plural}", "Cleanup")
    
    def log_vertices_removed(self, count: int, obj_name: Optional[str] = None) -> None:
        """
        Log vertex removal with proper formatting.
        
        Args:
            count: Number of vertices removed
            obj_name: Optional object name
        """
        self.stats['vertices_removed'] += count
        
        obj_str = f" from {obj_name}" if obj_name else ""
        plural = "s" if count != 1 else ""
        self.debug(f"Removed {count} vertice{plural}{obj_str}", "Optimization")
    
    def log_export_start(self, export_type: str, file_path: str) -> None:
        """
        Log export start with proper formatting.
        
        Args:
            export_type: Type of export (FBX, OpenDRIVE, etc.)
            file_path: Path to export file
        """
        self.info(f"{export_type} export starting: '{file_path}'", "Export")
    
    def log_export_complete(self, export_type: str, duration: float, file_size: Optional[int] = None) -> None:
        """
        Log export completion with proper formatting.
        
        Args:
            export_type: Type of export
            duration: Export duration in seconds
            file_size: Optional file size in bytes
        """
        self.stats['exports_completed'] += 1
        
        size_str = ""
        if file_size is not None:
            if file_size > 1024 * 1024:
                size_str = f" ({file_size / (1024 * 1024):.1f} MB)"
            elif file_size > 1024:
                size_str = f" ({file_size / 1024:.1f} KB)"
            else:
                size_str = f" ({file_size} bytes)"
        
        self.success(f"{export_type} export completed in {duration:.3f}s{size_str}", "Export")
    
    def log_warning_duplicate_links(self, link_type: str, count: int = 1) -> None:
        """
        Log warnings about duplicate links in a cleaner format.
        
        Args:
            link_type: Type of link (road, junction, etc.)
            count: Number of duplicate links
        """
        plural = "s" if count != 1 else ""
        self.warning(f"Found {count} duplicate {link_type} link{plural} - using first occurrence", "Validation")
    
    def print_summary(self) -> None:
        """Print a summary of the session."""
        elapsed_time = time.time() - self.start_time
        
        print("\n" + "="*60)
        print(f"{self.colors['BOLD']}🎯 {self.name} - Session Summary{self.colors['RESET']}")
        print("="*60)
        
        # Time information
        print(f"⏱️  Total time: {elapsed_time:.2f}s")
        print(f"📅 Session started: {datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S')}")
        
        # Statistics
        print(f"\n📊 Statistics:")
        print(f"   • Objects created: {self.stats['objects_created']}")
        print(f"     - Roads: {self.stats['roads_created']}")
        print(f"     - Entities: {self.stats['entities_created']}")
        print(f"   • Objects deleted: {self.stats['objects_deleted']}")
        print(f"   • Vertices optimized: {self.stats['vertices_removed']}")
        print(f"   • Exports completed: {self.stats['exports_completed']}")
        
        # Issues
        if self.stats['warnings'] > 0 or self.stats['errors'] > 0:
            print(f"\n⚠️  Issues:")
            if self.stats['warnings'] > 0:
                print(f"   • Warnings: {self.stats['warnings']}")
            if self.stats['errors'] > 0:
                print(f"   • Errors: {self.stats['errors']}")
        else:
            print(f"\n✅ No issues detected")
        
        print("="*60 + "\n")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics.
        
        Returns:
            Dictionary with current statistics
        """
        return {
            **self.stats,
            'session_duration': time.time() - self.start_time,
            'total_log_entries': len(self.log_entries)
        }


# Global logger instance
_logger: Optional[DSCLogger] = None


def get_logger() -> DSCLogger:
    """
    Get the global logger instance.
    
    Returns:
        The global DSC logger
    """
    global _logger
    if _logger is None:
        _logger = DSCLogger()
    return _logger


def reset_logger() -> None:
    """Reset the global logger (useful for testing)."""
    global _logger
    _logger = None


# Convenience functions for direct logging
def debug(message: str, category: Optional[str] = None, **kwargs) -> None:
    """Log a debug message."""
    get_logger().debug(message, category, **kwargs)


def info(message: str, category: Optional[str] = None, **kwargs) -> None:
    """Log an info message."""
    get_logger().info(message, category, **kwargs)


def warning(message: str, category: Optional[str] = None, **kwargs) -> None:
    """Log a warning message."""
    get_logger().warning(message, category, **kwargs)


def error(message: str, category: Optional[str] = None, **kwargs) -> None:
    """Log an error message."""
    get_logger().error(message, category, **kwargs)


def success(message: str, category: Optional[str] = None, **kwargs) -> None:
    """Log a success message."""
    get_logger().success(message, category, **kwargs)


def start_operation(operation_name: str, category: Optional[str] = None) -> None:
    """Start a new operation."""
    get_logger().start_operation(operation_name, category)


def end_operation(operation_name: Optional[str] = None, success: bool = True, 
                 duration: Optional[float] = None, **stats) -> None:
    """End the current operation."""
    get_logger().end_operation(operation_name, success, duration, **stats)


def log_object_creation(obj_type: str, obj_name: str, obj_id: Optional[int] = None) -> None:
    """Log object creation."""
    get_logger().log_object_creation(obj_type, obj_name, obj_id)


def log_object_deletion(count: int, obj_type: Optional[str] = None) -> None:
    """Log object deletion."""
    get_logger().log_object_deletion(count, obj_type)


def log_vertices_removed(count: int, obj_name: Optional[str] = None) -> None:
    """Log vertex removal."""
    get_logger().log_vertices_removed(count, obj_name)


def log_export_start(export_type: str, file_path: str) -> None:
    """Log export start."""
    get_logger().log_export_start(export_type, file_path)


def log_export_complete(export_type: str, duration: float, file_size: Optional[int] = None) -> None:
    """Log export completion."""
    get_logger().log_export_complete(export_type, duration, file_size)


def print_summary() -> None:
    """Print session summary."""
    get_logger().print_summary()


def get_statistics() -> Dict[str, Any]:
    """Get current statistics."""
    return get_logger().get_statistics() 