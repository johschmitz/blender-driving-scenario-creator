"""
Geometry utility functions for the Driving Scenario Creator add-on.
"""

import math
from typing import List, Tuple, Optional, Union
from mathutils import Vector, Matrix
from .math_utils import *
from ..core.exceptions import GeometryError
import bpy
import bmesh


def create_line_mesh_vertices(start: Vector, end: Vector, width: float = 1.0) -> List[Vector]:
    """
    Create vertices for a line mesh with specified width.
    
    Args:
        start: Start point of the line
        end: End point of the line
        width: Width of the line
        
    Returns:
        List of vertices for the line mesh
        
    Raises:
        GeometryError: If line creation fails
    """
    try:
        if point_distance_3d(start, end) < 1e-6:
            raise GeometryError("Line start and end points are too close")
        
        # Calculate direction and perpendicular vectors
        direction = (end - start).normalized()
        up = Vector((0, 0, 1))
        
        # Handle vertical lines
        if abs(direction.dot(up)) > 0.99:
            perpendicular = Vector((1, 0, 0))
        else:
            perpendicular = direction.cross(up).normalized()
        
        half_width = width / 2.0
        offset = perpendicular * half_width
        
        # Create vertices
        vertices = [
            start - offset,  # Bottom left
            start + offset,  # Bottom right
            end + offset,    # Top right
            end - offset     # Top left
        ]
        
        return vertices
    except Exception as e:
        raise GeometryError(f"Failed to create line mesh vertices: {str(e)}")


def create_arc_mesh_vertices(center: Vector, radius: float, start_angle: float, 
                           end_angle: float, width: float = 1.0, 
                           segments: int = 32) -> List[Vector]:
    """
    Create vertices for an arc mesh.
    
    Args:
        center: Center point of the arc
        radius: Radius of the arc
        start_angle: Start angle in radians
        end_angle: End angle in radians
        width: Width of the arc
        segments: Number of segments
        
    Returns:
        List of vertices for the arc mesh
        
    Raises:
        GeometryError: If arc creation fails
    """
    try:
        if radius <= 0:
            raise GeometryError("Arc radius must be positive")
        
        if segments < 3:
            raise GeometryError("Arc must have at least 3 segments")
        
        # Normalize angles
        start_angle = normalize_angle(start_angle)
        end_angle = normalize_angle(end_angle)
        
        # Calculate angle span
        angle_span = end_angle - start_angle
        if angle_span <= 0:
            angle_span += 2 * math.pi
        
        # Create vertices
        vertices = []
        inner_radius = radius - width / 2.0
        outer_radius = radius + width / 2.0
        
        for i in range(segments + 1):
            t = i / segments
            angle = start_angle + t * angle_span
            
            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)
            
            # Inner vertex
            inner_point = center + Vector((
                inner_radius * cos_angle,
                inner_radius * sin_angle,
                0
            ))
            vertices.append(inner_point)
            
            # Outer vertex
            outer_point = center + Vector((
                outer_radius * cos_angle,
                outer_radius * sin_angle,
                0
            ))
            vertices.append(outer_point)
        
        return vertices
    except Exception as e:
        raise GeometryError(f"Failed to create arc mesh vertices: {str(e)}")


def create_bezier_curve_points(p0: Vector, p1: Vector, p2: Vector, p3: Vector, 
                              num_points: int = 10) -> List[Vector]:
    """
    Create points along a cubic Bezier curve.
    
    Args:
        p0: Start point
        p1: First control point
        p2: Second control point
        p3: End point
        num_points: Number of points to generate
        
    Returns:
        List of points along the curve
        
    Raises:
        GeometryError: If curve creation fails
    """
    try:
        if num_points < 2:
            raise GeometryError("Bezier curve must have at least 2 points")
        
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            
            # Cubic Bezier formula
            point = (
                (1 - t) ** 3 * p0 +
                3 * (1 - t) ** 2 * t * p1 +
                3 * (1 - t) * t ** 2 * p2 +
                t ** 3 * p3
            )
            points.append(point)
        
        return points
    except Exception as e:
        raise GeometryError(f"Failed to create Bezier curve points: {str(e)}")


def create_clothoid_points(start: Vector, start_heading: float, start_curvature: float,
                          end_curvature: float, length: float, 
                          num_points: int = 50) -> List[Vector]:
    """
    Create points along a clothoid curve.
    
    Args:
        start: Start point
        start_heading: Start heading in radians
        start_curvature: Start curvature
        end_curvature: End curvature
        length: Length of the clothoid
        num_points: Number of points to generate
        
    Returns:
        List of points along the clothoid
        
    Raises:
        GeometryError: If clothoid creation fails
    """
    try:
        if num_points < 2:
            raise GeometryError("Clothoid must have at least 2 points")
        
        if length <= 0:
            raise GeometryError("Clothoid length must be positive")
        
        points = []
        curvature_change = end_curvature - start_curvature
        
        current_pos = start.copy()
        current_heading = start_heading
        
        for i in range(num_points):
            points.append(current_pos.copy())
            
            if i < num_points - 1:
                # Calculate step
                step = length / (num_points - 1)
                s = i * step
                
                # Calculate curvature at this point
                curvature = start_curvature + curvature_change * s / length
                
                # Update heading
                current_heading += curvature * step
                
                # Update position
                current_pos += Vector((
                    math.cos(current_heading) * step,
                    math.sin(current_heading) * step,
                    0
                ))
        
        return points
    except Exception as e:
        raise GeometryError(f"Failed to create clothoid points: {str(e)}")


def create_road_cross_section(center_line: List[Vector], lane_widths_left: List[float],
                            lane_widths_right: List[float]) -> Tuple[List[Vector], List[List[int]]]:
    """
    Create a road cross-section mesh from a center line and lane widths.
    
    Args:
        center_line: Points along the center line
        lane_widths_left: Lane widths on the left side
        lane_widths_right: Lane widths on the right side
        
    Returns:
        Tuple of (vertices, faces)
        
    Raises:
        GeometryError: If cross-section creation fails
    """
    try:
        if len(center_line) < 2:
            raise GeometryError("Center line must have at least 2 points")
        
        vertices = []
        faces = []
        
        # Calculate total width
        total_width_left = sum(lane_widths_left)
        total_width_right = sum(lane_widths_right)
        
        for i, center_point in enumerate(center_line):
            # Calculate tangent direction
            if i == 0:
                tangent = (center_line[1] - center_line[0]).normalized()
            elif i == len(center_line) - 1:
                tangent = (center_line[i] - center_line[i-1]).normalized()
            else:
                tangent = (center_line[i+1] - center_line[i-1]).normalized()
            
            # Calculate perpendicular vector
            perpendicular = Vector((-tangent.y, tangent.x, 0))
            
            # Create vertices for this cross-section
            section_vertices = []
            
            # Left side
            current_offset = total_width_left
            for width in reversed(lane_widths_left):
                vertex = center_point + perpendicular * current_offset
                section_vertices.append(vertex)
                current_offset -= width
            
            # Center
            section_vertices.append(center_point)
            
            # Right side
            current_offset = 0
            for width in lane_widths_right:
                current_offset += width
                vertex = center_point - perpendicular * current_offset
                section_vertices.append(vertex)
            
            vertices.extend(section_vertices)
            
            # Create faces (except for the last section)
            if i < len(center_line) - 1:
                verts_per_section = len(section_vertices)
                base_idx = i * verts_per_section
                next_base_idx = (i + 1) * verts_per_section
                
                for j in range(verts_per_section - 1):
                    # Create quad face
                    face = [
                        base_idx + j,
                        base_idx + j + 1,
                        next_base_idx + j + 1,
                        next_base_idx + j
                    ]
                    faces.append(face)
        
        return vertices, faces
    except Exception as e:
        raise GeometryError(f"Failed to create road cross-section: {str(e)}")


def calculate_curve_length(points: List[Vector]) -> float:
    """
    Calculate the total length of a curve defined by points.
    
    Args:
        points: Points along the curve
        
    Returns:
        Total curve length
    """
    if len(points) < 2:
        return 0.0
    
    total_length = 0.0
    for i in range(1, len(points)):
        total_length += point_distance_3d(points[i-1], points[i])
    
    return total_length


def simplify_curve(points: List[Vector], tolerance: float = 0.1) -> List[Vector]:
    """
    Simplify a curve by removing redundant points using Douglas-Peucker algorithm.
    
    Args:
        points: Points to simplify
        tolerance: Simplification tolerance
        
    Returns:
        Simplified points
    """
    if len(points) <= 2:
        return points
    
    def distance_point_to_line(point: Vector, line_start: Vector, line_end: Vector) -> float:
        """Calculate perpendicular distance from point to line."""
        try:
            return point_to_line_distance(point, line_start, line_end)
        except:
            return point_distance_3d(point, line_start)
    
    def douglas_peucker(points: List[Vector], start: int, end: int, tolerance: float) -> List[int]:
        """Recursive Douglas-Peucker algorithm."""
        if end - start <= 1:
            return [start, end]
        
        # Find point with maximum distance
        max_distance = 0.0
        max_index = start
        
        for i in range(start + 1, end):
            distance = distance_point_to_line(points[i], points[start], points[end])
            if distance > max_distance:
                max_distance = distance
                max_index = i
        
        # If max distance is greater than tolerance, recursively simplify
        if max_distance > tolerance:
            left_result = douglas_peucker(points, start, max_index, tolerance)
            right_result = douglas_peucker(points, max_index, end, tolerance)
            
            # Combine results (remove duplicate middle point)
            return left_result[:-1] + right_result
        else:
            return [start, end]
    
    # Apply Douglas-Peucker algorithm
    indices = douglas_peucker(points, 0, len(points) - 1, tolerance)
    return [points[i] for i in indices]


def offset_curve(points: List[Vector], offset: float) -> List[Vector]:
    """
    Create an offset curve parallel to the original curve.
    
    Args:
        points: Original curve points
        offset: Offset distance (positive = right, negative = left)
        
    Returns:
        Offset curve points
        
    Raises:
        GeometryError: If offset creation fails
    """
    try:
        if len(points) < 2:
            raise GeometryError("Curve must have at least 2 points")
        
        offset_points = []
        
        for i, point in enumerate(points):
            # Calculate tangent direction
            if i == 0:
                tangent = (points[1] - points[0]).normalized()
            elif i == len(points) - 1:
                tangent = (points[i] - points[i-1]).normalized()
            else:
                tangent = (points[i+1] - points[i-1]).normalized()
            
            # Calculate perpendicular vector (90 degrees to the right)
            perpendicular = Vector((-tangent.y, tangent.x, 0))
            
            # Apply offset
            offset_point = point - perpendicular * offset
            offset_points.append(offset_point)
        
        return offset_points
    except Exception as e:
        raise GeometryError(f"Failed to create offset curve: {str(e)}")


def smooth_curve(points: List[Vector], iterations: int = 1, strength: float = 0.5) -> List[Vector]:
    """
    Smooth a curve using simple averaging.
    
    Args:
        points: Points to smooth
        iterations: Number of smoothing iterations
        strength: Smoothing strength (0.0 to 1.0)
        
    Returns:
        Smoothed points
    """
    if len(points) < 3:
        return points
    
    smoothed = points.copy()
    
    for _ in range(iterations):
        for i in range(1, len(smoothed) - 1):
            # Calculate average of neighboring points
            prev_point = smoothed[i - 1]
            current_point = smoothed[i]
            next_point = smoothed[i + 1]
            
            average = (prev_point + next_point) / 2.0
            
            # Blend with original position
            smoothed[i] = current_point.lerp(average, strength)
    
    return smoothed


def calculate_curve_curvature(points: List[Vector]) -> List[float]:
    """
    Calculate curvature at each point along a curve.
    
    Args:
        points: Points along the curve
        
    Returns:
        Curvature values at each point
    """
    if len(points) < 3:
        return [0.0] * len(points)
    
    curvatures = []
    
    for i in range(len(points)):
        if i == 0 or i == len(points) - 1:
            curvatures.append(0.0)
        else:
            # Calculate curvature using three consecutive points
            p1 = points[i - 1]
            p2 = points[i]
            p3 = points[i + 1]
            
            # Calculate vectors
            v1 = p2 - p1
            v2 = p3 - p2
            
            # Calculate curvature
            if v1.length < 1e-6 or v2.length < 1e-6:
                curvatures.append(0.0)
            else:
                cross_product = v1.cross(v2).length
                dot_product = v1.dot(v2)
                
                # Curvature = |v1 × v2| / |v1|³
                curvature = cross_product / (v1.length ** 3)
                
                # Determine sign based on turn direction
                if dot_product < 0:  # Sharp turn
                    curvature = -curvature
                
                curvatures.append(curvature)
    
    return curvatures


def create_box_mesh(name: str, size: Tuple[float, float, float]) -> bpy.types.Mesh:
    """
    Create a box mesh with specified dimensions.
    
    Args:
        name: Name for the mesh
        size: Tuple of (length, width, height) dimensions
        
    Returns:
        Blender mesh object representing a box
        
    Raises:
        GeometryError: If box creation fails
    """
    try:
        length, width, height = size
        
        if length <= 0 or width <= 0 or height <= 0:
            raise GeometryError("Box dimensions must be positive")
        
        # Create new mesh
        mesh = bpy.data.meshes.new(name)
        
        # Create bmesh instance
        bm = bmesh.new()
        
        # Create box
        bmesh.ops.create_cube(bm, size=1.0)
        
        # Scale to desired dimensions
        bmesh.ops.scale(bm, 
                       vec=(length, width, height),
                       verts=bm.verts)
        
        # Update mesh
        bm.to_mesh(mesh)
        bm.free()
        
        # Update mesh
        mesh.update()
        
        return mesh
        
    except Exception as e:
        raise GeometryError(f"Failed to create box mesh: {str(e)}")


def create_cylinder_mesh(name: str, radius: float, height: float, segments: int = 32) -> bpy.types.Mesh:
    """
    Create a cylinder mesh with specified dimensions.
    
    Args:
        name: Name for the mesh
        radius: Cylinder radius
        height: Cylinder height
        segments: Number of segments around the circumference
        
    Returns:
        Blender mesh object representing a cylinder
        
    Raises:
        GeometryError: If cylinder creation fails
    """
    try:
        if radius <= 0 or height <= 0:
            raise GeometryError("Cylinder dimensions must be positive")
        
        if segments < 3:
            raise GeometryError("Cylinder must have at least 3 segments")
        
        # Create new mesh
        mesh = bpy.data.meshes.new(name)
        
        # Create bmesh instance
        bm = bmesh.new()
        
        # Create cylinder
        bmesh.ops.create_cylinder(bm, 
                                 radius=radius,
                                 depth=height,
                                 segments=segments)
        
        # Update mesh
        bm.to_mesh(mesh)
        bm.free()
        
        # Update mesh
        mesh.update()
        
        return mesh
        
    except Exception as e:
        raise GeometryError(f"Failed to create cylinder mesh: {str(e)}")


def create_plane_mesh(name: str, size: Tuple[float, float]) -> bpy.types.Mesh:
    """
    Create a plane mesh with specified dimensions.
    
    Args:
        name: Name for the mesh
        size: Tuple of (width, length) dimensions
        
    Returns:
        Blender mesh object representing a plane
        
    Raises:
        GeometryError: If plane creation fails
    """
    try:
        width, length = size
        
        if width <= 0 or length <= 0:
            raise GeometryError("Plane dimensions must be positive")
        
        # Create new mesh
        mesh = bpy.data.meshes.new(name)
        
        # Create bmesh instance
        bm = bmesh.new()
        
        # Create plane
        bmesh.ops.create_grid(bm, 
                             x_segments=1,
                             y_segments=1,
                             size=1.0)
        
        # Scale to desired dimensions
        bmesh.ops.scale(bm, 
                       vec=(width, length, 1.0),
                       verts=bm.verts)
        
        # Update mesh
        bm.to_mesh(mesh)
        bm.free()
        
        # Update mesh
        mesh.update()
        
        return mesh
        
    except Exception as e:
        raise GeometryError(f"Failed to create plane mesh: {str(e)}")


def create_sphere_mesh(name: str, radius: float, subdivisions: int = 2) -> bpy.types.Mesh:
    """
    Create a sphere mesh with specified radius.
    
    Args:
        name: Name for the mesh
        radius: Sphere radius
        subdivisions: Number of subdivisions for sphere smoothness
        
    Returns:
        Blender mesh object representing a sphere
        
    Raises:
        GeometryError: If sphere creation fails
    """
    try:
        if radius <= 0:
            raise GeometryError("Sphere radius must be positive")
        
        if subdivisions < 0:
            raise GeometryError("Sphere subdivisions must be non-negative")
        
        # Create new mesh
        mesh = bpy.data.meshes.new(name)
        
        # Create bmesh instance
        bm = bmesh.new()
        
        # Create UV sphere
        bmesh.ops.create_uvsphere(bm, 
                                 u_segments=16,
                                 v_segments=8,
                                 radius=radius)
        
        # Apply subdivisions for smoothness
        if subdivisions > 0:
            bmesh.ops.subdivide_smooth(bm,
                                      geom=bm.faces[:] + bm.edges[:],
                                      cuts=subdivisions)
        
        # Update mesh
        bm.to_mesh(mesh)
        bm.free()
        
        # Update mesh
        mesh.update()
        
        return mesh
        
    except Exception as e:
        raise GeometryError(f"Failed to create sphere mesh: {str(e)}") 