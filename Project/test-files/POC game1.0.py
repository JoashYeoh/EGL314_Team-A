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
import matplotlib.pyplot as plt  # Provides the underlying dark theme styles used for the game board canvas
import matplotlib.patches as mpatches
# ^^^ CRITICAL FOR DANGER ZONES: 
# This is where 'mpatches.Circle' comes from. It is used to generate 
# the actual visual circles (the red danger balls) on your game grid.

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# ^^^ Standard GUI library. It creates 'plot_frame', which acts as the 
# physical container holding your game arena and the moving danger zones.

from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

# ---------------------------------------------------------------------------
# OSC to Multiplay -- when enter zone and exit zone
# ---------------------------------------------------------------------------
OSC_TARGET_IP = "192.168.254.189"    # IP of laptop running Multi-play
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
# Anchor layout and view config  (must match uart.py)
# ---------------------------------------------------------------------------
ANCHORS = {
    0: (0.0, 0.0),
    1: (0.0, 0.50),
    2: (0.0, 1.0),
    3: (1.0, 1.0),
    4: (1.0, 0.50),
    5: (1.0, 0.0),
}

VIEW_BOUNDS = (-0.50, 1.50, -0.50, 1.50)

# ---------------------------------------------------------------------------
# Zone configs
# ---------------------------------------------------------------------------
ZONE_HIT_TOLERANCE = 0.0

ZONES = [
    {
        "center": (0.25, 0.25),  #top left
        "radius": 0.10,
        "max_radius": 0.25,
        "min_radius": 0.10,
        "expand_rate": 0.005,
        "shrink_rate": 0.0012,
        "color": "#00e5ff",
        "label": "ZONE A",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },
    {
        "center": (0.25, 0.75),  #top right
        "radius": 0.10,
        "max_radius": 0.25,
        "min_radius": 0.10,
        "expand_rate": 0.005,
        "shrink_rate": 0.0005,
        "color": "#ff40c3",
        "label": "ZONE B",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },
    {
        "center": (0.75, 0.75),  #bottom left
        "radius": 0.10,
        "max_radius": 0.25,
        "min_radius": 0.10,
        "expand_rate": 0.005,
        "shrink_rate": 0.002,
        "color": "#66ff66",
        "label": "ZONE C",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },
    {
        "center": (0.75, 0.25),  #bottom right
        "radius": 0.10,
        "max_radius": 0.25,
        "min_radius": 0.10,
        "expand_rate": 0.005,
        "shrink_rate": 0.0011,
        "color": "#c266ff",
        "label": "ZONE D",
        "active": True,
        "safe": True,
        "expanded_sent": False,
        "captured": False,
        "destroyed": False,
    },


    # --- DANGER ZONE 1: Vertical (Up/Down) within Anchors ---
    {
        "center": [0.5, 0.5],
        "radius": 0.10,          #show big my danger zone is
        "color": "#ff0000",
        "label": "DANGER-V",
        "active": True,
        "is_danger": True,          # Unique flag to identify this as an enemy zone
        "velocity": [0.0, 0.015],    # [X-speed, Y-speed] -> Moves ONLY up/down
    },
    # --- DANGER ZONE 2: Horizontal (Left/Right) within Anchors ---
    {
        "center": [0.5, 0.5],
        "radius": 0.10,
        "color": "#ff0000",
        "label": "DANGER-H",
        "active": True,
        "is_danger": True,
        "velocity": [0.015, 0.0],  # [X-speed, Y-speed] -> Moves ONLY left/right
    },
]

# ---------------------------------------------------------------------------
# Game Phases - round progression
# ---------------------------------------------------------------------------
ROUND_EXPAND = 0
ROUND_SURVIVE = 1


TAG_COLORS = [
    "#ff5252", "#42a5f5", "#66bb6a", "#ffb74d",
    "#ab47bc", "#26a69a", "#ec407a", "#bdbdbd",
]

COLOR_NAMES = [
    "red", "blue", "green", "orange",
    "purple", "teal", "pink", "gray",
]

DEFAULT_PORT = 5005  # UDP port to listen on


# ---------------------------------------------------------------------------
# Trilateration (linear least-squares multilateration — no numpy needed)
# ---------------------------------------------------------------------------
def trilaterate_2d(anchor_positions, distances):
    valid = [(p[0], p[1], d) for p, d in zip(anchor_positions, distances)
            if p is not None and 0.05 < d < 50.0]
    if len(valid) < 3:
        return None

    xr, yr, rr = valid[-1]
    A, b = [], []
    for xi, yi, ri in valid[:-1]:
        A.append((2 * (xi - xr), 2 * (yi - yr)))
        b.append(ri**2 - rr**2 - xi**2 + xr**2 - yi**2 + yr**2)
    if len(A) < 2:
        return None

    m00 = sum(ax * ax for ax, ay in A)
    m01 = sum(ax * ay for ax, ay in A)
    m11 = sum(ay * ay for ax, ay in A)
    v0  = sum(ax * bi for (ax, ay), bi in zip(A, b))
    v1  = sum(ay * bi for (ax, ay), bi in zip(A, b))

    det = m00 * m11 - m01 * m01
    if abs(det) < 1e-9:
        return None

    x = -(v0 * m11 - v1 * m01) / det
    y = -(m00 * v1 - m01 * v0) / det
    return x, y

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
# Kalman filter (position + velocity, 2-D)
# ---------------------------------------------------------------------------
class Kalman2D:
    def __init__(self, dt=0.10, q=0.12, r=1.1):
        self.dt = dt
        self.q  = q
        self.r  = r
        self.state = [0.0, 0.0, 0.0, 0.0]
        self.P = [[1.0, 0, 0, 0], [0, 1.0, 0, 0],
                [0, 0, 1.0, 0], [0, 0, 0, 1.0]]
        self.initialized = False

    def predict(self):
        if not self.initialized:
            return
        self.state[0] += self.state[2] * self.dt
        self.state[1] += self.state[3] * self.dt
        for i in range(4):
            self.P[i][i] += self.q

    def update(self, mx, my):
        if not self.initialized:
            self.state = [mx, my, 0.0, 0.0]
            self.initialized = True
            return mx, my
        Kx = self.P[0][0] / (self.P[0][0] + self.r)
        Ky = self.P[1][1] / (self.P[1][1] + self.r)
        old_x, old_y = self.state[0], self.state[1]
        self.state[0] += Kx * (mx - self.state[0])
        self.state[1] += Ky * (my - self.state[1])
        self.state[2] = (self.state[0] - old_x) / self.dt
        self.state[3] = (self.state[1] - old_y) / self.dt
        self.P[0][0] *= (1 - Kx)
        self.P[1][1] *= (1 - Ky)
        return self.state[0], self.state[1]


# ---------------------------------------------------------------------------
# Per-tag state and shared state container
# ---------------------------------------------------------------------------
@dataclass
class TagState:
    last_distances: list = field(default_factory=lambda: [0.0] * 8)
    raw_position:   tuple = None
    filt_position:  tuple = None
    last_update:    float = 0.0
    kalman: Kalman2D = field(default_factory=Kalman2D)
    zones_inside: set = field(default_factory=set)

class SharedState:
    def __init__(self, n_tags, simulate=False):
        self.n_tags = n_tags
        self.tags   = [TagState() for _ in range(n_tags)]
        self.row_color_index = list(range(n_tags))
        self.lock   = threading.Lock()
        self.frame_count = 0
        self.start_time  = time.time()
        self.game_started = False
        self.stop = False
        self.game_over_sent = False # to check if game over state has been sent out on osc (so it doesn't spam)
        self.round = ROUND_EXPAND  # for game to start in expand mode (round1)
        self.simulate = simulate # tag simulation state
        self.survival_start_time = None # survival state for survival round
        self.game_won = False


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
                zone["velocity"] = [v * SPEED_MULTIPLIER for v in zone["velocity"]]
        print(f"[GAME] Danger zone speeds increased by {SPEED_MULTIPLIER}x!")

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







# ---------------------------------------------------------------------------
# Viewer App
# Tutorial/Instructions for game
#----------------------------------------------------------------------------
class TutorialWindow:
    def __init__(self, parent, state, fullscreen):
        self.parent = parent
        self.state = state
        self.fullscreen = fullscreen
        
        # Create a Toplevel pop-up container
        self.top = tk.Toplevel(parent)
        self.top.title("Game Instructions & Tutorial")
        self.top.configure(bg="#111111")

        # --- Make it cover the whole laptop screen ---
        self.top.attributes("-fullscreen", True)
        
        # Enforce target exit routine if window closed via Alt+F4 or system keys
        self.top.protocol("WM_DELETE_WINDOW", self.on_close)

        # Define the instruction pages (Text + optional placeholder image file)
        self.pages = [
            {"text": "1. Welcome to Zone Capturing. click next to view how to play the game.", "img": "Assets/step1.png"},
            {"text": "2. The objective of this game is to capture all safe zones, by standing withitn the zone.", "img": "Assets/step2.png"},
            {"text": "3. Upon reaching a safe zone, you have to remain in the zone, as capturing commences! (zone stops expanding when captured)", "img": "Assets/step3.png"},
            {"text": "4. Once all safe zones have been captured successfully, you will progress to the next round.", "img": "Assets/step4.png"},
            {"text": "5. However, beware of the DANGER ZONES. AVOID THEM AT ALL COST! Coming into contact with them would end the game.", "img": "Assets/step5.png"},
            {"text": "6. There will be two rounds in total. In the second round, the speed of the moving danger zones increases!", "img": "Assets/step6.png"},
            {"text": "7. Leaving the safe zones, will cause the safe zones to shrink. STAY ON IT!", "img": "Assets/step7.png"},
            {"text": "8. That's it! Are you ready to take on the challenge explorer? If you are, click on 'start game'.", "img": "Assets/step8.png"}
        ]
        self.current_page = 0

        # --- UI LAYOUT STRUCTURE ---
        # Configure grid row weights to allocate vertical space: Text (Top) -> Image (Middle) -> Buttons (Bottom)
        self.top.grid_rowconfigure(0, weight=1) # Top text spacing
        self.top.grid_rowconfigure(1, weight=3) # Middle image spacing (gets the most room)
        self.top.grid_rowconfigure(2, weight=1) # Bottom navigation spacing
        self.top.grid_columnconfigure(0, weight=1)


        # 1. Top Section: Instruction text label
        self.txt_lbl = tk.Label(
            self.top, text="", 
            bg="#111111", fg="white", justify="center",
            font=("Helvetica", 24, "bold"), wraplength=1000
        )
        self.txt_lbl.grid(row=0, column=0, pady=(50, 20), sticky="nsew")

        # 2. Middle Section: Image rendering container box
        self.img_frame = tk.Frame(self.top, bg="#222222", width=900, height=500)
        self.img_frame.grid(row=1, column=0, padx=50, pady=20)
        self.img_frame.pack_propagate(False) # Stop frame from shrinking to text size
        
        self.img_lbl = tk.Label(self.img_frame, text="", bg="#222222", fg="#777777", font=("Helvetica", 14, "italic"))
        self.img_lbl.pack(expand=True, fill="both")

        # 3. Bottom Section: Navigation control buttons panel
        self.nav_frame = tk.Frame(self.top, bg="#111111")
        self.nav_frame.grid(row=2, column=0, pady=(20, 50), sticky="ew")
        self.nav_frame.grid_columnconfigure(0, weight=1)
        self.nav_frame.grid_columnconfigure(1, weight=1)

        # Previous Button (Left Side)
        self.prev_btn = tk.Button(
            self.nav_frame, text="Previous", 
            bg="#333333", fg="white", activebackground="#555555",
            font=("Helvetica", 14, "bold"), padx=30, pady=10,
            command=self.show_prev_page
        )
        self.prev_btn.grid(row=0, column=0, padx=40, sticky="w")

        # Next / Start Button (Right Side)
        self.next_btn = tk.Button(
            self.nav_frame, text="Next", 
            bg="#00e5ff", fg="black", activebackground="#ff4081",
            font=("Helvetica", 14, "bold"), padx=30, pady=10,
            command=self.show_next_page
        )
        self.next_btn.grid(row=0, column=1, padx=40, sticky="e")

        # Bind the escape key to easily exit fullscreen during testing
        self.top.bind("<Escape>", lambda e: self.on_close())

        # Render the first page content instantly
        self.update_page_view()

    def update_page_view(self):
        """Refreshes the layout text, placeholder images, and buttons dynamically."""
        page_data = self.pages[self.current_page]
        
        # Update text string at the top
        self.txt_lbl.configure(text=page_data["text"])
        
        # Update middle placeholder label text
        self.img_lbl.configure(text=f"[ Diagram Image: {page_data['img']} ]")

        # --- Dynamic Optional Image Loading Segment ---
        import os
        try:
            # 1. Find the exact absolute folder directory where this game script sits
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 2. Combine that directory safely with your "Assets/step1.png" asset path
            full_image_path = os.path.join(script_dir, page_data["img"])
            
            # 3. Load the file from its definitive location
            self.current_img_asset = tk.PhotoImage(file=full_image_path)
            self.img_lbl.configure(image=self.current_img_asset, text="")
            
        except Exception as e:
            # Fallback safely to placeholder text description if file not found
            self.img_lbl.configure(image="", text=f"[ Missing Diagram Image: {page_data['img']} ]")
            print(f"DEBUG: Image failed to load because: {e}")

        # Control visibility of the "Previous" button
        if self.current_page == 0:
            self.prev_btn.grid_remove() # Hide completely on the first page
        else:
            self.prev_btn.grid() # Reveal on subsequent pages

        # Control context shifting of the "Next" / "Start Game Tracker" button
        if self.current_page == len(self.pages) - 1:
            self.next_btn.configure(
                text="Start Game", 
                bg="#ff4081", fg="white",
                command=self.start_game
            )
        else:
            self.next_btn.configure(
                text="Next", 
                bg="#00e5ff", fg="black",
                command=self.show_next_page
            )

    def show_next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_page_view()

    def show_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_view()

    def start_game(self):
        start_game_bgm(self.state)   # send OSC
        """Destroys the tutorial overlay completely and launches tracker interface."""
        self.top.destroy()
        self.state.game_started = True # toggles the start state of game

        # Only after Tutorial Window is destroyed would the ViewerApp (game) run
        ViewerApp(self.parent, self.state, True, self.fullscreen)

        self.parent.deiconify()
        self.parent.lift()
        self.parent.focus_force()

    def on_close(self):
        # Force clean terminate on early cancellation exit routines
        self.parent.destroy()
        sys.exit(0)
        

# ---------------------------------------------------------------------------
# Viewer  (Tkinter + matplotlib)
# ---------------------------------------------------------------------------
class ViewerApp:
    def __init__(self, root, state: SharedState, show_circles, fullscreen):
        self.root         = root
        self.state        = state
        self.show_circles = show_circles
        self.anchor_ids   = sorted(ANCHORS.keys())
        self.n_anchors    = len(self.anchor_ids)

        root.title("BU03 Live Tracker — game.py")
        root.configure(bg="#000000")

        root.grid_rowconfigure(0, weight=5)
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        plot_frame = tk.Frame(root, bg="#000000")
        plot_frame.grid(row=0, column=0, sticky="nsew")

        plt.style.use("dark_background")
        self.fig = Figure(figsize=(14, 8))
        self.fig.patch.set_facecolor("#000000")
        self.ax_plot = self.fig.add_subplot(111)

        x_min, x_max, y_min, y_max = VIEW_BOUNDS
        self.ax_plot.set_xlim(x_min, x_max)
        self.ax_plot.set_ylim(y_min, y_max)
        self.ax_plot.set_aspect("equal")
        self.ax_plot.set_facecolor("#000000")

        for aid, (ax_x, ax_y) in ANCHORS.items():
            self.ax_plot.plot(ax_x, ax_y, marker="^", markersize=14,
                            color="#ffeb3b", markeredgecolor="white")
            self.ax_plot.annotate(f"A{aid}", (ax_x, ax_y), xytext=(8, 8),
                                textcoords="offset points", color="#ffeb3b")

        self.zone_patches = []
        for zone in ZONES:
            circle = mpatches.Circle(zone["center"], zone["radius"], fill=False,
                                    linewidth=3, linestyle="--", edgecolor=zone["color"])
            self.ax_plot.add_patch(circle)
            txt = self.ax_plot.text(zone["center"][0], zone["center"][1], zone["label"],
                                color=zone["color"], ha="center", va="center", weight="bold")
            self.zone_patches.append((circle, txt, zone))

        self.row_dots = []
        self.row_circles_per_anchor = [[None] * self.n_anchors for _ in range(state.n_tags)]
        for i in range(state.n_tags):
            dot, = self.ax_plot.plot([], [], marker="o", markersize=10,
                                    color=TAG_COLORS[i], markeredgecolor="white")
            self.row_dots.append(dot)

        self.hud = self.ax_plot.text(0.02, 0.98, "", transform=self.ax_plot.transAxes,
                                    va="top", color="white", family="monospace",
                                    bbox=dict(facecolor="black", alpha=0.5))

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        if self.state.simulate: #-- if on simulate mode, 
            self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
            print("[SIM] Mouse simulation enabled")

        table_frame = tk.Frame(root, bg="#000000")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.id_labels, self.x_labels, self.y_labels = [], [], []
        self.color_combos, self.color_swatches = [], []

        for r in range(state.n_tags):
            id_lbl = tk.Label(table_frame, text=f"T{r}", bg="#111111", fg=TAG_COLORS[r], font=("Helvetica", 14, "bold"), relief="solid", borderwidth=1)
            id_lbl.grid(row=r+1, column=0, sticky="nsew")
            self.id_labels.append(id_lbl)

            x_lbl = tk.Label(table_frame, text="—", bg="#111111", fg="white", relief="solid", borderwidth=1)
            x_lbl.grid(row=r+1, column=1, sticky="nsew")
            self.x_labels.append(x_lbl)

            y_lbl = tk.Label(table_frame, text="—", bg="#111111", fg="white", relief="solid", borderwidth=1)
            y_lbl.grid(row=r+1, column=2, sticky="nsew")
            self.y_labels.append(y_lbl)

            color_cell = tk.Frame(table_frame, bg="#111111", relief="solid", borderwidth=1)
            color_cell.grid(row=r+1, column=3, sticky="nsew")
            swatch = tk.Frame(color_cell, bg=TAG_COLORS[r], width=24, height=24)
            swatch.pack(side="left", padx=8)
            self.color_swatches.append(swatch)
            combo = ttk.Combobox(color_cell, values=COLOR_NAMES, state="readonly", width=10)
            combo.set(COLOR_NAMES[r])
            combo.pack(side="left", padx=4)
            combo.bind("<<ComboboxSelected>>", lambda e, row=r: self.on_color_changed(row))
            self.color_combos.append(combo)

        root.bind("<KeyPress-q>", lambda e: self.shutdown())
        if fullscreen: root.attributes("-fullscreen", True)
        self.root.after(100, self.update_loop)

    def update_loop(self):
        if not self.state.stop:
            with self.state.lock:
                update_zones(self.state)

        if self.state.stop:
            if self.state.game_won:
                self.hud.set_text("🎉 YOU WIN! 🎉\n"
                    "All survival objectives completed!"
                )
                self.hud.set_color("lime")

            else:
                self.hud.set_text(
                    "!!! GAME OVER !!!\n"
                    "DANGER ZONE CLASH"
                )
                self.hud.set_color("red")

            self.canvas.draw_idle()
            return

        with self.state.lock:
            snapshot = [{"filt": t.filt_position, "dists": list(t.last_distances), "last": t.last_update} for t in self.state.tags]
            total, elapsed = self.state.frame_count, time.time() - self.state.start_time
            color_indices = list(self.state.row_color_index)

        now = time.time()

        # ----- SURVIVAL TIMER HUD -----
        if (self.state.round == ROUND_SURVIVE and self.state.survival_start_time is not None):
            SURVIVAL_TIME = 60
            remaining = max(0, SURVIVAL_TIME - (time.time() - self.state.survival_start_time))
            self.hud.set_text(
                f"SURVIVAL MODE\n"
                f"Time Left: {remaining:.0f}s"
            )
            self.hud.set_color("white")

        for patch, txt, zone_data in self.zone_patches:
            patch.center = zone_data["center"]
            patch.set_radius(zone_data["radius"])
            txt.set_position(zone_data["center"])
            # this is for survival mode, where if zone shrinks to minimum then remove zone from viewer
            if zone_data.get("destroyed"):
                patch.set_visible(False)
                txt.set_visible(False)
                continue

        for row, snap in enumerate(snapshot):
            color = TAG_COLORS[color_indices[row]]
            pos, stale = snap["filt"], (now - snap["last"] > 1.0) if snap["last"] else True
            self.row_dots[row].set_color(color)
            if pos and not stale:
                self.row_dots[row].set_data([pos[0]], [pos[1]])
                self.x_labels[row].configure(text=f"{pos[0]:.3f}")
                self.y_labels[row].configure(text=f"{pos[1]:.3f}")
            else:
                self.row_dots[row].set_data([], [])
                self.x_labels[row].configure(text="—")

        self.canvas.draw_idle()
        self.root.after(66, self.update_loop)

    def on_color_changed(self, row):
        name = self.color_combos[row].get()
        idx = COLOR_NAMES.index(name)
        with self.state.lock:
            self.state.row_color_index[row] = idx
        self.sync_color_widgets(self.state.row_color_index)

    def sync_color_widgets(self, indices):
        for r, ci in enumerate(indices):
            self.color_swatches[r].configure(bg=TAG_COLORS[ci])
            self.id_labels[r].configure(fg=TAG_COLORS[ci])

    def shutdown(self):
        self.state.stop = True
        self.root.destroy()


    #Viewerapp simulate
    def on_mouse_move(self, event):
        if not self.state.game_started:
            return

        if event.xdata is None:
            return

        if event.ydata is None:
            return

        with self.state.lock:

            tag = self.state.tags[0]

            tag.filt_position = (
                float(event.xdata),
                float(event.ydata)
            )

            tag.last_update = time.time()

            process_zone_transitions(0, tag)

        update_zones(self.state)





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

    TutorialWindow(root, state, not args.windowed)

    root.mainloop()

if __name__ == "__main__":
    main()