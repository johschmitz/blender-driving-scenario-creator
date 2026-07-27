from types import MethodType, SimpleNamespace

from addon.entity_pedestrian import DSC_OT_entity_pedestrian


def pedestrian_probe(subtype):
    pedestrian = SimpleNamespace(entity_subtype=subtype)
    for name, descriptor in DSC_OT_entity_pedestrian.__dict__.items():
        if isinstance(descriptor, staticmethod):
            setattr(pedestrian, name, descriptor.__func__)
        elif callable(descriptor):
            setattr(pedestrian, name, MethodType(descriptor, pedestrian))
        elif not name.startswith('__') and not hasattr(pedestrian, name):
            try:
                setattr(pedestrian, name, descriptor)
            except (AttributeError, TypeError):
                pass
    return pedestrian


def test_pedestrians_have_separate_legs_hands_eyes_hair_and_feet():
    for subtype, scale in (('adult', 1.0), ('child', 0.72)):
        pedestrian = pedestrian_probe(subtype)
        vertices, _edges, faces = pedestrian.get_vertices_edges_faces()
        materials = pedestrian.get_face_materials()
        assert len(materials) == len(faces)

        assignments = [assignment[0] if assignment else None
                       for assignment in materials]
        assert assignments.count('pedestrian_legs') == 12
        assert assignments.count('pedestrian_skin') == 24
        assert assignments.count('pedestrian_hair') == 6
        assert assignments.count('pedestrian_eyes') == 12
        assert assignments.count('pedestrian_shoes') == 12

        material_vertices = {}
        for face, assignment in zip(faces, assignments):
            if assignment:
                material_vertices.setdefault(assignment, []).extend(
                    vertices[index] for index in face)

        eye_vertices = material_vertices['pedestrian_eyes']
        assert min(vertex[0] for vertex in eye_vertices) > 0.09 * scale
        assert max(vertex[0] for vertex in eye_vertices) > 0.10 * scale
        eye_y = {round(vertex[1] / scale, 3) for vertex in eye_vertices}
        assert min(eye_y) < -0.04 and max(eye_y) > 0.04

        hair_vertices = material_vertices['pedestrian_hair']
        hair_width_x = max(vertex[0] for vertex in hair_vertices) - min(
            vertex[0] for vertex in hair_vertices)
        hair_width_y = max(vertex[1] for vertex in hair_vertices) - min(
            vertex[1] for vertex in hair_vertices)
        assert abs(hair_width_x - hair_width_y) < 1e-6
        assert max(vertex[2] for vertex in hair_vertices) > 1.75 * scale
        shoe_vertices = material_vertices['pedestrian_shoes']
        shoe_length = (max(vertex[0] for vertex in shoe_vertices)
                   - min(vertex[0] for vertex in shoe_vertices))
        assert abs(shoe_length - 0.22 * scale) < 1e-6
        assert abs(min(vertex[2] for vertex in shoe_vertices)) < 1e-6
        assert abs(max(vertex[2] for vertex in shoe_vertices)
               - 0.045 * scale) < 1e-6
        leg_vertices = material_vertices['pedestrian_legs']
        assert abs(min(vertex[2] for vertex in leg_vertices)
               - 0.045 * scale) < 1e-6

        hand_vertices = [
            vertex for vertex in material_vertices['pedestrian_skin']
            if 0.20 * scale < abs(vertex[1]) < 0.36 * scale
            and vertex[2] < 0.80 * scale
        ]
        assert hand_vertices
        assert max(vertex[2] for vertex in hand_vertices) <= 0.78 * scale + 1e-6
