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

from mathutils import Vector

from addon import helpers


params_input = {
    'points': [],
    'heading_start': 0.0,
    'heading_end': 0.0,
    'curvature_start': 0.0,
    'curvature_end': 0.0,
    'slope_start': 0.0,
    'slope_end': 0.0,
    'connected_start': False,
    'connected_end': False,
    'normal_start': Vector((0.0, 0.0, 1.0)),
    'design_speed': 130.0,
}


def get_heading_start(point_start, point_end):
    """Calculate heading for the line between two input points."""
    vector_start_end = (point_end - point_start).to_2d()
    if vector_start_end.length == 0:
        return 0
    return vector_start_end.angle_signed(Vector((1.0, 0.0)))


def test_raycast_excluding_entity_hides_hierarchy_and_restores_visibility(monkeypatch):
    class RaycastObject(dict):
        def __init__(self, name, initially_hidden=False):
            super().__init__(dsc_category='OpenSCENARIO')
            self.name = name
            self._hidden = initially_hidden
            self.children_recursive = []

        def hide_get(self):
            return self._hidden

        def hide_set(self, hidden):
            self._hidden = hidden

    moving_entity = RaycastObject('moving_entity')
    visible_child = RaycastObject('visible_child')
    hidden_child = RaycastObject('hidden_child', initially_hidden=True)
    moving_entity.children_recursive = [visible_child, hidden_child]
    road = RaycastObject('road')
    road['dsc_category'] = 'OpenDRIVE'
    context = type('Context', (), {
        'view_layer': type('ViewLayer', (), {'depsgraph': object()})(),
    })()

    def raycast(**_kwargs):
        assert moving_entity.hide_get()
        assert visible_child.hide_get()
        assert hidden_child.hide_get()
        return True, Vector((1.0, 2.0, 0.0)), Vector((0.0, 0.0, 1.0)), 0, road, None

    context.scene = type('Scene', (), {'ray_cast': staticmethod(raycast)})()
    monkeypatch.setattr(
        helpers, 'get_mouse_vectors',
        lambda _context, _event: (Vector((0.0, 0.0, -1.0)),
                                  Vector((0.0, 0.0, 10.0))))

    hit, _point, _normal, obj = helpers.raycast_mouse_to_dsc_object_excluding(
        context, object(), (moving_entity,))

    assert hit
    assert obj is road
    assert not moving_entity.hide_get()
    assert not visible_child.hide_get()
    assert hidden_child.hide_get()
