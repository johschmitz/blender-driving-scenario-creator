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

from addon.geometry_line import DSC_geometry_line
from . helpers_test import params_input, get_heading_start

from mathutils import Vector
from pytest import approx


def test_geometry_line_1d():
    '''
        Sample some 'line' geometry points and check correct results
    '''
    geometry = DSC_geometry_line()
    params_input['points'] = [Vector((10.0, 10.0, 0.0)), Vector((20.0, 10.0, 0.0))]
    params_input['heading_start'] = get_heading_start(params_input['points'][0], params_input['points'][1])
    geometry.add_section()
    geometry.update(params_input, None)
    length = geometry.total_length
    xyz_local, h, c = geometry.sample_cross_section(s=length/2.0, t_vec=[0.0])
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([15.0, 10.0, 0.0], 1e-5)

    params_input['points'] = [Vector((10.0, 10.0, 0.0)), Vector((20.0, 10.0, 0.0)), Vector((30.0, 10.0, 0.0))]
    geometry.add_section()
    geometry.update(params_input, None)
    length = geometry.total_length
    length_section = geometry.sections[1]['length']
    xyz_local, h, c = geometry.sample_cross_section(s=length-length_section/2, t_vec=[0.0])
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([25.0, 10.0, 0.0], 1e-5)

def test_geometry_line_2d():
    '''
        Sample some 'line' geometry points and check correct results
    '''
    geometry = DSC_geometry_line()
    params_input['points'] = [Vector((20.0, 10.0, 0.0)), Vector((60.0, 30.0, 0.0))]
    params_input['heading_start'] = get_heading_start(params_input['points'][0], params_input['points'][1])
    geometry.add_section()
    geometry.update(params_input, None)
    length = geometry.total_length
    xyz_local, h, c = geometry.sample_cross_section(s=length/2.0, t_vec=[0.0])
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([40.0, 20.0, 0.0], 1e-5)

    params_input['points'] = [Vector((20.0, 10.0, 0.0)), Vector((60.0, 30.0, 0.0)), Vector((100.0, 50.0, 0.0))]
    geometry.add_section()
    geometry.update(params_input, None)
    length = geometry.total_length
    length_section = geometry.sections[1]['length']
    xyz_local, h, c = geometry.sample_cross_section(s=length-length_section/2, t_vec=[0.0])
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([80.0, 40.0, 0.0], 1e-5)

    params_input['points'] = [Vector((20.0, 10.0, 0.0)), Vector((60.0, 30.0, 0.0)),
                              Vector((100.0, 50.0, 0.0)), Vector((320.0, 160.0, 0.0))]
    geometry.add_section()
    geometry.update(params_input, None)
    length = geometry.total_length
    xyz_local, h, c = geometry.sample_cross_section(s=length, t_vec=[0.0])
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([320.0, 160.0, 0.0], 1e-5)

def test_geometry_line_2d_projection():
    '''
        Sample some 'line' geometry points and check correct results
    '''
    geometry = DSC_geometry_line()
    params_input['points'] = [Vector((20.0, 10.0, 0.0)), Vector((60.0, 30.0, 0.0))]
    params_input['heading_start'] = get_heading_start(params_input['points'][0], params_input['points'][1])
    geometry.add_section()
    geometry.update(params_input, None)
    length = geometry.total_length
    xyz_local, h, c = geometry.sample_cross_section(s=length/2.0, t_vec=[0.0])
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([40.0, 20.0, 0.0], 1e-5)

    params_input['points'] = [Vector((20.0, 10.0, 0.0)), Vector((60.0, 30.0, 0.0)), Vector((90.0, 70.0, 0.0))]
    geometry.add_section()
    geometry.update(params_input, None)
    length = geometry.total_length
    length_section = geometry.sections[1]['length']
    xyz_local, h, c = geometry.sample_cross_section(s=length-length_section/2, t_vec=[0.0])
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    # FIXME there seems to be a small error in the projection
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([80.0, 40.0, 0.0], 1e-5)

def test_geometry_line_3d():
    '''
        Sample some 'line' geometry points and check correct results
    '''
    geometry = DSC_geometry_line()
    params_input['points'] = [Vector((2.0, 1.0, 1.0)), Vector((6.0, 3.0, 2.0))]
    params_input['heading_start'] = get_heading_start(params_input['points'][0], params_input['points'][1])
    geometry.add_section()
    geometry.update(params_input, None)
    length = geometry.total_length
    xyz_local, h, c = geometry.sample_cross_section(s=length/2.0, t_vec=[0.0])
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([4.0, 2.0, 1.5], 1e-5)

    params_input['points'] = [Vector((2.0, 1.0, 1.0)), Vector((6.0, 3.0, 2.0)), Vector((10.0, 5.0, 4.0))]
    geometry.add_section()
    geometry.update(params_input, None)
    length = geometry.total_length
    xyz_local, h, c = geometry.sample_cross_section(s=length, t_vec=[0.0])
    xyz_global = geometry.matrix_world @ Vector(xyz_local[0])
    assert [xyz_global.x, xyz_global.y, xyz_global.z] == approx([10.0, 5.0, 4.0], 1e-5)