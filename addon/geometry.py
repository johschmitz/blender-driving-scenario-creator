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
from math import pi, copysign
from numpy import linspace

class DSC_geometry():

    def __init__(self):
        # TODO: Maybe at some point implement mixed geometries
        self.sections = []
        self.section_curves = []
        self.total_length = 0

    def update_total_length(self):
        '''
            Update the total length of the geometry.
        '''
        self.total_length = 0
        for section in self.sections:
            self.total_length += section['length']

    def sample_cross_section(self, s, t):
        '''
            Return a list of samples x, y = f(s, t) and curvature c in local
            coordinates.
        '''
        raise NotImplementedError()

    def reset(self):
        '''
            Reset the sections list.
        '''
        self.sections = []
        self.section_curves = []
        self.total_length = 0

    def add_section(self):
        '''
            Add a geometry section.
        '''
        section = {
            'curve_type': None,
            'geometry_solver': None,
            'length': 0,
            'point_start': Vector((0.0,0.0,0.0)),
            'point_end': Vector((0.0,0.0,0.0)),
            'heading_start': 0,
            'curvature_start': 0,
            'slope_start': 0,
            'heading_end': 0,
            'curvature_end': 0,
            'slope_end': 0,
            'coefficients_u': {'a': 0, 'b': 0, 'c': 0, 'd': 0},
            'coefficients_v': {'a': 0, 'b': 0, 'c': 0, 'd': 0},
            'elevation': [{'s_section': 0, 'a': 0, 'b': 0, 'c': 0, 'd': 0}],
            'valid': True,
            'matrix_local': None, # Matrix for section to local transformation
        }
        self.sections.append(section)
        self.section_curves.append(None)

    def load_sections(self, section_data):
        '''
            Load sections from stored data.
        '''
        for section in section_data:
            self.add_section_from_params(section)

    def add_section_from_params(self, section_new):
        '''
            Add a geometry section with given parameters.
        '''
        section = {
            'curve_type': section_new['curve_type'],
            'geometry_solver': section_new['geometry_solver'],
            'length': section_new['length'],
            'point_start': section_new['point_start'],
            'point_end': section_new['point_end'],
            'heading_start': section_new['heading_start'],
            'curvature_start': section_new['curvature_start'],
            'slope_start': section_new['slope_start'],
            'heading_end': section_new['heading_end'],
            'curvature_end': section_new['curvature_end'],
            'slope_end': section_new['slope_end'],
            'coefficients_u': section_new['coefficients_u'],
            'coefficients_v': section_new['coefficients_v'],
            'elevation': section_new['elevation'],
            'valid': section_new['valid'],
            'matrix_local': Matrix(section_new['matrix_local']), # Matrix for section to local transformation
        }
        self.sections.append(section)
        # Set matrix world based on first section
        if len(self.sections) == 1:
            mat_translation = Matrix.Translation(section_new['point_start'])
            mat_rotation = Matrix.Rotation(section_new['heading_start'], 4, 'Z')
            self.matrix_world = mat_translation @ mat_rotation
        self.load_section_curve(section)
        self.update_total_length()

    def load_section_curve(self):
        '''
            Create section curves objects if necessary.
        '''
        raise NotImplementedError()

    def remove_last_section(self):
        '''
            Remove the last geometry section.
        '''
        if len(self.sections) > 1:
            self.sections.pop()
            self.section_curves.pop()
        self.update_total_length()
        self.matrix_world = None

    def update(self, params_input, geometry_solver):
        '''
            Update parameters of the geometry and local to global tranformation
            matrix.
        '''
        if len(self.sections) == 0:
            self.add_section()
        self.update_local_to_global(params_input)
        self.update_local_and_section_params(params_input)
        self.update_plan_view(params_input, geometry_solver)
        self.update_elevation(params_input)
        self.update_total_length()

    def update_local_to_global(self, params_input):
        '''
            Calculate matrix for local to global transform of the geometry.
        '''
        mat_translation = Matrix.Translation(params_input['points'][0])
        mat_rotation = Matrix.Rotation(params_input['heading_start'], 4, 'Z')
        self.matrix_world = mat_translation @ mat_rotation

    def update_local_and_section_params(self, params_input):
        '''
            Calculate and update parameters for section to local transform.
            Needs to be called after updating the local to global transform
            matrix.
        '''
        # Calculate parameters in local coordinate system
        self.point_start_local = self.matrix_world.inverted() @ params_input['points'][-2]
        self.point_end_local = self.matrix_world.inverted() @ params_input['points'][-1]
        if len(self.sections) == 1:
            self.heading_start_local = 0
            self.heading_end_local = params_input['heading_end'] - params_input['heading_start']
            self.curvature_start_local = params_input['curvature_start']
        else:
            self.heading_start_local = self.sections[-2]['heading_end'] \
                - self.sections[0]['heading_start']
            self.heading_end_local = params_input['heading_end'] \
                - self.sections[0]['heading_start']
            self.curvature_start_local = self.sections[-2]['curvature_end']
        self.curvature_end_local = params_input['curvature_end']

        # Calculate parameters in section coordinate system
        mat_translation = Matrix.Translation(self.point_start_local)
        mat_rotation = Matrix.Rotation(self.heading_start_local, 4, 'Z')
        self.sections[-1]['matrix_local'] = mat_translation @ mat_rotation

    def update_plan_view(self, params, geometry_solver):
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
        '''
        if len(self.sections) == 1:
            slope_start = params_input['slope_start']
            slope_end = params_input['slope_end']
        else:
            slope_start = self.get_slope_end_section(len(self.sections)-2)
            slope_end = slope_start
        if (self.point_start_local.z == self.point_end_local.z
            and slope_start == 0
            and slope_end == 0):
            # No additional elevation on this segment
            h_0 = self.point_start_local.z
            self.sections[-1]['elevation'] = [{'s_section': 0, 'a': h_0, 'b': 0, 'c': 0, 'd': 0}]
        elif params_input['connected_start'] == False and params_input['connected_end'] == False \
            and len(self.sections) == 1:
            # No incoming and outgoing roads connected
            # Symbols and equations used:
            #     Slope of road: m_0
            h_0 = self.point_start_local.z
            h_1 = self.point_end_local.z
            if self.sections[-1]['length'] > 0.0:
                m_0 = (h_1 - h_0) \
                    / self.sections[-1]['length']
            else:
                m_0 = 0
            self.sections[-1]['elevation'] = [{'s_section': 0, 'a': h_0, 'b': m_0, 'c': 0, 'd': 0}]
        elif len(self.sections) > 1 and params_input['connected_end'] == False:
            # Symbols and equations used:
            #     Height of incoming road: h_0
            #     Height of outgoing road: h_1
            #     Slope of incoming road: m_0
            #     Slope of outgoing road: m_1
            #     Length of road: s_1
            # https://en.m.wikipedia.org/wiki/Cubic_Hermite_spline
            h_0 = self.point_start_local.z
            h_1 = self.point_end_local.z
            s_1 = self.sections[-1]['length']
            m_0 = self.get_slope_end_section(len(self.sections)-2)
            if s_1 > 0.0:
                m_1 = (h_1 - h_0) / s_1
            else:
                m_1 = 0.0
            if s_1 > 0.0:
                a = h_0
                b = m_0
                c = (-3 * h_0 - 2 * s_1 * m_0 + 3 * h_1 - s_1 * m_1) / s_1**2
                d = (2 * h_0 + s_1 * m_0 - 2 * h_1 + s_1 * m_1) / s_1**3
                self.sections[-1]['elevation'] = [{'s_section': 0, 'a': a, 'b': b, 'c': c, 'd': d}]
            else:
                self.sections[-1]['elevation'] = [{'s_section': 0, 'a': h_0, 'b': 0, 'c': 0, 'd': 0}]
        elif params_input['connected_start'] == True and params_input['connected_end'] == True:
            # Symbols and equations used:
            #     Height of incoming road: h_0
            #     Height of outgoing road: h_1
            #     Slope of incoming road: m_0
            #     Slope of outgoing road: m_1
            #     Length of road: s_1
            # https://en.m.wikipedia.org/wiki/Cubic_Hermite_spline
            h_0 = self.point_start_local.z
            h_1 = self.point_end_local.z
            s_1 = self.sections[-1]['length']
            m_0 = params_input['slope_start']
            m_1 = -1.0 * params_input['slope_end']
            if s_1 > 0.0:
                a = h_0
                b = m_0
                c = (-3 * h_0 - 2 * s_1 * m_0 + 3 * h_1 - s_1 * m_1) / s_1**2
                d = (2 * h_0 + s_1 * m_0 - 2 * h_1 + s_1 * m_1) / s_1**3
                self.sections[-1]['elevation'] = [{'s_section': 0, 'a': a, 'b': b, 'c': c, 'd': d}]
            else:
                self.sections[-1]['elevation'] = [{'s_section': 0, 'a': h_0, 'b': 0, 'c': 0, 'd': 0}]
        else:
            # Symbols and equations used:
            #     Slope of incoming road: m_0
            #     Parabola (Curve 0): h_p1 = a_p1 + b_p1 * s + c_p1 * s^2
            #     Line (Curve 1): h_l = a_l + b_l * s
            #     Parabola (Curve 2): h_p2 = a_p2 + b_p2 * s + c_p2 * s^2
            #     Slope of outgoing road: m_3
            m_0 = params_input['slope_start']
            # TODO also use slope of the outgoing rope for this constellation
            m_3 = params_input['slope_end']

            # Convert to local (s, z) coordinate system [x_1, y_1] = [0, 0]
            h_start = self.point_start_local.z
            s_end = self.sections[-1]['length']
            h_end = self.point_end_local.z - h_start

            # End of parabola/beginning of straight line
            if s_end > 0.0:
                # TODO: Find correct equation for the parabola length from the literature
                s_1 = max(abs(m_0)/10, abs(h_end)/s_end) * params_input['design_speed']**2 / 120
                if s_1 > 0:
                    if s_1 < s_end:
                        # Case: parobla - line
                        c_p1 = (h_end - m_0 * s_end) / (2 * s_1 * s_end - s_1**2)
                        h_1 = m_0 * s_1 + c_p1 * s_1**2
                        b_l = (h_end - h_1) / (s_end - s_1)
                        a_l = h_end - b_l * s_end
                        self.sections[-1]['elevation'] = [
                            {'s_section': 0, 'a': 0, 'b': m_0, 'c': c_p1, 'd': 0}]
                        self.sections[-1]['elevation'].append(
                            {'s_section': s_1, 'a': a_l, 'b': b_l, 'c': 0, 'd': 0})
                    else:
                        # Case: parablola
                        c_p1 = (h_end - m_0 * s_end) / s_end**2
                        self.sections[-1]['elevation'] = [
                            {'s_section': 0, 'a': 0, 'b': m_0, 'c': c_p1, 'd': 0}]
                else:
                    self.sections[-1]['elevation'] = [{'s_section': 0, 'a': 0, 'b': 0, 'c': 0, 'd': 0}]
            else:
                self.sections[-1]['elevation'] = [{'s_section': 0, 'a': 0, 'b': 0, 'c': 0, 'd': 0}]

        self.sections[-1]['slope_start'] = self.get_slope_start()
        self.sections[-1]['slope_end'] = self.get_slope_end()

    def get_slope_start(self):
        '''
            Return slope at beginning of geometry.
        '''
        return self.sections[-1]['elevation'][0]['b']

    def get_slope_end(self):
        '''
            Return slope at end of geometry.
        '''
        length = self.sections[-1]['length']
        slope = self.sections[-1]['elevation'][-1]['b'] + \
            2 * self.sections[-1]['elevation'][-1]['c'] * length + \
            3 * self.sections[-1]['elevation'][-1]['d'] * length**2
        return slope

    def get_slope_end_section(self, section_idx):
        '''
            Return slope at end of geometry section.
        '''
        length = self.sections[section_idx]['length']
        slope = self.sections[section_idx]['elevation'][-1]['b'] + \
            2 * self.sections[section_idx]['elevation'][-1]['c'] * length + \
            3 * self.sections[section_idx]['elevation'][-1]['d'] * length**2
        return slope

    def sample_plan_view(self, s):
        '''
            Return x(s), y(s), curvature(s), hdg_t(s) the geometry section with
            the given index.
        '''
        return NotImplementedError()

    def get_closest_ref_line_x_y_heading_s_t(self, point):
        '''
            Return the x, y and heading of the closest point on the reference
            line to the given point and the s, and t coordinate values of the
            point.
        '''
        point_local = self.matrix_world.inverted() @ point
        sample_points = []
        sample_headings = []
        # Step 1: search on the complete geometry
        step_size = 1.0
        num_steps = int((self.total_length // step_size) + 1)
        s_values = linspace(0.0, self.total_length, num_steps).tolist()
        for s in s_values:
            x, y, h, c = self.sample_plan_view(s)
            sample_points.append(Vector((x, y)))
            sample_headings.append(h)
        distance = []
        for sample_point in sample_points:
            distance.append((point_local.to_2d() - sample_point).length)
        idx_min = distance.index(min(distance))
        closest_point = sample_points[idx_min]
        closest_point_heading = sample_headings[idx_min]
        closest_point_s = s_values[idx_min]
        # Step 2: refine the result
        sample_points = []
        sample_headings = []
        step_size = 0.01
        s_min = closest_point_s - 1.0
        if s_min < 0.0:
            s_min = 0.0
        s_max = closest_point_s + 1.0
        if s_max > self.total_length:
            s_max = self.total_length
        num_steps = int(((s_max - s_min) // step_size) + 1)
        s_values = linspace(s_min, s_max, num_steps).tolist()
        for s in s_values:
            x, y, h, c = self.sample_plan_view(s)
            sample_points.append(Vector((x, y)))
            sample_headings.append(h)
        distance = []
        for sample_point in sample_points:
            distance.append((point_local.to_2d() - sample_point).length)
        idx_min = distance.index(min(distance))
        closest_point = sample_points[idx_min]
        closest_point_heading = sample_headings[idx_min]
        # Calculate Frenet t coordinate value
        vec_t = Vector((1.0, 0.0))
        vec_t.rotate(Matrix.Rotation(closest_point_heading + pi/2, 2))
        t = copysign(distance[idx_min], vec_t.dot(point_local.to_2d() - closest_point))
        return closest_point, closest_point_heading, s_values[idx_min], t

    def get_section_idx_and_s(self, s):
        '''
            Return the index of the geometry section with the given s and the s
            value realtive to the start of the section.
        '''
        idx_section = 0
        s_acc = 0
        s_section = 0
        for idx in range(len(self.sections)):
            s_section = s - s_acc
            s_acc += self.sections[idx]['length']
            if s <= s_acc:
                idx_section = idx
                break
        return idx_section, s_section

    def get_elevation(self, s):
        '''
            Return the elevation level for the given value of s in the
            geometry section with the given index and its curvature.
        '''
        idx_section, s_section = self.get_section_idx_and_s(s)
        idx_elevation = 0
        while idx_elevation < len(self.sections[idx_section]['elevation'])-1:
            if s_section >= self.sections[idx_section]['elevation'][idx_elevation+1]['s_section']:
                idx_elevation += 1
            else:
                break
        elevation = self.sections[idx_section]['elevation'][idx_elevation]
        # Calculate curvature of the elevation function
        # TODO convert curvature for t unequal 0
        d2e_d2s = 2 * elevation['c'] + 3 * elevation['d'] * s_section
        if d2e_d2s != 0:
            de_ds = elevation['b']+ 2 * elevation['c'] * s_section + 3 * elevation['d'] * s_section
            curvature_elevation = (1 + de_ds**2)**(3/2) / d2e_d2s
        else:
            curvature_elevation = 0
        z = elevation['a'] + \
            elevation['b'] * s_section + \
            elevation['c'] * s_section**2 + \
            elevation['d'] * s_section**3
        return z, curvature_elevation

    def sample_cross_section(self, s, t_vec):
        '''
            Sample a cross section (multiple t values) in the local coordinate
            system. Also return corresponding curvature and heading of the
            reference line.
        '''
        x_s, y_s, hdg, curvature_plan_view = self.sample_plan_view(s)
        z, curvature_elevation = self.get_elevation(s)
        curvature_abs = max(abs(curvature_plan_view), abs(curvature_elevation))
        vector_hdg_t = Vector((1.0, 0.0))
        vector_hdg_t.rotate(Matrix.Rotation(hdg + pi/2, 2))
        xyz = []
        for t in t_vec:
            xy_vec = Vector((x_s, y_s)) + t * vector_hdg_t
            xyz += [(xy_vec.x, xy_vec.y, z)]
        return xyz, hdg, curvature_abs

