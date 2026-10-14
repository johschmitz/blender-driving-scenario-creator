"""Bicycle geometry provider for the shared vehicle operator."""


class BicycleGeometryMixin:
    """Build bicycle geometry through shared two-wheeler mesh utilities."""

    def _get_bicycle_vertices_edges_faces(self):
        return self._get_two_wheeler_vertices_edges_faces()
