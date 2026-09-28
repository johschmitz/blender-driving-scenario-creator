import bmesh
import bpy

from collections import Counter

from addon.entity_car import DSC_OT_entity_car


def test_car_cut_regions_are_one_connected_manifold_mesh():
    car = DSC_OT_entity_car
    vertices, edges, faces = car.get_vertices_edges_faces(car)
    face_materials = car.get_face_materials(car)
    mesh = bpy.data.meshes.new('CarTopologyTest')
    bm = bmesh.new()
    try:
        mesh.from_pydata(vertices, edges, faces)
        mesh.update()
        assert len(mesh.polygons) == len(face_materials)

        bm.from_mesh(mesh)
        assert all(len(edge.link_faces) == 2 for edge in bm.edges)
        assert all(edge.is_contiguous for edge in bm.edges)
        assert bm.calc_volume(signed=True) > 0
        remaining = set(bm.verts)
        components = 0
        while remaining:
            components += 1
            stack = [remaining.pop()]
            while stack:
                vertex = stack.pop()
                for edge in vertex.link_edges:
                    other = edge.other_vert(vertex)
                    if other in remaining:
                        remaining.remove(other)
                        stack.append(other)
        assert components == 1

        regions = Counter(name for assignment in face_materials if assignment
                          for name, _color in [assignment])
        assert regions == {
            'glass': 6,
            'headlight': 2,
            'taillight': 2,
            'indicator': 4,
        }

        wheel_x = {name: position[0]
                   for name, position, *_rest in car.get_wheel_configs(car)}
        assert wheel_x['wheel_rl'] == 0.0
        assert wheel_x['wheel_rr'] == 0.0
        assert wheel_x['wheel_fl'] == 2.9
        assert wheel_x['wheel_fr'] == 2.9
    finally:
        bm.free()
        bpy.data.meshes.remove(mesh)