"""Connection anchors and snapping helpers for tow vehicles and trailers."""

import xml.etree.ElementTree as ET

import bpy
from mathutils import Matrix, Vector


CONNECTION_SNAP_DISTANCE = 1.0


# OpenSCENARIO uses the towing vehicle's TrailerHitch and the trailer's
# TrailerCoupler. Coordinates are relative to each Blender entity origin.
ENTITY_CONNECTION_POINTS = {
    'heavyTruck': {
        'element': 'TrailerHitch',
        'x': 3.15 - 2.60,
        'z': (0.96 + 1.20) * 0.5,
        'partner': 'semiTrailer',
    },
    'semiTrailer': {
        'element': 'TrailerCoupler',
        # Trailer mesh is converted from the shared tractor datum to the
        # standalone trailer datum in DSC_OT_entity_trailer.
        'x': 3.15 - 2.60 + 2.60 - (-5.25),
        'z': (0.96 + 1.20) * 0.5,
        'partner': 'heavyTruck',
    },
}


def get_connection_point_world(obj):
    """Return (element name, world-space anchor) for a connectable entity."""
    point = ENTITY_CONNECTION_POINTS.get(obj.get('entity_subtype'))
    if point is None:
        return None
    local_point = Vector((point['x'], 0.0, point['z']))
    return point['element'], obj.matrix_world @ local_point


def _connection_anchor_world(position, heading, normal, entity_subtype):
    point = ENTITY_CONNECTION_POINTS.get(entity_subtype)
    if point is None:
        return None
    normal_rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(
        Vector(normal)).to_matrix().to_4x4()
    heading_rotation = Matrix.Rotation(heading, 4, 'Z')
    local_point = Vector((point['x'], 0.0, point['z'], 1.0))
    return (Matrix.Translation(position) @ normal_rotation @ heading_rotation
            @ local_point).to_3d()


def get_entity_position_from_connection_anchor(anchor_world, heading, normal,
                                              entity_subtype):
    """Return the entity origin that keeps its connection anchor fixed."""
    point = ENTITY_CONNECTION_POINTS.get(entity_subtype)
    if point is None:
        return None
    normal_rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(
        Vector(normal).normalized()).to_matrix()
    heading_rotation = Matrix.Rotation(heading, 3, 'Z')
    local_anchor = Vector((point['x'], 0.0, point['z']))
    anchor_offset = normal_rotation @ heading_rotation @ local_anchor
    return Vector(anchor_world) - anchor_offset


def get_connection_snap(context, candidate_position, candidate_heading,
                        candidate_normal, entity_subtype,
                        max_distance=CONNECTION_SNAP_DISTANCE,
                        moving_obj=None):
    """Find a compatible world-space anchor within the snap radius in meters."""
    point = ENTITY_CONNECTION_POINTS.get(entity_subtype)
    if point is None:
        return None

    candidate_anchor = _connection_anchor_world(
        candidate_position, candidate_heading, candidate_normal,
        entity_subtype)

    scenario_collection = bpy.data.collections.get('OpenSCENARIO')
    if scenario_collection is None:
        return None
    entity_collection = scenario_collection.children.get('entities')
    if entity_collection is None:
        return None

    best = None
    best_distance = max_distance
    for obj in entity_collection.objects:
        if obj.parent is not None or obj.get('dsc_type') != 'entity':
            continue
        if obj.get('entity_subtype') != point['partner']:
            continue
        if (entity_subtype == 'heavyTruck'
                and obj.get('towing_vehicle_entity')
                and obj.get('towing_vehicle_entity')
                != getattr(moving_obj, 'name', None)):
            continue
        if (entity_subtype == 'semiTrailer'
                and obj.get('trailer_entity')
                and obj.get('trailer_entity')
                != getattr(moving_obj, 'name', None)):
            continue
        anchor = get_connection_point_world(obj)
        if anchor is None:
            continue
        _element, world_point = anchor
        distance = (world_point - candidate_anchor).length
        if distance < best_distance:
            best = (obj, world_point)
            best_distance = distance
    return best


def record_entity_connection(placed_obj, target_obj):
    """Store a bidirectional trailer/towing-vehicle entity-name relation."""
    if target_obj is None:
        return
    subtype = placed_obj.get('entity_subtype')
    target_subtype = target_obj.get('entity_subtype')
    if subtype == 'semiTrailer' and target_subtype == 'heavyTruck':
        target_obj['trailer_entity'] = placed_obj.name
        placed_obj['towing_vehicle_entity'] = target_obj.name
    elif subtype == 'heavyTruck' and target_subtype == 'semiTrailer':
        placed_obj['trailer_entity'] = target_obj.name
        target_obj['towing_vehicle_entity'] = placed_obj.name


def clear_entity_connection(obj):
    """Remove an entity's connection and its matching reference, if present."""
    for own_key, other_key in (
            ('trailer_entity', 'towing_vehicle_entity'),
            ('towing_vehicle_entity', 'trailer_entity')):
        other_name = obj.get(own_key)
        if not other_name:
            continue
        other = bpy.data.objects.get(other_name)
        if other is not None and other.get(other_key) == obj.name:
            del other[other_key]
        del obj[own_key]


def order_entities_for_scenario(entities):
    """Put referenced trailer objects before the towing vehicles that use them.

    esmini resolves TrailerRef while parsing each ScenarioObject, so the
    referenced trailer must already have been declared in the Entities list.
    """
    pending = list(entities)
    ordered = []
    while pending:
        pending_names = {obj.name for obj in pending}
        ready = [
            obj for obj in pending
            if obj.get('trailer_entity') not in pending_names
        ]
        if not ready:
            # Preserve deterministic output for malformed cyclic references;
            # normal connection validation/export handles their diagnostics.
            ready = [pending[0]]
        for obj in ready:
            ordered.append(obj)
            pending.remove(obj)
    return ordered


def add_connections_to_vehicle_catalog(catalog_path, entity_records):
    """Add standard hitch/coupler points and entity trailer references."""
    try:
        tree = ET.parse(str(catalog_path))
    except (OSError, ET.ParseError):
        return False

    vehicle_elements = {
        element.get('name'): element
        for element in tree.getroot().iter('Vehicle')
        if element.get('name')
    }
    records_by_name = {record[0]: record[1:] for record in entity_records}
    for name, (subtype, trailer_name) in records_by_name.items():
        vehicle_element = vehicle_elements.get(name)
        connection = ENTITY_CONNECTION_POINTS.get(subtype)
        if vehicle_element is None or connection is None:
            continue

        for element_name in ('TrailerHitch', 'TrailerCoupler', 'Trailer'):
            for existing in vehicle_element.findall(element_name):
                vehicle_element.remove(existing)

        ET.SubElement(vehicle_element, connection['element'], {
            'dx': format(connection['x'], '.8g'),
            'dz': format(connection['z'], '.8g'),
        })
        if subtype == 'heavyTruck' and trailer_name in vehicle_elements:
            trailer = ET.SubElement(vehicle_element, 'Trailer')
            ET.SubElement(trailer, 'TrailerRef', {'entityRef': trailer_name})

    tree.write(str(catalog_path), encoding='utf-8', xml_declaration=True)
    return True
