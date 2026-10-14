"""Motorcycle geometry provider for the shared vehicle operator."""


class MotorcycleGeometryMixin:
    """Build motorcycle geometry through shared two-wheeler mesh utilities."""

    def _get_motorcycle_vertices_edges_faces(self):
        return self._get_two_wheeler_vertices_edges_faces()
