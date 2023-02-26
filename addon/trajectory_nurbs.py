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


class DSC_OT_trajectory_nurbs(DSC_OT_modal_trajectory_base):
    bl_idname = "dsc.trajectory_nurbs"
    bl_label = "NURBS"
    bl_description = "Create a NURBS based trajectory"
    bl_options = {'REGISTER', 'UNDO'}

    def create_trajectory_temp(self, context):
        self.trajectory = bpy.data.objects.get('trajectory_temp')
        if self.trajectory is not None:
            if context.scene.objects.get('trajectory_temp') is None:
                context.scene.collection.objects.link(self.trajectory)
        else:
            curve = self.get_curve()
            self.trajectory = bpy.data.objects.new('trajectory_temp', curve)
            helpers.link_object_openscenario(context, self.trajectory, subcategory='trajectories')
        # Shift origin to start point below vehicle
        self.trajectory.location = self.point_start

    def set_xosc_properties(self):
        self.trajectory['dsc_category'] = 'OpenSCENARIO'
        self.trajectory['dsc_type'] = 'trajectory'
        self.trajectory['dsc_subtype'] = 'nurbs'

        self.trajectory['owner_name'] = self.trajectory_owner_name

    def update_trajectory(self, context):
        curve = self.get_curve()
        self.trajectory.data = curve

    def get_curve(self):
        curve = bpy.data.curves.new('curve_nurbs', 'CURVE')
        curve.dimensions = '3D'

        nurbs = curve.splines.new('NURBS')
        nurbs.use_endpoint_u = True
        nurbs.points.add(len(self.trajectory_points)-1)
        for idx, point in enumerate(self.trajectory_points):
            x, y, z = point - self.point_start
            nurbs.points[idx].co = (x, y, z, 1)
        nurbs.order_u = 3
        nurbs.resolution_u = 16
        return curve
