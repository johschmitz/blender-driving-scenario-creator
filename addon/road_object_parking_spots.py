import bpy
from mathutils import Matrix, Vector

from . import helpers


class road_object_parking_spots:

    def __init__(self, context, road_object_type):
        self.context = context
        self.road_object_type = road_object_type

    def create_object_3d(self, context, params_input, id_road, road_obj, geometry):
        valid, mesh, matrix_world, materials = self.update_params_get_mesh(
            context, params_input, road_obj, geometry, wireframe=False)
        if not valid:
            return None
        id_obj = helpers.get_new_id_opendrive(context)
        obj_name = self.road_object_type + '_' + str(id_obj)
        mesh.name = obj_name
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.matrix_world = matrix_world
        helpers.link_object_opendrive(context, obj)
        helpers.select_activate_object(context, obj)
        helpers.assign_materials(obj)
        for polygon in obj.data.polygons:
            polygon.material_index = helpers.get_material_index(obj, 'road_mark_white')
        context.area.spaces.active.shading.color_type = 'TEXTURE'
        obj['dsc_category'] = 'OpenDRIVE'
        obj['dsc_type'] = 'road_object'
        obj['road_object_type'] = self.road_object_type
        obj['id_odr'] = id_obj
        obj['id_road'] = id_road
        obj['position_s'] = params_input['point_s']
        obj['position_t'] = params_input['point_t']
        obj['width'] = params_input['lane_width']
        obj['length'] = params_input['spot_length']
        obj['num_spots'] = params_input['num_spots']
        obj['lane_side'] = params_input['lane_side']
        obj['lane_index'] = params_input['lane_index']
        obj['lane_inset'] = params_input['lane_inset']
        obj['zOffset'] = 0.0
        obj['height'] = 0.01
        obj['catalog_type'] = 294
        obj['catalog_subtype'] = None
        obj['value'] = 0
        return obj

    def update_params_get_mesh(self, context, params_input, road_obj, geometry, wireframe):
        if not params_input.get('parking_lane_valid', False):
            return False, None, Matrix.Identity(4), {'road_mark_white': ()}
        vertices = []
        faces = []
        marking_width = 0.12
        end_marking_width = marking_width
        lane_inset = params_input['lane_inset']
        lane_side = params_input['lane_side']
        lane_index = params_input['lane_index']
        spot_length = params_input['spot_length']
        num_spots = params_input['num_spots']
        total_length = road_obj['geometry_total_length']
        center_s = params_input['point_s']
        start_s = max(0.0, center_s - num_spots * spot_length / 2.0)
        end_s = min(total_length, start_s + num_spots * spot_length)
        start_s = max(0.0, end_s - num_spots * spot_length)

        def lane_edges(s):
            widths_start = road_obj['lanes_left_widths_start'] if lane_side == 'left' else road_obj['lanes_right_widths_start']
            widths_end = road_obj['lanes_left_widths_end'] if lane_side == 'left' else road_obj['lanes_right_widths_end']
            widths = helpers._interpolate_lane_widths(widths_start, widths_end, s, total_length)
            lane_offset = helpers.calculate_lane_offset(s, road_obj['lane_offset_coefficients'], total_length)
            width = widths[lane_index]
            if lane_side == 'left':
                inner = lane_offset + sum(widths[:lane_index])
                return inner + lane_inset, inner + width - lane_inset
            inner = lane_offset - sum(widths[:lane_index])
            return inner - lane_inset, inner - width + lane_inset

        def point_at(s, t):
            local = geometry.sample_cross_section(s, [t], False)[0][0]
            return geometry.matrix_world @ Vector(local)

        def add_strip(point_a, point_b, width, lateral):
            direction = (point_b - point_a).to_2d()
            if direction.length == 0.0:
                return
            normal = Vector((-direction.y, direction.x)).normalized() * width / 2.0
            if lateral:
                normal = -normal
            base = len(vertices)
            vertices.extend([
                (point_a.x + normal.x, point_a.y + normal.y, point_a.z + 0.005),
                (point_a.x - normal.x, point_a.y - normal.y, point_a.z + 0.005),
                (point_b.x - normal.x, point_b.y - normal.y, point_b.z + 0.005),
                (point_b.x + normal.x, point_b.y + normal.y, point_b.z + 0.005),
            ])
            if lateral:
                faces.append((base, base + 3, base + 2, base + 1))
            else:
                faces.append((base, base + 1, base + 2, base + 3))

        for idx in range(num_spots):
            s0 = start_s + idx * spot_length
            s1 = min(start_s + (idx + 1) * spot_length, end_s)
            t0, t1 = lane_edges(s0)
            t2, t3 = lane_edges(s1)
            side_start_s = min(s0 + end_marking_width / 2.0, s1)
            side_end_s = max(s1 - end_marking_width / 2.0, s0)
            side_t0, side_t1 = lane_edges(side_start_s)
            side_t2, side_t3 = lane_edges(side_end_s)
            inner_side_start = point_at(side_start_s, side_t0)
            outer_side_start = point_at(side_start_s, side_t1)
            inner_side_end = point_at(side_end_s, side_t2)
            outer_side_end = point_at(side_end_s, side_t3)
            end_direction_start = 1.0 if t1 >= t0 else -1.0
            end_direction_end = 1.0 if t3 >= t2 else -1.0
            inner_start = point_at(s0, t0 - end_direction_start * marking_width / 2.0)
            outer_start = point_at(s0, t1 + end_direction_start * marking_width / 2.0)
            inner_end = point_at(s1, t2 - end_direction_end * marking_width / 2.0)
            outer_end = point_at(s1, t3 + end_direction_end * marking_width / 2.0)
            add_strip(inner_side_start, inner_side_end, marking_width, False)
            add_strip(outer_side_start, outer_side_end, marking_width, False)
            add_strip(inner_start, outer_start, end_marking_width, True)
            add_strip(inner_end, outer_end, end_marking_width, True)

        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, [], faces)
        return True, mesh, Matrix.Identity(4), {'road_mark_white': tuple(range(len(faces)))}