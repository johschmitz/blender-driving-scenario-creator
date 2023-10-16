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

from .geometry import DSC_geometry

from mathutils import Vector
from math import pi
from pyclothoids import SolveG2


class Clothoid_triple():

    def __init__(self, point_start, heading_start, curvature_start,
                 point_end, heading_end, curvature_end, matrix_local2global):
        self.matrix_local2global = matrix_local2global
        self.segments = SolveG2(
            point_start.x, point_start.y, heading_start, curvature_start,
            point_end.x, point_end.y, heading_end, curvature_end)
        
    def length(self):
        return sum((self.segments[0].length, self.segments[1].length, self.segments[2].length))

    def get_segment_params(self):
        heading_rotation = self.matrix_local2global.to_euler().z
        return [ {'point_start': self.matrix_local2global @ Vector((segment.XStart, segment.YStart, 0.0)),
                  'heading_start': segment.ThetaStart + heading_rotation,
                  'heading_end': segment.ThetaEnd + heading_rotation,
                  'curvature_start': segment.KappaStart,
                  'curvature_end': segment.KappaEnd,
                  'length': segment.length,}
                  for segment in self.segments ]

class DSC_geometry_clothoid_triple(DSC_geometry):

    def __init__(self):
        super().__init__(curve_type='spiral_triple')

    def update_plan_view(self, params, geometry_solver='default'):
        # Calculate geometry
        self.sections[-1]['curve'] = Clothoid_triple(
            self.point_start_local, self.heading_start_local, self.curvature_start_local,
            self.point_end_local, self.heading_end_local, self.curvature_end_local, self.matrix_world)

        # Avoid gigantic road sections
        if self.sections[-1]['curve'].length() > 10000.0:
            self.sections[-1]['params']['valid'] = False
        else:
            # Remember geometry parameters
            self.sections[-1]['params']['valid'] = True
            self.sections[-1]['params']['curve_type'] = 'spiral_triple'
            self.sections[-1]['params']['point_start'] = params['points'][-2]
            self.sections[-1]['params']['heading_start'] = params['heading_start'] + self.heading_start_local
            self.sections[-1]['params']['point_end'] = params['points'][-1]
            self.sections[-1]['params']['heading_end'] = params['heading_start'] + self.sections[-1]['curve'].segments[-1].ThetaEnd
            self.sections[-1]['params']['length'] = self.sections[-1]['curve'].length()
            self.sections[-1]['params']['curvature_start'] = self.sections[-1]['curve'].segments[0].KappaStart
            self.sections[-1]['params']['curvature_end'] = self.sections[-1]['curve'].segments[-1].KappaEnd
            self.sections[-1]['params']['angle_end'] = self.sections[-1]['curve'].segments[-1].ThetaEnd

    def sample_plan_view(self, s):
        idx_section, s_section = self.get_section_idx_and_s(s)

        # Find the s value in the right segment of the triple clothoid
        s_segment = s_section
        idx_segment = 0
        for idx in range(2):
            length_segment = self.sections[idx_section]['curve'].segments[idx].length
            if s_segment <= length_segment and idx_segment <= 2:
                break
            idx_segment += 1
            s_segment -= length_segment

        x_s = self.sections[idx_section]['curve'].segments[idx_segment].X(s_segment)
        y_s = self.sections[idx_section]['curve'].segments[idx_segment].Y(s_segment)
        curvature = self.sections[idx_section]['curve'].segments[idx_segment].KappaStart \
                  + self.sections[idx_section]['curve'].segments[idx_segment].dk * s_segment
        hdg_t = self.sections[idx_section]['curve'].segments[idx_segment].Theta(s_segment) + pi/2
        return x_s, y_s, curvature, hdg_t
