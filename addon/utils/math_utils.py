"""
Mathematical utility functions for the Driving Scenario Creator add-on.
"""

import math
from typing import Tuple, List, Optional, Union
from mathutils import Vector, Matrix
from ..core.exceptions import GeometryError


def normalize_angle(angle: float) -> float:
    """
    Normalize angle to [-π, π] range.
    
    Args:
        angle: Angle in radians
        
    Returns:
        Normalized angle in radians
    """
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def angle_difference(angle1: float, angle2: float) -> float:
    """
    Calculate the shortest angular difference between two angles.
    
    Args:
        angle1: First angle in radians
        angle2: Second angle in radians
        
    Returns:
        Angular difference in radians
    """
    diff = angle2 - angle1
    return normalize_angle(diff)


def degrees_to_radians(degrees: float) -> float:
    """
    Convert degrees to radians.
    
    Args:
        degrees: Angle in degrees
        
    Returns:
        Angle in radians
    """
    return degrees * math.pi / 180.0


def radians_to_degrees(radians: float) -> float:
    """
    Convert radians to degrees.
    
    Args:
        radians: Angle in radians
        
    Returns:
        Angle in degrees
    """
    return radians * 180.0 / math.pi


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between minimum and maximum bounds.
    
    Args:
        value: Value to clamp
        min_val: Minimum bound
        max_val: Maximum bound
        
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        a: Start value
        b: End value
        t: Interpolation parameter [0, 1]
        
    Returns:
        Interpolated value
    """
    return a + t * (b - a)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """
    Smooth Hermite interpolation between 0 and 1.
    
    Args:
        edge0: Lower edge
        edge1: Upper edge
        x: Input value
        
    Returns:
        Smoothed value
    """
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def point_distance_2d(p1: Vector, p2: Vector) -> float:
    """
    Calculate 2D distance between two points.
    
    Args:
        p1: First point
        p2: Second point
        
    Returns:
        Distance between points
    """
    return (p2.to_2d() - p1.to_2d()).length


def point_distance_3d(p1: Vector, p2: Vector) -> float:
    """
    Calculate 3D distance between two points.
    
    Args:
        p1: First point
        p2: Second point
        
    Returns:
        Distance between points
    """
    return (p2 - p1).length


def project_point_on_line(point: Vector, line_start: Vector, line_end: Vector) -> Vector:
    """
    Project a point onto a line segment.
    
    Args:
        point: Point to project
        line_start: Start of line segment
        line_end: End of line segment
        
    Returns:
        Projected point on line
        
    Raises:
        GeometryError: If line has zero length
    """
    try:
        line_vec = line_end - line_start
        line_length_sq = line_vec.length_squared
        
        if line_length_sq < 1e-10:
            raise GeometryError("Line segment has zero length")
        
        # Calculate projection parameter
        t = max(0.0, min(1.0, (point - line_start).dot(line_vec) / line_length_sq))
        
        # Return projected point
        return line_start + t * line_vec
    except Exception as e:
        raise GeometryError(f"Failed to project point on line: {str(e)}")


def point_to_line_distance(point: Vector, line_start: Vector, line_end: Vector) -> float:
    """
    Calculate distance from point to line segment.
    
    Args:
        point: Point
        line_start: Start of line segment
        line_end: End of line segment
        
    Returns:
        Distance from point to line
    """
    try:
        projected_point = project_point_on_line(point, line_start, line_end)
        return point_distance_3d(point, projected_point)
    except GeometryError:
        # If projection fails, return distance to nearest endpoint
        dist_start = point_distance_3d(point, line_start)
        dist_end = point_distance_3d(point, line_end)
        return min(dist_start, dist_end)


def cubic_polynomial(t: float, a: float, b: float, c: float, d: float) -> float:
    """
    Evaluate cubic polynomial: a + bt + ct² + dt³.
    
    Args:
        t: Parameter value
        a: Constant coefficient
        b: Linear coefficient
        c: Quadratic coefficient
        d: Cubic coefficient
        
    Returns:
        Polynomial value
    """
    return a + b * t + c * t * t + d * t * t * t


def cubic_polynomial_derivative(t: float, a: float, b: float, c: float, d: float) -> float:
    """
    Evaluate derivative of cubic polynomial: b + 2ct + 3dt².
    
    Args:
        t: Parameter value
        a: Constant coefficient (unused in derivative)
        b: Linear coefficient
        c: Quadratic coefficient
        d: Cubic coefficient
        
    Returns:
        Derivative value
    """
    return b + 2 * c * t + 3 * d * t * t


def cubic_polynomial_second_derivative(t: float, a: float, b: float, c: float, d: float) -> float:
    """
    Evaluate second derivative of cubic polynomial: 2c + 6dt.
    
    Args:
        t: Parameter value
        a: Constant coefficient (unused)
        b: Linear coefficient (unused)
        c: Quadratic coefficient
        d: Cubic coefficient
        
    Returns:
        Second derivative value
    """
    return 2 * c + 6 * d * t


def arc_length_from_curvature(curvature_start: float, curvature_end: float, length: float) -> float:
    """
    Calculate arc length from curvature parameters.
    
    Args:
        curvature_start: Starting curvature
        curvature_end: Ending curvature
        length: Segment length
        
    Returns:
        Arc length
    """
    if abs(curvature_start) < 1e-10 and abs(curvature_end) < 1e-10:
        return length
    
    avg_curvature = (curvature_start + curvature_end) / 2.0
    if abs(avg_curvature) < 1e-10:
        return length
    
    return abs(length / avg_curvature)


def solve_quadratic(a: float, b: float, c: float) -> List[float]:
    """
    Solve quadratic equation ax² + bx + c = 0.
    
    Args:
        a: Quadratic coefficient
        b: Linear coefficient
        c: Constant coefficient
        
    Returns:
        List of real solutions
        
    Raises:
        GeometryError: If equation is not quadratic
    """
    try:
        if abs(a) < 1e-10:
            if abs(b) < 1e-10:
                if abs(c) < 1e-10:
                    raise GeometryError("Infinitely many solutions")
                else:
                    raise GeometryError("No solution")
            return [-c / b]
        
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return []  # No real solutions
        elif discriminant == 0:
            return [-b / (2 * a)]  # One solution
        else:
            sqrt_discriminant = math.sqrt(discriminant)
            return [
                (-b + sqrt_discriminant) / (2 * a),
                (-b - sqrt_discriminant) / (2 * a)
            ]
    except Exception as e:
        raise GeometryError(f"Failed to solve quadratic equation: {str(e)}")


def rotation_matrix_2d(angle: float) -> Matrix:
    """
    Create 2D rotation matrix.
    
    Args:
        angle: Rotation angle in radians
        
    Returns:
        2D rotation matrix
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    return Matrix([
        [cos_a, -sin_a],
        [sin_a, cos_a]
    ])


def rotation_matrix_z(angle: float) -> Matrix:
    """
    Create 3D rotation matrix around Z-axis.
    
    Args:
        angle: Rotation angle in radians
        
    Returns:
        3D rotation matrix
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    return Matrix([
        [cos_a, -sin_a, 0.0, 0.0],
        [sin_a, cos_a, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def transformation_matrix(translation: Vector, rotation: float) -> Matrix:
    """
    Create transformation matrix from translation and rotation.
    
    Args:
        translation: Translation vector
        rotation: Rotation angle around Z-axis
        
    Returns:
        4x4 transformation matrix
    """
    rotation_mat = rotation_matrix_z(rotation)
    translation_mat = Matrix.Translation(translation)
    return translation_mat @ rotation_mat


def is_point_in_polygon_2d(point: Vector, polygon: List[Vector]) -> bool:
    """
    Check if a point is inside a 2D polygon using ray casting algorithm.
    
    Args:
        point: Point to test
        polygon: List of polygon vertices
        
    Returns:
        True if point is inside polygon
    """
    if len(polygon) < 3:
        return False
    
    x, y = point.x, point.y
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0].x, polygon[0].y
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n].x, polygon[i % n].y
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safe division that returns a default value when dividing by zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value for division by zero
        
    Returns:
        Division result or default value
    """
    if abs(denominator) < 1e-10:
        return default
    return numerator / denominator


def sign(value: float) -> int:
    """
    Return the sign of a number.
    
    Args:
        value: Input value
        
    Returns:
        1 for positive, -1 for negative, 0 for zero
    """
    if value > 0:
        return 1
    elif value < 0:
        return -1
    else:
        return 0 