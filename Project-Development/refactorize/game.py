#!/usr/bin/env python3
"""
game.py  —  OSC Receiver + Trilateration + Kalman Filter + Visualizer
======================================================================
Runs on the "game" Pi that drives the display.

Listens for OSC messages sent by uart.py:
    /distances  <tag_id:int> <d0:float> ... <d7:float>

For each incoming frame it:
    1. Runs multilateration (trilaterate_2d) to get a raw (x, y) position.
    2. Smooths it through a per-tag Kalman2D filter.
    3. Updates a live Tkinter / matplotlib visualizer (identical to the
        original viewer).
"""

import argparse
import csv
import sys
import threading
import time
import tkinter as tk
# ^^^ Standard GUI library. It creates 'plot_frame', which acts as the 
# physical container holding your game arena and the moving danger zones.

from tkinter import ttk
from dataclasses import dataclass, field

import matplotlib
matplotlib.use("TkAgg")   # Embedded backend that allows the game map to display inside a Tkinter window
import matplotlib.pyplot as plt  # Provides the dark theme styles used for the game board canvas
import matplotlib.patches as mpatches
# ^^^ CRITICAL FOR DANGER ZONES: 
# This is where 'mpatches.Circle' comes from. It is used to generate the actual visual circles (the red danger balls) on your game grid.

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# ^^^ Standard GUI library. It creates 'plot_frame', which acts as the 
# physical container holding your game arena and the moving danger zones.

from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from pythonosc import udp_client


from constants import *
from shared_state import *
from trilateration import trilaterate_2d

from viewer import ViewerApp
from tutorial import TutorialWindow


# ---------------------------------------------------------------------------
# OSC to Multiplay -- when enter zone and exit zone
# ---------------------------------------------------------------------------
OSC_TARGET_IP = "127.0.0.1"    # IP of laptop running Multi-play
OSC_TARGET_PORT = 8888

osc_tx_multiPlay = udp_client.SimpleUDPClient(OSC_TARGET_IP, OSC_TARGET_PORT)


def start_game_bgm(state): #-- start game track

    print("START BUTTON PRESSED")
    osc_tx_multiPlay.send_message("/cue/1/go", "")

    state.game_music_started = True


def send_zone_enter(tag_id, zone_index): #-- when tag enter zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_multiPlay.send_message("/cue/3/go", "")

    if zone_name == "ZONE B":
        osc_tx_multiPlay.send_message("/cue/4/go", "")

    if zone_name == "ZONE C":
        osc_tx_multiPlay.send_message("/cue/5/go", "")
    
    if zone_name == "ZONE D":
        osc_tx_multiPlay.send_message("/cue/6/go", "")
    
    print(
        f"[OSC] Sent ENTER "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_zone_exit(tag_id, zone_index): #-- when tag exit zone triger multiplay
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_multiPlay.send_message("/cue/3/stop", "")

    if zone_name == "ZONE B":
        osc_tx_multiPlay.send_message("/cue/4/stop", "")

    if zone_name == "ZONE C":
        osc_tx_multiPlay.send_message("/cue/5/stop", "")
    
    if zone_name == "ZONE D":
        osc_tx_multiPlay.send_message("/cue/6/stop", "")

    print(
        f"[OSC] Sent EXIT "
        f"Tag={tag_id} Zone={zone_name}"
    )


def send_zone_expanded(zone_index): #-- when respective zone fully expanded, trigger stinger
    zone_name = ZONES[zone_index]["label"]

    if zone_name == "ZONE A":
        osc_tx_multiPlay.send_message("/cue/7/go", "")
        osc_tx_multiPlay.send_message("/cue/3/stop", "")

    if zone_name == "ZONE B":
        osc_tx_multiPlay.send_message("/cue/8/go", "")
        osc_tx_multiPlay.send_message("/cue/4/stop", "")

    if zone_name == "ZONE C":
        osc_tx_multiPlay.send_message("/cue/9/go", "")
        osc_tx_multiPlay.send_message("/cue/5/stop", "")
    
    if zone_name == "ZONE D":
        osc_tx_multiPlay.send_message("/cue/10/go", "")
        osc_tx_multiPlay.send_message("/cue/6/stop", "")

    print(f"[OSC] Zone {zone_index} Fully Expanded")


def send_game_over(tag_id, zone_label):  #-- when tag hit danger zone triger multiplay
    osc_tx_multiPlay.send_message("/stopall", "")
    osc_tx_multiPlay.send_message("/cue/2/go", "")

    print(
        f"[OSC] Sent Game Over "
        f"Tag={tag_id} Zone={zone_label}"
    )


def send_game_win():
    osc_tx_multiPlay.send_message("/stopall", "")
    osc_tx_multiPlay.send_message("/cue/11/go", "") # you win stinger
    print("WIN")



# ---------------------------------------------------------------------------
# Game Phases - round progression
# ---------------------------------------------------------------------------
ROUND_EXPAND = 0
ROUND_SURVIVE = 1



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


# ---------------------------------------------------------------------------
# OSC handler
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

# ---------------------------------------------------------------------------
# OSC handler — called from the OSC server thread for every distances message
# ---------------------------------------------------------------------------
def make_osc_handler(state: SharedState, anchor_ids, anchor_positions_list,
                    csv_writer=None):
    def handle_distances(address, *args):
        if not state.game_started:
            return

        if state.stop: return 

        if len(args) < 9:
            print(f"[osc] malformed message (got {len(args)} args)")
            return

        tag_id    = int(args[0])
        if state.simulate and tag_id == 0: #-- Ignore real update of tag 0 if simulation is active
            return
        distances = [float(v) for v in args[1:9]]

        if tag_id >= state.n_tags:
            return

        tag = state.tags[tag_id]
        dist_for_trilat = [distances[i] for i in anchor_ids]
        raw_pos = trilaterate_2d(anchor_positions_list, dist_for_trilat)

        with state.lock:
            tag.last_distances = distances
            tag.last_update = time.time()
            if raw_pos is not None:
                tag.kalman.predict()
                fx, fy = tag.kalman.update(raw_pos[0], raw_pos[1])
                tag.raw_position  = raw_pos
                tag.filt_position = (fx, fy)
                
                current_zones = set()
                for zi, zone in enumerate(ZONES):
                    if point_in_zone(tag.filt_position, zone):
                        current_zones.add(zi)

                entered = current_zones - tag.zones_inside
                exited  = tag.zones_inside - current_zones

                for zi in entered:
                    zone = ZONES[zi]
                    if zone.get("captured"): # checks if zone is already captured, so as to not re-trigger osc
                        continue
                    print(f"[ZONE] Tag {tag_id} ENTERED {ZONES[zi]['label']}")
                    send_zone_enter(tag_id, zi)

                for zi in exited:
                    print(f"[ZONE] Tag {tag_id} EXITED {ZONES[zi]['label']}")
                    send_zone_exit(tag_id, zi)

                tag.zones_inside = current_zones
            else:
                tag.kalman.predict()
            
            state.frame_count += 1

        if csv_writer is not None:
            row_data = [time.time(), tag_id, COLOR_NAMES[state.row_color_index[tag_id]]]
            row_data += [f"{distances[i]:.3f}" for i in anchor_ids]
            if raw_pos is not None:
                row_data += [f"{raw_pos[0]:.3f}", f"{raw_pos[1]:.3f}"]
            else:
                row_data += ["", ""]
            if tag.filt_position is not None:
                row_data += [f"{tag.filt_position[0]:.3f}", f"{tag.filt_position[1]:.3f}"]
            else:
                row_data += ["", ""]
            csv_writer.writerow(row_data)

    return handle_distances


# ---------------------------------------------------------------------------
# Reusable function for mouse simulation
#----------------------------------------------------------------------------

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





def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", type=int, default=2)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--csv", type=str, default=None)
    ap.add_argument("--windowed", action="store_true")
    ap.add_argument("--simulate", action="store_true")
    args = ap.parse_args()

    state = SharedState(n_tags=args.tags, simulate=args.simulate)
    disp = osc_dispatcher.Dispatcher()
    handler = make_osc_handler(state, sorted(ANCHORS.keys()), [ANCHORS[i] for i in sorted(ANCHORS.keys())])
    disp.map("/distances", handler)

    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", args.port), disp)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # 
    root = tk.Tk()
    root.withdraw()  # Hide root window

    tutorial = TutorialWindow(root, state, not args.windowed, ViewerApp, start_game_bgm, process_zone_transitions, update_zones)

    root.mainloop()

if __name__ == "__main__":
    main()