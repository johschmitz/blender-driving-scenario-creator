# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.geometry import intersect_line_line_2d
from pyclothoids import SolveG2

from . import helpers

from math import pi


class junction_joint:
    def __init__(self, id_joint, id_incoming, contact_point_type, contact_point_vec,
                 heading, curvature, slope, lane_widths_left, lane_widths_right, lane_types_left, lane_types_right):
        self.id_joint = id_joint
        self.id_incoming = id_incoming
        self.contact_point_type = contact_point_type
        self.contact_point_vec = contact_point_vec
        self.heading = heading
        self.curvature = curvature
        self.slope = slope
        self.lane_widths_left = lane_widths_left
        self.lane_widths_right = lane_widths_right
        self.lane_types_left = lane_types_left
        self.lane_types_right = lane_types_right

class junction:

    def __init__(self, context):
        self.id_odr = None
        self.id_joint_next = 0
        self.context = context
        self.joints = []
        self.stencil = None

    def joint_exists(self, id_incoming):
        '''
            Return True if a joint with the same incoming road ID exists,
            otherwise False.
        '''
        for joint in self.joints:
            if joint.id_incoming == id_incoming:
                return True
        return False

    def get_new_id_joint(self):
        '''
            Generate a new unique ID for a joint.
        '''
        id_next = self.id_joint_next
        self.id_joint_next += 1
        return id_next

    def add_joint_incoming(self, id_incoming, contact_point_type, contact_point_vec,
                 heading, curvature, slope, lane_widths_left, lane_widths_right, lane_types_left, lane_types_right):
        '''
            Add a new joint, i.e. an incoming road to the junction if it does
            not exist yet.
        '''
        if self.joint_exists(id_incoming):
            return False
        else:
            id_joint = self.get_new_id_joint()
            joint = junction_joint(id_joint, id_incoming, contact_point_type, contact_point_vec,
                                   heading, curvature, slope, lane_widths_left, lane_widths_right, lane_types_left, lane_types_right)
            self.joints.append(joint)
            return True

    def add_joint_open(self, contact_point_vec, heading, slope,
                       lane_widths_left, lane_widths_right, lane_types_left, lane_types_right):
        '''
            Add a new joint without connecting to an incoming road.
        '''
        id_joint = self.get_new_id_joint()
        joint = junction_joint(id_joint, None, 'junction_joint_open', contact_point_vec,
            heading, 0.0, slope, lane_widths_left, lane_widths_right, lane_types_left, lane_types_right)
        self.joints.append(joint)
        return True

    def remove_last_joint(self):
        '''
            Remove the last added joint from the junction.
        '''
        if len(self.joints) > 0:
            self.joints.pop()
            self.id_joint_next -= 1

    def has_joints(self):
        '''
            Return True if there is a least one joint, otherwise False
        '''
        if len(self.joints) > 0:
            return True
        else:
            return False

    def add_connecting_road(self, connection_new):
        '''
            Add a new connecting road to the junction if it does not exist yet.
        '''
        pass

    def create_object_3d(self):
        '''
            Create a 3d junction blender object
        '''
        valid, mesh, matrix_world = self.get_mesh(wireframe=False)
        if not valid:
            return None
        else:
            id_obj = helpers.get_new_id_opendrive(self.context)
            mesh.name = 'junction_area_' + str(id_obj)
            obj = bpy.data.objects.new(mesh.name, mesh)
            obj.matrix_world = matrix_world
            helpers.link_object_opendrive(self.context, obj)

            # Assign transparent junction area material
            material = bpy.data.materials.get('junction_area')
            if material is None:
                # Create material
                material = bpy.data.materials.new(name='junction_area')
                material.diffuse_color = (.1, .1, .1, .1)
            obj.data.materials.append(material)

            helpers.select_activate_object(self.context, obj)

            # Convert the ngons to tris and quads to get a defined surface for elevated roads
            helpers.triangulate_quad_mesh(obj)

            # Metadata
            obj['dsc_category'] = 'OpenDRIVE'
            obj['dsc_type'] = 'junction_area'

            # Remember joint (contact) points for snapping
            joints = []
            for joint in self.joints:
                joint_dict = vars(joint)
                joints.append(joint_dict)
            obj['joints'] = joints

            # Set OpenDRIVE custom properties
            obj['id_odr'] = id_obj
            self.id_odr = id_obj

            obj['incoming_roads'] = {}

            return obj

    def create_stencil(self):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene currently only support OBJECT mode.
        '''
        stencil = bpy.data.objects.get('dsc_stencil')
        if stencil is not None:
            if self.context.scene.objects.get('dsc_stencil') is None:
                self.context.scene.collection.objects.link(stencil)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new('dsc_stencil')
            vertices, edges, faces = [(0.0, 0.0, 0.0)], [], []
            mesh.from_pydata(vertices, edges, faces)
            # Rotate in start heading direction
            self.stencil = bpy.data.objects.new('dsc_stencil', mesh)
            self.stencil.location = self.joints[0].contact_point_vec
            # Link
            self.context.scene.collection.objects.link(self.stencil)
            self.stencil.use_fake_user = True
            self.stencil.data.use_fake_user = True
        # Make stencil active object
        helpers.select_activate_object(self.context, self.stencil)

    def remove_stencil(self):
        '''
            Unlink stencil, needs to be in OBJECT mode.
        '''
        stencil = bpy.data.objects.get('dsc_stencil')
        if stencil is not None:
            bpy.data.objects.remove(stencil, do_unlink=True)
            self.stencil = None

    def update_stencil(self):
        '''
            Transform stencil object to follow the mouse pointer.
        '''
        if self.stencil == None:
            # Create helper stencil mesh
                self.create_stencil()
        # Try getting data for a new mesh
        valid, mesh, matrix_world = self.get_mesh(wireframe=True)
        # If we get a valid solution we can update the mesh, otherwise just return
        if valid:
            helpers.replace_mesh(self.stencil, mesh)
            # Set stencil global transform
            self.stencil.matrix_world = matrix_world
        else:
            self.remove_stencil()

    def get_mesh(self, wireframe=False):
        '''
            Calculate and return the vertices, edges and faces to create a
            junction mesh.
        '''
        if len(self.joints) == 0:
            valid_mesh = False
            return valid_mesh, None, None
        else:
            # Shift origin to connecting point
            mat_translation = Matrix.Translation(self.joints[0].contact_point_vec)
            mat_rotation = Matrix.Rotation(self.joints[0].heading, 4, 'Z')
            matrix_world = mat_translation @ mat_rotation
            # Create mesh
            joints_corners = []
            joints_heading = []
            joints_corners_curvatures = []
            joints_slopes = []
            for joint in self.joints:
                # Find corner points of incoming road joint
                vector_s = Vector((1.0, 0.0, 0.0))
                vector_s.rotate(Matrix.Rotation(joint.heading + pi/2, 3, 'Z'))
                width_left = sum(joint.lane_widths_left)
                point_local_left = matrix_world.inverted() \
                    @ (joint.contact_point_vec + vector_s * width_left)
                width_right = sum(joint.lane_widths_right)
                point_local_right = matrix_world.inverted() \
                    @ (joint.contact_point_vec - vector_s * width_right)
                joints_heading.append(joint.heading)
                joints_corners.append([point_local_left, point_local_right])
                if abs(joint.curvature) > 0.0:
                    if joint.curvature < 0.0:
                        curvature_left = 1 / (1/joint.curvature + width_left)
                        curvature_right = 1 / (1/joint.curvature - width_right)
                    else:
                        curvature_left = 1 / (1/joint.curvature - width_left)
                        curvature_right = 1 / (1/joint.curvature + width_right)
                else:
                    curvature_left = 0
                    curvature_right = 0
                joints_corners_curvatures.append([curvature_left, curvature_right])
                joints_slopes.append(joint.slope)
            # Obtain the junction boundary vertices and create a Blender mesh based of it
            valid_boundary, vertices = get_junction_boundary(mat_rotation, joints_corners, joints_heading, joints_corners_curvatures, joints_slopes)
            if valid_boundary:
                edges = [[idx, idx+1] for idx in range(len(vertices)-1)]
                edges += [[len(vertices)-1, 0]]
                if wireframe:
                    faces = []
                else:
                    if len(vertices) > 2:
                        faces = [[idx for idx in range(len(vertices))]]
                    else:
                        faces = []
            else:
                # No suitable solution found but at least mark road ends
                vertices = [joints_corners[0][0], joints_corners[0][1]]
                for corners in joints_corners:
                    vertices.append(corners[0])
                    vertices.append(corners[1])
                edges = [[2*idx, 2*idx+1] for idx in range(int(len(vertices)/2))]
                faces = []
            # Create blender mesh
            mesh = bpy.data.meshes.new('temp')
            mesh.from_pydata(vertices, edges, faces)

            # Set corner vertex crease values to prepare for usage of
            # subdivision surface modifier
            bm = bmesh.new()
            bm.from_mesh(mesh)
            crease_layer = bm.verts.layers.crease.verify()
            for vert in bm.verts:
                vert[crease_layer] = 1.0
            bm.to_mesh(mesh)
            bm.free()

            valid_mesh = True
            return valid_mesh, mesh, matrix_world

def get_junction_boundary(mat_rotation, joints_corners, joints_heading, joints_corners_curvatures, joints_slopes):
    '''
        Try to return junction boundary vertices based on joint corners to
        connect [[left corner 0, right corner 0], ... ].
    '''
    ordered_indices = [0]
    vertices = []
    idx_current = 0
    idx_next = 0
    valid_boundary = False
    # Start at 1 since we now the first joint and need to find all others (in order)
    joint_count = 1
    for _ in range(len(joints_corners)):
        vec_right_2_left = joints_corners[idx_current][1] - joints_corners[idx_current][0]
        vec_right = joints_corners[idx_current][1]
        angle_current = 0
        found = False
        # Search for next joint to connect to
        for idx_i, corners_next in enumerate(joints_corners):
            if not idx_i in ordered_indices:
                vec_left_next = corners_next[0]
                vec_right_2_left_next = vec_right - vec_left_next
                if vec_right_2_left_next == Vector((0.0, 0.0, 0.0)):
                    idx_next = idx_i
                    found = True
                else:
                    angle_check = vec_right_2_left.to_2d().angle_signed(vec_right_2_left_next.to_2d())
                    # Convert -pi .. pi to 0 .. 2*pi
                    if angle_check < 0:
                        angle_check = 2 * pi + angle_check
                    # Check if not self crossing and larger than before (make "as convex as possible")
                    if angle_check < (3/2*pi) and angle_check > angle_current:
                        # Do not add this connection if it crosses any other road
                        crossing = False
                        for idx_j, corners_check in enumerate(joints_corners):
                            if idx_j != idx_current and idx_j != idx_i:
                                vec_left_check = corners_check[0]
                                vec_right_check = corners_check[1]

                                # Get heading vector of incoming road joint (t-direction)
                                vector_t = Vector((1.0, 0.0, 0.0))
                                vector_t.rotate(Matrix.Rotation(joints_heading[idx_j], 3, 'Z'))
                                vector_t.rotate(mat_rotation.inverted())
                                far_point_left = corners_check[0] - vector_t * 10000
                                far_point_right = corners_check[1] - vector_t * 10000
                                intersection_left = intersect_line_line_2d(
                                    vec_right, vec_left_next, vec_left_check, far_point_left)
                                intersection_right = intersect_line_line_2d(
                                    vec_right, vec_left_next, vec_right_check, far_point_right)
                                if intersection_left != None or intersection_right != None:
                                    crossing = True
                        if crossing == False:
                            angle_current = angle_check
                            idx_next = idx_i
                            found = True
        if found:
            # Calculate boundary curve points for the next segment and add to vertices
            joint_count += 1
            ordered_indices.append(idx_next)
            heading_current = joints_heading[idx_current] - joints_heading[0]
            heading_next = joints_heading[idx_next] -joints_heading[0]
            boundary_section = calculate_junction_boundary_section(
                joints_corners[idx_current][1], heading_current, joints_corners_curvatures[idx_current][1], joints_slopes[idx_current],
                joints_corners[idx_next][0], heading_next-pi, -joints_corners_curvatures[idx_next][0], -joints_slopes[idx_next])
            # Combine the samples from muliple clothoid segments
            vertices += [point for curve_segment in boundary_section for point in curve_segment]
        idx_current = idx_next
    if joint_count > 1:
        # Add last segment to close the boundary
        heading_current = joints_heading[idx_current] - joints_heading[0]
        boundary_section = calculate_junction_boundary_section(
                joints_corners[idx_current][1], heading_current, joints_corners_curvatures[idx_current][1], joints_slopes[idx_current],
                joints_corners[0][0], pi, -joints_corners_curvatures[0][0], -joints_slopes[0])
        vertices += [point for curve_segment in boundary_section for point in curve_segment]
        if joint_count == len(joints_corners):
            valid_boundary = True
    return valid_boundary, vertices

def calculate_junction_boundary_section(corner_right, heading_right, curvature_right, slope_right,
                                        corner_left, heading_left, curvature_left, slope_left):
    '''
        Calculate junction boundary between right corner of joint n and left
        corner of joint n+1. Use a 3 segment clothoid curve.
    '''
    boundary_segment_curve = SolveG2(
        corner_right.x, corner_right.y, heading_right, curvature_right,
        corner_left.x, corner_left.y, heading_left, curvature_left)
    length = sum((boundary_segment_curve[0].length, boundary_segment_curve[1].length, boundary_segment_curve[2].length))
    # Use Hermite interpolation for elevation:
    #     https://en.m.wikipedia.org/wiki/Cubic_Hermite_spline
    elevation = lambda s : \
        corner_right[2] \
        + slope_right * s \
        + (-3 * corner_right[2] - 2 * length * slope_right + 3 * corner_left[2] - length * -slope_left) / length**2 * s**2 \
        + (2 * corner_right[2] + length * slope_right - 2 * corner_left[2] + length * -slope_left) / length**3 * s**3

    boundary_points = []
    length_current = 0
    for clothoid in boundary_segment_curve:
        # TODO make sampling adaptive
        num_intervals = 5
        sample_points = [i/num_intervals * clothoid.length for i in range(num_intervals+1)]
        boundary_points.append([[clothoid.X(s), clothoid.Y(s), elevation(length_current+s)] for s in sample_points])
        length_current += clothoid.length

    return boundary_points