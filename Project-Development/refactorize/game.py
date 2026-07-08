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

from viewer import ViewerApp
from tutorial import TutorialWindow

from game_manager import GameManager

from zones import *

from osc_handler import *

from osc_sender import *



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

    tutorial = TutorialWindow(root, state, not args.windowed, ViewerApp, send_start_game_bgm, game_manager)

    root.mainloop()

if __name__ == "__main__":
    main()