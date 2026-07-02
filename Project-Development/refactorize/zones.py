import time

from constants import (ZONE_HIT_TOLERANCE, ZONES, VIEW_BOUNDS, ROUND_SURVIVE, ROUND_EXPAND)

from osc_handler import *

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


def process_zone_transitions(tag_id, tag):

    current_zones = set()

    for zi, zone in enumerate(ZONES):
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

        occupied = zone_is_occupied(zone, state.tags)

        # Expand while occupied
        if occupied:
            if zone["radius"] < zone["max_radius"]:
                zone["radius"] += zone["expand_rate"]
                zone["radius"] = min(zone["radius"], zone["max_radius"])

                # Check if respective zone fully expanded
                if zone["radius"] == zone["max_radius"] and not zone["expanded_sent"]:
                    send_zone_expanded(zi)
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

        if zone.get("is_danger"): # skip danger zone
            continue

        occupied = zone_is_occupied(zone, state.tags)

        if not occupied:
            if zone["radius"] > zone["min_radius"]:
                zone["radius"] -= zone["shrink_rate"]
                zone["radius"] = max(zone["radius"], zone["min_radius"])
                if zone["radius"] <= zone["min_radius"]: # checks if zone shrinks to min_radius to trigger game end
                    zone["destroyed"] = True
                    zone["active"] = False
                    print(f"{zone['label']} LOST!")

        else:
            # Tag is inside — grow back up to max_radius
            if zone["radius"] < zone["max_radius"]:
                zone["radius"] += zone.get("grow_rate", zone["shrink_rate"] * 0.5)
                zone["radius"] = min(zone["radius"], zone["max_radius"])



# ---------------------------------------------------------------------------
# Danger Zone Movement logic
# ---------------------------------------------------------------------------
def update_danger_zones(state):
    # Anchor Boundaries (0.0 to 1.0)
    L_X_MIN, L_X_MAX = 0.0, 1.0   # Set the left and right outer boundary walls
    L_Y_MIN, L_Y_MAX = 0.0, 1.0   # Set the bottom and top outer boundary walls

    x_min, x_max, y_min, y_max = VIEW_BOUNDS
    for zone in ZONES:
        if not zone["active"]:
            continue   # Skip checking this zone if it's turned off
            
        if zone.get("is_danger"):
            cx, cy = zone["center"]     # Get current X and Y center position of the ball     
            vx, vy = zone["velocity"]   # Get current horizontal and vertical speeds
            
            new_x, new_y = cx + vx, cy + vy  # Calculate its potential next position step
            
            # Bounce logic at Anchor edges
            if new_x - zone["radius"] < L_X_MIN or new_x + zone["radius"] > L_X_MAX:
                vx = -vx
            if new_y - zone["radius"] < L_Y_MIN or new_y + zone["radius"] > L_Y_MAX:
                vy = -vy
                # Reverse the horizontal direction (bounce!)
                
            zone["center"] = (cx + vx, cy + vy)
            zone["velocity"] = [vx, vy]
            # Reverse the vertical direction (bounce!)
            
            
            # Check for clash
            for tag_id, tag in enumerate(state.tags):

                if not state.game_over_sent and tag.filt_position and point_in_zone(tag.filt_position, zone):

                    send_game_over(tag_id, zone["label"])

                    print(f"!!! GAME OVER - {zone['label']} CLASH !!!")   #when game hits the danger zone it will end and show game over

                    state.game_over_sent = True
                    state.stop = True 



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
                send_game_win()
                state.game_won = True
                state.stop = True

        update_shrinking_zones(state)

        if check_all_zones_lost(state):
            print("ALL SAFE ZONES LOST")
            send_game_over(-1, "ALL SAFE ZONES")
            state.stop = True

    update_danger_zones(state)
