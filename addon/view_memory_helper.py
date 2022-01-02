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

from math import pi, cos


class view_memory_helper():

    # Lookup dictionary with the quaternions for all axis view directions
    axis_views = {
        (1.0, 0.0, 0.0, 0.0)                               : 'TOP',
        (0.0, 1.0, 0.0, 0.0)                               : 'BOTTOM',
        (0.7071067690849304, 0.7071067690849304, 0.0, 0.0) : 'FRONT',
        (0.0, 0.0, 0.7071067690849304, 0.7071067690849304) : 'BACK',
        (0.5, 0.5, -0.5, -0.5)                             : 'LEFT',
        (0.5, 0.5, 0.5, 0.5)                               : 'RIGHT',
    }

    def remember_view(self, context):
        '''
            Store the current view parameters given a context.
        '''
        view3d = context.space_data
        self.view_rotation_previous = view3d.region_3d.view_rotation.copy()
        self.view_perspective_previous = view3d.region_3d.view_perspective
        self.is_orthographic_side_view_previous = view3d.region_3d.is_orthographic_side_view
        self.axis_view = self.axis_views.get(tuple(self.view_rotation_previous), 'USER')

    def restore_view(self, context):
        '''
            Restore the view with the stored parameters to the context.
        '''
        if self.axis_view == 'USER':
            view3d = context.space_data
            view3d.region_3d.view_rotation = self.view_rotation_previous
            view3d.region_3d.view_perspective = self.view_perspective_previous
            view3d.region_3d.is_orthographic_side_view = self.is_orthographic_side_view_previous
        else:
            bpy.ops.view3d.view_axis(type=self.axis_view, align_active=False, relative=False)
