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

class DSC_OT_trajectory_waypoints(bpy.types.Operator):
    bl_idname = "dsc.trajectory_waypoints"
    bl_label = "Waypoints"
    bl_description = "Place a waypoints trajectory"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        meshes = scene.meshes
        objects = scene.objects

        bm = bmesh.new()
        verts = [bm.verts.new((0, 0, z)) for z in range(5)]

        for i in range(len(verts)-1):
            bm.edges.new([verts[i], verts[i+1]])

        me = meshes.new('placeholder_mesh')
        mesh_obj = objects.new('polyline', me)

        if not "OpenSCENARIO" in scene.collections:
            collection = scene.collections.new("OpenSCENARIO")
            scene.collection.children.link(collection)

        scene.collections['OpenSCENARIO'].objects.link(mesh_obj)

        bm.to_mesh(me)
        bm.free()

        return {'FINISHED'}