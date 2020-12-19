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
from pathlib import Path

class DSC_OT_export(bpy.types.Operator):
    bl_idname = "dsc.export_driving_scenario"
    bl_label = "Export driving scenario"
    bl_description = "Export driving scenario as OpenDRIVE, OpenSCENARIO and Mesh (e.g. FBX, glTF 2.0)"

    filepath: bpy.props.StringProperty(
        name="File Path", description="Target filename for OpenDRIVE(.xosc) and OpenSCENARIO(.xodr)")
    
    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        xodr_name = Path(self.filepath).with_suffix('.xodr')
        file = open(xodr_name, 'w')
        file.write("Hello World " + context.object.name)
        xosc_name = Path(self.filepath).with_suffix('.xosc')
        file = open(xosc_name, 'w')
        file.write("Hello World " + context.object.name)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
