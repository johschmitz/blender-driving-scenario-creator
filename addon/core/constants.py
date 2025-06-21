"""
Constants used throughout the Blender Driving Scenario Creator add-on.
"""

from typing import Dict, Any
from enum import Enum

# Add-on Information
ADDON_NAME = "Driving Scenario Creator"
ADDON_VERSION = (0, 28, 5)
BLENDER_VERSION_MIN = (3, 6, 0)

# Collections
COLLECTION_DSC = "Driving Scenario Creator"
COLLECTION_OPENDRIVE = "OpenDRIVE"
COLLECTION_OPENSCENARIO = "OpenSCENARIO"

# Object Types
class ObjectType(Enum):
    ROAD_STRAIGHT = "road_straight"
    ROAD_ARC = "road_arc"
    ROAD_CLOTHOID = "road_clothoid"
    ROAD_CLOTHOID_TRIPLE = "road_clothoid_triple"
    ROAD_PARAMPOLY3 = "road_parampoly3"
    JUNCTION_AREA = "junction_area"
    JUNCTION_CONNECTING_ROAD = "junction_connecting_road"
    JUNCTION_FOUR_WAY = "junction_four_way"
    JUNCTION_DIRECT = "junction_direct"
    ENTITY_VEHICLE = "entity_vehicle"
    ENTITY_PEDESTRIAN = "entity_pedestrian"
    ROAD_OBJECT_SIGN = "road_object_sign"
    ROAD_OBJECT_TRAFFIC_LIGHT = "road_object_traffic_light"
    ROAD_OBJECT_STOP_LINE = "road_object_stop_line"
    ROAD_OBJECT_STENCIL = "road_object_stencil"
    TRAJECTORY_NURBS = "trajectory_nurbs"
    TRAJECTORY_POLYLINE = "trajectory_polyline"

# Lane Types
class LaneType(Enum):
    DRIVING = "driving"
    STOP = "stop"
    BORDER = "border"
    SHOULDER = "shoulder"
    MEDIAN = "median"
    ENTRY = "entry"
    EXIT = "exit"
    ON_RAMP = "onRamp"
    OFF_RAMP = "offRamp"
    NONE = "none"
    CENTER = "center"

# Road Mark Types
class RoadMarkType(Enum):
    NONE = "none"
    SOLID = "solid"
    BROKEN = "broken"
    SOLID_SOLID = "solid_solid"

# Road Mark Colors
class RoadMarkColor(Enum):
    NONE = "none"
    WHITE = "white"
    YELLOW = "yellow"

# Road Mark Weights
class RoadMarkWeight(Enum):
    NONE = "none"
    STANDARD = "standard"
    BOLD = "bold"

# Vehicle Categories
class VehicleCategory(Enum):
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"

# Pedestrian Categories
class PedestrianCategory(Enum):
    PEDESTRIAN = "pedestrian"

# Geometry Solvers
class GeometrySolver(Enum):
    DEFAULT = "default"
    HERMITE = "hermite"
    FORWARD = "forward"

# Default Measurements (in meters)
DEFAULT_LANE_WIDTH = 3.5
DEFAULT_BORDER_WIDTH = 0.5
DEFAULT_SHOULDER_WIDTH = 1.5
DEFAULT_MEDIAN_WIDTH = 2.0
DEFAULT_STOP_WIDTH = 2.5
DEFAULT_NONE_WIDTH = 2.5

# Line Widths (in meters)
DEFAULT_LINE_WIDTH_STANDARD = 0.12
DEFAULT_LINE_WIDTH_BOLD = 0.25

# Default Speeds (in km/h)
DEFAULT_DESIGN_SPEED = 130.0
DEFAULT_ENTITY_SPEED = 50.0

# File Extensions
SUPPORTED_MESH_FORMATS = [".fbx", ".glb", ".gltf", ".osgb", ".obj", ".dae"]
OPENDRIVE_EXTENSION = ".xodr"
OPENSCENARIO_EXTENSION = ".xosc"

# Export Settings
DEFAULT_EXPORT_FILENAME = "bdsc_export"
EXPORT_SUBDIRS = {
    "models": "models",
    "static_scene": "models/static_scene",
    "entities": "models/entities",
    "catalogs": "catalogs",
    "vehicles": "catalogs/vehicles",
    "pedestrians": "catalogs/pedestrians",
    "xosc": "xosc",
}

# Material Names
MATERIAL_ROAD_ASPHALT = "road_asphalt"
MATERIAL_ROAD_MARK_WHITE = "road_mark_white"
MATERIAL_ROAD_MARK_YELLOW = "road_mark_yellow"
MATERIAL_GRASS = "grass"
MATERIAL_JUNCTION_AREA = "junction_area"

# Contact Point Types
class ContactPointType(Enum):
    START = "cp_start_l"
    START_LEFT = "cp_start_l"
    START_RIGHT = "cp_start_r"
    END = "cp_end_l"
    END_LEFT = "cp_end_l"
    END_RIGHT = "cp_end_r"
    JUNCTION_JOINT = "junction_joint"

# Modal States
class ModalState(Enum):
    INIT = "INIT"
    SELECT_START = "SELECT_START"
    SELECT_POINT = "SELECT_POINT"

# Elevation Adjustment Types
class ElevationAdjustment(Enum):
    DISABLED = "DISABLED"
    SIDEVIEW = "SIDEVIEW"
    GENERIC = "GENERIC"

# Cross Section Presets
CROSS_SECTION_PRESETS = [
    "two_lanes_default",
    "two_lanes_turning_lane_offset_left_open",
    "ekl4_rq9",
    "ekl3_rq11",
    "eka1_rq31",
    "eka1_rq31_exit_lane_right_open",
    "eka1_rq31_exit_lane_right_to_off_ramp",
    "eka1_rq31_exit_right_continuation_begin_end",
    "eka1_rq31_exit_right_continuation_shoulder_begin",
    "eka1_rq31_exit_right_continuation_shoulder_end",
    "eka1_rq31_entry_right_from_on_ramp",
    "eka1_rq31_entry_right_close",
    "eka1_rq36",
    "eka1_rq43_5",
    "off_ramp_begin",
    "off_ramp_shoulder_begin",
    "off_ramp_middle",
    "off_ramp_end",
    "on_ramp_end",
    "on_ramp_shoulder_end",
    "on_ramp_middle",
    "on_ramp_begin",
    "shoulder_left",
    "shoulder_right",
    "junction_connecting_road",
]

# Validation Limits
MIN_LANE_WIDTH = 0.01
MAX_LANE_WIDTH = 20.0
MIN_DESIGN_SPEED = 1.0
MAX_DESIGN_SPEED = 400.0
MAX_LANES_PER_SIDE = 20

# Keyboard Shortcuts
SHORTCUT_TOGGLE_SIDEBAR = "N"
SHORTCUT_GRID_SNAP = "CTRL"
SHORTCUT_ADD_SECTION = "SHIFT"
SHORTCUT_ADJUST_HEADING = "ALT"
SHORTCUT_ELEVATION_3D = "E"
SHORTCUT_ELEVATION_SIDE = "S"

# Export format constants
MESH_EXPORT_FORMATS = [
    'fbx',     # Autodesk FBX
    'gltf',    # glTF 2.0
    'glb',     # glTF Binary
    'osgb',    # OpenSceneGraph Binary
    'obj',     # Wavefront OBJ
    'dae',     # Collada DAE
]

ENTITY_TYPES = [
    'vehicle',
    'pedestrian',
    'miscellaneous'
]

TRAJECTORY_TYPES = [
    'polyline',
    'nurbs',
    'clothoid'
]

# Road type constants
ROAD_TYPES = [
    'straight',
    'arc',
    'clothoid',
    'clothoid_triple',
    'parampoly3'
]

# Lane type mappings for export (as lists for easier iteration)
LANE_TYPES = [lane_type.value for lane_type in LaneType]

# Sampling and Geometry Constants
DEFAULT_SAMPLING_STEP_STRAIGHT = 5.0  # meters for straight road sampling
DEFAULT_SAMPLING_STEP_CURVED = 1.0    # meters for curved road sampling
DEFAULT_SAMPLING_STEP_MIN = 1.0       # minimum sampling step
DEFAULT_SAMPLING_STEP_MAX = 5.0       # maximum sampling step
DEFAULT_CURVATURE_THRESHOLD = 0.1     # threshold for curvature-based sampling

# Road Object Thickness Constants
SIGN_THICKNESS = 0.002          # 2mm steel thickness for signs
TRAFFIC_LIGHT_THICKNESS = 0.002 # 2mm thickness for traffic lights
STOP_LINE_THICKNESS = 0.002     # thickness for stop lines

# Broken Line Parameters
DEFAULT_BROKEN_LINE_LENGTH = 3.0     # meters
DEFAULT_BROKEN_LINE_GAP_RATIO = 1    # ratio of gap to line
DEFAULT_BROKEN_LINE_OFFSET = 0.5     # offset for broken line patterns

# Geometry Precision Constants
PARAMETRIC_POLY_SAMPLE_POINTS = 100  # number of sample points for ParamPoly3
PRECISION_TOLERANCE = 1e-6           # general precision tolerance
ANGLE_PRECISION = 1e-8               # precision for angle calculations

# Entity Speed Limits
MIN_ENTITY_SPEED = 0.1              # minimum entity speed in km/h
MAX_ENTITY_SPEED = 500.0            # maximum entity speed in km/h

# Road Geometry Limits
MIN_ROAD_LENGTH = 0.1               # minimum road segment length in meters
MAX_ROAD_LENGTH = 10000.0           # maximum road segment length in meters
MIN_RADIUS = 1.0                    # minimum curve radius in meters
MAX_RADIUS = 10000.0                # maximum curve radius in meters

# Junction Constants
DEFAULT_JUNCTION_ELEVATION = 0.0    # default elevation for junctions
JUNCTION_SAMPLING_STEP = 1.0        # sampling step for junction geometry

# Material Color Constants (RGBA tuples)
COLOR_ROAD_ASPHALT = (0.3, 0.3, 0.3, 1.0)
COLOR_ROAD_MARK_WHITE = (1.0, 1.0, 1.0, 1.0)
COLOR_ROAD_MARK_YELLOW = (1.0, 1.0, 0.0, 1.0)
COLOR_GRASS = (0.2, 0.6, 0.2, 1.0)
COLOR_JUNCTION_AREA = (0.4, 0.4, 0.4, 1.0)

# Entity Default Colors
COLOR_VEHICLE_DEFAULT = (0.9, 0.1, 0.1, 1.0)
COLOR_PEDESTRIAN_DEFAULT = (0.1, 0.1, 0.9, 1.0)

# Export Constants
DEFAULT_MESH_SUBDIVISION = 0        # default subdivision level for mesh export
EXPORT_DECIMAL_PRECISION = 6        # decimal precision for export files

# Performance Constants
MAX_UNDO_STEPS = 50                 # maximum undo steps to keep
VIEWPORT_REFRESH_RATE = 60          # viewport refresh rate in Hz

# File I/O Constants
MAX_FILE_SIZE_MB = 100              # maximum file size for import in MB
BACKUP_FILE_COUNT = 5               # number of backup files to keep

# Validation Constants
MAX_WARNING_DISTANCE = 1000.0       # maximum distance for warning messages
MIN_OBJECT_SEPARATION = 0.01        # minimum separation between objects

# UI Constants
PANEL_WIDTH_MIN = 200               # minimum panel width in pixels
ICON_SIZE_DEFAULT = 32              # default icon size in pixels
TOOLTIP_DELAY = 0.5                 # tooltip delay in seconds