"""
Mesh Exporter

This module handles the export of 3D mesh files (FBX, glTF, OSGB, etc.) from Blender scenes.
"""

import bpy
import pathlib
import subprocess
import time
import os
from typing import Dict, Any, List, Optional, Union
from mathutils import Vector

from ..core.constants import MESH_EXPORT_FORMATS
from ..core.exceptions import ExportError
from ..utils.validation_utils import validate_not_none, validate_in_range
from ..utils.file_utils import ensure_directory_exists
from ..utils.logging_utils import (
    log_export_start, log_export_complete, info, warning, error, debug,
    start_operation, end_operation
)


class MeshExporter:
    """
    Handles export of 3D mesh files from Blender scenes.
    """
    
    def __init__(self, context: Optional[bpy.types.Context] = None):
        """Initialize the mesh exporter."""
        self.context = context
        self.supported_formats = ['fbx', 'glb', 'gltf', 'osgb', 'obj', 'dae']
        
    def export(self, filepath: str, format_type: str = 'fbx', 
               objects: Optional[List[bpy.types.Object]] = None,
               context: Optional[bpy.types.Context] = None) -> Dict[str, Any]:
        """
        Export mesh to the specified format.
        
        Args:
            filepath: Path where to save the mesh file
            format_type: Export format ('fbx', 'glb', 'gltf', 'osgb', 'obj', 'dae')
            objects: List of objects to export (None for all selected)
            context: Blender context (optional)
            
        Returns:
            Dictionary with export statistics
            
        Raises:
            ExportError: If export fails
        """
        try:
            validate_not_none(filepath, "filepath")
            
            if format_type not in self.supported_formats:
                raise ExportError(f"Unsupported format: {format_type}")
            
            # Log export start
            log_export_start(format_type.upper(), filepath)
            export_start_time = time.time()
            
            # Ensure directory exists
            file_path = pathlib.Path(filepath)
            ensure_directory_exists(str(file_path.parent))
            
            # Select objects if specified
            if objects:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in objects:
                    obj.select_set(True)
                    debug(f"Selected object: {obj.name}", "Export")
            
            # Export based on format
            exported_objects = len(bpy.context.selected_objects)
            info(f"Exporting {exported_objects} objects to {format_type.upper()}", "Export")
            
            if format_type == 'fbx':
                self._export_fbx(filepath)
            elif format_type in ['glb', 'gltf']:
                self._export_gltf(filepath, format_type)
            elif format_type == 'osgb':
                self._export_osgb(filepath)
            elif format_type == 'obj':
                self._export_obj(filepath)
            elif format_type == 'dae':
                self._export_dae(filepath)
            
            # Calculate file size and log completion
            export_duration = time.time() - export_start_time
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else None
            log_export_complete(format_type.upper(), export_duration, file_size)
            
            return {
                'objects_exported': exported_objects,
                'format': format_type,
                'filepath': filepath,
                'file_size_bytes': file_size,
                'duration_seconds': export_duration
            }
            
        except Exception as e:
            error(f"Failed to export mesh: {str(e)}", "Export")
            raise ExportError(f"Failed to export mesh: {str(e)}") from e
    
    def _export_fbx(self, filepath: str) -> None:
        """Export to FBX format."""
        debug("Starting FBX export operation", "Export")
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=True,
            use_mesh_modifiers=True,
            use_armature_deform_only=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_NONE',
            use_space_transform=True,
            bake_space_transform=False,
            object_types={'ARMATURE', 'CAMERA', 'EMPTY', 'LIGHT', 'MESH', 'OTHER'},
            use_mesh_modifiers_render=True,
            mesh_smooth_type='OFF',
            use_subsurf=False,
            use_mesh_edges=False,
            use_tspace=False,
            use_custom_props=False,
            add_leaf_bones=True,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
            armature_nodetype='NULL',
            bake_anim=True,
            bake_anim_use_all_bones=True,
            bake_anim_use_nla_strips=True,
            bake_anim_use_all_actions=True,
            bake_anim_force_startend_keying=True,
            bake_anim_step=1.0,
            bake_anim_simplify_factor=1.0,
            path_mode='AUTO',
            embed_textures=False,
            batch_mode='OFF',
            use_batch_own_dir=True,
            use_metadata=True,
            axis_forward='-Z',
            axis_up='Y'
        )
    
    def _export_gltf(self, filepath: str, format_type: str) -> None:
        """Export to glTF format."""
        debug(f"Starting {format_type.upper()} export operation", "Export")
        export_format = 'GLB' if format_type == 'glb' else 'GLTF_SEPARATE'
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format=export_format,
            use_selection=True,
            export_copyright='Blender Driving Scenario Creator',
            export_image_format='AUTO',
            export_texture_dir='',
            export_keep_originals=False,
            export_texcoords=True,
            export_normals=True,
            export_draco_mesh_compression_enable=False,
            export_tangents=False,
            export_materials='EXPORT',
            export_original_specular=False,
            export_colors=True,
            use_mesh_edges=False,
            use_mesh_vertices=False,
            export_cameras=False,
            use_visible=False,
            use_renderable=False,
            use_active_collection=False,
            use_active_scene=False,
            export_extras=False,
            export_yup=True,
            export_apply=False,
            export_animations=True,
            export_frame_range=True,
            export_frame_step=1,
            export_force_sampling=True,
            export_nla_strips=True,
            export_nla_strips_merged_animation_name='Animation',
            export_def_bones=False,
            export_optimize_animation_size=False,
            export_anim_single_armature=True,
            export_current_frame=False,
            export_skins=True,
            export_all_influences=False,
            export_morph=True,
            export_morph_normal=True,
            export_morph_tangent=False,
            export_lights=False,
            will_save_settings=False
        )
    
    def _export_obj(self, filepath: str) -> None:
        """Export to OBJ format."""
        debug("Starting OBJ export operation", "Export")
        bpy.ops.wm.obj_export(
            filepath=filepath,
            check_existing=True,
            filter_blender=False,
            filter_backup=False,
            filter_image=False,
            filter_movie=False,
            filter_python=False,
            filter_font=False,
            filter_sound=False,
            filter_text=False,
            filter_archive=False,
            filter_btx=False,
            filter_collada=False,
            filter_alembic=False,
            filter_usd=False,
            filter_obj=False,
            filter_volume=False,
            filter_folder=True,
            filter_blenlib=False,
            filemode=8,
            display_type='DEFAULT',
            sort_method='DEFAULT',
            export_animation=False,
            start_frame=-2147483648,
            end_frame=2147483647,
            forward_axis='NEGATIVE_Z',
            up_axis='Y',
            global_scale=1.0,
            apply_modifiers=True,
            export_eval_mode='DAG_EVAL_VIEWPORT',
            export_selected_objects=True,
            export_uv=True,
            export_normals=True,
            export_colors=False,
            export_materials=True,
            export_pbr_extensions=False,
            path_mode='AUTO',
            export_triangulated_mesh=True,
            export_curves_as_nurbs=False,
            export_object_groups=False,
            export_material_groups=False,
            export_vertex_groups=False,
            export_smooth_groups=False,
            smooth_group_bitflags=False
        )
    
    def _export_dae(self, filepath: str) -> None:
        """Export to DAE (Collada) format."""
        debug("Starting DAE export operation", "Export")
        try:
            bpy.ops.wm.collada_export(
                filepath=filepath,
                apply_modifiers=True,
                selected=True,
                include_children=False,
                include_armatures=False,
                include_animations=False,
                triangulate=True
            )
        except TypeError as e:
            # If parameters are not recognized, try with minimal parameters
            warning(f"DAE export with full parameters failed: {e}", "Export")
            info("Trying DAE export with minimal parameters", "Export")
            bpy.ops.wm.collada_export(
                filepath=filepath,
                selected=True
            )
    
    def _export_osgb(self, filepath: str) -> None:
        """
        Export to OSGB format via OBJ intermediate format.
        Note: This requires external tools for conversion.
        """
        debug("Starting OSGB export operation", "Export")
        # Use OBJ format (well supported by OpenSceneGraph)
        temp_filepath = str(pathlib.Path(filepath).with_suffix('.obj'))
        info("Creating intermediate OBJ file for OSGB conversion", "Export")
        self._export_obj(temp_filepath)
        
        # Convert to OSGB using external tool
        info("Converting OBJ to OSGB format", "Export")
        self._convert_to_osgb(temp_filepath, filepath)
        
        # Clean up temporary file
        try:
            os.remove(temp_filepath)
            debug(f"Cleaned up temporary file: {temp_filepath}", "Export")
        except OSError:
            warning(f"Could not remove temporary file: {temp_filepath}", "Export")
    
    def _convert_to_osgb(self, input_filepath: str, output_filepath: str) -> None:
        """
        Convert file to OSGB format using external tools.
        
        Args:
            input_filepath: Path to input file
            output_filepath: Path to output OSGB file
        """
        try:
            # Try to use osgconv if available
            debug(f"Running osgconv: {input_filepath} -> {output_filepath}", "Export")
            result = subprocess.run([
                'osgconv', input_filepath, output_filepath
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                error(f"OSGB conversion failed: {result.stderr}", "Export")
                raise ExportError(f"OSGB conversion failed: {result.stderr}")
            else:
                info("OSGB conversion completed successfully", "Export")
                
        except FileNotFoundError:
            error("osgconv tool not found - install OpenSceneGraph tools", "Export")
            raise ExportError("osgconv tool not found. Please install OpenSceneGraph tools.")
        except subprocess.TimeoutExpired:
            error("OSGB conversion timed out", "Export")
            raise ExportError("OSGB conversion timed out")
    
    def export_static_scene(self, directory: str, filename: str = 'static_scene',
                           format_type: str = 'fbx') -> Dict[str, Any]:
        """
        Export the static scene (excluding entities).
        
        Args:
            directory: Export directory
            filename: Base filename
            format_type: Export format
            
        Returns:
            Dictionary with export statistics
        """
        start_operation("Static Scene Export", "Export")
        
        file_path = pathlib.Path(directory) / f'{filename}.{format_type}'
        info(f"Exporting static scene to: {file_path}", "Export")
        
        # Select all objects except entities
        bpy.ops.object.select_all(action='SELECT')
        selected_count = len(bpy.context.selected_objects)
        
        # Deselect entity objects if they exist
        deselected_count = 0
        if bpy.data.collections.get('OpenSCENARIO'):
            for obj in bpy.data.collections['OpenSCENARIO'].objects:
                if obj.select_get():
                    obj.select_set(False)
                    deselected_count += 1
            for child in bpy.data.collections['OpenSCENARIO'].children:
                for obj in child.objects:
                    if obj.select_get():
                        obj.select_set(False)
                        deselected_count += 1
        
        final_count = len(bpy.context.selected_objects)
        debug(f"Selected {selected_count} objects, deselected {deselected_count} entities, exporting {final_count} objects", "Export")
        
        result = self.export(str(file_path), format_type)
        end_operation(success=True, objects_exported=result['objects_exported'])
        return result
    
    def export_entity_models(self, directory: str, format_type: str = 'fbx') -> Dict[str, Any]:
        """
        Export individual entity models.
        
        Args:
            directory: Export directory  
            format_type: Export format
            
        Returns:
            Dictionary with export statistics
        """
        start_operation("Entity Models Export", "Export")
        
        stats = {'entities_exported': 0, 'models': []}
        
        # Check if OpenSCENARIO collection exists
        openscenario_collection = bpy.data.collections.get('OpenSCENARIO')
        if not openscenario_collection:
            warning("No OpenSCENARIO collection found - skipping entity export", "Export")
            end_operation(success=True, entities_exported=0)
            return stats
        
        # Check if entities child collection exists
        entities_collection = None
        for child in openscenario_collection.children:
            if child.name == 'entities':
                entities_collection = child
                break
        
        if not entities_collection:
            warning("No entities collection found - skipping entity export", "Export")
            end_operation(success=True, entities_exported=0)
            return stats
        total_entities = len(entities_collection.objects)
        info(f"Found {total_entities} entities to export", "Export")
        
        for i, obj in enumerate(entities_collection.objects, 1):
            info(f"Exporting entity {i}/{total_entities}: {obj.name}", "Export")
            model_path = pathlib.Path(directory) / f'{obj.name}.{format_type}'
            
            # Create temporary copy without transform
            obj_export = obj.copy()
            bpy.context.collection.objects.link(obj_export)
            
            # Clear transforms
            bpy.ops.object.select_all(action='DESELECT')
            obj_export.select_set(True)
            bpy.ops.object.location_clear()
            bpy.ops.object.rotation_clear()
            
            # Export
            result = self.export(str(model_path), format_type, [obj_export])
            
            # Clean up
            bpy.data.objects.remove(obj_export)
            
            stats['entities_exported'] += 1
            stats['models'].append({
                'name': obj.name,
                'path': str(model_path),
                'type': obj.get('entity_type', 'unknown')
            })
        
        return stats 