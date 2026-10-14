"""Heavy-truck geometry provider for the shared vehicle operator."""


class HeavyTruckGeometryMixin:
    """Expose heavy-truck mesh generation without a separate Blender operator."""

    def _build_heavy_truck_geometry(self):
        """Implemented by the shared vehicle operator."""
        raise NotImplementedError

    def _get_heavy_truck_vertices_edges_faces(self):
        return self._build_heavy_truck_geometry()
