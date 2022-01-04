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

from mathutils import Vector, Matrix


class DSC_geometry():

    params = {
        'curve': None,
        'length': 0,
        'point_start': Vector((0.0,0.0,0.0)),
        'heading_start': 0,
        'curvature_start': 0,
        'slope_start':0,
        'point_end': Vector((0.0,0.0,0.0)),
        'heading_end': 0,
        'curvature_end': 0,
        'slope_end': 0,
        'elevation': [{'s': 0, 'a': 0, 'b': 0, 'c': 0, 'd': 0}],
        'valid': True,
    }

    def sample_cross_section(self, s, t):
        '''
            Return a list of samples x, y = f(s, t) and curvature c in local
            coordinates.
        '''
        raise NotImplementedError()

    def update(self, params_input, geometry_solver):
        '''
            Update parameters of the geometry and local to global tranformation
            matrix.
        '''
        self.update_plan_view(params_input, geometry_solver)
        self.update_elevation(params_input)

    def update_local_to_global(self, point_start, heading_start, point_end, heading_end):
        '''
            Calculate matrix for local to global transform of the geometry.
        '''
        mat_translation = Matrix.Translation(point_start)
        mat_rotation = Matrix.Rotation(heading_start, 4, 'Z')
        self.matrix_world = mat_translation @ mat_rotation
        self.point_end_local = self.matrix_world.inverted() @ point_end
        self.heading_end_local = heading_end - heading_start

    def update_plan_view(self, params):
        '''
            Update plan view (2D) geometry of road.
        '''
        raise NotImplementedError()

    def update_elevation(self, params_input):
        '''
            Update elevation of road geometry based on predecessor, successor,
            start and end point.

            TODO: Later allow elevations across multiple geometries for now we
            use
                parabola
                parabola - line
                parablola - line - parablola
                line - parabola
            curve combination inside one geometry.

            Symbols and equations used:
                Slope of incoming road: m_0
                Parabola (Curve 0): h_p1 = a_p1 + b_p1 * s + c_p1 * s^2
                Line (Curve 1): h_l = a_l + b_l * s
                Parabola (Curve 2): h_p2 = a_p2 + b_p2 * s + c_p2 * s^2
                Slope of outgoing road: m_3
        '''
        if (params_input['point_start'].z == params_input['point_end'].z
            and params_input['slope_start'] == 0
            and params_input['slope_end'] == 0):
            # No elevation
            self.params['elevation'] = [{'s': 0, 'a': 0, 'b': 0, 'c': 0, 'd': 0}]
        else:
            # TODO: get slope of predecessor and succesor
            m_0 = params_input['slope_start']
            m_3 = params_input['slope_end']

            # Convert to local (s, z) coordinate system [x_1, y_1] = [0, 0]
            h_start = params_input['point_start'].z
            s_end = self.params['length']
            h_end = params_input['point_end'].z - h_start

            # End of parabola/beginning of straight line
            # TODO: Find correct equation for the parabola length from the literature
            s_1 = max(abs(m_0)/10, abs(h_end)/s_end) * params_input['design_speed']**2 / 120
            if s_1 > 0:
                if s_1 < s_end:
                    # Case: parobla - line
                    c_p1 = (h_end - m_0 * s_end) / (2 * s_1 * s_end - s_1**2)
                    h_1 = m_0 * s_1 + c_p1 * s_1**2
                    b_l = (h_end - h_1) / (s_end - s_1)
                    a_l = h_end - b_l * s_end
                    self.params['elevation'] = [{'s': 0, 'a': 0, 'b': m_0, 'c': c_p1, 'd': 0}]
                    self.params['elevation'].append({'s': s_1, 'a': a_l, 'b': b_l, 'c': 0, 'd': 0})
                else:
                    # Case: parablola
                    c_p1 = (h_end - m_0 * s_end) / s_end**2
                    self.params['elevation'] = [{'s': 0, 'a': 0, 'b': m_0, 'c': c_p1, 'd': 0}]
            else:
                self.params['elevation'] = [{'s': 0, 'a': 0, 'b': 0, 'c': 0, 'd': 0}]

        self.params['slope_start'] = self.get_slope_start()
        self.params['slope_end'] = self.get_slope_end()

    def get_slope_start(self):
        '''
            Return slope at beginning of geometry.
        '''
        return self.params['elevation'][0]['b']

    def get_slope_end(self):
        '''
            Return slope at end of geometry.
        '''
        length = self.params['length']
        slope = self.params['elevation'][-1]['b'] + \
            2 * self.params['elevation'][-1]['c'] * length + \
            3 * self.params['elevation'][-1]['d'] * length**2
        return slope


    def sample_plan_view(self, s):
        '''
            Return x(s), y(s), curvature(s), hdg_t(s)
        '''
        return NotImplementedError()

    def get_elevation(self, s):
        '''
            Return the elevation coefficients for the given value of s.
        '''
        idx_elevation = 0
        while idx_elevation < len(self.params['elevation'])-1:
            if s >= self.params['elevation'][idx_elevation+1]['s']:
                idx_elevation += 1
            else:
                break
        return self.params['elevation'][idx_elevation]

    def sample_cross_section(self, s, t_vec):
        '''
            Sample a cross section (multiple t values) in the local coordinate
            system.
        '''
        x_s, y_s, curvature_plan_view, hdg_t = self.sample_plan_view(s)
        elevation = self.get_elevation(s)
        # Calculate curvature of the elevation function
        d2e_d2s = 2 * elevation['c'] + 3 * elevation['d'] * s
        if d2e_d2s != 0:
            de_ds = elevation['b']+ 2 * elevation['c'] * s + 3 * elevation['d'] * s
            curvature_elevation = (1 + de_ds**2)**(3/2) / d2e_d2s
        else:
            curvature_elevation = 0
        # FIXME convert curvature for t unequal 0
        curvature_abs = max(abs(curvature_plan_view), abs(curvature_elevation))
        vector_hdg_t = Vector((1.0, 0.0))
        vector_hdg_t.rotate(Matrix.Rotation(hdg_t, 2))
        xyz = []
        for t in t_vec:
            xy_vec = Vector((x_s, y_s)) + t * vector_hdg_t
            z = elevation['a'] + \
                elevation['b'] * s + \
                elevation['c'] * s**2 + \
                elevation['d'] * s**3
            xyz += [(xy_vec.x, xy_vec.y, z)]
        return xyz, curvature_abs