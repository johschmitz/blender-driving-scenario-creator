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

from . geometry import DSC_geometry

from mathutils import Vector, Matrix
from math import sqrt, pi
import numpy as np
from scipy.integrate import quad


class DSC_geometry_parampoly3(DSC_geometry):

    def __init__(self):
        super().__init__(curve_type='parampoly3')

    def evaluate_cubic_polynomial_derivative(self, control_points_1d, t):
        """
            Evaluate the derivative of the cubic polynomial at a given parameter t
        """
        p0, p1, p2, p3 = control_points_1d
        return 3 * (1 - t)**2 * (p1 - p0) + 6 * (1 - t) * t * (p2 - p1) + 3 * t**2 * (p3 - p2)

    def arc_length_integrand(self, control_points, t):
        """
            Integrand function for calculating arc length
        """
        control_points_x = [p.x for p in control_points]
        control_points_y = [p.y for p in control_points]
        derivative_x = self.evaluate_cubic_polynomial_derivative(control_points_x, t)
        derivative_y = self.evaluate_cubic_polynomial_derivative(control_points_y, t)
        return np.sqrt(derivative_x**2 + derivative_y**2)

    def calculate_arc_length(self, control_points, num_points=100):
        """
            Calculate the arc length of the cubic curve
        """
        t_values = np.linspace(0, 1, num_points)
        arc_lengths = np.array([quad(lambda t: self.arc_length_integrand(control_points, t), 0, t)[0] for t in t_values])
        return arc_lengths[-1]

    def calculate_cubic_polynomial_coefficients(self, control_points):
        """
            Calculate the coefficients of the cubic polynomial
        """
        p0_x, p1_x, p2_x, p3_x = [p.x for p in control_points]
        p0_y, p1_y, p2_y, p3_y = [p.y for p in control_points]
        coefficients_x = np.array([p0_x, 3 * (p1_x - p0_x), 3 * (p2_x - 2 * p1_x + p0_x), p3_x - 3 * p2_x + 3 * p1_x - p0_x])
        coefficients_y = np.array([p0_y, 3 * (p1_y - p0_y), 3 * (p2_y - 2 * p1_y + p0_y), p3_y - 3 * p2_y + 3 * p1_y - p0_y])
        return coefficients_x, coefficients_y

    def calculate_control_points(self):
        '''
            Calculate 4 control points for the cubic Bezier curve
        '''
        vec_hdg_start = Vector((1.0, 0.0, 0.0))
        vec_hdg_start.rotate(Matrix.Rotation(self.heading_start_local, 4, 'Z'))
        vec_hdg_end = Vector((1.0, 0.0, 0.0))
        vec_hdg_end.rotate(Matrix.Rotation(self.heading_end_local, 4, 'Z'))
        p0 = self.point_start_local
        p1 = self.point_start_local \
            + (self.point_end_local - self.point_start_local).length/3 * vec_hdg_start
        p2 = self.point_end_local \
            - (self.point_end_local - self.point_start_local).length/3 * vec_hdg_end
        p3 = self.point_end_local
        return [p0, p1, p2, p3]

    def update_plan_view(self, params, geometry_solver='default'):
        # Calculate curve length for arc length parameterization
        # TODO: make sure 100 points are sufficient and not too much
        num_points_arc_length = 100
        control_points = self.calculate_control_points()
        length = self.calculate_arc_length(control_points, num_points_arc_length)

        # Calculate coefficients using the length
        coefficients_u, coefficients_v = self.calculate_cubic_polynomial_coefficients(control_points)

        # Calculate the end heading using the first derivative
        control_points_x = [control_points[0][0], control_points[1][0],
                            control_points[2][0], control_points[3][0]]
        control_points_y = [control_points[0][1], control_points[1][1],
                            control_points[2][1], control_points[3][1]]
        hdg_end_u = self.evaluate_cubic_polynomial_derivative(control_points_x, t=1.0)
        hdg_end_v = self.evaluate_cubic_polynomial_derivative(control_points_y, t=1.0)
        vec_1_0 = Vector((1.0, 0.0))
        vec_hdg = Vector((hdg_end_u, hdg_end_v))
        if vec_hdg.length > 0.0:
            hdg_end = vec_hdg.angle_signed(vec_1_0)
        else:
            hdg_end = 0

        # Remember geometry parameters
        self.sections[-1]['params']['curve_type'] = 'parampoly3'
        self.sections[-1]['params']['point_start'] = params['points'][-2]
        self.sections[-1]['params']['heading_start'] = params['heading_start']
        # FIXME curvature is not always 0
        self.sections[-1]['params']['curvature_start'] = 0
        self.sections[-1]['params']['point_end'] = params['points'][-1]
        self.sections[-1]['params']['heading_end'] = params['heading_start'] + hdg_end
        # FIXME curvature is not always 0
        self.sections[-1]['params']['curvature_end'] = 0
        self.sections[-1]['params']['length'] = length
        self.sections[-1]['params']['coefficients_u']['a'] = coefficients_u[0]
        self.sections[-1]['params']['coefficients_u']['b'] = coefficients_u[1]
        self.sections[-1]['params']['coefficients_u']['c'] = coefficients_u[2]
        self.sections[-1]['params']['coefficients_u']['d'] = coefficients_u[3]
        self.sections[-1]['params']['coefficients_v']['a'] = coefficients_v[0]
        self.sections[-1]['params']['coefficients_v']['b'] = coefficients_v[1]
        self.sections[-1]['params']['coefficients_v']['c'] = coefficients_v[2]
        self.sections[-1]['params']['coefficients_v']['d'] = coefficients_v[3]
        self.sections[-1]['params']['valid'] = True

    def sample_plan_view(self, s):
        idx_section, s_section = self.get_section_idx_and_s(s)
        coeffs_u = self.sections[idx_section]['params']['coefficients_u']
        coeffs_v = self.sections[idx_section]['params']['coefficients_v']
        length_section = self.sections[idx_section]['params']['length']
        t = s_section / length_section
        x_s = coeffs_u['a'] + coeffs_u['b'] * t \
            + coeffs_u['c'] * t**2 + coeffs_u['d'] * t**3
        y_s = coeffs_v['a'] + coeffs_v['b'] * t \
            + coeffs_v['c'] * t**2 + coeffs_v['d'] * t**3
        hdg_x = coeffs_u['b'] + 2 * coeffs_u['c'] * t + 3 * coeffs_u['d'] * t**2
        hdg_y = coeffs_v['b'] + 2 * coeffs_v['c'] * t + 3 * coeffs_v['d'] * t**2
        vec_1_0 = Vector((1.0, 0.0))
        vec_hdg = Vector((hdg_x, hdg_y))
        if vec_hdg.length > 0.0:
            hdg_t = vec_hdg.angle_signed(vec_1_0) + pi/2
        else:
            hdg_t = 0
        curvature = 0 # FIXME
        return x_s, y_s, curvature, hdg_t
