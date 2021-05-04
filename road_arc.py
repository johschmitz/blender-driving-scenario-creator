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

from .operator_snap_draw import DSC_OT_snap_draw
from . import helpers

from math import pi, sin, cos, acos, ceil


class DSC_OT_road_arc(DSC_OT_snap_draw, bpy.types.Operator):
    bl_idname = "dsc.road_arc"
    bl_label = "Arc"
    bl_description = "Create an arc road"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def create_object_xodr(self, context, point_start, heading_start, snapped_start,
                           point_end, heading_end, snapped_end):
        '''
            Create an arc road object
        '''
        valid, center, r_center, determinant = self.get_arc_center_radius_det(
            point_start, heading_start, point_end)
        if not valid:
            self.report({"WARNING"}, "Can not calculate arc!")
            return
        else:
            obj_id = helpers.get_new_id_opendrive(context)
            mesh = bpy.data.meshes.new('road_arc_' + str(obj_id))
            obj = bpy.data.objects.new(mesh.name, mesh)
            helpers.link_object_opendrive(context, obj)

            # Generate new mesh
            angle = (point_end.to_2d() - center).angle_signed(point_start.to_2d() - center)
            vertices, edges, faces = self.get_ring_segment_vertices(r_center, 4.0, angle, determinant)
            obj.data.from_pydata(vertices, edges, faces)
            # Shift origin from arc center to contact point and rotate
            if determinant > 0:
                matrix = Matrix.Translation((0.0, r_center, 0.0))
            else:
                matrix = Matrix.Translation((0.0, -r_center, 0.0))
            obj.data.transform(matrix)
            self.transform_object_wrt_start(obj, point_start, heading_start)


            helpers.select_activate_object(context, obj)

            # Remember connecting points for road snapping
            obj['cp_start'] = point_start
            obj['cp_end'] = point_end

            # Set OpenDRIVE custom properties
            obj['id_xodr'] = obj_id
            obj['t_road_planView_geometry'] = 'arc'
            obj['t_road_planView_geometry_s'] = 0
            obj['t_road_planView_geometry_x'] = point_start.x
            obj['t_road_planView_geometry_y'] = point_start.y
            obj['t_road_planView_geometry_hdg'] = heading_start
            obj['t_road_planView_geometry_angle'] = angle
            if determinant < 0:
                obj['t_road_planView_geometry_curvature'] = -1/r_center
            else:
                obj['t_road_planView_geometry_curvature'] = 1/r_center

            return obj

    def create_stencil(self, context, point_start, heading_start, snapped_start):
        '''
            Create a stencil object with fake user or find older one in bpy data and
            relink to scene currently only support OBJECT mode.
        '''
        stencil = bpy.data.objects.get('dsc_stencil_object')
        if stencil is not None:
            if context.scene.objects.get('dsc_stencil_object') is None:
                context.scene.collection.objects.link(stencil)
        else:
            # Create object from mesh
            mesh = bpy.data.meshes.new("dsc_stencil_object")
            vertices = [(0.0,   0.0, 0.0),
                        (0.01,  0.0, 0.0),
                        (0.01, -4.0, 0.0),
                        (0.0,  -4.0, 0.0),
                        (0.0,   4.0, 0.0),
                        (0.01,  4.0, 0.0)
                        ]
            edges = [[0, 1],[1, 2],[2, 3],[3, 4],
                     [0, 4,],[4, 5],[5, 1]]
            faces = []
            mesh.from_pydata(vertices, edges, faces)
            self.stencil = bpy.data.objects.new("dsc_stencil_object", mesh)
            # Rotate in start heading direction
            self.transform_object_wrt_start(self.stencil, point_start, heading_start)
            # Link
            context.scene.collection.objects.link(self.stencil)
            self.stencil.use_fake_user = True
            self.stencil.data.use_fake_user = True
        # Make stencil active object
        helpers.select_activate_object(context, self.stencil)

    def update_stencil(self, point_start, heading_start, snapped_start,
                             point_end, heading_end, snapped_end):
        '''
            Update stencil object mesh to follow the mouse pointer.
        '''
        # We need to calculate the center and radius of the arc based on the
        # start point and the end point location
        valid, center, r_center, determinant = self.get_arc_center_radius_det(
            point_start, heading_start, point_end)
        # If cursor is not in line with connection we get a solution and update the mesh
        if valid:
            # Delete old mesh data
            bm = bmesh.new()
            bm.from_mesh(self.stencil.data)
            verts = [v for v in bm.verts]
            bmesh.ops.delete(bm, geom=verts, context='VERTS')
            bm.to_mesh(self.stencil.data)
            bm.free()
            # Generate new mesh
            angle = (point_end.to_2d() - center).angle_signed(point_start.to_2d() - center)
            vertices, edges, faces = self.get_ring_segment_vertices(r_center, 4.0, angle, determinant)
            faces = []
            self.stencil.data.from_pydata(vertices, edges, faces)
            # Shift origin from arc center to contact point and rotate
            if determinant > 0:
                matrix = Matrix.Translation((0.0, r_center, 0.0))
            else:
                matrix = Matrix.Translation((0.0, -r_center, 0.0))
            self.stencil.data.transform(matrix)
            self.transform_object_wrt_start(self.stencil, point_start, heading_start)

    def project_point_end(self, point_start, heading_start, point_selected):
        '''
            Project selected point to direction vector.
        '''
        return point_selected

    def get_ring_segment_vertices(self, r_center, width_lane, angle, determinant):
        '''
            Return vertices of a ring segment.
        '''
        if determinant > 0:
            startangle = 0
            if angle < 0:
                endangle = pi
            else:
                endangle = angle
        else:
            startangle = pi
            if angle > 0:
                endangle = 0
            else:
                endangle = angle + pi

        vertices = []
        edges = []

        # Adaptive steps based on
        # https://stackoverflow.com/questions/11774038/how-to-render-a-circle-with-as-few-vertices-as-possible
        error_max = 0.25
        steps = ceil(2 * pi / acos(2 * (1 - error_max / r_center)**2 - 1))
        angle_step = (endangle - startangle) / steps
        radii = [r_center - width_lane, r_center, r_center + width_lane]
        # Vertices
        for r in radii:
            x = cos(startangle - pi/2) * r
            y = sin(startangle - pi/2) * r
            vertices.append([x, y, 0])
            j = 1
            while j < steps:
                t = angle_step * j
                x = cos(t + startangle - pi/2) * r
                y = sin(t + startangle - pi/2) * r
                vertices.append([x, y, 0])
                j += 1
            x = cos(endangle - pi/2) * r
            y = sin(endangle - pi/2) * r
            vertices.append([x, y, 0])
        # Edges
        num_single = int(len(vertices)/3)
        for i in range(3):
            for j in range(num_single-1) :
                edges.append([num_single * i + j, num_single * i + j + 1])
        edges.append([0, num_single])
        edges.append([num_single,2*num_single])
        edges.append([num_single-1,2*num_single-1])
        edges.append([2*num_single-1,3*num_single-1])
        # Faces
        faces = [[v for v in range(steps+1)]+[v for v in range(2*steps+1, steps, -1)],
                 [v for v in range(steps+1, 2*steps+2)]+[v for v in range(3*steps+2, 2*steps+1, -1)]]
        return vertices, edges, faces

    def get_arc_center_radius_det(self, point_start, heading_start, point_end):
        '''
            Calculate center and radius of the arc that is defined by the
            starting point (predecessor connection point), the start heading
            (heading of the connected road) and the end point. Also return
            determinant of that tells if point end is left or right of heading
            direction.
        '''
        # The center of the arc is the crossing point of line orthogonal to the
        # predecessor road in the connection point and the perpendicular
        # bisector of the connection between start and end point.
        p = point_start.to_2d()
        a = Vector((0.0, 1.0))
        a.rotate(Matrix.Rotation(heading_start, 2))
        q = 0.5 * (point_start + point_end).to_2d()
        b_normal = (point_start - point_end)
        b = Vector((-b_normal[1], b_normal[0]))
        if a.orthogonal() @ b != 0:
            # See https://mathepedia.de/Schnittpunkt.html for crossing point equation
            center = 1 / (a @ b.orthogonal()) * ((q @ b.orthogonal()) * a - (p @ a.orthogonal()) * b)
            radius = (center - p).length
            # Calculate determinant to know where to start drawing the arc {0, pi}
            vec_hdg = Vector((1.0, 0.0, 0.0))
            vec_hdg.rotate(Matrix.Rotation(heading_start, 4, 'Z'))
            det = Matrix([vec_hdg.to_2d(), (point_end - point_start).to_2d()]).transposed().determinant()
            return True, center, radius, det
        else:
            return False, 0, 0, 0
