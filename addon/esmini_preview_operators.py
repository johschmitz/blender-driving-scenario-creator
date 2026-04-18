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

from . import esmini_preview


class DSC_OT_esmini_preview_start(bpy.types.Operator):
    bl_idname = 'dsc.esmini_preview_start'
    bl_label = 'Start / Pause'
    bl_description = 'Start preview if stopped, otherwise toggle pause/resume'

    @classmethod
    def poll(cls, context):
        del cls
        del context
        return True

    def execute(self, context):
        try:
            action = esmini_preview.toggle_preview_play_pause(context)
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        if action == 'started':
            self.report({'INFO'}, 'esmini preview started.')
        elif action == 'paused':
            self.report({'INFO'}, 'esmini preview paused.')
        else:
            self.report({'INFO'}, 'esmini preview resumed.')
        return {'FINISHED'}


class DSC_OT_esmini_preview_stop(bpy.types.Operator):
    bl_idname = 'dsc.esmini_preview_stop'
    bl_label = 'Stop Preview'
    bl_description = 'Stop running esmini preview and restore entity transforms'

    @classmethod
    def poll(cls, context):
        del cls
        del context
        return esmini_preview.is_preview_active()

    def execute(self, context):
        del context
        esmini_preview.stop_preview_session(restore=True, reason='')
        self.report({'INFO'}, 'esmini preview stopped.')
        return {'FINISHED'}


class DSC_OT_esmini_preview_step(bpy.types.Operator):
    bl_idname = 'dsc.esmini_preview_step'
    bl_label = 'Step'
    bl_description = 'Advance preview by one simulation step and one frame'

    @classmethod
    def poll(cls, context):
        del cls
        del context
        return True

    def execute(self, context):
        try:
            esmini_preview.step_preview_session_once(context)
        except Exception as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        self.report({'INFO'}, 'Preview advanced by one step.')
        return {'FINISHED'}


class DSC_OT_esmini_open_preferences(bpy.types.Operator):
    bl_idname = 'dsc.esmini_open_preferences'
    bl_label = 'Preview Settings'
    bl_description = 'Open Add-on Preferences to configure esmini library path'

    def execute(self, context):
        del context
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        bpy.ops.preferences.addon_show(module=__package__)
        return {'FINISHED'}
