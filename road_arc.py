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

class DSC_OT_road_arc(bpy.types.Operator):
    bl_idname = "dsc.road_arc"
    bl_label = "Arc"
    bl_description = "Place an arc road"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def add_object(self, context, event):
        scene = context.scene
        meshes = bpy.data.meshes
        objects = bpy.data.objects

        bm = bmesh.new()

        # Vertices
        verts = []
        verts.append(bm.verts.new((4.0, 4.0, 0.0)))
        verts.append(bm.verts.new((-4.0, 4.0, 0.0)))
        verts.append(bm.verts.new((-4.0, -4.0, 0.0)))
        verts.append(bm.verts.new((4.0, -4.0, 0.0)))

        # Edges
        for i in range(len(verts)-1):
            bm.edges.new([verts[i], verts[i+1]])
        bm.edges.new([verts[-1], verts[0]])

        # Faces
        bm.faces.new(bm.verts)

        mesh = meshes.new('road_straight')
        obj = objects.new('road_straight', mesh)

        # OpenDRIVE custom properties
        obj['xodr'] = {'asdf':"asdf"}

        if not 'OpenDRIVE' in bpy.data.collections:
            collection = bpy.data.collections.new('OpenDRIVE')
            scene.collection.children.link(collection)

        bpy.data.collections['OpenDRIVE'].objects.link(obj)

        bm.to_mesh(mesh)
        bm.free()

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':  # Apply
            self.value = event.mouse_x
        elif event.type == 'LEFTMOUSE':  # Confirm
            self.add_object(context, event)
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            context.object.region.x = self.init_loc_x
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.init_loc_x = context.region.x
        self.value = event.mouse_x

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
