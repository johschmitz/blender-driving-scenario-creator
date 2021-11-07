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
from pyclothoids import Clothoid
from math import pi


class DSC_geometry_clothoid(DSC_geometry):

    def update_plan_view(self, params):
        # Calculate transform between global and local coordinates
        self.update_local_to_global(params['point_start'], params['heading_start'],
            params['point_end'], params['heading_end'])

        # Calculate geometry
        self.geometry_base = Clothoid.G1Hermite(0, 0, 0,
            self.point_end_local.x, self.point_end_local.y, self.heading_end_local)

        # Remember geometry parameters
        self.params['curve'] = 'spiral'
        self.params['point_start'] = params['point_start']
        self.params['heading_start'] = params['heading_start']
        self.params['point_end'] = params['point_end']
        self.params['heading_end'] = params['heading_start'] + self.geometry_base.ThetaEnd
        self.params['length'] = self.geometry_base.length
        self.params['curvature_start'] = self.geometry_base.KappaStart
        self.params['curvature_end'] = self.geometry_base.KappaEnd
        self.params['angle_end'] = self.geometry_base.ThetaEnd

    def sample_plan_view(self, s):
        x_s = self.geometry_base.X(s)
        y_s = self.geometry_base.Y(s)
        curvature = self.geometry_base.KappaStart + self.geometry_base.dk * s
        hdg_t = self.geometry_base.Theta(s) + pi/2
        return x_s, y_s, curvature, hdg_t
