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

from addon.geometry_arc import DSC_geometry_arc
from . helpers_test import params_input, get_heading_start

from mathutils import Vector
from math import pi, sqrt
from pytest import approx


def test_geometry_arc_straight_case():
    ''' Sample some 'arc' geometry points and check correct results '''
    geometry = DSC_geometry_arc()
    solver = 'default'

    params_input['points'] = [Vector((2.0, 1.0, 0.0)), Vector((6.0, 3.0, 0.0))]
    params_input['heading_start'] = get_heading_start(params_input['points'][0], params_input['points'][1])
    params_input['heading_end'] = params_input['heading_start']
    geometry.add_section()
    geometry.update(params_input, 0.0, 0.0 solver)

    # Sample the first section
    length_0 = geometry.total_length
    xyz_local_0, h_0, c_0 = geometry.sample_cross_section(s=length_0, t_vec=[0.0], with_lane_offset=False)
    xyz_global_0 = geometry.matrix_world @ Vector(xyz_local_0[0])
    assert [xyz_global_0.x, xyz_global_0.y, xyz_global_0.z] == approx([6.0, 3.0, 0.0], 1e-5)

    # Add a second section
    params_input['points'] = [Vector((2.0, 1.0, 0.0)), Vector((6.0, 3.0, 0.0)), Vector((8.0, 4.0, 0.0))]
    geometry.add_section()
    geometry.update(params_input, 0.0, 0.0 solver)

    # Sample the first section again
    length_0 = geometry.sections[0]['length']
    xyz_local_0, h_0, c_0 = geometry.sample_cross_section(s=length_0, t_vec=[0.0], with_lane_offset=False)
    xyz_global_0 = geometry.matrix_world @ Vector(xyz_local_0[0])
    assert [xyz_global_0.x, xyz_global_0.y, xyz_global_0.z] == approx([6.0, 3.0, 0.0], 1e-5)

    # Sample the second section
    length_1 = geometry.total_length
    xyz_local_1, h_0, c_1 = geometry.sample_cross_section(s=length_1, t_vec=[0.0], with_lane_offset=False)
    xyz_global_1 = geometry.matrix_world @ Vector(xyz_local_1[0])
    assert [xyz_global_1.x, xyz_global_1.y, xyz_global_1.z] == approx([8.0, 4.0, 0.0], 1e-5)

def test_geometry_arc_180():
    ''' Sample some 'arc' geometry points and check correct results '''
    geometry = DSC_geometry_arc()
    solver = 'default'

    params_input['points'] = [Vector((0.0, 0.0, 0.0)), Vector((0.0, 2.0, 0.0))]
    params_input['heading_start'] = 0
    geometry.add_section()
    geometry.update(params_input, 0.0, 0.0 solver)

    length_0 = geometry.total_length
    xyz_local_0, h_0, c_0 = geometry.sample_cross_section(s=length_0/2, t_vec=[0.0], with_lane_offset=False)
    xyz_global_0 = geometry.matrix_world @ Vector(xyz_local_0[0])
    assert [xyz_global_0.x, xyz_global_0.y, xyz_global_0.z] == approx([1.0, 1.0, 0.0], 1e-5)

def test_geometry_arc_negative_start_heading():
    ''' Sample some 'arc' geometry points and check correct results '''
    geometry = DSC_geometry_arc()
    solver = 'default'

    params_input['points'] = [Vector((0.0, 0.0, 0.0)), Vector((-1.0, 1.0, 0.0))]
    params_input['heading_start'] = 3/4*pi
    geometry.add_section()
    geometry.update(params_input, 0.0, 0.0 solver)

    xyz_local, h, c = geometry.sample_cross_section(s=geometry.total_length, t_vec=[sqrt(2.0)], with_lane_offset=False)
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([-2.0, 0.0, 0.0], abs=1e-5)

def test_geometry_arc_y_axis_straight():
    ''' Sample some 'arc' geometry points and check correct results '''
    geometry = DSC_geometry_arc()
    solver = 'default'

    params_input['points'] = [Vector((0.0, 0.0, 0.0)), Vector((0.0, 2.0, 0.0))]
    params_input['heading_start'] = get_heading_start(params_input['points'][0], params_input['points'][1])
    params_input['heading_end'] = params_input['heading_start']
    geometry.add_section()
    geometry.update(params_input, 0.0, 0.0 solver)

    length_0 = geometry.total_length
    xyz_local_0, h_0, c_0 = geometry.sample_cross_section(s=length_0/2, t_vec=[0.0], with_lane_offset=False)
    xyz_global_0 = geometry.matrix_world @ Vector(xyz_local_0[0])
    assert [xyz_global_0.x, xyz_global_0.y, xyz_global_0.z] == approx([0.0, 1.0, 0.0], abs=1e-5)

def test_geometry_arc_270_three_pieces():
    ''' Sample some 'arc' geometry points and check correct results '''
    geometry = DSC_geometry_arc()
    solver = 'default'

    params_input['points'] = [Vector((10.0, 10.0, 0.0)),
                              Vector((20.0, 20.0, 0.0))]
    params_input['heading_start'] = 0
    geometry.add_section()
    geometry.update(params_input, 0.0, 0.0 solver)

    length_0 = geometry.total_length
    xyz_local, h_0, c_0 = geometry.sample_cross_section(s=length_0, t_vec=[5.0], with_lane_offset=False)
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([15.0, 20.0, 0.0], 1e-5)

    params_input['points'] = [Vector((10.0, 10.0, 0.0)),
                              Vector((20.0, 20.0, 0.0)),
                              Vector((10.0, 30.0, 0.0))]
    geometry.add_section()
    geometry.update(params_input, 0.0, 0.0 solver)

    length = geometry.total_length
    xyz_local, h_0, c_0 = geometry.sample_cross_section(s=length, t_vec=[2.0], with_lane_offset=False)
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([10.0, 28.0, 0.0], 1e-5)

    params_input['points'] = [Vector((10.0, 10.0, 0.0)),
                              Vector((20.0, 20.0, 0.0)),
                              Vector((10.0, 30.0, 0.0)),
                              Vector((0.0, 20.0, 0.0))]
    geometry.add_section()
    geometry.update(params_input, 0.0, 0.0 solver)

    length = geometry.total_length
    xyz_local, h_0, c_0 = geometry.sample_cross_section(s=length, t_vec=[-5.0], with_lane_offset=False)
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([-5.0, 20.0, 0.0], 1e-5)