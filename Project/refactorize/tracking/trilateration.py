# tracking/trilateration.py

from typing import Sequence


def trilaterate_2d(
    anchor_positions: Sequence[tuple[float, float]],
    distances: Sequence[float]
) -> tuple[float, float] | None:
    """
    Linear least-squares 2D trilateration.

    Parameters
    ----------
    anchor_positions:
        List of (x, y) anchor coordinates.

    distances:
        Distance measurements corresponding
        to each anchor.

    Returns
    -------
    (x, y) tuple or None if a solution
    cannot be calculated.
    """

    valid = [
        (x, y, d)
        for (x, y), d in zip(anchor_positions, distances)
        if 0.05 < d < 50.0
    ]

    if len(valid) < 3:
        return None

    xr, yr, rr = valid[-1]

    A = []
    b = []

    for xi, yi, ri in valid[:-1]:

        A.append(
            (
                2 * (xi - xr),
                2 * (yi - yr)
            )
        )

        b.append(
            ri**2
            - rr**2
            - xi**2
            + xr**2
            - yi**2
            + yr**2
        )

    if len(A) < 2:
        return None

    m00 = sum(ax * ax for ax, ay in A)
    m01 = sum(ax * ay for ax, ay in A)
    m11 = sum(ay * ay for ax, ay in A)

    v0 = sum(
        ax * bi
        for (ax, ay), bi in zip(A, b)
    )

    v1 = sum(
        ay * bi
        for (ax, ay), bi in zip(A, b)
    )

    det = m00 * m11 - m01 * m01

    if abs(det) < 1e-9:
        return None

    x = -(v0 * m11 - v1 * m01) / det
    y = -(m00 * v1 - m01 * v0) / det

    return (x, y)