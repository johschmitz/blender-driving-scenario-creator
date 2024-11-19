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

import bpy
import os
from mathutils import Matrix

from math import pi

from . import helpers


def get_road_stencil_mesh_mapping():
    """Return vertices, edges and faces of the different road stencils."""
    road_stencil_type_subtype_mapping = {
        'fahrbahnmarkierung_pfeil_g': {
            'vertices': [
                (3.000059, -0.239954, 0.000000),(5.000099, 0.000000, 0.000000),(3.000059, 0.239954, 0.000000),
                (3.000059, 0.079985, 0.000000),(0.000000, 0.119977, 0.000000),(0.000000, -0.119977, 0.000000),
                (3.000059, -0.079985, 0.000000),(0.000000, 0.000000, 0.000000),
            ],
            'edges': [
                (0, 1),(1, 2),(2, 3),(3, 4),(7, 5),(5, 6),(1, 6),(1, 3),(0, 6),(4, 7),(7, 6),(6, 4),(6, 3),
            ],
            'faces': [
                (3, 1, 2),(6, 0, 1),(7, 6, 4),(5, 6, 7),(6, 1, 3),(3, 4, 6),
            ],
        },
        'fahrbahnmarkierung_pfeil_gl': {
            'vertices': [
                (1.199771, 0.104002, 0.000000),(1.236089, 0.104648, 0.000000),(1.272051, 0.106569, 0.000000),
                (1.307550, 0.109742, 0.000000),(1.342481, 0.114143, 0.000000),(1.376735, 0.119749, 0.000000),
                (1.410206, 0.126534, 0.000000),(1.442787, 0.134476, 0.000000),(1.474372, 0.143551, 0.000000),
                (1.504852, 0.153734, 0.000000),(1.534123, 0.165003, 0.000000),(1.562076, 0.177333, 0.000000),
                (1.588605, 0.190700, 0.000000),(1.613437, 0.204980, 0.000000),(1.636343, 0.220027, 0.000000),
                (1.657276, 0.235784, 0.000000),(1.676195, 0.252191, 0.000000),(1.693053, 0.269193, 0.000000),
                (1.707807, 0.286731, 0.000000),(1.720412, 0.304749, 0.000000),(1.730825, 0.323188, 0.000000),
                (1.739001, 0.341990, 0.000000),(1.744896, 0.361100, 0.000000),(1.748466, 0.380458, 0.000000),
                (1.749665, 0.400008, 0.000000),(1.738846, 0.400008, 0.000000),(1.708932, 0.400008, 0.000000),
                (1.663744, 0.400008, 0.000000),(1.607100, 0.400008, 0.000000),(1.542818, 0.400008, 0.000000),
                (1.474718, 0.400008, 0.000000),(1.406618, 0.400008, 0.000000),(1.342336, 0.400008, 0.000000),
                (1.285692, 0.400008, 0.000000),(1.240504, 0.400008, 0.000000),(1.210590, 0.400008, 0.000000),
                (1.199771, 0.400008, 0.000000),(1.899637, 0.700014, 0.000000),(2.799464, 0.400008, 0.000000),
                (2.149589, 0.400008, 0.000000),(2.147516, 0.366720, 0.000000),(2.141351, 0.333759, 0.000000),
                (2.131169, 0.301221, 0.000000),(2.117047, 0.269205, 0.000000),(2.099061, 0.237809, 0.000000),
                (2.077288, 0.207131, 0.000000),(2.051803, 0.177269, 0.000000),(2.022685, 0.148320, 0.000000),
                (1.990008, 0.120383, 0.000000),(0.000000, 0.000000, 0.000000),(0.000000, 0.120002, 0.000000),
                (2.999426, 0.080001, 0.000000),(2.999426, 0.240005, 0.000000),(4.999043, -0.000000, 0.000000),
                (2.999426, -0.240005, 0.000000),(2.999426, -0.080002, 0.000000),
                (-0.000000, -0.120002, 0.000000),(1.953849, 0.093945, 0.000000),
            ],
            'edges': [
                (0, 1),(2, 3),(4, 5),(6, 7),(8, 9),(10, 11),(12, 13),(14, 15),(16, 17),(18, 19),(20, 21),
                (22, 23),(24, 25),(26, 27),(28, 29),(30, 31),(32, 33),(34, 35),(24, 37),(38, 39),(40, 41),
                (42, 43),(44, 45),(46, 47),(25, 26),(27, 37),(29, 37),(31, 37),(33, 37),(35, 36),(35, 37),
                (37, 40),(37, 42),(1, 2),(3, 4),(37, 44),(7, 8),(9, 10),(11, 12),(13, 14),(37, 46),(17, 18),
                (19, 20),(21, 22),(23, 24),(37, 48),(27, 28),(29, 30),(31, 32),(33, 34),(25, 37),(37, 38),
                (37, 39),(39, 40),(37, 41),(41, 42),(37, 43),(43, 44),(37, 45),(45, 46),(37, 47),(47, 48),
                (5, 6),(50, 0),(26, 37),(28, 37),(30, 37),(32, 37),(15, 16),(34, 37),(36, 37),(57, 51),(51, 55),
                (52, 53),(53, 54),(52, 54),(55, 56),(51, 56),(52, 55),(51, 52),(54, 55),(49, 56),(50, 49),
                (37, 57),(0, 57),(48, 57),(0, 49),(56, 57),(57, 49),(1, 57),(2, 57),(57, 24),(57, 23),(3, 57),
                (4, 57),(57, 22),(57, 21),(5, 57),(6, 57),(57, 20),(57, 19),(7, 57),(8, 57),(57, 18),(57, 17),
                (9, 57),(10, 57),(57, 16),(57, 15),(11, 57),(12, 57),(57, 14),(13, 57),
            ],
            'faces': [
                (39, 38, 37),(40, 39, 37),(41, 40, 37),(42, 41, 37),(43, 42, 37),(44, 43, 37),(45, 44, 37),
                (46, 45, 37),(47, 46, 37),(48, 47, 37),(57, 48, 37),(24, 37, 25),(25, 37, 26),(26, 37, 27),
                (27, 37, 28),(28, 37, 29),(29, 37, 30),(30, 37, 31),(31, 37, 32),(32, 37, 33),(33, 37, 34),
                (34, 37, 35),(35, 37, 36),(54, 53, 52),(55, 54, 52),(56, 55, 51),(51, 55, 52),(0, 50, 49),
                (56, 57, 49),(57, 0, 49),(57, 56, 51),(13, 57, 14),(57, 1, 0),(57, 2, 1),(24, 57, 37),
                (23, 57, 24),(57, 3, 2),(57, 4, 3),(22, 57, 23),(21, 57, 22),(57, 5, 4),(57, 6, 5),(20, 57, 21),
                (19, 57, 20),(57, 7, 6),(57, 8, 7),(18, 57, 19),(17, 57, 18),(57, 9, 8),(57, 10, 9),
                (16, 57, 17),(15, 57, 16),(57, 11, 10),(57, 12, 11),(14, 57, 15),(57, 13, 12),
            ]
        },
        'fahrbahnmarkierung_pfeil_gr': {
            'vertices': [
                (1.199771, -0.104002, 0.000000),(1.236089, -0.104648, 0.000000),(1.272051, -0.106569, 0.000000),
                (1.307550, -0.109742, 0.000000),(1.342481, -0.114143, 0.000000),(1.376735, -0.119749, 0.000000),
                (1.410206, -0.126534, 0.000000),(1.442787, -0.134476, 0.000000),(1.474372, -0.143551, 0.000000),
                (1.504852, -0.153734, 0.000000),(1.534123, -0.165003, 0.000000),(1.562076, -0.177333, 0.000000),
                (1.588605, -0.190700, 0.000000),(1.613437, -0.204980, 0.000000),(1.636343, -0.220027, 0.000000),
                (1.657276, -0.235784, 0.000000),(1.676195, -0.252191, 0.000000),(1.693053, -0.269193, 0.000000),
                (1.707807, -0.286731, 0.000000),(1.720412, -0.304749, 0.000000),(1.730825, -0.323188, 0.000000),
                (1.739001, -0.341990, 0.000000),(1.744896, -0.361100, 0.000000),(1.748466, -0.380458, 0.000000),
                (1.749665, -0.400008, 0.000000),(1.738846, -0.400008, 0.000000),(1.708932, -0.400008, 0.000000),
                (1.663744, -0.400008, 0.000000),(1.607100, -0.400008, 0.000000),(1.542818, -0.400008, 0.000000),
                (1.474718, -0.400008, 0.000000),(1.406618, -0.400008, 0.000000),(1.342336, -0.400008, 0.000000),
                (1.285692, -0.400008, 0.000000),(1.240504, -0.400008, 0.000000),(1.210590, -0.400008, 0.000000),
                (1.199771, -0.400008, 0.000000),(1.899637, -0.700014, 0.000000),(2.799464, -0.400008, 0.000000),
                (2.149589, -0.400008, 0.000000),(2.147516, -0.366720, 0.000000),(2.141351, -0.333759, 0.000000),
                (2.131169, -0.301221, 0.000000),(2.117047, -0.269205, 0.000000),(2.099061, -0.237809, 0.000000),
                (2.077288, -0.207131, 0.000000),(2.051803, -0.177269, 0.000000),(2.022685, -0.148320, 0.000000),
                (1.990008, -0.120383, 0.000000),(0.000000, 0.000000, 0.000000),(0.000000, -0.120002, 0.000000),
                (2.999426, -0.080001, 0.000000),(2.999426, -0.240005, 0.000000),(4.999043, 0.000000, 0.000000),
                (2.999426, 0.240005, 0.000000),(2.999426, 0.080002, 0.000000),(-0.000000, 0.120002, 0.000000),
                (1.953849, -0.093945, 0.000000),
            ],
            'edges': [
                (0, 1),(2, 3),(4, 5),(6, 7),(8, 9),(10, 11),(12, 13),(14, 15),(16, 17),(18, 19),(20, 21),
                (22, 23),(24, 25),(26, 27),(28, 29),(30, 31),(32, 33),(34, 35),(24, 37),(38, 39),(40, 41),
                (42, 43),(44, 45),(46, 47),(25, 26),(27, 37),(29, 37),(31, 37),(33, 37),(35, 36),(35, 37),
                (37, 40),(37, 42),(1, 2),(3, 4),(37, 44),(7, 8),(9, 10),(11, 12),(13, 14),(37, 46),(17, 18),
                (19, 20),(21, 22),(23, 24),(37, 48),(27, 28),(29, 30),(31, 32),(33, 34),(25, 37),(37, 38),
                (37, 39),(39, 40),(37, 41),(41, 42),(37, 43),(43, 44),(37, 45),(45, 46),(37, 47),(47, 48),
                (5, 6),(50, 0),(26, 37),(28, 37),(30, 37),(32, 37),(15, 16),(34, 37),(36, 37),(57, 51),(51, 55),
                (52, 53),(53, 54),(52, 54),(55, 56),(51, 56),(52, 55),(51, 52),(54, 55),(49, 56),(50, 49),
                (37, 57),(0, 57),(48, 57),(0, 49),(56, 57),(57, 49),(1, 57),(2, 57),(57, 24),(57, 23),(3, 57),
                (4, 57),(57, 22),(57, 21),(5, 57),(6, 57),(57, 20),(57, 19),(7, 57),(8, 57),(57, 18),(57, 17),
                (9, 57),(10, 57),(57, 16),(57, 15),(11, 57),(12, 57),(57, 14),(13, 57),
            ],
            'faces': [
                (39, 37, 38),(40, 37, 39),(41, 37, 40),(42, 37, 41),(43, 37, 42),(44, 37, 43),(45, 37, 44),
                (46, 37, 45),(47, 37, 46),(48, 37, 47),(57, 37, 48),(24, 25, 37),(25, 26, 37),(26, 27, 37),
                (27, 28, 37),(28, 29, 37),(29, 30, 37),(30, 31, 37),(31, 32, 37),(32, 33, 37),(33, 34, 37),
                (34, 35, 37),(35, 36, 37),(54, 52, 53),(55, 52, 54),(56, 51, 55),(51, 52, 55),(0, 49, 50),
                (56, 49, 57),(57, 49, 0),(57, 51, 56),(13, 14, 57),(57, 0, 1),(57, 1, 2),(24, 37, 57),
                (23, 24, 57),(57, 2, 3),(57, 3, 4),(22, 23, 57),(21, 22, 57),(57, 4, 5),(57, 5, 6),(20, 21, 57),
                (19, 20, 57),(57, 6, 7),(57, 7, 8),(18, 19, 57),(17, 18, 57),(57, 8, 9),(57, 9, 10),
                (16, 17, 57),(15, 16, 57),(57, 10, 11),(57, 11, 12),(14, 15, 57),(57, 12, 13),
            ],
        },
        'fahrbahnmarkierung_pfeil_l': {
            'vertices': [
                (-0.000000, -0.120002, 0.000000),(2.999426, -0.080001, 0.000000),
                (3.058855, -0.079173, 0.000000),(3.117703, -0.076706, 0.000000),(3.175793, -0.072632, 0.000000),
                (3.232952, -0.066982, 0.000000),(3.289004, -0.059786, 0.000000),(3.343775, -0.051075, 0.000000),
                (3.397090, -0.040879, 0.000000),(3.448773, -0.029229, 0.000000),(3.498651, -0.016156, 0.000000),
                (3.546548, -0.001689, 0.000000),(3.592289, 0.014139, 0.000000),(3.635700, 0.031300, 0.000000),
                (3.676335, 0.049633, 0.000000),(3.713816, 0.068950, 0.000000),(3.748072, 0.089178, 0.000000),
                (3.779029, 0.110241, 0.000000),(3.806615, 0.132068, 0.000000),(3.830758, 0.154583, 0.000000),
                (3.851386, 0.177714, 0.000000),(3.868425, 0.201385, 0.000000),(3.881804, 0.225524, 0.000000),
                (3.891450, 0.250056, 0.000000),(3.897291, 0.274908, 0.000000),(3.899254, 0.300006, 0.000000),
                (3.920893, 0.300006, 0.000000),(3.980720, 0.300006, 0.000000),(4.071096, 0.300006, 0.000000),
                (4.184384, 0.300006, 0.000000),(4.312948, 0.300006, 0.000000),(4.449149, 0.300006, 0.000000),
                (4.585350, 0.300006, 0.000000),(4.713913, 0.300006, 0.000000),(4.827201, 0.300006, 0.000000),
                (4.917578, 0.300006, 0.000000),(4.977404, 0.300006, 0.000000),(4.999043, 0.300006, 0.000000),
                (3.599311, 0.600012, 0.000000),(2.499521, 0.300006, 0.000000),(3.399349, 0.300006, 0.000000),
                (3.398477, 0.285476, 0.000000),(3.395881, 0.271088, 0.000000),(3.391594, 0.256885, 0.000000),
                (3.385648, 0.242910, 0.000000),(3.378075, 0.229205, 0.000000),(3.368907, 0.215814, 0.000000),
                (3.358177, 0.202779, 0.000000),(3.345916, 0.190142, 0.000000),(3.332157, 0.177947, 0.000000),
                (3.316933, 0.166237, 0.000000),(3.300274, 0.155053, 0.000000),(3.282214, 0.144439, 0.000000),
                (3.262921, 0.134504, 0.000000),(3.242591, 0.125340, 0.000000),(3.221304, 0.116965, 0.000000),
                (3.199136, 0.109396, 0.000000),(3.176165, 0.102651, 0.000000),(3.152470, 0.096748, 0.000000),
                (3.128127, 0.091705, 0.000000),(3.103215, 0.087539, 0.000000),(3.077811, 0.084268, 0.000000),
                (3.051993, 0.081910, 0.000000),(3.025839, 0.080482, 0.000000),(2.999426, 0.080002, 0.000000),
                (-0.000000, 0.000000, 0.000000),(-0.000000, 0.120003, 0.000000),
            ],
            'edges': [
                (0, 1),(2, 3),(4, 5),(6, 7),(8, 9),(10, 11),(7, 42),(12, 13),(14, 15),(16, 17),(9, 40),(18, 19),
                (63, 64),(20, 21),(7, 44),(22, 23),(24, 25),(26, 27),(28, 29),(30, 31),(7, 46),(32, 33),
                (11, 40),(34, 35),(36, 37),(36, 38),(38, 39),(13, 38),(40, 41),(8, 42),(42, 43),(44, 45),
                (5, 52),(46, 47),(48, 49),(6, 50),(50, 51),(6, 52),(52, 53),(54, 55),(15, 38),(56, 57),(4, 58),
                (58, 59),(3, 58),(60, 61),(2, 62),(62, 63),(1, 62),(1, 63),(3, 60),(17, 38),(64, 65),(1, 64),
                (65, 66),(19, 38),(21, 38),(23, 38),(25, 38),(27, 38),(29, 38),(61, 62),(31, 38),(33, 38),
                (7, 48),(35, 38),(5, 53),(1, 2),(3, 4),(5, 6),(7, 8),(9, 10),(11, 12),(13, 14),(8, 41),(15, 16),
                (17, 18),(19, 20),(21, 22),(23, 24),(4, 55),(25, 26),(27, 28),(29, 30),(31, 32),(33, 34),
                (35, 36),(37, 38),(6, 49),(39, 40),(12, 40),(7, 43),(43, 44),(7, 45),(45, 46),(7, 47),(14, 38),
                (7, 49),(49, 50),(51, 52),(8, 40),(53, 54),(5, 55),(55, 56),(4, 56),(3, 59),(59, 60),(2, 60),
                (4, 57),(16, 38),(2, 61),(0, 65),(18, 38),(20, 38),(47, 48),(22, 38),(64, 66),(24, 38),(5, 54),
                (10, 40),(26, 38),(41, 42),(28, 38),(12, 38),(30, 38),(32, 38),(1, 65),(34, 38),(57, 58),
                (6, 51),(38, 40),
            ],
            'faces': [
                (38, 36, 37),(38, 35, 36),(38, 34, 35),(38, 33, 34),(38, 32, 33),(38, 31, 32),(38, 30, 31),
                (38, 29, 30),(38, 28, 29),(38, 27, 28),(38, 26, 27),(38, 25, 26),(38, 24, 25),(38, 23, 24),
                (38, 22, 23),(38, 21, 22),(38, 20, 21),(38, 19, 20),(38, 18, 19),(38, 17, 18),(38, 16, 17),
                (38, 15, 16),(38, 14, 15),(38, 13, 14),(38, 12, 13),(39, 40, 38),(40, 12, 38),(40, 11, 12),
                (40, 10, 11),(40, 9, 10),(40, 8, 9),(41, 8, 40),(42, 8, 41),(42, 7, 8),(43, 7, 42),(44, 7, 43),
                (45, 7, 44),(46, 7, 45),(47, 7, 46),(48, 7, 47),(49, 7, 48),(49, 6, 7),(50, 6, 49),(51, 6, 50),
                (52, 6, 51),(52, 5, 6),(53, 5, 52),(54, 5, 53),(55, 5, 54),(55, 4, 5),(56, 4, 55),(57, 4, 56),
                (58, 4, 57),(58, 3, 4),(59, 3, 58),(60, 3, 59),(60, 2, 3),(61, 2, 60),(62, 2, 61),(62, 1, 2),
                (63, 1, 62),(64, 1, 63),(1, 64, 65),(65, 0, 1),(64, 66, 65),
            ],
        },
        'fahrbahnmarkierung_pfeil_lr': {
            'vertices': [
                (-0.000000, -0.120002, 0.000000),(2.999426, -0.080002, 0.000000),
                (3.546548, -0.001690, 0.000000),(3.592289, 0.014139, 0.000000),(3.635700, 0.031300, 0.000000),
                (3.676335, 0.049633, 0.000000),(3.713817, 0.068950, 0.000000),(3.748072, 0.089177, 0.000000),
                (3.779029, 0.110241, 0.000000),(3.806615, 0.132068, 0.000000),(3.830758, 0.154583, 0.000000),
                (3.851386, 0.177714, 0.000000),(3.868425, 0.201385, 0.000000),(3.881804, 0.225524, 0.000000),
                (3.891450, 0.250056, 0.000000),(3.897291, 0.274908, 0.000000),(3.899254, 0.300006, 0.000000),
                (3.920893, 0.300006, 0.000000),(3.980720, 0.300006, 0.000000),(4.071096, 0.300006, 0.000000),
                (4.184384, 0.300006, 0.000000),(4.312948, 0.300006, 0.000000),(4.449149, 0.300006, 0.000000),
                (4.585350, 0.300006, 0.000000),(4.713913, 0.300006, 0.000000),(4.827202, 0.300006, 0.000000),
                (4.917578, 0.300006, 0.000000),(4.977405, 0.300006, 0.000000),(4.999043, 0.300006, 0.000000),
                (3.599311, 0.600012, 0.000000),(2.499522, 0.300006, 0.000000),(3.399350, 0.300006, 0.000000),
                (3.398477, 0.285476, 0.000000),(3.395881, 0.271088, 0.000000),(3.391594, 0.256885, 0.000000),
                (3.385648, 0.242910, 0.000000),(3.378075, 0.229205, 0.000000),(3.368907, 0.215814, 0.000000),
                (3.358177, 0.202779, 0.000000),(3.345916, 0.190142, 0.000000),(3.332158, 0.177947, 0.000000),
                (3.316933, 0.166237, 0.000000),(3.300275, 0.155053, 0.000000),(3.282215, 0.144439, 0.000000),
                (3.262921, 0.134504, 0.000000),(3.242591, 0.125340, 0.000000),(3.221304, 0.116965, 0.000000),
                (3.199136, 0.109396, 0.000000),(3.176166, 0.102651, 0.000000),(3.152470, 0.096748, 0.000000),
                (3.128128, 0.091705, 0.000000),(3.103215, 0.087539, 0.000000),(3.077811, 0.084268, 0.000000),
                (3.051994, 0.081910, 0.000000),(3.025839, 0.080482, 0.000000),(2.999426, 0.080001, 0.000000),
                (0.000000, 0.120002, 0.000000),(3.592289, -0.014140, 0.000000),(3.635700, -0.031300, 0.000000),
                (3.676335, -0.049633, 0.000000),(3.713817, -0.068950, 0.000000),(3.748072, -0.089178, 0.000000),
                (3.779029, -0.110242, 0.000000),(3.806615, -0.132068, 0.000000),(3.830758, -0.154584, 0.000000),
                (3.851386, -0.177714, 0.000000),(3.868425, -0.201386, 0.000000),(3.881804, -0.225525, 0.000000),
                (3.891450, -0.250057, 0.000000),(3.897291, -0.274909, 0.000000),(3.899254, -0.300006, 0.000000),
                (3.920893, -0.300006, 0.000000),(3.980720, -0.300006, 0.000000),(4.071096, -0.300006, 0.000000),
                (4.184384, -0.300006, 0.000000),(4.312948, -0.300006, 0.000000),(4.449149, -0.300006, 0.000000),
                (4.585350, -0.300006, 0.000000),(4.713913, -0.300006, 0.000000),(4.827202, -0.300006, 0.000000),
                (4.917578, -0.300006, 0.000000),(4.977405, -0.300006, 0.000000),(4.999043, -0.300006, 0.000000),
                (3.599311, -0.600012, 0.000000),(2.499522, -0.300006, 0.000000),(3.399350, -0.300006, 0.000000),
                (3.398477, -0.285476, 0.000000),(3.395881, -0.271088, 0.000000),(3.391594, -0.256885, 0.000000),
                (3.385648, -0.242910, 0.000000),(3.378075, -0.229206, 0.000000),(3.368907, -0.215814, 0.000000),
                (3.358177, -0.202779, 0.000000),(3.345916, -0.190143, 0.000000),(3.332158, -0.177948, 0.000000),
                (3.316933, -0.166237, 0.000000),(3.300275, -0.155054, 0.000000),(3.282215, -0.144439, 0.000000),
                (3.262921, -0.134504, 0.000000),(3.242591, -0.125340, 0.000000),(3.221304, -0.116965, 0.000000),
                (3.199136, -0.109396, 0.000000),(3.176166, -0.102651, 0.000000),(3.152470, -0.096749, 0.000000),
                (3.128128, -0.091705, 0.000000),(3.103215, -0.087539, 0.000000),(3.077811, -0.084268, 0.000000),
                (3.051994, -0.081910, 0.000000),(3.025839, -0.080482, 0.000000),(0.000000, 0.000000, 0.000000),
            ],
            'edges': [
                (0, 1),(3, 4),(5, 6),(7, 8),(9, 10),(54, 55),(11, 12),(13, 14),(15, 16),(17, 18),(19, 20),
                (21, 22),(23, 24),(2, 31),(25, 26),(27, 28),(27, 29),(29, 30),(4, 29),(31, 32),(33, 34),
                (35, 36),(37, 38),(39, 40),(41, 42),(43, 44),(45, 46),(6, 29),(47, 48),(49, 50),(51, 52),
                (53, 54),(107, 52),(107, 53),(8, 29),(1, 55),(109, 56),(10, 29),(12, 29),(14, 29),(16, 29),
                (18, 29),(20, 29),(52, 53),(22, 29),(24, 29),(26, 29),(2, 3),(4, 5),(6, 7),(8, 9),(10, 11),
                (12, 13),(14, 15),(16, 17),(18, 19),(20, 21),(22, 23),(24, 25),(26, 27),(28, 29),(30, 31),
                (3, 31),(34, 35),(36, 37),(5, 29),(40, 41),(42, 43),(44, 45),(46, 47),(50, 51),(7, 29),
                (55, 109),(9, 29),(11, 29),(38, 39),(13, 29),(1, 109),(15, 29),(17, 29),(32, 33),(19, 29),
                (3, 29),(21, 29),(23, 29),(25, 29),(48, 49),(29, 31),(104, 105),(57, 58),(59, 60),(61, 62),
                (63, 64),(65, 66),(67, 68),(69, 70),(71, 72),(73, 74),(75, 76),(106, 107),(77, 78),(79, 80),
                (81, 82),(81, 83),(83, 84),(58, 83),(87, 88),(89, 90),(91, 92),(93, 94),(97, 98),(99, 100),
                (60, 83),(103, 104),(107, 108),(62, 83),(85, 86),(64, 83),(66, 83),(68, 83),(70, 83),(95, 96),
                (72, 83),(90, 91),(74, 83),(76, 83),(78, 83),(80, 83),(101, 102),(108, 1),(58, 59),(60, 61),
                (62, 63),(105, 106),(64, 65),(66, 67),(68, 69),(70, 71),(72, 73),(74, 75),(76, 77),(78, 79),
                (80, 81),(82, 83),(84, 85),(57, 85),(59, 83),(94, 95),(96, 97),(88, 89),(100, 101),(61, 83),
                (63, 83),(65, 83),(92, 93),(67, 83),(69, 83),(71, 83),(86, 87),(73, 83),(57, 83),(75, 83),
                (98, 99),(77, 83),(79, 83),(102, 103),(83, 85),(2, 85),(2, 57),(108, 54),(108, 53),(55, 108),
                (106, 52),(106, 51),(105, 51),(105, 50),(104, 50),(104, 49),(103, 49),(102, 48),(49, 102),
                (101, 47),(48, 101),(101, 46),(100, 46),(100, 45),(99, 45),(99, 44),(98, 44),(98, 43),(97, 43),
                (2, 42),(43, 2),(97, 2),(96, 2),(2, 41),(95, 2),(2, 40),(94, 2),(2, 39),(93, 2),(2, 38),(92, 2),
                (2, 37),(91, 2),(2, 36),(90, 2),(2, 35),(89, 2),(2, 34),(88, 2),(2, 33),(87, 2),(32, 2),(2, 86),
                (0, 109),(55, 56),
            ],
            'faces': [
                (29, 27, 28),(29, 26, 27),(29, 25, 26),(29, 24, 25),(29, 23, 24),(29, 22, 23),(29, 21, 22),
                (29, 20, 21),(29, 19, 20),(29, 18, 19),(29, 17, 18),(29, 16, 17),(29, 15, 16),(29, 14, 15),
                (29, 13, 14),(29, 12, 13),(29, 11, 12),(29, 10, 11),(29, 9, 10),(29, 8, 9),(29, 7, 8),
                (29, 6, 7),(29, 5, 6),(29, 4, 5),(29, 3, 4),(30, 31, 29),(31, 3, 29),(31, 2, 3),(53, 108, 107),
                (53, 54, 108),(1, 55, 109),(109, 0, 1),(81, 83, 82),(80, 83, 81),(79, 83, 80),(78, 83, 79),
                (77, 83, 78),(76, 83, 77),(75, 83, 76),(74, 83, 75),(73, 83, 74),(72, 83, 73),(71, 83, 72),
                (70, 83, 71),(69, 83, 70),(68, 83, 69),(67, 83, 68),(66, 83, 67),(65, 83, 66),(64, 83, 65),
                (63, 83, 64),(62, 83, 63),(61, 83, 62),(60, 83, 61),(59, 83, 60),(58, 83, 59),(57, 83, 58),
                (57, 85, 83),(85, 84, 83),(2, 85, 57),(87, 86, 2),(54, 55, 108),(55, 1, 108),(52, 53, 107),
                (52, 107, 106),(51, 52, 106),(51, 106, 105),(50, 51, 105),(50, 105, 104),(49, 50, 104),
                (49, 104, 103),(48, 49, 102),(49, 103, 102),(47, 48, 101),(48, 102, 101),(46, 47, 101),
                (46, 101, 100),(45, 46, 100),(45, 100, 99),(44, 45, 99),(44, 99, 98),(43, 44, 98),(43, 98, 97),
                (42, 43, 2),(43, 97, 2),(97, 96, 2),(41, 42, 2),(96, 95, 2),(40, 41, 2),(95, 94, 2),(39, 40, 2),
                (94, 93, 2),(38, 39, 2),(93, 92, 2),(37, 38, 2),(92, 91, 2),(36, 37, 2),(91, 90, 2),(35, 36, 2),
                (90, 89, 2),(34, 35, 2),(89, 88, 2),(33, 34, 2),(88, 87, 2),(2, 31, 32),(32, 33, 2),(86, 85, 2),
                (55, 56, 109),
            ],
        },
        'fahrbahnmarkierung_pfeil_r': {
            'vertices': [
                (0.000000, 0.120003, 0.000000),(2.999426, 0.080002, 0.000000),(3.058856, 0.079173, 0.000000),
                (3.117703, 0.076706, 0.000000),(3.175793, 0.072632, 0.000000),(3.232952, 0.066982, 0.000000),
                (3.289004, 0.059786, 0.000000),(3.343775, 0.051075, 0.000000),(3.397090, 0.040879, 0.000000),
                (3.448774, 0.029229, 0.000000),(3.498651, 0.016156, 0.000000),(3.546548, 0.001689, 0.000000),
                (3.592289, -0.014139, 0.000000),(3.635700, -0.031300, 0.000000),(3.676335, -0.049633, 0.000000),
                (3.713817, -0.068950, 0.000000),(3.748072, -0.089178, 0.000000),(3.779029, -0.110242, 0.000000),
                (3.806615, -0.132068, 0.000000),(3.830758, -0.154584, 0.000000),(3.851386, -0.177714, 0.000000),
                (3.868425, -0.201386, 0.000000),(3.881804, -0.225525, 0.000000),(3.891450, -0.250057, 0.000000),
                (3.897291, -0.274909, 0.000000),(3.899254, -0.300006, 0.000000),(3.920893, -0.300006, 0.000000),
                (3.980720, -0.300006, 0.000000),(4.071096, -0.300006, 0.000000),(4.184384, -0.300006, 0.000000),
                (4.312948, -0.300006, 0.000000),(4.449149, -0.300006, 0.000000),(4.585350, -0.300006, 0.000000),
                (4.713913, -0.300006, 0.000000),(4.827202, -0.300006, 0.000000),(4.917578, -0.300006, 0.000000),
                (4.977405, -0.300006, 0.000000),(4.999043, -0.300006, 0.000000),(3.599311, -0.600012, 0.000000),
                (2.499522, -0.300006, 0.000000),(3.399350, -0.300006, 0.000000),(3.398477, -0.285476, 0.000000),
                (3.395881, -0.271088, 0.000000),(3.391594, -0.256885, 0.000000),(3.385648, -0.242910, 0.000000),
                (3.378075, -0.229206, 0.000000),(3.368907, -0.215814, 0.000000),(3.358177, -0.202779, 0.000000),
                (3.345916, -0.190143, 0.000000),(3.332158, -0.177948, 0.000000),(3.316933, -0.166237, 0.000000),
                (3.300275, -0.155054, 0.000000),(3.282215, -0.144439, 0.000000),(3.262921, -0.134504, 0.000000),
                (3.242591, -0.125340, 0.000000),(3.221304, -0.116965, 0.000000),(3.199136, -0.109396, 0.000000),
                (3.176166, -0.102651, 0.000000),(3.152470, -0.096748, 0.000000),(3.128128, -0.091705, 0.000000),
                (3.103215, -0.087539, 0.000000),(3.077811, -0.084268, 0.000000),(3.051994, -0.081910, 0.000000),
                (3.025839, -0.080481, 0.000000),(2.999426, -0.080001, 0.000000),(0.000000, 0.000000, 0.000000),
                (-0.000000, -0.120002, 0.000000),
            ],
            'edges': [
                (0, 1),(2, 3),(4, 5),(59, 60),(6, 7),(8, 9),(10, 11),(7, 42),(12, 13),(14, 15),(16, 17),(9, 40),
                (18, 19),(63, 64),(20, 21),(22, 23),(24, 25),(26, 27),(28, 29),(30, 31),(61, 62),(32, 33),
                (11, 40),(34, 35),(36, 37),(36, 38),(38, 39),(13, 38),(8, 41),(8, 42),(42, 43),(44, 45),(5, 52),
                (46, 47),(48, 49),(6, 50),(6, 51),(6, 52),(52, 53),(54, 55),(15, 38),(4, 57),(4, 58),(58, 59),
                (3, 58),(2, 61),(2, 62),(62, 63),(1, 62),(17, 38),(1, 64),(65, 66),(40, 41),(19, 38),(21, 38),
                (23, 38),(25, 38),(50, 51),(27, 38),(45, 46),(29, 38),(31, 38),(33, 38),(7, 48),(35, 38),
                (56, 57),(5, 53),(1, 2),(3, 4),(5, 6),(7, 8),(9, 10),(11, 12),(13, 14),(15, 16),(17, 18),
                (60, 61),(19, 20),(21, 22),(23, 24),(4, 55),(25, 26),(27, 28),(29, 30),(31, 32),(33, 34),
                (35, 36),(37, 38),(6, 49),(39, 40),(12, 40),(7, 43),(7, 44),(7, 45),(7, 46),(7, 47),(14, 38),
                (7, 49),(49, 50),(51, 52),(8, 40),(43, 44),(5, 55),(55, 56),(4, 56),(3, 59),(3, 60),(2, 60),
                (1, 63),(16, 38),(65, 1),(0, 65),(18, 38),(20, 38),(47, 48),(22, 38),(64, 66),(24, 38),(5, 54),
                (10, 40),(26, 38),(41, 42),(28, 38),(12, 38),(30, 38),(53, 54),(32, 38),(34, 38),(57, 58),
                (38, 40),(64, 65),
            ],
            'faces': [
                (36, 38, 37),(35, 38, 36),(34, 38, 35),(33, 38, 34),(32, 38, 33),(31, 38, 32),(30, 38, 31),
                (29, 38, 30),(28, 38, 29),(27, 38, 28),(26, 38, 27),(25, 38, 26),(24, 38, 25),(23, 38, 24),
                (22, 38, 23),(21, 38, 22),(20, 38, 21),(19, 38, 20),(18, 38, 19),(17, 38, 18),(16, 38, 17),
                (15, 38, 16),(14, 38, 15),(13, 38, 14),(12, 38, 13),(12, 40, 38),(40, 39, 38),(11, 40, 12),
                (10, 40, 11),(9, 40, 10),(8, 40, 9),(8, 41, 40),(8, 42, 41),(7, 42, 8),(7, 43, 42),(7, 44, 43),
                (7, 45, 44),(7, 46, 45),(7, 47, 46),(7, 48, 47),(7, 49, 48),(6, 49, 7),(6, 50, 49),(6, 51, 50),
                (6, 52, 51),(5, 52, 6),(5, 53, 52),(5, 54, 53),(5, 55, 54),(4, 55, 5),(4, 56, 55),(4, 57, 56),
                (4, 58, 57),(3, 58, 4),(3, 59, 58),(3, 60, 59),(2, 60, 3),(2, 61, 60),(2, 62, 61),(1, 62, 2),
                (1, 63, 62),(1, 64, 63),(65, 64, 1),(1, 0, 65),(65, 66, 64),
            ],
        },
        'fahrbahnmarkierung_pfeil_vl': {
            'vertices': [
                (-0.000000, -0.120002, 0.000000),(2.699483, -0.080001, 0.000000),
                (2.766620, -0.079443, 0.000000),(2.833715, -0.077770, 0.000000),(2.900754, -0.074983, 0.000000),
                (2.967725, -0.071083, 0.000000),(3.034611, -0.066072, 0.000000),(3.101401, -0.059951, 0.000000),
                (3.168081, -0.052722, 0.000000),(3.234635, -0.044386, 0.000000),(3.301051, -0.034944, 0.000000),
                (3.367315, -0.024399, 0.000000),(3.433412, -0.012750, 0.000000),(3.499330, -0.000000, 0.000000),
                (3.506561, 0.001436, 0.000000),(3.526552, 0.005405, 0.000000),(3.556752, 0.011401, 0.000000),
                (3.594608, 0.018918, 0.000000),(3.637568, 0.027448, 0.000000),(3.683080, 0.036486, 0.000000),
                (3.728592, 0.045523, 0.000000),(3.771553, 0.054053, 0.000000),(3.809408, 0.061570, 0.000000),
                (3.839608, 0.067566, 0.000000),(3.859600, 0.071535, 0.000000),(3.866830, 0.072971, 0.000000),
                (4.499139, -0.050001, 0.000000),(4.999043, 0.450009, 0.000000),(2.699483, 0.300006, 0.000000),
                (3.331792, 0.177034, 0.000000),(3.280137, 0.163160, 0.000000),(3.228240, 0.150331, 0.000000),
                (3.176117, 0.138549, 0.000000),(3.123785, 0.127815, 0.000000),(3.071258, 0.118133, 0.000000),
                (3.018554, 0.109505, 0.000000),(2.965688, 0.101933, 0.000000),(2.912676, 0.095419, 0.000000),
                (2.859534, 0.089967, 0.000000),(2.806277, 0.085578, 0.000000),(2.752922, 0.082256, 0.000000),
                (2.699483, 0.080002, 0.000000),(0.000000, 0.000000, 0.000000),(0.000000, 0.120002, 0.000000),
            ],
            'edges': [
                (0, 1),(14, 29),(2, 3),(3, 4),(4, 5),(5, 6),(6, 7),(7, 8),(8, 9),(15, 29),(10, 11),(11, 12),
                (12, 13),(13, 14),(14, 15),(15, 16),(16, 17),(17, 18),(18, 19),(19, 20),(20, 21),(21, 22),
                (22, 23),(23, 24),(24, 25),(25, 26),(26, 27),(27, 28),(28, 29),(29, 30),(30, 31),(31, 32),
                (32, 33),(18, 29),(34, 35),(35, 36),(36, 37),(37, 38),(38, 39),(39, 40),(40, 41),(19, 29),
                (20, 29),(41, 42),(0, 42),(42, 43),(21, 29),(22, 29),(23, 29),(41, 43),(6, 34),(24, 29),
                (25, 29),(7, 33),(16, 29),(1, 2),(26, 29),(27, 29),(8, 32),(7, 34),(9, 10),(8, 33),(17, 29),
                (1, 42),(33, 34),(1, 40),(2, 39),(4, 36),(1, 41),(3, 38),(5, 35),(2, 40),(4, 37),(8, 31),
                (3, 39),(5, 36),(9, 30),(4, 38),(6, 35),(10, 29),(9, 31),(10, 30),(11, 29),(12, 29),(13, 29),
            ],
            'faces': [
                (28, 29, 27),(29, 26, 27),(29, 25, 26),(29, 24, 25),(29, 23, 24),(29, 22, 23),(29, 21, 22),
                (29, 20, 21),(29, 19, 20),(29, 18, 19),(29, 17, 18),(29, 16, 17),(29, 15, 16),(29, 14, 15),
                (29, 13, 14),(29, 12, 13),(29, 11, 12),(29, 10, 11),(30, 10, 29),(30, 9, 10),(31, 9, 30),
                (31, 8, 9),(32, 8, 31),(33, 8, 32),(33, 7, 8),(34, 7, 33),(34, 6, 7),(35, 6, 34),(35, 5, 6),
                (36, 5, 35),(36, 4, 5),(37, 4, 36),(38, 4, 37),(38, 3, 4),(39, 3, 38),(39, 2, 3),(40, 2, 39),
                (40, 1, 2),(41, 1, 40),(1, 41, 42),(42, 0, 1),(41, 43, 42),
            ],
        },
        'fahrbahnmarkierung_pfeil_vr': {
            'vertices': [
                (0.000000, 0.120003, 0.000000),(2.699483, 0.080002, 0.000000),(2.766620, 0.079443, 0.000000),
                (2.833715, 0.077770, 0.000000),(2.900754, 0.074983, 0.000000),(2.967724, 0.071083, 0.000000),
                (3.034611, 0.066072, 0.000000),(3.101401, 0.059951, 0.000000),(3.168081, 0.052722, 0.000000),
                (3.234635, 0.044386, 0.000000),(3.301051, 0.034945, 0.000000),(3.367315, 0.024399, 0.000000),
                (3.433413, 0.012750, 0.000000),(3.499330, -0.000000, 0.000000),(3.506561, -0.001436, 0.000000),
                (3.526552, -0.005405, 0.000000),(3.556752, -0.011402, 0.000000),(3.594608, -0.018919, 0.000000),
                (3.637568, -0.027449, 0.000000),(3.683080, -0.036486, 0.000000),(3.728592, -0.045523, 0.000000),
                (3.771553, -0.054053, 0.000000),(3.809408, -0.061570, 0.000000),(3.839608, -0.067566, 0.000000),
                (3.859600, -0.071536, 0.000000),(3.866830, -0.072972, 0.000000),(4.499139, 0.050001, 0.000000),
                (4.999043, -0.450009, 0.000000),(2.699483, -0.300006, 0.000000),(3.331792, -0.177034, 0.000000),
                (3.280137, -0.163160, 0.000000),(3.228240, -0.150331, 0.000000),(3.176117, -0.138549, 0.000000),
                (3.123785, -0.127815, 0.000000),(3.071258, -0.118133, 0.000000),(3.018554, -0.109505, 0.000000),
                (2.965688, -0.101933, 0.000000),(2.912676, -0.095419, 0.000000),(2.859533, -0.089967, 0.000000),
                (2.806276, -0.085578, 0.000000),(2.752921, -0.082256, 0.000000),(2.699483, -0.080002, 0.000000),
                (-0.000000, -0.120002, 0.000000),(0.000000, 0.000000, 0.000000),
            ],
            'edges': [
                (0, 1),(14, 29),(2, 3),(3, 4),(4, 5),(5, 6),(6, 7),(7, 8),(8, 9),(15, 29),(10, 11),(11, 12),
                (12, 13),(13, 14),(14, 15),(15, 16),(16, 17),(17, 18),(18, 19),(19, 20),(20, 21),(21, 22),
                (22, 23),(23, 24),(24, 25),(25, 26),(26, 27),(27, 28),(26, 29),(10, 30),(9, 31),(8, 32),(8, 33),
                (18, 29),(6, 35),(5, 36),(4, 37),(4, 38),(3, 39),(2, 40),(1, 41),(19, 29),(20, 29),(43, 42),
                (21, 29),(22, 29),(23, 29),(6, 34),(24, 29),(40, 41),(25, 29),(7, 33),(16, 29),(1, 2),(39, 40),
                (27, 29),(28, 29),(9, 10),(29, 30),(17, 29),(30, 31),(31, 32),(32, 33),(41, 42),(33, 34),
                (34, 35),(35, 36),(43, 1),(1, 40),(2, 39),(4, 36),(3, 38),(5, 35),(36, 37),(8, 31),(9, 30),
                (10, 29),(7, 34),(37, 38),(11, 29),(12, 29),(38, 39),(13, 29),(0, 43),(41, 43),
            ],
            'faces': [
                (26, 29, 27),(29, 28, 27),(25, 29, 26),(24, 29, 25),(23, 29, 24),(22, 29, 23),(21, 29, 22),
                (20, 29, 21),(19, 29, 20),(18, 29, 19),(17, 29, 18),(16, 29, 17),(15, 29, 16),(14, 29, 15),
                (13, 29, 14),(12, 29, 13),(11, 29, 12),(10, 29, 11),(10, 30, 29),(9, 30, 10),(9, 31, 30),
                (8, 31, 9),(8, 32, 31),(8, 33, 32),(7, 33, 8),(7, 34, 33),(6, 34, 7),(6, 35, 34),(5, 35, 6),
                (5, 36, 35),(4, 36, 5),(4, 37, 36),(4, 38, 37),(3, 38, 4),(3, 39, 38),(2, 39, 3),(2, 40, 39),
                (1, 40, 2),(1, 41, 40),(43, 41, 1),(1, 0, 43),(43, 42, 41),
            ],
        },
    }
    return road_stencil_type_subtype_mapping

class road_object_stencil:

    def __init__(self, context, road_object_type):
        self.context = context
        self.road_object_type = road_object_type
        self.road_object_odr_info = {}
        self.params = {}

    def create_object_3d(self, context, params_input, road_id):
        '''
            Create a 3d entity object
        '''
        valid, mesh, matrix_world, materials = self.update_params_get_mesh(
            context, params_input, wireframe=False)
        if not valid:
            return None
        else:
            id_obj = helpers.get_new_id_opendrive(context)
            obj_name = self.road_object_type + '_' + str(id_obj)
            mesh.name = obj_name
            obj = bpy.data.objects.new(mesh.name, mesh)
            obj.matrix_world = matrix_world
            helpers.link_object_opendrive(context, obj)

            helpers.select_activate_object(context, obj)

            # Assign materials
            helpers.assign_materials(obj)
            for idx in range(len(obj.data.polygons)):
                # TODO: later we might support multicolor stencils
                obj.data.polygons[idx].material_index = \
                    helpers.get_material_index(obj, 'road_mark_white')

            # Metadata
            obj['dsc_category'] = 'OpenDRIVE'
            obj['dsc_type'] = 'road_object'
            obj['road_object_type'] = self.road_object_type
            obj['id_odr'] = id_obj
            obj['id_road'] = road_id
            obj['position_s'] = params_input['point_s']
            obj['position_t'] = params_input['point_t']
            obj['position'] = params_input['point']
            obj['hdg'] = params_input['heading']
            # FIXME calculate correct width
            obj['width'] = 2.0
            obj['height'] = 0.01
            obj['length'] = 5.0
            obj['zOffset'] = 0.0
            stencil_info = self.get_stencil_catalog_info(context)
            obj['catalog_type'] = stencil_info['type']
            obj['catalog_subtype'] = stencil_info['subtype']

        return obj

    def update_params_get_mesh(self, context, params_input, wireframe):
        '''
            Calculate and return the vertices, edges and faces to create a stencil
            pole or plate mesh.
        '''
        origin_point = params_input['point']
        heading = params_input['heading']
        vertices, edges, faces, materials = self.get_vertices_edges_faces_materials(context)
        # Raise the stencil a bit above the road surface to avoid z fighting issues
        origin_point.z += 0.01
        mat_translation = Matrix.Translation(origin_point)
        mat_rotation = Matrix.Rotation(heading, 4, 'Z')
        matrix_world = mat_translation @ mat_rotation
        # Create blender mesh
        if wireframe:
            mat_rotation_inverted = Matrix.Rotation(-heading, 4, 'Z')
            point_ref_line_rel = mat_rotation_inverted @ (params_input['point_ref_line'] - origin_point)
            vertices.append((0.0, 0.0, 0.0))
            vertices.append((point_ref_line_rel.x, point_ref_line_rel.y, 0.0))
            edges.append((len(vertices)-2, len(vertices)-1))
            faces = []
        mesh = bpy.data.meshes.new('temp')
        mesh.from_pydata(vertices, edges, faces)
        valid = True
        return valid, mesh, matrix_world, materials

    def get_vertices_edges_faces_materials(self, context):
        '''
            Return the vertices, edges and faces to create a stencil.
        '''
        # Get the name for the selected road stencil
        stencil_name_selected = None
        for stencil in context.scene.dsc_properties.road_object_stencil_properties.stencil_catalog:
            if stencil.selected == True:
                stencil_name_selected = stencil.name
                texture_file_name = stencil.texture_name + '_texture.png'
                break
        mesh_map = get_road_stencil_mesh_mapping()
        vertices, edges, faces = mesh_map[stencil_name_selected].values()
        # Materials currently not used for stencils, only one color for now
        # TODO: This needs to be changed for multi color stencils
        materials = {}

        return vertices, edges, faces, materials

    def get_stencil_catalog_info(self, context):
        '''
            Return stencil OpenDRIVE type and subtype information.
        '''
        for stencil in context.scene.dsc_properties.road_object_stencil_properties.stencil_catalog:
            if stencil.selected == True:
                return {"type": stencil.type, "subtype": stencil.subtype}
        return {"type": None, "subtype": None}
