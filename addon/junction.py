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
from mathutils import Vector, Matrix

from . import helpers

from math import pi


class junction_joint:
    def __init__(self, id_incoming, contact_point, contact_point_vec,
                 heading, slope, width_left, width_right):
        self.id_incoming = id_incoming
        self.contact_point = contact_point
        self.contact_point_vec = contact_point_vec
        self.heading = heading
        self.slope = slope
        self.width_left = width_left
        self.width_right = width_right


class junction_connection:
    def __init__(self, id_incoming, contact_point, id_linked):
        self.id_incoming = id_incoming
        self.contact_point = contact_point
        self.id_linked = id_linked


class junction:

    def __init__(self, context):
        self.context = context
        self.joints = []
        self.connections = []
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

    def add_joint(self, id_incoming, contact_point, contact_point_vec,
                 heading, slope, width_left, width_right):
        '''
            Add a new joint, i.e. an incoming road to the junction if it does
            not exist yet.
        '''
        if self.joint_exists(id_incoming):
            return False
        else:
            joint = junction_joint(id_incoming, contact_point, contact_point_vec,
                heading, slope, width_left, width_right)
            self.joints.append(joint)
            return True

    def remove_last_joint(self):
        '''
            Remove the last added joint from the junction.
        '''
        if len(self.joints) > 0:
            self.joints.pop()

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

    def create_3d_object(self):
        '''
            Create a junction blender object
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

            # Metadata
            obj['dsc_category'] = 'OpenDRIVE'
            obj['dsc_type'] = 'junction_area'

            # Remember joint (contact) points for snapping
            joints = []
            for joint in self.joints:
                joints.append(vars(joint))
            obj['joints'] = joints

            # Set OpenDRIVE custom properties
            obj['id_xodr'] = id_obj

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
            valid = False
            return valid, None, None
        else:
            # Shift origin to connecting point
            mat_translation = Matrix.Translation(self.joints[0].contact_point_vec)
            mat_rotation = Matrix.Rotation(self.joints[0].heading, 4, 'Z')
            matrix_world = mat_translation @ mat_rotation
            # Create mesh
            corners_joints = []
            for joint in self.joints:
                vector_hdg = Vector((1.0, 0.0, 0.0))
                vector_hdg.rotate(Matrix.Rotation(joint.heading + pi/2, 3, 'Z'))
                point_local_left = matrix_world.inverted() \
                    @ (joint.contact_point_vec + vector_hdg * joint.width_left)
                point_local_right = matrix_world.inverted() \
                    @ (joint.contact_point_vec - vector_hdg * joint.width_right)
                corners_joints.append([point_local_left, point_local_right])
            vertices = get_junction_hull(corners_joints)
            edges = [[idx, idx+1] for idx in range(len(vertices)-1)]
            edges += [[len(vertices)-1, 0]]
            if wireframe:
                faces = []
            else:
                if len(vertices) > 2:
                    faces = [[idx for idx in range(len(vertices))] + [0]]
                else:
                    faces = []
            # Create blender mesh
            mesh = bpy.data.meshes.new('temp')
            mesh.from_pydata(vertices, edges, faces)
            valid = True
            return valid, mesh, matrix_world

def get_junction_hull(corners_joints):
    '''
        Return ordered list of junction hull corners based on joint corners
        [[left corner 0, right corner 0], ... ].
    '''
    ordered_indices = [0]
    vertices = [corners_joints[0][0], corners_joints[0][1]]
    idx_next = 0
    for _ in range(len(corners_joints)):
        vec_right_2_left = corners_joints[idx_next][1] - corners_joints[idx_next][0]
        vec_right = corners_joints[idx_next][1]
        angle_next = 0
        found = False
        for idx_j, corners in enumerate(corners_joints):
            if not idx_j in ordered_indices:
                vec_right_2_left_next = vec_right - corners[0]
                angle_check = vec_right_2_left.angle(vec_right_2_left_next)
                if angle_check > angle_next:
                    angle_next = angle_check
                    idx_next = idx_j
                    found = True
        if found:
            ordered_indices.append(idx_next)
            vertices.append(corners_joints[idx_next][0])
            vertices.append(corners_joints[idx_next][1])
    return vertices

