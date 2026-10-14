"""Small geometry helpers shared by vehicle-specific mesh providers."""


def transverse_rectangle(u0, u1, y0, y1):
    """Return a rectangular loop on a vehicle's transverse facet."""
    return [(u0, y0), (u1, y0), (u1, y1), (u0, y1)]
