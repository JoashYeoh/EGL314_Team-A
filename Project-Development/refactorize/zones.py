import time

from constants import (
    ZONE_HIT_TOLERANCE,
    ZONES,
    VIEW_BOUNDS,
    ROUND_SURVIVE,
    ROUND_EXPAND,
)

from osc_sender import *

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
                    #send_zone_expanded(zi)
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
        
        # --- NEW CONDITION ADDED HERE  when it goes to stage 2 for the danger zone ---
        SPEED_MULTIPLIER = 2.0  #when it reach zone 2 the game will speed up
        for zone in ZONES:
            if zone.get("is_danger"):
                # Multiplies both X and Y components of the velocity vector
                zone["velocity"] = [v * SPEED_MULTIPLIER for v in zone["velocity"]] # Multiply both the horizontal (X) and vertical (Y) speed values by your multiplier
        print(f"[GAME] Danger zone speeds increased by {SPEED_MULTIPLIER}x!")   # Print an alert to the terminal to tell people that it is moving faster




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
                zone["radius"] += zone.get("grow_rate", zone["shrink_rate"] * 0.5)
                zone["radius"] = min(zone["radius"], zone["max_radius"])

            # -------- Lighting Cue --------
            update_zone_cue(zone)



# ---------------------------------------------------------------------------
# Danger Zone Movement logic
# ---------------------------------------------------------------------------
def update_danger_zones(state):
    x_min, x_max, y_min, y_max = DANGER_BOUNDS
    for zone in ZONES:
        if not zone["active"]:
            continue   # Skip checking this zone if it's turned off
            
        if zone.get("is_danger"):
            cx, cy = zone["center"]     # Get current X and Y center position of the ball     
            vx, vy = zone["velocity"]   # Get current horizontal and vertical speeds
            
            new_x, new_y = cx + vx, cy + vy  # Calculate its potential next position step
            
            # Bounce logic at Anchor edges
            if new_x - zone["radius"] < x_min or new_x + zone["radius"] > x_max:
                vx = -vx
                send_danger_movement()
            if new_y - zone["radius"] < y_min or new_y + zone["radius"] > y_max:
                vy = -vy
                send_danger_movement()
                # Reverse the horizontal direction (bounce!)
                
            zone["center"] = (cx + vx, cy + vy)
            zone["velocity"] = [vx, vy]
            # Reverse the vertical direction (bounce!)
            
            
            # Check for clash
            for tag_id, tag in enumerate(state.tags):

                if not state.game_over_sent and tag.filt_position and point_in_zone(tag.filt_position, zone):

                    print(f"!!! GAME OVER - {zone['label']} CLASH !!!")   #when game hits the danger zone it will end and show game over

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
    new_cue = percentage_to_cue(percentage)

    if new_cue != zone["current_cue"]:
        zone["current_cue"] = new_cue
        print(f"{zone['label']} -> Cue {new_cue}")
        send_zone_cue(zone, new_cue)


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
