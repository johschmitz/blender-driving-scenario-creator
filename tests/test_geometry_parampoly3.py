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

from addon.geometry_parampoly3 import DSC_geometry_parampoly3
from .helpers_test import params_input, get_heading_start

from mathutils import Vector
from pytest import approx


def test_geometry_parampoly3():
    ''' Sample some 'parampoly3' geometry points and check correct results '''
    solver = 'hermite'
    geometry = DSC_geometry_parampoly3()

    params_input['points'] = [Vector((10.0, 0.0, 0.0)), Vector((30.0, 0.0, 0.0))]
    params_input['heading_start'] = get_heading_start(params_input['points'][0], params_input['points'][1])
    params_input['heading_end'] = params_input['heading_start']
    geometry.add_section()
    geometry.update(params_input, solver)

    length_0 = geometry.total_length
    xyz_local_0, h_0, c_0 = geometry.sample_cross_section(s=length_0, t_vec=[0.0])
    xyz_global_0 = geometry.matrix_world @ Vector(xyz_local_0[0])
    assert [xyz_global_0.x, xyz_global_0.y, xyz_global_0.z] == approx([30.0, 0.0, 0.0], 1e-5)

    params_input['points'] = [Vector((10.0, 0.0, 0.0)), Vector((30.0, 0.0, 0.0)), Vector((40.0, 0.0, 0.0))]
    geometry.add_section()
    geometry.update(params_input, solver)

    length_0 = geometry.sections[0]['length']
    xyz_local_0, h_0, c_0 = geometry.sample_cross_section(s=length_0, t_vec=[0.0])
    xyz_global_0 = geometry.matrix_world @ Vector(xyz_local_0[0])
    assert [xyz_global_0.x, xyz_global_0.y, xyz_global_0.z] == approx([30.0, 0.0, 0.0], 1e-5)

    length_1 = geometry.total_length
    xyz_local_1, h_1, c_1 = geometry.sample_cross_section(s=length_1, t_vec=[0.0])
    xyz_global_1 = geometry.matrix_world @ Vector(xyz_local_1[0])
    assert [xyz_global_1.x, xyz_global_1.y, xyz_global_1.z] == approx([40.0, 0.0, 0.0], 1e-5)
