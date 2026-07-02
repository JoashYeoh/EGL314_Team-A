
from constants import (ZONE_HIT_TOLERANCE, ZONES)

# ---------------------------------------------------------------------------
# Zone detection
# ---------------------------------------------------------------------------
def point_in_zone(point, zone):
    if point is None:
        return False

    px, py = point
    zx, zy = zone["center"]
    r = zone["radius"] + ZONE_HIT_TOLERANCE

    dx = px - zx
    dy = py - zy

    return (dx * dx + dy * dy) <= (r * r)


def zone_is_occupied(zone, tags):
    for tag in tags:
        if tag.filt_position is None:
            continue
        if point_in_zone(tag.filt_position, zone):
            return True
    return False


def check_all_zones_lost(state):
    safe_zones = [z for z in ZONES if z.get("safe")]
    return all(z.get("destroyed", False) for z in safe_zones)