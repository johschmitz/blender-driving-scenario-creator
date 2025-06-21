"""
Export Package

This package handles all export operations for the Driving Scenario Creator.
Provides unified interface for exporting OpenDRIVE, OpenSCENARIO, and mesh files.
"""

import bpy
import pathlib
import time
from typing import Dict, Any, Optional

from .export_manager import ExportManager
from .opendrive_exporter import OpenDriveExporter
from .openscenario_exporter import OpenScenarioExporter  
from .mesh_exporter import MeshExporter
from ..core.exceptions import ExportError
from ..utils.logging_utils import (
    start_operation, end_operation, info, error, success, print_summary, 
    get_statistics, reset_logger
)

# Re-export classes for external use
__all__ = [
    'ExportManager',
    'OpenDriveExporter', 
    'OpenScenarioExporter',
    'MeshExporter',
    'DSC_OT_export'
]


class DSC_OT_export(bpy.types.Operator):
    """Export driving scenario to various formats."""
    
    bl_idname = "dsc.export"
    bl_label = "Export Driving Scenario"
    bl_description = "Export driving scenario as OpenDRIVE, OpenSCENARIO and mesh files"
    bl_options = {'REGISTER'}
    
    # Export options
    directory: bpy.props.StringProperty(
        name="Export Directory",
        description="Directory where files will be exported",
        subtype='DIR_PATH'
    )
    
    filename: bpy.props.StringProperty(
        name="Filename",
        description="Base filename for exported files (without extension)",
        default="scenario",
        maxlen=64
    )
    
    export_opendrive: bpy.props.BoolProperty(
        name="Export OpenDRIVE",
        description="Export road network as OpenDRIVE (.xodr)",
        default=True
    )
    
    export_openscenario: bpy.props.BoolProperty(
        name="Export OpenSCENARIO", 
        description="Export scenario as OpenSCENARIO (.xosc)",
        default=True
    )
    
    export_meshes: bpy.props.BoolProperty(
        name="Export Meshes",
        description="Export 3D models",
        default=True
    )
    
    mesh_format: bpy.props.EnumProperty(
        name="Mesh Format",
        description="Format for 3D mesh export",
        items=[
            ('fbx', 'FBX', 'Autodesk FBX format'),
            ('glb', 'glTF Binary', 'glTF 2.0 binary format (.glb)'),
            ('gltf', 'glTF Separate', 'glTF 2.0 with separate textures (.gltf)'),
            ('osgb', 'OpenSceneGraph Binary', 'OpenSceneGraph binary format'),
            ('obj', 'Wavefront OBJ', 'Wavefront OBJ format'),
            ('dae', 'Collada DAE', 'Collada DAE format')
        ],
        default='fbx'
    )
    
    # Internal state tracking
    _directory_selected: bpy.props.BoolProperty(default=False, options={'HIDDEN', 'SKIP_SAVE'})
    
    @classmethod
    def poll(cls, context):
        """Check if export is possible."""
        return True
    
    def invoke(self, context, event):
        """Invoke the export dialog."""
        # Reset state for fresh invocation
        self.directory = ""
        self._directory_selected = False
        
        # Reset mesh format to default to prevent caching issues
        self.mesh_format = 'fbx'
        
        # Set default filename based on current blend file or default
        if bpy.data.filepath:
            blend_name = pathlib.Path(bpy.data.filepath).stem
            self.filename = blend_name if blend_name else "scenario"
        else:
            self.filename = "scenario"
        
        # Show popup dialog first to get filename and options
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def execute(self, context):
        """Execute the export operation or show directory browser."""
        # Validate filename first
        if not self.filename.strip():
            self.report({'ERROR'}, "Filename cannot be empty")
            return {'CANCELLED'}
        
        # Always show the file browser to select directory
        # This ensures user can choose export location every time
        if not self._directory_selected:
            context.window_manager.fileselect_add(self)
            self._directory_selected = True
            return {'RUNNING_MODAL'}
        
        # Directory browser was shown and directory selected, proceed with export
        return self._perform_export(context)
    
    def _perform_export(self, context):
        """Perform the actual export operation."""
        try:
            # Reset logger for clean session
            reset_logger()
            
            # Start main export operation
            start_operation("Driving Scenario Export", "Export")
            export_start_time = time.time()
            
            # Validate inputs
            if not self.directory:
                error("No export directory specified", "Export")
                self.report({'ERROR'}, "No export directory specified")
                end_operation(success=False)
                return {'CANCELLED'}
            
            # Create export manager
            export_manager = ExportManager(context)
            
            # Prepare export options
            export_options = {
                'export_opendrive': self.export_opendrive,
                'export_openscenario': self.export_openscenario,
                'export_meshes': self.export_meshes,
                'mesh_format': self.mesh_format,
                'filename': self.filename
            }
            
            info(f"Starting export to: {self.directory}", "Export")
            info(f"Export options: OpenDRIVE={self.export_opendrive}, OpenSCENARIO={self.export_openscenario}, Meshes={self.export_meshes}", "Export")
            info(f"Mesh format selected: {self.mesh_format}", "Export")
            
            # Perform export
            results = export_manager.export_all(self.directory, export_options)
            
            # Report results
            export_duration = time.time() - export_start_time
            
            if results['success']:
                files_created = len(results['files_created'])
                success(f"Export completed successfully", "Export")
                info(f"Created {files_created} files in {export_duration:.2f}s", "Export")
                
                # Report to Blender UI
                self.report({'INFO'}, f"Export completed successfully - {files_created} files created")
                end_operation(success=True, duration=export_duration, files_created=files_created)
            else:
                error_count = len(results['errors'])
                error(f"Export completed with {error_count} errors", "Export")
                for err in results['errors']:
                    error(err, "Export")
                
                # Report to Blender UI
                self.report({'ERROR'}, f"Export failed with {error_count} errors")
                end_operation(success=False, duration=export_duration)
            
            # Print session summary
            print_summary()
            
            return {'FINISHED'}
            
        except ExportError as e:
            error(f"Export failed: {str(e)}", "Export")
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            end_operation(success=False)
            print_summary()
            return {'CANCELLED'}
        except Exception as e:
            error(f"Unexpected error during export: {str(e)}", "Export")
            self.report({'ERROR'}, f"Unexpected error: {str(e)}")
            end_operation(success=False)
            print_summary()
            return {'CANCELLED'}
    
    def draw(self, context):
        """Draw the export options dialog."""
        layout = self.layout
        
        # Filename section
        box = layout.box()
        box.label(text="Export Settings", icon='EXPORT')
        box.prop(self, "filename", icon='FILE_TEXT')
        
        # Export options section
        box = layout.box()
        box.label(text="Export Components", icon='SETTINGS')
        
        col = box.column(align=True)
        col.prop(self, "export_opendrive", icon='DRIVER_ROTATIONAL_DIFFERENCE')
        col.prop(self, "export_openscenario", icon='SEQUENCE')
        
        row = col.row(align=True)
        row.prop(self, "export_meshes", icon='MESH_DATA')
        if self.export_meshes:
            row.prop(self, "mesh_format", text="", icon='FILE_3D')
        
        # Info section
        box = layout.box()
        box.label(text="Click OK to choose export directory", icon='INFO')


def register():
    """Register the export operator."""
    bpy.utils.register_class(DSC_OT_export)


def unregister():
    """Unregister the export operator."""
    bpy.utils.unregister_class(DSC_OT_export)


# Legacy compatibility - provide access to original export functionality
def export_driving_scenario(directory: str, mesh_file_type: str = 'osgb', 
                           context: Optional[bpy.types.Context] = None) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    
    Args:
        directory: Export directory path
        mesh_file_type: Mesh export format
        context: Blender context
        
    Returns:
        Dictionary with export results
    """
    export_manager = ExportManager()
    
    export_params = {
        'directory': directory,
        'mesh_format': mesh_file_type,
        'filename': 'bdsc_export'
    }
    
    return export_manager.export_all(export_params, context) 