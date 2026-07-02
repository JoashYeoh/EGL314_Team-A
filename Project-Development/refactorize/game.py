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

from game_manager import GameManager

from zones import *

from osc_handler import *



# ---------------------------------------------------------------------------
# Game Phases - round progression
# ---------------------------------------------------------------------------
ROUND_EXPAND = 0
ROUND_SURVIVE = 1




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










def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", type=int, default=2)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--csv", type=str, default=None)
    ap.add_argument("--windowed", action="store_true")
    ap.add_argument("--simulate", action="store_true")
    args = ap.parse_args()

    state = SharedState(n_tags=args.tags, simulate=args.simulate)
    game_manager = GameManager(state, update_zones, process_zone_transitions)
    disp = osc_dispatcher.Dispatcher()
    handler = make_osc_handler(state, sorted(ANCHORS.keys()), [ANCHORS[i] for i in sorted(ANCHORS.keys())])
    disp.map("/distances", handler)

    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", args.port), disp)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # 
    root = tk.Tk()
    root.withdraw()  # Hide root window

    tutorial = TutorialWindow(root, state, not args.windowed, ViewerApp, start_game_bgm, game_manager)

    root.mainloop()

if __name__ == "__main__":
    main()