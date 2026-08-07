import random

from constants import (
    ALL_ZONES,
    DANGER_BOUNDS,
    LEVEL_CONFIGS,
    TUTORIAL_ZONES,
    ZONES,
    ZONE_HIT_TOLERANCE,
)
from osc_sender import (
    send_tutorial_zone_enter,
    send_tutorial_zone_exit,
    send_zone_enter,
    send_zone_exit,
    send_zone_percentage,
)


# ---------------------------------------------------------------------------
# Zone detection
# ---------------------------------------------------------------------------
def point_in_zone(point, zone):
    if point is None:
        return False

    px, py = point
    zx, zy = zone["center"]
    radius = zone["radius"] + ZONE_HIT_TOLERANCE

    return (px - zx) ** 2 + (py - zy) ** 2 <= radius ** 2


def zone_is_occupied(zone, tags):
    return any(
        tag.filt_position is not None
        and point_in_zone(tag.filt_position, zone)
        for tag in tags
    )


def get_zone_by_label(zone_label):
    for zone in ALL_ZONES:
        if zone.get("label") == zone_label:
            return zone
    return None


def get_level_safe_zones(level_number):
    required_labels = set(LEVEL_CONFIGS[level_number]["zone_labels"])
    return [
        zone
        for zone in ZONES
        if zone.get("safe") and zone["label"] in required_labels
    ]


def reset_zone_list(zone_list):
    for zone in zone_list:
        if not zone.get("safe"):
            continue

        zone["radius"] = zone["min_radius"]
        zone["captured"] = False
        zone["expanded_sent"] = False
        zone["active"] = False
        zone["tutorial_max_sent"] = False
        zone["last_percentage_step"] = None
        zone["osc_target_step"] = None


def reset_zones(state):
    reset_zone_list(ZONES)
    reset_zone_list(TUTORIAL_ZONES)

    for zone in ZONES:
        if zone.get("is_danger"):
            zone["active"] = False

    for tag in state.tags:
        tag.zones_inside.clear()


def configure_zones_for_level(level_number):
    required_labels = set(LEVEL_CONFIGS[level_number]["zone_labels"])

    for zone in ZONES:
        if not zone.get("safe"):
            continue

        is_required = zone["label"] in required_labels
        zone["active"] = is_required
        zone["radius"] = zone["max_radius"] if is_required else zone["min_radius"]
        zone["captured"] = False
        zone["expanded_sent"] = False
        zone["last_percentage_step"] = None
        zone["osc_target_step"] = None

        # Each active level zone begins at 100%, so send its initial cue once.
        if is_required:
            initialise_zone_percentage_osc(zone)


def configure_tutorial_survival_zones():
    for zone in TUTORIAL_ZONES:
        zone["active"] = True
        zone["radius"] = zone["max_radius"]
        zone["captured"] = False
        zone["tutorial_max_sent"] = False
        zone["last_percentage_step"] = None
        zone["osc_target_step"] = None


# ---------------------------------------------------------------------------
# Aggregate occupancy-based OSC transitions
# ---------------------------------------------------------------------------
def zone_occupied_by_other_tag(zone, tags, current_tag):
    for other_tag in tags:
        if other_tag is current_tag:
            continue

        if other_tag.filt_position is None:
            continue

        if point_in_zone(other_tag.filt_position, zone):
            return True

    return False


def process_zone_transitions(state, tag_id, tag, current_level=None):
    current = set()
    zone_lookup = {}

    for zone in ALL_ZONES:
        if not zone.get("safe"):
            continue

        if not zone.get("active", True):
            continue

        zone_label = zone["label"]
        zone_lookup[zone_label] = zone

        if point_in_zone(tag.filt_position, zone):
            current.add(zone_label)

    entered = current - tag.zones_inside
    exited = tag.zones_inside - current

    for zone_label in entered:
        zone = zone_lookup.get(zone_label)
        if zone is None:
            continue

        print(f"[ZONE] Tag {tag_id} ENTERED {zone_label}")

        if zone_occupied_by_other_tag(zone, state.tags, tag):
            print(f"[ZONE] {zone_label} already occupied; enter OSC suppressed")
            continue

        if zone.get("tutorial", False):
            tutorial_zone_index = TUTORIAL_ZONES.index(zone)
            send_tutorial_zone_enter(tag_id, tutorial_zone_index)
        else:
            zone_index = ZONES.index(zone)
            send_zone_enter(tag_id, zone_index, current_level)

    for zone_label in exited:
        zone = get_zone_by_label(zone_label)
        if zone is None:
            continue

        print(f"[ZONE] Tag {tag_id} EXITED {zone_label}")

        if zone_occupied_by_other_tag(zone, state.tags, tag):
            print(f"[ZONE] {zone_label} still occupied; exit OSC suppressed")
            continue

        if zone.get("tutorial", False):
            tutorial_zone_index = TUTORIAL_ZONES.index(zone)
            send_tutorial_zone_exit(tag_id, tutorial_zone_index)
        else:
            zone_index = ZONES.index(zone)
            send_zone_exit(tag_id, zone_index, current_level)

    tag.zones_inside = current
    return entered, exited


# ---------------------------------------------------------------------------
# Zone percentage OSC tracking
# ---------------------------------------------------------------------------
def get_zone_percentage(zone):
    """Return zone size from 0 to 100 based on its radius range."""
    radius_range = zone["max_radius"] - zone["min_radius"]

    if radius_range <= 0:
        return 100.0

    percentage = (
        (zone["radius"] - zone["min_radius"])
        / radius_range
    ) * 100.0

    return max(0.0, min(100.0, percentage))


def initialise_zone_percentage_osc(zone):
    """Set an active game zone to 100% and send its initial GrandMA cue."""
    if zone not in ZONES or not zone.get("safe"):
        return

    zone["last_percentage_step"] = 100
    zone["osc_target_step"] = None
    send_zone_percentage(ZONES.index(zone), 100, "initial")


def check_percentage_target_reached(zone):
    """Mark the current 10% target as reached once Python gets close to it."""
    target = zone.get("osc_target_step")
    if target is None:
        return

    percentage = get_zone_percentage(zone)

    if abs(percentage - target) <= 1.0:
        zone["last_percentage_step"] = target
        zone["osc_target_step"] = None


def update_zone_percentage_target(zone, direction):
    """
    Send GrandMA the next 10% destination before Python reaches it.

    This lets GrandMA fade continuously while the Python radius moves through
    the same interval. The same target is not resent every frame.
    """
    if zone not in ZONES or not zone.get("safe"):
        return

    current_step = zone.get("last_percentage_step")
    if current_step is None:
        initialise_zone_percentage_osc(zone)
        current_step = 100

    if direction == "shrinking":
        target_step = max(0, current_step - 10)
    elif direction == "expanding":
        target_step = min(100, current_step + 10)
    else:
        return

    # Already at the end in this direction.
    if target_step == current_step:
        return

    # Don't resend the same destination every update frame.
    if zone.get("osc_target_step") == target_step:
        return

    zone["osc_target_step"] = target_step

    send_zone_percentage(
        ZONES.index(zone),
        target_step,
        direction,
    )


# ---------------------------------------------------------------------------
# Tutorial and survival zone updates
# ---------------------------------------------------------------------------
def update_tutorial_zones(state):
    for zone in TUTORIAL_ZONES:
        if not zone.get("active", False):
            continue

        if zone_is_occupied(zone, state.tags):
            zone["radius"] = min(
                zone["max_radius"],
                zone["radius"] + zone["expand_rate"],
            )
        else:
            zone["radius"] = max(
                zone["min_radius"],
                zone["radius"] - zone["shrink_rate"],
            )


def update_survival_zones(state, current_level):
    for zone in get_level_safe_zones(current_level):
        if not zone.get("active", True):
            continue

        occupied = zone_is_occupied(zone, state.tags)

        # First acknowledge any percentage destination Python has reached.
        check_percentage_target_reached(zone)

        if occupied:
            # Tell GrandMA the next larger destination first, then move Python.
            update_zone_percentage_target(zone, "expanding")

            zone["radius"] = min(
                zone["max_radius"],
                zone["radius"] + zone["expand_rate"],
            )
        else:
            # Tell GrandMA the next smaller destination first, then move Python.
            update_zone_percentage_target(zone, "shrinking")

            zone["radius"] = max(
                zone["min_radius"],
                zone["radius"] - zone["shrink_rate"],
            )

        # Catch the target on the frame that the radius arrives.
        check_percentage_target_reached(zone)


def any_level_zone_at_minimum(level_number):
    tolerance = 0.001
    return any(
        zone["radius"] <= zone["min_radius"] + tolerance
        for zone in get_level_safe_zones(level_number)
    )


def any_tutorial_zone_at_minimum():
    tolerance = 0.001
    return any(
        zone["radius"] <= zone["min_radius"] + tolerance
        for zone in TUTORIAL_ZONES
        if zone.get("active", False)
    )


# ---------------------------------------------------------------------------
# Danger-zone movement
# ---------------------------------------------------------------------------
def initialise_danger_zones():
    for zone in ZONES:
        if not zone.get("is_danger"):
            continue

        zone["active"] = True
        zone["center"] = list(zone["start_center"])

        direction = random.choice([-1, 1])
        if zone["axis"] == "horizontal":
            zone["velocity"] = [abs(zone["velocity"][0]) * direction, 0.0]
        else:
            zone["velocity"] = [0.0, abs(zone["velocity"][1]) * direction]


def update_danger_zones(state):
    xmin, xmax, ymin, ymax = DANGER_BOUNDS

    for zone in ZONES:
        if not zone.get("is_danger") or not zone.get("active", True):
            continue

        x, y = zone["center"]
        vx, vy = zone["velocity"]
        radius = zone["radius"]

        x += vx
        y += vy

        if x - radius < xmin or x + radius > xmax:
            vx = -vx
            x = max(xmin + radius, min(xmax - radius, x))

        if y - radius < ymin or y + radius > ymax:
            vy = -vy
            y = max(ymin + radius, min(ymax - radius, y))

        zone["center"] = [x, y]
        zone["velocity"] = [vx, vy]

# Compatibility wrapper retained because game.py imports update_zones.
# GameManager calls the dedicated tutorial/survival functions directly.
def update_zones(state):
    update_tutorial_zones(state)
