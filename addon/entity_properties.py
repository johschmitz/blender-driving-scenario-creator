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


class DSC_entity_properties_vehicle(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='Entity', maxlen=0, options={'ANIMATABLE'})
    speed_initial: bpy.props.FloatProperty(default=50, min=0.1, max=500.0, step=100)
    color : bpy.props.FloatVectorProperty(subtype='COLOR_GAMMA', size=4,
        default=(0.9,0.1,0.1,1.0), min=0.0, max=1.0)

class DSC_entity_properties_pedestrian(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default='Entity', maxlen=0, options={'ANIMATABLE'})
    speed_initial: bpy.props.FloatProperty(default=4, min=0.1, max=500.0, step=50)
    color : bpy.props.FloatVectorProperty(subtype='COLOR_GAMMA', size=4,
        default=(0.9,0.1,0.1,1.0), min=0.0, max=1.0)