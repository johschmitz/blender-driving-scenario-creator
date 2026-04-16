import pytest

from addon import script_api


def test_normalize_road_payload_minimal():
    payload = {
        'start': {
            'point': [0.0, 0.0, 0.0],
            'heading': 0.0,
        },
        'sections': [
            {'point': [10.0, 0.0, 0.0]},
        ],
    }

    normalized = script_api.normalize_road_payload(payload)

    assert normalized['start']['point'] == (0.0, 0.0, 0.0)
    assert normalized['start']['heading'] == 0.0
    assert normalized['sections'][0]['point'] == (10.0, 0.0, 0.0)
    assert normalized['sections'][0]['connected_end'] is False


def test_normalize_road_payload_uses_link_for_connect_flags():
    payload = {
        'start': {
            'point': [0.0, 0.0, 0.0],
            'heading': 0.0,
        },
        'sections': [
            {'point': [10.0, 0.0, 0.0]},
        ],
        'link_start': {
            'cp_type': 'cp_end_l',
            'id_obj': 1,
        },
        'link_end': {
            'cp_type': 'cp_start_l',
            'id_obj': 2,
        },
    }

    normalized = script_api.normalize_road_payload(payload)

    assert normalized['start']['connected'] is True
    assert normalized['sections'][-1]['connected_end'] is True


def test_normalize_road_payload_requires_sections():
    payload = {
        'start': {
            'point': [0.0, 0.0, 0.0],
            'heading': 0.0,
        },
        'sections': [],
    }

    with pytest.raises(script_api.ScriptPayloadError):
        script_api.normalize_road_payload(payload)


def test_normalize_two_point_payload_with_nested_format():
    payload = {
        'start': {
            'point': [0.0, 0.0, 0.0],
            'heading': 0.1,
        },
        'end': {
            'point': [5.0, 5.0, 0.0],
            'heading': 0.2,
        },
    }

    normalized = script_api.normalize_two_point_payload(payload)

    assert normalized['start']['heading'] == 0.1
    assert normalized['end']['heading'] == 0.2


def test_apply_road_properties_with_explicit_lanes():
    class DummyProps:
        def __init__(self):
            self.lanes = []
            self.lock_lanes = False
            self.width_line_standard = 0.12
            self.width_line_bold = 0.25
            self.num_lanes_left = 0
            self.num_lanes_right = 0
            self.road_split_type = 'none'
            self.road_split_lane_idx = 1

        def init(self):
            pass

        def clear_lanes(self):
            self.lanes = []

        def add_lane(self, side, lane_type, width_start, width_end,
                     road_mark_type, road_mark_weight, road_mark_width, road_mark_color,
                     split_right=False):
            self.lanes.append(type('Lane', (), {
                'side': side,
                'type': lane_type,
                'width_start': width_start,
                'width_end': width_end,
                'road_mark_type': road_mark_type,
                'road_mark_weight': road_mark_weight,
                'road_mark_width': road_mark_width,
                'road_mark_color': road_mark_color,
                'split_right': split_right,
            })())

    props = DummyProps()
    script_api.apply_road_properties(props, {
        'lanes': [
            {'side': 'left', 'type': 'driving', 'width_start': 3.0, 'width_end': 3.0},
            {'side': 'right', 'type': 'driving', 'width_start': 3.2, 'width_end': 3.2},
        ],
    })

    assert props.num_lanes_left == 1
    assert props.num_lanes_right == 1
    assert any(lane.side == 'center' for lane in props.lanes)
