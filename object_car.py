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

class DSC_OT_object_car(bpy.types.Operator):
    bl_idname = "dsc.object_car"
    bl_label = "Car"
    bl_description = "Place a car object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        meshes = bpy.data.meshes
        objects = bpy.data.objects

        bm = bmesh.new()
        

        # Vertices
        verts = []
        verts.append(bm.verts.new((2.0, 1.0, 0.0)))
        verts.append(bm.verts.new((-2.0, 1.0, 0.0)))
        verts.append(bm.verts.new((-2.0, -1.0, 0.0)))
        verts.append(bm.verts.new((2.0, -1.0, 0.0)))
        verts.append(bm.verts.new((2.0, 1.0, 1.0)))
        verts.append(bm.verts.new((-2.0, 1.0, 1.0)))
        verts.append(bm.verts.new((-2.0, -1.0, 1.0)))
        verts.append(bm.verts.new((2.0, -1.0, 1.0)))

        # Edges
        bm.edges.new([verts[0], verts[1]])
        bm.edges.new([verts[1], verts[2]])
        bm.edges.new([verts[2], verts[3]])
        bm.edges.new([verts[3], verts[0]])
        bm.edges.new([verts[4], verts[5]])
        bm.edges.new([verts[5], verts[6]])
        bm.edges.new([verts[6], verts[7]])
        bm.edges.new([verts[7], verts[4]])
        bm.edges.new([verts[0], verts[4]])
        bm.edges.new([verts[1], verts[5]])
        bm.edges.new([verts[2], verts[6]])
        bm.edges.new([verts[3], verts[7]])

        mesh = meshes.new('object_car')
        obj = objects.new('object_car', mesh)

        # OpenSCENARIO custom properties
        obj['xosc'] = {'asdf':"asdf"}

        if not 'OpenSCENARIO' in bpy.data.collections:
            collection = bpy.data.collections.new('OpenSCENARIO')
            scene.collection.children.link(collection)

        bpy.data.collections['OpenSCENARIO'].objects.link(obj)

        bm.to_mesh(mesh)
        bm.free()

        return {'FINISHED'}