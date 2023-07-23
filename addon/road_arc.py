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

from . road_base import DSC_OT_road
from . geometry_arc import DSC_geometry_arc


class DSC_OT_road_arc(DSC_OT_road):
    bl_idname = "dsc.road_arc"
    bl_label = "Arc"
    bl_description = "Create an arc road"
    bl_options = {'REGISTER', 'UNDO'}

    object_type = 'road_arc'

    def __init__(self):
        self.geometry = DSC_geometry_arc()
