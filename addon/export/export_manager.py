"""
Export manager for coordinating all export operations.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import bpy
from bpy.types import Context, Operator

from ..core.constants import *
from ..core.exceptions import ExportError, ValidationError
from ..core.config import get_config
from ..utils.file_utils import ensure_directory, sanitize_filename
from ..utils.validation_utils import validate_filename, validate_export_format
from ..utils.logging_utils import (
    start_operation, end_operation, info, warning, error, 
    log_export_start, log_export_complete, get_statistics
)
from .opendrive_exporter import OpenDriveExporter
from .openscenario_exporter import OpenScenarioExporter
from .mesh_exporter import MeshExporter


class ExportManager:
    """
    Manages all export operations for the Driving Scenario Creator.
    """
    
    def __init__(self, context: Context):
        self.context = context
        self.config = get_config()
        
        # Initialize exporters
        self.opendrive_exporter = OpenDriveExporter(context)
        self.openscenario_exporter = OpenScenarioExporter(context)
        self.mesh_exporter = MeshExporter(context)
        
        # Export statistics
        self.export_stats = {
            'roads_exported': 0,
            'junctions_exported': 0,
            'entities_exported': 0,
            'files_created': 0,
            'total_size_bytes': 0
        }
    
    def export_all(self, export_path: Union[str, Path], export_options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export all scenario data to the specified path.
        
        Args:
            export_path: Directory to export to
            export_options: Export configuration options
            
        Returns:
            Export results dictionary
            
        Raises:
            ExportError: If export operation fails
        """
        try:
            start_operation("Complete Export", "Export")
            export_start_time = time.time()
            
            export_path = Path(export_path)
            self._validate_export_path(export_path)
            
            # Reset statistics
            self._reset_stats()
            
            # Create export directory structure
            self._create_export_directories(export_path)
            
            results = {
                'success': True,
                'export_path': str(export_path),
                'files_created': [],
                'errors': [],
                'warnings': []
            }
            
            # Export OpenDRIVE
            if export_options.get('export_opendrive', True):
                try:
                    opendrive_result = self._export_opendrive(export_path, export_options)
                    results['files_created'].extend(opendrive_result.get('files_created', []))
                    results['warnings'].extend(opendrive_result.get('warnings', []))
                except Exception as e:
                    error_msg = f"OpenDRIVE export failed: {str(e)}"
                    error(error_msg, "Export")
                    results['errors'].append(error_msg)
            
            # Export OpenSCENARIO
            if export_options.get('export_openscenario', True):
                try:
                    openscenario_result = self._export_openscenario(export_path, export_options)
                    results['files_created'].extend(openscenario_result.get('files_created', []))
                    results['warnings'].extend(openscenario_result.get('warnings', []))
                except Exception as e:
                    error_msg = f"OpenSCENARIO export failed: {str(e)}"
                    error(error_msg, "Export")
                    results['errors'].append(error_msg)
            
            # Export meshes
            if export_options.get('export_meshes', True):
                try:
                    mesh_result = self._export_meshes(export_path, export_options)
                    results['files_created'].extend(mesh_result.get('files_created', []))
                    results['warnings'].extend(mesh_result.get('warnings', []))
                except Exception as e:
                    error_msg = f"Mesh export failed: {str(e)}"
                    error(error_msg, "Export")
                    results['errors'].append(error_msg)
            
            # Update success status
            results['success'] = len(results['errors']) == 0
            results['statistics'] = self.export_stats.copy()
            
            # Log completion
            export_duration = time.time() - export_start_time
            files_created = len(results['files_created'])
            end_operation(success=results['success'], duration=export_duration, 
                         files_created=files_created)
            
            return results
            
        except Exception as e:
            end_operation(success=False)
            raise ExportError(f"Export operation failed: {str(e)}")
    
    def export_opendrive_only(self, export_path: Union[str, Path], 
                             filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Export only OpenDRIVE data.
        
        Args:
            export_path: Directory to export to
            filename: Optional custom filename
            
        Returns:
            Export results dictionary
        """
        try:
            start_operation("OpenDRIVE Export", "Export")
            
            export_path = Path(export_path)
            self._validate_export_path(export_path)
            
            options = {
                'filename': filename or self.config.export.default_filename,
                'format': 'xodr'
            }
            
            result = self._export_opendrive(export_path, options)
            end_operation(success=True)
            return result
            
        except Exception as e:
            end_operation(success=False)
            raise ExportError(f"OpenDRIVE export failed: {str(e)}")
    
    def export_openscenario_only(self, export_path: Union[str, Path], 
                                filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Export only OpenSCENARIO data.
        
        Args:
            export_path: Directory to export to
            filename: Optional custom filename
            
        Returns:
            Export results dictionary
        """
        try:
            start_operation("OpenSCENARIO Export", "Export")
            
            export_path = Path(export_path)
            self._validate_export_path(export_path)
            
            options = {
                'filename': filename or self.config.export.default_filename,
                'format': 'xosc'
            }
            
            result = self._export_openscenario(export_path, options)
            end_operation(success=True)
            return result
            
        except Exception as e:
            end_operation(success=False)
            raise ExportError(f"OpenSCENARIO export failed: {str(e)}")
    
    def export_meshes_only(self, export_path: Union[str, Path], 
                          mesh_format: str = 'osgb') -> Dict[str, Any]:
        """
        Export only mesh data.
        
        Args:
            export_path: Directory to export to
            mesh_format: Mesh format to export
            
        Returns:
            Export results dictionary
        """
        try:
            start_operation("Mesh Export", "Export")
            
            export_path = Path(export_path)
            self._validate_export_path(export_path)
            validate_export_format(mesh_format)
            
            options = {
                'format': mesh_format,
                'separate_objects': True
            }
            
            result = self._export_meshes(export_path, options)
            end_operation(success=True)
            return result
            
        except Exception as e:
            end_operation(success=False)
            raise ExportError(f"Mesh export failed: {str(e)}")
    
    def get_export_preview(self) -> Dict[str, Any]:
        """
        Get a preview of what would be exported.
        
        Returns:
            Preview information dictionary
        """
        try:
            preview = {
                'roads': [],
                'junctions': [],
                'entities': [],
                'objects': [],
                'estimated_files': 0,
                'estimated_size_mb': 0
            }
            
            # Get OpenDRIVE objects
            collection = bpy.data.collections.get(COLLECTION_OPENDRIVE)
            if collection:
                for obj in collection.objects:
                    obj_type = obj.get('object_type')
                    if obj_type:
                        if 'road' in obj_type:
                            preview['roads'].append({
                                'name': obj.name,
                                'type': obj_type,
                                'id': obj.get('id_odr', 0)
                            })
                        elif 'junction' in obj_type:
                            preview['junctions'].append({
                                'name': obj.name,
                                'type': obj_type,
                                'id': obj.get('id_odr', 0)
                            })
                        else:
                            preview['objects'].append({
                                'name': obj.name,
                                'type': obj_type,
                                'id': obj.get('id_odr', 0)
                            })
            
            # Get OpenSCENARIO entities
            collection = bpy.data.collections.get(COLLECTION_OPENSCENARIO)
            if collection:
                for obj in collection.objects:
                    obj_type = obj.get('object_type')
                    if obj_type and 'entity' in obj_type:
                        preview['entities'].append({
                            'name': obj.name,
                            'type': obj_type,
                            'category': obj.get('entity_category', 'unknown')
                        })
            
            # Estimate output
            preview['estimated_files'] = 2  # Basic xodr + xosc
            if len(preview['roads']) > 0:
                preview['estimated_files'] += 1  # Static scene mesh
            if len(preview['entities']) > 0:
                preview['estimated_files'] += len(preview['entities'])  # Entity meshes
            
            preview['estimated_size_mb'] = max(1, len(preview['roads']) + len(preview['entities']))
            
            return preview
            
        except Exception as e:
            raise ExportError(f"Failed to generate export preview: {str(e)}")
    
    def _validate_export_path(self, export_path: Path) -> None:
        """Validate the export path."""
        if not export_path.parent.exists():
            raise ValidationError(f"Parent directory does not exist: {export_path.parent}")
        
        if export_path.exists() and not export_path.is_dir():
            raise ValidationError(f"Export path exists but is not a directory: {export_path}")
    
    def _create_export_directories(self, export_path: Path) -> None:
        """Create the export directory structure."""
        try:
            ensure_directory(export_path)
            
            # Create subdirectories
            for subdir in self.config.export.subdirectories.values():
                ensure_directory(export_path / subdir)
                
        except Exception as e:
            raise ExportError(f"Failed to create export directories: {str(e)}")
    
    def _export_opendrive(self, export_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export OpenDRIVE data."""
        filename = sanitize_filename(options.get('filename', self.config.export.default_filename))
        if not filename.endswith('.xodr'):
            filename += '.xodr'
        
        output_path = export_path / filename
        
        result = self.opendrive_exporter.export(str(output_path), self.context)
        
        if result.get('success', False):
            self.export_stats['roads_exported'] += result.get('roads_exported', 0)
            self.export_stats['junctions_exported'] += result.get('junctions_exported', 0)
            self.export_stats['files_created'] += 1
            
            if output_path.exists():
                self.export_stats['total_size_bytes'] += output_path.stat().st_size
        
        return result
    
    def _export_openscenario(self, export_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export OpenSCENARIO data."""
        filename = sanitize_filename(options.get('filename', self.config.export.default_filename))
        if not filename.endswith('.xosc'):
            filename += '.xosc'
        
        # Export to xosc subdirectory
        xosc_dir = export_path / self.config.export.subdirectories['xosc']
        output_path = xosc_dir / filename
        
        result = self.openscenario_exporter.export(str(output_path), self.context)
        
        if result.get('success', False):
            self.export_stats['entities_exported'] += result.get('entities_exported', 0)
            self.export_stats['files_created'] += 1
            
            if output_path.exists():
                self.export_stats['total_size_bytes'] += output_path.stat().st_size
        
        return result
    
    def _export_meshes(self, export_path: Path, options: Dict[str, Any]) -> Dict[str, Any]:
        """Export mesh data."""
        mesh_format = options.get('mesh_format', options.get('format', self.config.export.default_format))
        
        # Export static scene
        static_scene_dir = export_path / self.config.export.subdirectories['static_scene']
        
        # Export entities
        entities_dir = export_path / self.config.export.subdirectories['entities']
        
        # Export static scene and entities separately
        results = {'success': True, 'files_created': [], 'errors': []}
        
        try:
            # Export static scene
            static_result = self.mesh_exporter.export_static_scene(str(static_scene_dir), 'static_scene', mesh_format)
            results['files_created'].append(static_result['filepath'])
        except Exception as e:
            results['errors'].append(f"Static scene export failed: {str(e)}")
        
        try:
            # Export entity models
            entity_result = self.mesh_exporter.export_entity_models(str(entities_dir), mesh_format)
            results['files_created'].extend([m['path'] for m in entity_result.get('models', [])])
        except Exception as e:
            results['errors'].append(f"Entity export failed: {str(e)}")
        
        # Set success based on whether we have any files or errors
        results['success'] = len(results['files_created']) > 0 or len(results['errors']) == 0
        result = results
        
        if result.get('success', False):
            files_created = result.get('files_created', [])
            self.export_stats['files_created'] += len(files_created)
            
            # Calculate total size
            for file_path in files_created:
                if Path(file_path).exists():
                    self.export_stats['total_size_bytes'] += Path(file_path).stat().st_size
        
        return result
    
    def _reset_stats(self) -> None:
        """Reset export statistics."""
        self.export_stats = {
            'roads_exported': 0,
            'junctions_exported': 0,
            'entities_exported': 0,
            'files_created': 0,
            'total_size_bytes': 0
        } 