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
        'sides' : ['left', 'left', 'center', 'right', 'right'],
        'widths' : [0.20, 3.75, 0.0, 3.75, 0.20],
        'types' : ['border', 'driving', 'center', 'driving', 'border'],
        'road_mark_types' : ['none', 'solid', 'broken', 'solid', 'none'],
        'road_mark_weights' : ['none', 'standard', 'standard', 'standard', 'none'],
        'road_mark_widths' : [0.0, 0.12, 0.12, 0.12, 0.0],
        'road_mark_colors' : ['none', 'white', 'white', 'white', 'none'],
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
        'sides' : ['left', 'left', 'center', 'right', 'right', 'right'],
        'widths' : [1.5, 0.5, 0.0, 3.5, 0.5, 1.5],
        'types' : ['shoulder', 'border', 'center', 'driving', 'border', 'shoulder'],
        'road_mark_types' : ['none', 'none', 'broken', 'broken', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'standard', 'standard', 'none', 'none'],
        'road_mark_widths' : [0.0, 0.0, 0.12, 0.12, 0.0, 0.0],
        'road_mark_colors' : ['none', 'none', 'white', 'white', 'none', 'none'],
    },
    'ekl3_rq11' : {
        'sides' : ['left', 'left', 'left', 'center', 'right', 'right', 'right'],
        'widths' : [1.5, 0.50, 3.5, 0.0, 3.5, 0.50, 1.5],
        'types' : ['shoulder', 'border', 'driving', 'center', 'driving', 'border', 'shoulder'],
        'road_mark_types' : ['none', 'none', 'solid', 'broken', 'solid', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'standard', 'standard', 'standard', 'none', 'none'],
        'road_mark_widths' : [0.0, 0.0, 0.12, 0.12, 0.12, 0.0, 0.0],
        'road_mark_colors' : ['none', 'none', 'white', 'white', 'white', 'none', 'none'],
    },
    'eka1_rq31' : {
        'sides' : ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
        'widths' : [1.5, 3.0, 0.75, 3.75, 3.75, 0.75, 2.0, 0.0, 2.0, 0.75, 3.75, 3.75, 0.75, 3.0, 1.5],
        'types' : ['shoulder', 'stop', 'border', 'driving', 'driving', 'border', 'median', 'center', 'median', 'border', 'driving', 'driving', 'border', 'stop', 'shoulder'],
        'road_mark_types' : ['none', 'none', 'none', 'solid', 'broken', 'solid', 'none', 'none', 'none', 'solid', 'broken', 'solid', 'none', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'none', 'bold', 'standard', 'bold', 'none', 'none', 'none', 'bold', 'standard', 'bold', 'none', 'none', 'none'],
        'road_mark_widths' : [0.0, 0.0, 0.0, 0.30, 0.15, 0.30, 0.0, 0.0, 0.0, 0.30, 0.15, 0.30, 0.0, 0.0, 0.0],
        'road_mark_colors' : ['none', 'none', 'none', 'white', 'white', 'white', 'none', 'none', 'none', 'white', 'white', 'white', 'none', 'none', 'none'],
    },
    'eka1_rq36' : {
        'sides' : ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
        'widths' : [1.5, 2.5, 0.5, 3.75, 3.5, 3.5, 0.75, 2.0, 0.0, 2.0, 0.75, 3.5, 3.5, 3.75, 0.5, 2.5, 1.5],
        'types' : ['shoulder', 'stop', 'border', 'driving', 'driving', 'driving', 'border', 'median', 'center', 'median', 'border', 'driving', 'driving', 'driving', 'border', 'stop', 'shoulder'],
        'road_mark_types' : ['none', 'none', 'none', 'solid', 'broken', 'broken', 'solid', 'none', 'none', 'none', 'solid', 'broken', 'broken', 'solid', 'none', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'none', 'bold', 'standard', 'standard', 'bold', 'none', 'none', 'none', 'bold', 'standard', 'standard', 'bold', 'none', 'none', 'none'],
        'road_mark_widths' : [0.0, 0.0, 0.0, 0.30, 0.15, 0.15, 0.30, 0.0, 0.0, 0.0, 0.30, 0.15, 0.15, 0.30, 0.0, 0.0, 0.0],
        'road_mark_colors' : ['none', 'none', 'none', 'white', 'white', 'white', 'white', 'none', 'none', 'none', 'white', 'white', 'white', 'white', 'none', 'none', 'none'],
    },
    'eka1_rq36_exit_right' : {
        'sides' : ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right'],
        'widths' : [1.5, 2.5, 0.5, 3.75, 3.5, 3.5, 0.75, 2.0, 0.0, 2.0, 0.75, 3.5, 3.5],
        'types' : ['shoulder', 'stop', 'border', 'driving', 'driving', 'driving', 'border', 'median', 'center', 'median', 'border', 'driving', 'driving'],
        'road_mark_types' : ['none', 'none', 'none', 'solid', 'broken', 'broken', 'solid', 'none', 'none', 'none', 'solid', 'broken', 'solid'],
        'road_mark_weights' : ['none', 'none', 'none', 'bold', 'standard', 'standard', 'bold', 'none', 'none', 'none', 'bold', 'standard', 'standard'],
        'road_mark_widths' : [0.0, 0.0, 0.0, 0.30, 0.15, 0.15, 0.30, 0.0, 0.0, 0.0, 0.30, 0.15, 0.12],
        'road_mark_colors' : ['none', 'none', 'none', 'white', 'white', 'white', 'white', 'none', 'none', 'none', 'white', 'white', 'white'],
    },
    'eka1_rq43_5' : {
        'sides' : ['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'center', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
        'widths' : [2.5, 2.5, 0.5, 3.75, 3.75, 3.5, 3.5, 0.75, 2.0, 0.0, 2.0, 0.75, 3.5, 3.5, 3.75, 3.75, 0.5, 2.5, 2.5],
        'types' : ['shoulder', 'stop', 'border', 'driving', 'driving', 'driving', 'driving', 'border', 'median', 'center', 'median', 'border', 'driving', 'driving', 'driving', 'driving', 'border', 'stop', 'shoulder'],
        'road_mark_types' : ['none', 'none', 'none', 'solid', 'broken', 'broken', 'broken', 'solid', 'none', 'none', 'none', 'solid', 'broken', 'broken', 'broken', 'solid', 'none', 'none', 'none'],
        'road_mark_weights' : ['none', 'none', 'none', 'bold', 'standard', 'standard', 'standard', 'bold', 'none', 'none', 'none', 'bold', 'standard', 'standard', 'standard', 'bold', 'none', 'none', 'none'],
        'road_mark_widths' : [0.0, 0.0, 0.0, 0.30, 0.15, 0.15, 0.15, 0.30, 0.0, 0.0, 0.0, 0.30, 0.15, 0.15, 0.15, 0.30, 0.0, 0.0, 0.0],
        'road_mark_colors' : ['none', 'none', 'none', 'white', 'white', 'white', 'white', 'white', 'none', 'none', 'none', 'white', 'white', 'white', 'white', 'white', 'none', 'none', 'none'],
    },
}
