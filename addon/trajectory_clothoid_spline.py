# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import bpy
import json

from math import hypot, isfinite, pi
from mathutils import Vector
from pyclothoids import Clothoid

from . modal_trajectory_base import DSC_OT_modal_trajectory_base
from . import helpers


class DSC_OT_trajectory_clothoid_spline(DSC_OT_modal_trajectory_base):
    bl_idname = 'dsc.trajectory_clothoid_spline'
    bl_label = 'Clothoid spline'
    bl_description = 'Create a clothoid spline based trajectory'
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def normalize_heading(heading):
        return (heading + pi) % (2.0 * pi) - pi

    def create_trajectory_temp(self, context):
        self.trajectory = bpy.data.objects.get('trajectory_temp')
        if self.trajectory is not None:
            bpy.data.objects.remove(self.trajectory, do_unlink=True)
        self.trajectory = bpy.data.objects.new('trajectory_temp', self.get_mesh())
        helpers.link_object_openscenario(context, self.trajectory, subcategory='trajectories')
        self.trajectory.location = self.point_start

    def set_xosc_properties(self):
        self.trajectory['dsc_category'] = 'OpenSCENARIO'
        self.trajectory['dsc_type'] = 'trajectory'
        self.trajectory['dsc_subtype'] = 'clothoid_spline'
        self.trajectory['owner_name'] = self.trajectory_owner_name
        self.trajectory['clothoid_segments'] = json.dumps([
            {
                'curvature_start': segment['curvature_start'],
                'curvature_end': segment['curvature_end'],
                'length': segment['length'],
                'heading': segment['heading'],
                'position_start': [
                    segment['point_start'].x - self.point_start.x,
                    segment['point_start'].y - self.point_start.y,
                    segment['point_start'].z - self.point_start.z,
                ],
                'backwards': segment['backwards'],
            }
            for segment in self.get_segments()
        ])

    def update_trajectory(self, context):
        helpers.replace_mesh(self.trajectory, self.get_mesh())

    def get_segments(self):
        segments = []
        points, backwards = self.get_preview_points()
        heading_end_extra = self.get_preview_heading_end_extra()
        if len(points) < 2:
            return segments

        heading = self.normalize_heading(self.trajectory_heading_start)
        curvature_start = 0.0
        for idx in range(len(points) - 1):
            point_start = points[idx]
            point_end = points[idx + 1]
            if hypot(point_end.x - point_start.x, point_end.y - point_start.y) <= 1e-6:
                break
            segment_backwards = bool(backwards[idx + 1])
            segment_heading = self.normalize_heading(
                heading + pi if segment_backwards else heading)
            segment_curvature_start = 0.0 if segment_backwards else curvature_start
            try:
                curve = Clothoid.Forward(
                    point_start.x, point_start.y, segment_heading, segment_curvature_start,
                    point_end.x, point_end.y)
                end_heading_extra = heading_end_extra[idx + 1]
                if end_heading_extra != 0.0:
                    end_heading = self.normalize_heading(curve.ThetaEnd)
                    end_heading_difference = self.normalize_heading(
                        end_heading - segment_heading)
                    if end_heading_difference < 0.0:
                        end_heading_extra = -end_heading_extra
                    end_heading = self.normalize_heading(
                        segment_heading + end_heading_difference + end_heading_extra)
                    curve = Clothoid.G1Hermite(
                        point_start.x, point_start.y, segment_heading,
                        point_end.x, point_end.y,
                        end_heading)
            except RuntimeError:
                # Forward can reject cursor positions behind the current heading.
                break
            if not isfinite(curve.length) or curve.length <= 1e-6 or curve.length >= 10000.0:
                break
            segments.append({
                'curve': curve,
                'point_start': point_start.copy(),
                'heading': segment_heading,
                'curvature_start': curve.KappaStart,
                'curvature_end': curve.KappaEnd,
                'length': curve.length,
                'backwards': segment_backwards,
            })
            heading = curve.ThetaEnd
            curvature_start = curve.KappaEnd
        return segments

    def get_mesh(self):
        vertices = []
        for segment in self.get_segments():
            curve = segment['curve']
            sample_count = max(8, min(64, int(curve.length / 0.5) + 1))
            for sample_idx in range(sample_count + 1):
                if vertices and sample_idx == 0:
                    continue
                s = curve.length * sample_idx / sample_count
                vertices.append(Vector((curve.X(s), curve.Y(s),
                                        self.get_preview_points()[0][0].z)) - self.point_start)
        edges = [[idx, idx + 1] for idx in range(len(vertices) - 1)]
        mesh = bpy.data.meshes.new('trajectory_clothoid_spline')
        mesh.from_pydata(vertices, edges, [])
        return mesh