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

from .operator_snap_draw import DSC_OT_snap_draw
from . import helpers

from math import pi, sin, cos, acos, ceil


class DSC_OT_road_arc(DSC_OT_snap_draw):
    bl_idname = "dsc.road_arc"
    bl_label = "Arc"
    bl_description = "Create an arc road"
    bl_options = {'REGISTER', 'UNDO'}

    object_type = 'road_arc'

    def create_object(self, context):
        '''
            Create an arc road object
        '''
        # Try getting data for a new mesh
        valid, mesh, materials, params = self.get_mesh_and_params(context, for_stencil=False)
        if not valid:
            return None
        else:
            obj_id = helpers.get_new_id_opendrive(context)
            mesh.name = self.object_type + '_' + str(obj_id)
            obj = bpy.data.objects.new(mesh.name, mesh)
            obj.location = self.point_start
            helpers.link_object_opendrive(context, obj)

            # Paint some road markings
            helpers.assign_road_materials(obj)
            obj.data.polygons[0].material_index = helpers.get_material_index(obj, 'road_asphalt')
            obj.data.polygons[1].material_index = helpers.get_material_index(obj, 'road_mark')
            obj.data.polygons[2].material_index = helpers.get_material_index(obj, 'road_asphalt')
            obj.data.polygons[3].material_index = helpers.get_material_index(obj, 'road_mark')
            obj.data.polygons[4].material_index = helpers.get_material_index(obj, 'road_asphalt')
            obj.data.polygons[5].material_index = helpers.get_material_index(obj, 'road_mark')
            obj.data.polygons[6].material_index = helpers.get_material_index(obj, 'road_asphalt')

            helpers.select_activate_object(context, obj)

            # Remember connecting points for road snapping
            obj['cp_start'] = self.point_start
            obj['cp_end'] = params['point_end']

            # Set OpenDRIVE custom properties
            obj['id_xodr'] = obj_id
            obj['geometry'] = 'arc'
            obj['geometry_s'] = 0
            obj['geometry_x'] = self.point_start.x
            obj['geometry_y'] = self.point_start.y
            obj['geometry_hdg_start'] = self.heading_start
            obj['geometry_hdg_end'] = params['heading_end']
            obj['geometry_angle'] = params['angle']
            obj['geometry_curvature'] = params['curvature']

            obj['lanes_left_num'] = 2
            obj['lanes_right_num'] = 2
            obj['lanes_left_types'] = [ 'driving', 'border' ]
            obj['lanes_right_types'] = [ 'driving', 'border' ]
            obj['lanes_left_widths'] = [3.75, 0.20]
            obj['lanes_right_widths'] = [3.75, 0.20]
            obj['lanes_left_road_mark_types'] = ['solid', 'none']
            obj['lanes_right_road_mark_types'] = ['solid', 'none']
            obj['lane_center_road_mark_type'] = 'solid'

            return obj

    def get_mesh_and_params(self, context, for_stencil):
        '''
            Calculate and return the vertices, edges, faces and parameters to create a road mesh.
        '''
        if self.point_start == self.point_selected_end:
            self.report({"WARNING"}, "Start and end point can not be the same!")
            valid = False
            return valid, None, {}
        # We need to calculate the center and radius of the arc based on the
        # start point and the end point location
        valid, r_center, angle, determinant = self.get_arc_radius_angle_det(
            self.point_start, self.heading_start, self.point_selected_end)
        # If cursor is not in line with connection we get a solution and update the mesh
        if valid:
            if determinant > 0:
                startangle = 0
                offset = r_center
                curvature = 1/r_center
                if angle < 0:
                    # Limit angle to 180 degrees
                    endangle = pi
                else:
                    endangle = angle
                heading_end = self.heading_start + endangle
            else:
                startangle = pi
                offset = -r_center
                curvature = -1/r_center
                if angle > 0:
                    # Limit angle to 180 degrees
                    endangle = 0
                else:
                    endangle = angle + pi
                heading_end = self.heading_start + pi + endangle
            point_end = Vector((cos(endangle - pi/2) * r_center,
                                sin(endangle - pi/2) * r_center + offset,
                                0.0))
            mat_rotation = Matrix.Rotation(self.heading_start, 3, 'Z')
            point_end.rotate(mat_rotation)
            point_end = point_end + self.point_start
            # Calculate adaptive polyline steps based on
            # https://stackoverflow.com/questions/11774038/how-to-render-a-circle-with-as-few-vertices-as-possible
            width_lane = 3.75
            width_marking = 0.12
            width_border = 0.2
            error_max = 0.25
            steps = ceil(2 * pi / acos(2 * (1 - error_max / max(2 * width_lane, r_center))**2 - 1))
            angle_step = (endangle - startangle) / steps
            radii = [r_center + width_lane + width_border,
                     r_center + width_lane + width_marking/2,
                     r_center + width_lane - width_marking/2,
                     r_center + width_marking / 2,
                     r_center - width_marking / 2,
                     r_center - width_lane + width_marking/2,
                     r_center - width_lane - width_marking/2,
                     r_center - width_lane - width_border]
            # Vertices
            vertices = []
            for r in radii:
                x = cos(startangle - pi/2) * r
                y = sin(startangle - pi/2) * r + offset
                vertices.append([x, y, 0])
                j = 1
                while j < steps:
                    t = angle_step * j
                    x = cos(t + startangle - pi/2) * r
                    y = sin(t + startangle - pi/2) * r + offset
                    vertices.append([x, y, 0])
                    j += 1
                x = cos(endangle - pi/2) * r
                y = sin(endangle - pi/2) * r + offset
                vertices.append([x, y, 0])
            # Edges
            edges = []
            # How many vertices in single arc
            num_single = int(len(vertices) / len(radii))
            for i in range(len(radii)):
                for j in range(num_single-1) :
                    edges.append([num_single * i + j, num_single * i + j + 1])
            edges_start = [ [ v + o for v in [0, num_single] ] for o in range(0, 7*num_single, num_single) ]
            edges_end = [ [ v + o for v in [num_single-1, 2*num_single-1] ] for o in range(0, 7*num_single, num_single) ]
            edges = edges + edges_start
            edges = edges + edges_end
            # Faces
            if for_stencil:
                faces = []
            else:
                # Make sure we define faces counterclockwise for correct normals
                if determinant > 0:
                    faces = [  [v + o for v in range(steps + 1)] + \
                               [v + o for v in range(2 * steps + 1, steps, -1)] \
                             for o in range(0, 7 * num_single, num_single)
                            ]
                else:
                    faces = [  [v + o for v in range(steps + 1, 2 * steps + 2)] + \
                               [v + o for v in range(steps, -1, -1)] \
                             for o in range(0, 7*num_single, num_single)
                            ]
            # Create blender mesh
            mesh = bpy.data.meshes.new('temp')
            mesh.from_pydata(vertices, edges, faces)
            # Rotate and translate mesh according to selected start point
            self.transform_mesh_wrt_start(mesh, self.point_start, self.heading_start, self.snapped_start)
            road_parameters = {'point_start': self.point_start,
                               'heading_start': self.heading_start,
                               'point_end': point_end,
                               'heading_end': heading_end,
                               'angle': angle,
                               'curvature': curvature}
            # TODO implement material dictionary for the faces
            materials = {}
            return True, mesh, materials, road_parameters
        else:
            return False, None, {}, {}

    def get_arc_radius_angle_det(self, point_start, heading_start, point_end):
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
            determinant = Matrix([vec_hdg.to_2d(), (point_end - point_start).to_2d()]).transposed().determinant()
            angle = (point_end.to_2d() - center).angle_signed(point_start.to_2d() - center)
            return True, radius, angle, determinant
        else:
            return False, 0, 0, 0
