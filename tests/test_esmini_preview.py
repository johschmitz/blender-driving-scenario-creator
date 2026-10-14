from types import SimpleNamespace

from addon.esmini_preview import (
    EsminiBindings,
    _build_fixed_object_index_mapping,
    _calibrate_coordinate_mapping,
    _resolve_object_for_state,
)


class FakeBindings:
    def __init__(self, names_by_id, ids_by_index):
        self.names_by_id = names_by_id
        self.ids_by_index = ids_by_index
        self.fn_get_object_name = self.get_object_name

    def get_number_of_objects(self):
        return len(self.ids_by_index)

    def get_object_id(self, index):
        return self.ids_by_index[index]

    def get_object_state(self, object_id):
        return SimpleNamespace(x=float(object_id), y=0.0, z=0.0)

    def get_object_name(self, object_id, fallback_name=''):
        return self.names_by_id.get(object_id, fallback_name)


def make_session(bindings, named_objects):
    object_states = [
        SimpleNamespace(
            name=name,
            object_ref=SimpleNamespace(location=SimpleNamespace(x=x, y=0.0, z=0.0)),
        )
        for name, x in named_objects.items()
    ]
    return SimpleNamespace(
        bindings=bindings,
        object_states=object_states,
        objects_by_name={state.name: state.object_ref for state in object_states},
        ordered_names=[state.name for state in object_states],
        object_name_by_index={},
        object_index_by_name={},
        xy_map=(1.0, 0.0, 0.0, 1.0),
    )


def test_esmini_get_object_name_passes_object_id():
    bindings = EsminiBindings.__new__(EsminiBindings)
    calls = []
    bindings.fn_get_object_name = lambda object_id: calls.append(object_id) or b'truck'

    assert bindings.get_object_name(37) == 'truck'
    assert calls == [37]


def test_preview_maps_states_by_id_resolved_name_not_object_order():
    bindings = FakeBindings(
        names_by_id={101: 'trailer', 7: 'truck'},
        ids_by_index=[101, 7],
    )
    session = make_session(bindings, {'truck': 0.0, 'trailer': 20.0})

    _build_fixed_object_index_mapping(session)

    assert session.object_name_by_index == {0: 'trailer', 1: 'truck'}
    assert _resolve_object_for_state(session, 0) is session.objects_by_name['trailer']
    assert _resolve_object_for_state(session, 1) is session.objects_by_name['truck']


def test_preview_does_not_guess_vehicle_mapping_by_nearest_position():
    bindings = FakeBindings(
        names_by_id={5: 'unknown', 6: 'also_unknown'}, ids_by_index=[5, 6])
    session = make_session(bindings, {'truck': 0.0, 'trailer': 0.1})

    _build_fixed_object_index_mapping(session)

    assert session.object_name_by_index == {}
    assert _resolve_object_for_state(session, 0) is None


def test_preview_uses_identity_world_xy_mapping():
    session = make_session(FakeBindings({}, []), {'truck': 0.0})
    session.xy_map = (0.0, 1.0, 1.0, 0.0)

    _calibrate_coordinate_mapping(session)

    assert session.xy_map == (1.0, 0.0, 0.0, 1.0)
