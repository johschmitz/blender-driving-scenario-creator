"""Trailer placement operator and geometry for standalone trailer entities."""

import bpy

from .entity import entity as EntityMesh
from .entity_base import DSC_OT_entity
from .entity_vehicle import DSC_OT_entity_vehicle, VEHICLE_GEOMETRY_DIMENSIONS


TRAILER_CATEGORY_ITEMS = (
    ('semiTrailer', 'Semi-trailer', 'Create a semi-trailer entity'),
)


class DSC_OT_entity_trailer(DSC_OT_entity):
    """Place a trailer independently of the tractor unit."""

    bl_idname = 'dsc.entity_trailer'
    bl_label = 'Trailer'
    bl_description = 'Place a trailer entity object'
    bl_options = {'REGISTER', 'UNDO'}

    entity_type = 'vehicle'
    entity_subtype = 'semiTrailer'
    _build_wheel_mesh = DSC_OT_entity_vehicle._build_wheel_mesh

    trailer_category: bpy.props.EnumProperty(
        name='Trailer category',
        description='Trailer type to place',
        items=TRAILER_CATEGORY_ITEMS,
        default='semiTrailer',
    )

    def invoke(self, context, event):
        self.entity_subtype = self.trailer_category
        return super().invoke(context, event)

    def get_vertices_edges_faces(self):
        mesh_data = DSC_OT_entity_vehicle._get_semi_trailer_mesh()
        vertices, edges, faces, self.face_materials = mesh_data
        config = VEHICLE_GEOMETRY_DIMENSIONS['semiTrailer']
        origin_shift = config['source_origin_x'] - config['origin_x']
        vertices = [(x + origin_shift, y, z) for x, y, z in vertices]
        return vertices, edges, faces

    def get_face_materials(self):
        return getattr(self, 'face_materials', [])

    def get_wheel_configs(self):
        wheels = DSC_OT_entity_vehicle.get_wheel_configs(
            self, subtype='semiTrailer')

        config = VEHICLE_GEOMETRY_DIMENSIONS['semiTrailer']
        first_axle_x = config['wheel_positions'][0][1]
        origin_shift = config['origin_x'] - first_axle_x
        return [
            (name, (position[0] + origin_shift, position[1], position[2]),
             vertices, edges, faces)
            for name, position, vertices, edges, faces in wheels
        ]

    def create_object_model(self, context):
        self.entity = EntityMesh(
            context, self.entity_type, self.entity_subtype,
            self.get_vertices_edges_faces,
            get_wheel_configs=self.get_wheel_configs,
            get_face_materials=self.get_face_materials,
        )
