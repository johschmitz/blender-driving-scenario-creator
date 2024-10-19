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


def callback_selected(self, context):
    self.update_selected(context)

class DSC_road_object_traffic_light_properties(bpy.types.PropertyGroup):

    pole_height: bpy.props.FloatProperty(default=4.0, min=1.0, max=10.0, step=10)
    height: bpy.props.FloatProperty(default=1.5, min=0.5, max=3.0, step=10)

    # A lock for deactivating callbacks
    lock_signs: bpy.props.BoolProperty(default=False)
