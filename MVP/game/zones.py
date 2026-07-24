import time

from MVP.game.constants import (
    ZONE_HIT_TOLERANCE,
    ZONES,
    DANGER_BOUNDS,
    ROUND_SURVIVE,
    ROUND_EXPAND,
)

from MVP.game.osc_sender import *

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

def point_in_safe_zone(point, zone):
    px, py = point
    zx, zy = zone["center"]

    r = zone["radius"] + ZONE_HIT_TOLERANCE + 0.2

    dx = px - zx
    dy = py - zy

    return (dx * dx + dy * dy) <= (r * r)


def zone_is_occupied(zone, tags):
    for tag in tags:
        if tag.filt_position is None:
            continue
        if point_in_safe_zone(tag.filt_position, zone):
            return True
    return False


def check_all_zones_lost(state):
    for zone in ZONES:
        # Ignore danger zones
        if not zone.get("safe"):
            continue
        # Ignore inactive zones
        if not zone.get("active", True):
            continue
        # One destroyed zone = game over
        if zone.get("destroyed", False):
            return True
    return False


def process_zone_transitions(tag_id, tag):

    current_zones = set()

    for zi, zone in enumerate(ZONES):
        if not zone.get("active", True):
            continue
        if point_in_zone(tag.filt_position, zone):
            current_zones.add(zi)

    entered = current_zones - tag.zones_inside
    exited = tag.zones_inside - current_zones

    for zi in entered:
        print(f"[ZONE] Tag {tag_id} ENTERED {ZONES[zi]['label']}")
        send_zone_enter(tag_id, zi)

    for zi in exited:
        print(f"[ZONE] Tag {tag_id} EXITED {ZONES[zi]['label']}")
        send_zone_exit(tag_id, zi)

    tag.zones_inside = current_zones




# ---------------------------------------------------------------------------
#  Zone Grow Logic (round 1)
# ---------------------------------------------------------------------------
def update_expansion_phase(state):
    all_expanded = True

    for zi, zone in enumerate(ZONES):
        if not zone.get("safe"):
            continue
        if not zone.get("active", True):
            continue

        occupied = zone_is_occupied(zone, state.tags)

        # Expand while occupied
        if occupied:
            if zone["radius"] < zone["max_radius"]:
                zone["radius"] += zone["expand_rate"]
                zone["radius"] = min(zone["radius"], zone["max_radius"])

                # Check if respective zone fully expanded
                if zone["radius"] == zone["max_radius"] and not zone["expanded_sent"]:
                    zone["expanded_sent"] = True
                    zone["captured"] = True
        
        # Global round progression check
        if zone["radius"] < zone["max_radius"]:
            all_expanded = False

    # Transition to next phase
    if all_expanded:
        print("=== ROUND 2: SURVIVAL PHASE ===")
        state.round = ROUND_SURVIVE
        state.survival_start_time = time.time()



# ---------------------------------------------------------------------------
#  Zone Shrink & Grow Logic (round 2) 
# ---------------------------------------------------------------------------
def update_shrinking_zones(state):

    for zone in ZONES:
        if not zone["active"]:
            continue

        if not zone.get("active", True):
            continue

        if zone.get("is_danger"): # skip danger zone
            continue

        occupied = zone_is_occupied(zone, state.tags)

        if not occupied:
            if zone["radius"] > zone["min_radius"]:
                zone["radius"] -= zone["shrink_rate"]
                zone["radius"] = max(zone["radius"], zone["min_radius"])

                #--------------- Lighting Cue ---------------
                update_zone_cue(zone)

                #--------------- Lose Condition ---------------
                if zone["radius"] <= zone["min_radius"]: # checks if zone shrinks to min_radius to trigger game end
                    zone["radius"] = zone["min_radius"]
                    zone["destroyed"] = True
                    zone["active"] = False
                    print(f"{zone['label']} LOST!")
                    state.safe_zone_lost = True

        else:
            # Tag is inside — grow back up to max_radius
            if zone["radius"] < zone["max_radius"]:
                zone["radius"] += zone.get("expand_rate", zone["shrink_rate"] * 0.5)
                zone["radius"] = min(zone["radius"], zone["max_radius"])

            # -------- Lighting Cue --------
            update_zone_cue(zone)

        current_direction = "growing" if occupied else "shrinking"
        previous_direction = zone.get("last_direction")

        if previous_direction is None:
            # Initialise without sending an unnecessary nudge.
            zone["last_direction"] = current_direction

        elif previous_direction != current_direction:
            zone["last_direction"] = current_direction

            print(
                f"{zone['label']} changed from "
                f"{previous_direction} to {current_direction}"
            )

            nudge_zone_cue(zone, current_direction)




def nudge_zone_cue(zone, direction):
    current_cue = zone["current_cue"]

    if direction == "growing":
        # Growing moves toward Cue 1.
        new_cue = max(1, current_cue - 1)

    elif direction == "shrinking":
        # Shrinking moves toward Cue 11.
        new_cue = min(11, current_cue + 1)

    else:
        return

    if new_cue == current_cue:
        return

    zone["current_cue"] = new_cue
    zone["hysteresis_active"] = True

    print(
        f"[HYSTERESIS] {zone['label']} "
        f"{direction} -> Cue {new_cue}"
    )

    send_zone_cue(zone, new_cue)

# ---------------------------------------------------------------------------
# Danger Zone Movement logic
# ---------------------------------------------------------------------------

DANGER_CUES = {
    "centre": 1,
    "min": 2,
    "max": 3,
}

def initialise_danger_zones():
    x_min, x_max, y_min, y_max = DANGER_BOUNDS

    centre_x = (x_min + x_max) / 2
    centre_y = (y_min + y_max) / 2

    for zone in ZONES:
        if not zone.get("is_danger"):
            continue

        zone["current_osc_cue"] = None

        if zone["axis"] == "horizontal":
            cx, cy = zone["center"]
            zone["center"] = (centre_x, cy)

            vx, vy = zone["velocity"]
            zone["velocity"] = [abs(vx), 0]

            send_danger_target(zone, "max")

        elif zone["axis"] == "vertical":
            cx, cy = zone["center"]
            zone["center"] = (cx, centre_y)

            vx, vy = zone["velocity"]
            zone["velocity"] = [0, abs(vy)]

            send_danger_target(zone, "max")


def send_danger_target(zone, target):
    cue = DANGER_CUES[target]

    # Avoid sending the same cue repeatedly.
    if zone.get("current_osc_cue") == cue:
        return

    zone["current_osc_cue"] = cue
    zone["movement_target"] = target

    print(
        f"[DANGER OSC] {zone['label']} "
        f"-> {target} | Cue {cue}"
    )

    send_danger_movement(
        zone["axis"],
        cue
    )


def update_danger_zones(state):
    x_min, x_max, y_min, y_max = DANGER_BOUNDS

    centre_x = (x_min + x_max) / 2
    centre_y = (y_min + y_max) / 2

    for zone in ZONES:
        if not zone["active"]:
            continue

        if not zone.get("is_danger"):
            continue

        cx, cy = zone["center"]
        vx, vy = zone["velocity"]

        old_x = cx
        old_y = cy

        new_x = cx + vx
        new_y = cy + vy

        axis = zone.get("axis")

        # ----------------------------------------
        # Horizontal danger-zone movement
        # ----------------------------------------
        if axis == "horizontal":

            # Hit maximum/right edge.
            if new_x + zone["radius"] > x_max:
                new_x = x_max - zone["radius"]
                vx = -abs(vx)

                # Now travel back toward centre.
                send_danger_target(zone, "centre")

            # Hit minimum/left edge.
            elif new_x - zone["radius"] < x_min:
                new_x = x_min + zone["radius"]
                vx = abs(vx)

                # Now travel back toward centre.
                send_danger_target(zone, "centre")

            else:
                target = zone.get("movement_target")

                # Crossed centre while travelling left from maximum.
                if (
                    target == "centre"
                    and old_x > centre_x
                    and new_x <= centre_x
                ):
                    new_x = centre_x

                    # Continue toward minimum.
                    send_danger_target(zone, "min")

                # Crossed centre while travelling right from minimum.
                elif (
                    target == "centre"
                    and old_x < centre_x
                    and new_x >= centre_x
                ):
                    new_x = centre_x

                    # Continue toward maximum.
                    send_danger_target(zone, "max")

        # ----------------------------------------
        # Vertical danger-zone movement
        # ----------------------------------------
        elif axis == "vertical":

            # Hit maximum/top edge.
            if new_y + zone["radius"] > y_max:
                new_y = y_max - zone["radius"]
                vy = -abs(vy)

                # Now travel back toward centre.
                send_danger_target(zone, "centre")

            # Hit minimum/bottom edge.
            elif new_y - zone["radius"] < y_min:
                new_y = y_min + zone["radius"]
                vy = abs(vy)

                # Now travel back toward centre.
                send_danger_target(zone, "centre")

            else:
                target = zone.get("movement_target")

                # Crossed centre while travelling down from maximum.
                if (
                    target == "centre"
                    and old_y > centre_y
                    and new_y <= centre_y
                ):
                    new_y = centre_y

                    # Continue toward minimum.
                    send_danger_target(zone, "min")

                # Crossed centre while travelling up from minimum.
                elif (
                    target == "centre"
                    and old_y < centre_y
                    and new_y >= centre_y
                ):
                    new_y = centre_y

                    # Continue toward maximum.
                    send_danger_target(zone, "max")

        else:
            print(
                f"Invalid danger-zone axis for "
                f"{zone['label']}: {axis}"
            )

        zone["center"] = (new_x, new_y)
        zone["velocity"] = [vx, vy]

        # ----------------------------------------
        # Check for clash
        # ----------------------------------------
        for tag_id, tag in enumerate(state.tags):
            if (
                not state.game_over_sent
                and tag.filt_position
                and point_in_zone(tag.filt_position, zone)
            ):
                print(
                    f"!!! GAME OVER - "
                    f"{zone['label']} CLASH !!!"
                )

                state.game_over_sent = True
                state.danger_zone_hit = True


# ---------------------------------------------------------------------------
# Zone Update Size Checker
# ---------------------------------------------------------------------------
def get_zone_percentage(zone):
    """
    Returns how full a safe zone is from 0-100%.
    """
    radius = zone["radius"]
    min_r = zone["min_radius"]
    max_r = zone["max_radius"]

    if max_r == min_r:
        return 100

    percent = ((radius - min_r) / (max_r - min_r)) * 100
    return max(0, min(100, percent))


def percentage_to_cue(percentage):
    """
    Converts 0-100% into Cue 1-11.

    100% -> Cue 1
     90% -> Cue 2
      ...
      0% -> Cue 11
    """
    cue = 11 - int(percentage / 10)
    return max(1, min(11, cue))


def update_zone_cue(zone):
    percentage = get_zone_percentage(zone)
    calculated_cue = percentage_to_cue(percentage)

    current_cue = zone["current_cue"]
    direction = zone.get("last_direction")
    hysteresis_active = zone.get("hysteresis_active", False)

    if hysteresis_active:

        if direction == "growing":
            # Cue numbers decrease as the zone grows.
            # Wait until the real percentage catches up with the nudged cue.
            if calculated_cue <= current_cue:
                zone["hysteresis_active"] = False
            else:
                return

        elif direction == "shrinking":
            # Cue numbers increase as the zone shrinks.
            # Wait until the real percentage catches up with the nudged cue.
            if calculated_cue >= current_cue:
                zone["hysteresis_active"] = False
            else:
                return

    if calculated_cue != zone["current_cue"]:
        zone["current_cue"] = calculated_cue

        print(
            f"{zone['label']} -> Cue {calculated_cue} "
            f"({percentage:.1f}%)"
        )

        send_zone_cue(zone, calculated_cue)

# ---------------------------------------------------------------------------
# Master Zone Update
# ---------------------------------------------------------------------------
def update_zones(state):
    if state.round == ROUND_EXPAND:
        update_expansion_phase(state)

    elif state.round == ROUND_SURVIVE:
        SURVIVAL_TIME = 60
        if state.round == ROUND_SURVIVE:
            elapsed = time.time() - state.survival_start_time
            if elapsed >= SURVIVAL_TIME:
                state.game_won = True
                state.stop = True

        update_shrinking_zones(state)

        if check_all_zones_lost(state):
            print("ALL SAFE ZONES LOST")
            state.stop = True

    update_danger_zones(state)
