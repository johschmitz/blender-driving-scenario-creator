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

from . modal_trajectory_base import DSC_OT_modal_trajectory_base
from . import helpers


class DSC_OT_trajectory_polyline(DSC_OT_modal_trajectory_base):
    bl_idname = 'dsc.trajectory_polyline'
    bl_label = 'Polyline'
    bl_description = 'Create a polyline based trajectory'
    bl_options = {'REGISTER', 'UNDO'}

    def create_trajectory_temp(self, context):
        self.trajectory = bpy.data.objects.get('trajectory_temp')
        if self.trajectory is not None:
            if context.scene.objects.get('trajectory_temp') is None:
                context.scene.collection.objects.link(self.trajectory)
        else:
            mesh = self.get_mesh()
            self.trajectory = bpy.data.objects.new('trajectory_temp', mesh)
            helpers.link_object_openscenario(context, self.trajectory, subcategory='trajectories')
        # Shift origin to start point below vehicle
        self.trajectory.location = self.point_start

    def set_xosc_properties(self):
        self.trajectory['dsc_category'] = 'OpenSCENARIO'
        self.trajectory['dsc_type'] = 'trajectory'
        self.trajectory['dsc_subtype'] = 'polyline'

        self.trajectory['owner_name'] = self.trajectory_owner_name

    def update_trajectory(self, context):
        mesh = self.get_mesh()
        helpers.replace_mesh(self.trajectory, mesh)

    def get_mesh(self):
        vertices = [point - self.point_start for point in self.trajectory_points]
        edges = []
        for idx in range(len(vertices)-1):
            edges.append([idx, idx+1])
        faces = []

        mesh = bpy.data.meshes.new('trajectory')
        mesh.from_pydata(vertices, edges, faces)
        return mesh
