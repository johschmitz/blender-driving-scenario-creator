"""
Tests for refactored utility modules.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from mathutils import Vector

# Import test classes
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'addon'))

from utils.math_utils import *
from utils.validation_utils import *
from utils.file_utils import *
from utils.geometry_utils import *
from core.exceptions import *
from core.constants import *


class TestMathUtils(unittest.TestCase):
    """Test mathematical utility functions."""
    
    def test_normalize_angle(self):
        """Test angle normalization."""
        # Test normal angles
        self.assertAlmostEqual(normalize_angle(0), 0)
        self.assertAlmostEqual(normalize_angle(math.pi), math.pi)
        self.assertAlmostEqual(normalize_angle(-math.pi), -math.pi)
        
        # Test angles outside range
        self.assertAlmostEqual(normalize_angle(3 * math.pi), -math.pi)
        self.assertAlmostEqual(normalize_angle(-3 * math.pi), -math.pi)
    
    def test_clamp(self):
        """Test value clamping."""
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-5, 0, 10), 0)
        self.assertEqual(clamp(15, 0, 10), 10)
    
    def test_point_distance(self):
        """Test point distance calculations."""
        p1 = Vector((0, 0, 0))
        p2 = Vector((3, 4, 0))
        
        self.assertAlmostEqual(point_distance_2d(p1, p2), 5.0)
        self.assertAlmostEqual(point_distance_3d(p1, p2), 5.0)
    
    def test_solve_quadratic(self):
        """Test quadratic equation solver."""
        # x² - 5x + 6 = 0, solutions: x = 2, 3
        solutions = solve_quadratic(1, -5, 6)
        self.assertEqual(len(solutions), 2)
        self.assertIn(2.0, solutions)
        self.assertIn(3.0, solutions)
        
        # No real solutions
        solutions = solve_quadratic(1, 0, 1)
        self.assertEqual(len(solutions), 0)


class TestValidationUtils(unittest.TestCase):
    """Test validation utility functions."""
    
    def test_validate_lane_width(self):
        """Test lane width validation."""
        # Valid values
        self.assertEqual(validate_lane_width(3.5), 3.5)
        self.assertEqual(validate_lane_width(2), 2.0)
        
        # Invalid values
        with self.assertRaises(ValidationError):
            validate_lane_width(-1)
        
        with self.assertRaises(ValidationError):
            validate_lane_width(100)
        
        with self.assertRaises(ValidationError):
            validate_lane_width("invalid")
    
    def test_validate_filename(self):
        """Test filename validation."""
        # Valid filenames
        self.assertEqual(validate_filename("test.txt"), "test.txt")
        self.assertEqual(validate_filename("  test  "), "test")
        
        # Invalid filenames
        with self.assertRaises(ValidationError):
            validate_filename("")
        
        with self.assertRaises(ValidationError):
            validate_filename("test<>file")
        
        with self.assertRaises(ValidationError):
            validate_filename("a" * 300)  # Too long
    
    def test_validate_vector(self):
        """Test vector validation."""
        # Valid vectors
        vec = Vector((1, 2, 3))
        result = validate_vector(vec)
        self.assertEqual(result, vec)
        
        # Invalid vectors
        with self.assertRaises(ValidationError):
            validate_vector("not a vector")
        
        with self.assertRaises(ValidationError):
            validate_vector(Vector((1e20, 0, 0)))  # Out of bounds
    
    def test_parameter_validator(self):
        """Test parameter validator class."""
        validator = ParameterValidator()
        
        # Valid parameters
        result = validator.validate_parameter("width", 3.5, validate_lane_width)
        self.assertEqual(result, 3.5)
        self.assertFalse(validator.has_errors())
        
        # Invalid parameters
        validator.validate_parameter("width", -1, validate_lane_width)
        self.assertTrue(validator.has_errors())
        
        # Test error summary
        summary = validator.get_error_summary()
        self.assertIn("width", summary)


class TestFileUtils(unittest.TestCase):
    """Test file utility functions."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_ensure_directory(self):
        """Test directory creation."""
        test_dir = self.temp_dir / "test" / "nested"
        result = ensure_directory(test_dir)
        
        self.assertTrue(test_dir.exists())
        self.assertEqual(result, test_dir)
    
    def test_safe_remove_file(self):
        """Test safe file removal."""
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Remove existing file
        self.assertTrue(safe_remove_file(test_file))
        self.assertFalse(test_file.exists())
        
        # Remove non-existing file (should not raise error)
        self.assertTrue(safe_remove_file(test_file))
    
    def test_copy_file(self):
        """Test file copying."""
        source = self.temp_dir / "source.txt"
        dest = self.temp_dir / "dest.txt"
        
        source.write_text("test content")
        
        self.assertTrue(copy_file(source, dest))
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "test content")
    
    def test_read_write_text_file(self):
        """Test text file operations."""
        test_file = self.temp_dir / "test.txt"
        content = "Hello, World!"
        
        # Write and read
        write_text_file(test_file, content)
        result = read_text_file(test_file)
        
        self.assertEqual(result, content)
    
    def test_read_write_json_file(self):
        """Test JSON file operations."""
        test_file = self.temp_dir / "test.json"
        data = {"key": "value", "number": 42}
        
        # Write and read
        write_json_file(test_file, data)
        result = read_json_file(test_file)
        
        self.assertEqual(result, data)
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        self.assertEqual(sanitize_filename("test<>file"), "test__file")
        self.assertEqual(sanitize_filename("  test  "), "test")
        self.assertEqual(sanitize_filename(""), "unnamed")
    
    def test_get_unique_filename(self):
        """Test unique filename generation."""
        base_file = self.temp_dir / "test.txt"
        base_file.write_text("content")
        
        unique_file = get_unique_filename(base_file)
        self.assertNotEqual(unique_file, base_file)
        self.assertFalse(unique_file.exists())


class TestGeometryUtils(unittest.TestCase):
    """Test geometry utility functions."""
    
    def test_create_line_mesh_vertices(self):
        """Test line mesh vertex creation."""
        start = Vector((0, 0, 0))
        end = Vector((10, 0, 0))
        width = 2.0
        
        vertices = create_line_mesh_vertices(start, end, width)
        
        self.assertEqual(len(vertices), 4)
        # Check that vertices form a rectangle
        self.assertAlmostEqual((vertices[1] - vertices[0]).length, width)
    
    def test_create_bezier_curve_points(self):
        """Test Bezier curve point generation."""
        p0 = Vector((0, 0, 0))
        p1 = Vector((0, 5, 0))
        p2 = Vector((5, 5, 0))
        p3 = Vector((5, 0, 0))
        
        points = create_bezier_curve_points(p0, p1, p2, p3, 10)
        
        self.assertEqual(len(points), 10)
        self.assertEqual(points[0], p0)
        self.assertEqual(points[-1], p3)
    
    def test_calculate_curve_length(self):
        """Test curve length calculation."""
        points = [
            Vector((0, 0, 0)),
            Vector((3, 0, 0)),
            Vector((3, 4, 0))
        ]
        
        length = calculate_curve_length(points)
        self.assertAlmostEqual(length, 7.0)  # 3 + 4
    
    def test_simplify_curve(self):
        """Test curve simplification."""
        # Create a line with redundant middle point
        points = [
            Vector((0, 0, 0)),
            Vector((5, 0, 0)),  # This point is on the line between start and end
            Vector((10, 0, 0))
        ]
        
        simplified = simplify_curve(points, tolerance=0.1)
        
        # Should remove the middle point
        self.assertEqual(len(simplified), 2)
        self.assertEqual(simplified[0], points[0])
        self.assertEqual(simplified[1], points[2])
    
    def test_offset_curve(self):
        """Test curve offsetting."""
        points = [
            Vector((0, 0, 0)),
            Vector((10, 0, 0))
        ]
        
        offset_points = offset_curve(points, 1.0)
        
        self.assertEqual(len(offset_points), 2)
        # Check that points are offset in the correct direction
        self.assertAlmostEqual(offset_points[0].y, -1.0)
        self.assertAlmostEqual(offset_points[1].y, -1.0)


class TestTemporaryDirectory(unittest.TestCase):
    """Test temporary directory context manager."""
    
    def test_temporary_directory(self):
        """Test temporary directory creation and cleanup."""
        temp_path = None
        
        # Use temporary directory
        with TemporaryDirectory() as temp_dir:
            temp_path = temp_dir
            self.assertTrue(temp_path.exists())
            
            # Create a test file
            test_file = temp_path / "test.txt"
            test_file.write_text("test")
            self.assertTrue(test_file.exists())
        
        # Directory should be cleaned up
        self.assertFalse(temp_path.exists())


if __name__ == '__main__':
    unittest.main() 