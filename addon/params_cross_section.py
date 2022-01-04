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

params_cross_section = {
    'two_lanes_default' : {
        'directions' : ['left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right'],
        'widths' : [0.0, 0.20, 0.0, 3.75, 0.0, 3.75, 0.0, 0.20, 0.0],
        'types' : ['line', 'border', 'line', 'driving', 'line', 'driving', 'line', 'border', 'line'],
        'road_mark_types' : ['none', 'none', 'solid', 'none', 'broken', 'none', 'solid', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'standard', 'none', 'standard', 'none', 'standard', 'none', 'none'],
        'road_mark_colors' : ['none', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'none'],
    },
    # Typical German road cross sections
    # See:
    #   https://de.wikipedia.org/wiki/Richtlinien_f%C3%BCr_die_Anlage_von_Stra%C3%9Fen_%E2%80%93_Querschnitt
    #   https://de.wikipedia.org/wiki/Richtlinien_f%C3%BCr_die_Anlage_von_Autobahnen
    #   https://de.wikipedia.org/wiki/Entwurfsklasse
    #   https://www.beton.wiki/index.php?title=Regelquerschnitt_im_Stra%C3%9Fenbau
    #   https://www.vsvi-mv.de/fileadmin/Medienpool/Seminarunterlagen/Seminare_2012/Vortrag_1_-_neue_RAL_Frau_Vetters.pdf
    #   https://dsgs.de/leitfaden-fahrbahnmarkierung1.html
    #
    'ekl4_rq9' : {
        'directions' : ['left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right', 'right', 'right'],
        'widths' : [0.0, 1.5, 0.0, 0.5, 0.0, 3.5, 0.0, 0.5, 0.0, 1.5, 0.0],
        'types' : ['line', 'shoulder', 'line', 'border', 'line', 'driving', 'line', 'border', 'line', 'shoulder', 'line'],
        'road_mark_types' : ['none', 'none', 'none', 'none', 'broken', 'none', 'broken', 'none', 'none', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'none', 'none', 'standard', 'none', 'standard', 'none', 'none', 'none', 'none'],
        'road_mark_colors' : ['none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'none', 'none', 'none'],
    },
    'ekl3_rq11' : {
        'directions' : ['left', 'left', 'left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right', 'right', 'right'],
        'widths' : [0.0, 1.5, 0.0, 0.50, 0.0, 3.5, 0.0, 3.5, 0.0, 0.50, 0.0, 1.5, 0.0],
        'types' : ['line', 'shoulder', 'line', 'border', 'line', 'driving', 'line', 'driving', 'line', 'border', 'line', 'shoulder', 'line'],
        'road_mark_types' : ['none', 'none', 'none', 'none', 'solid', 'none', 'broken', 'none', 'solid', 'none', 'none', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'none', 'none', 'standard', 'none', 'standard', 'none', 'standard', 'none', 'none', 'none', 'none'],
        'road_mark_colors' : ['none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'none', 'none', 'none'],
    },
    'eka1_rq31' : {
        'directions' : ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
        'widths' : [0.0, 1.5, 0.0, 3.0, 0.0, 0.75, 0.0, 3.75, 0.0, 3.75, 0.0, 0.75, 0.0, 2.0, 0.0, 2.0, 0.0, 0.75, 0.0, 3.75, 0.0, 3.75, 0.0, 0.75, 0.0, 3.0, 0.0, 1.5, 0.0],
        'types' : ['line', 'shoulder', 'line', 'stop', 'line', 'border', 'line', 'driving', 'line', 'driving', 'line', 'border', 'line', 'median', 'line', 'median', 'line', 'border', 'line', 'driving', 'line', 'driving', 'line', 'border', 'line', 'stop', 'line', 'shoulder', 'line'],
        'road_mark_types' : ['none', 'none', 'none', 'none', 'none', 'none', 'solid', 'none', 'broken', 'none', 'solid', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'solid', 'none', 'broken', 'none', 'solid', 'none', 'none', 'none', 'none', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'none', 'none', 'none', 'none', 'standard', 'none', 'standard', 'none', 'bold', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'bold', 'none', 'standard', 'none', 'standard', 'none', 'none', 'none', 'none', 'none', 'none'],
        'road_mark_colors' : ['none', 'none', 'none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'none', 'none', 'none', 'none', 'none'],
    },
    'eka1_rq36' : {
        'directions' : ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
        'widths' : [0.0, 1.5, 0.0, 2.5, 0.0, 0.5, 0.0, 3.75, 0.0, 3.5, 0.0, 3.5, 0.0, 0.75, 0.0, 2.0, 0.0, 2.0, 0.0, 0.75, 0.0, 3.5, 0.0, 3.5, 0.0, 3.75, 0.0, 0.5, 0.0, 2.5, 0.0, 1.5, 0.0],
        'types' : ['line', 'shoulder', 'line', 'stop', 'line', 'border', 'line', 'driving', 'line', 'driving', 'line', 'driving', 'line', 'border', 'line', 'median', 'line', 'median', 'line', 'border', 'line', 'driving', 'line', 'driving', 'line', 'driving', 'line', 'border', 'line', 'stop', 'line', 'shoulder', 'line'],
        'road_mark_types' : ['none', 'none', 'none', 'none', 'none', 'none', 'solid', 'none', 'broken', 'none', 'broken', 'none', 'solid', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'solid', 'none', 'broken', 'none', 'broken', 'none', 'solid', 'none', 'none', 'none', 'none', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'none', 'none', 'none', 'none', 'standard', 'none', 'standard', 'none', 'standard', 'none', 'bold', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'bold', 'none', 'standard', 'none', 'standard', 'none', 'standard', 'none', 'none', 'none', 'none', 'none', 'none'],
        'road_mark_colors' : ['none', 'none', 'none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'none', 'none', 'none', 'none', 'none'],
    },
    'eka1_rq36_exit_right' : {
        'directions' : ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
        'widths' : [0.0, 1.5, 0.0, 2.5, 0.0, 0.5, 0.0, 3.75, 0.0, 3.5, 0.0, 3.5, 0.0, 0.75, 0.0, 2.0, 0.0, 2.0, 0.0, 0.75, 0.0, 3.5, 0.0, 3.5, 0.0],
        'types' : ['line', 'shoulder', 'line', 'stop', 'line', 'border', 'line', 'driving', 'line', 'driving', 'line', 'driving', 'line', 'border', 'line', 'median', 'line', 'median', 'line', 'border', 'line', 'driving', 'line', 'driving', 'line'],
        'road_mark_types' : ['none', 'none', 'none', 'none', 'none', 'none', 'solid', 'none', 'broken', 'none', 'broken', 'none', 'solid', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'solid', 'none', 'broken', 'none', 'solid'],
        'road_mark_weights' : ['none', 'none', 'none', 'none', 'none', 'none', 'standard', 'none', 'standard', 'none', 'standard', 'none', 'bold', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'bold', 'none', 'standard', 'none', 'standard'],
        'road_mark_colors' : ['none', 'none', 'none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'white'],
    },
    'eka1_rq43_5' : {
        'directions' : ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
        'widths' : [0.0, 2.5, 0.0, 2.5, 0.0, 0.5, 0.0, 3.75, 0.0, 3.75, 0.0, 3.5, 0.0, 3.5, 0.0, 0.75, 0.0, 2.0, 0.0, 2.0, 0.0, 0.75, 0.0, 3.5, 0.0, 3.5, 0.0, 3.75, 0.0, 3.75, 0.0, 0.5, 0.0, 2.5, 0.0, 2.5, 0.0],
        'types' : ['line', 'shoulder', 'line', 'stop', 'line', 'border', 'line', 'driving', 'line', 'driving', 'line', 'driving', 'line', 'driving', 'line', 'border', 'line', 'median', 'line', 'median', 'line', 'border', 'line', 'driving', 'line', 'driving', 'line', 'driving', 'line', 'driving', 'line', 'border', 'line', 'stop', 'line', 'shoulder', 'line'],
        'road_mark_types' : ['none', 'none', 'none', 'none', 'none', 'none', 'solid', 'none', 'broken', 'none', 'broken', 'none', 'broken', 'none', 'solid', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'solid', 'none', 'broken', 'none', 'broken', 'none', 'broken', 'none', 'solid', 'none', 'none', 'none', 'none', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'none', 'none', 'none', 'none', 'standard', 'none', 'standard', 'none', 'standard', 'none', 'standard', 'none', 'bold', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'bold', 'none', 'standard', 'none', 'standard', 'none', 'standard', 'none', 'standard', 'none', 'none', 'none', 'none', 'none', 'none'],
        'road_mark_colors' : ['none', 'none', 'none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'none', 'none', 'none', 'none', 'none', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'white', 'none', 'none', 'none', 'none', 'none', 'none'],
    },
}
