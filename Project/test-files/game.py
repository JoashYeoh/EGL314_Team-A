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
import math
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server

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
        "center": (0.5, 0.5),
        "radius": 0.35,
        "min_radius": 0.10,
        "shrink_rate": 0.002,
        "color": "#00e5ff",
        "label": "ZONE A",
        "active": True,
    },
    {
        "center": (0.2, 0.8),
        "radius": 0.25,
        "min_radius": 0.10,
        "shrink_rate": 0.010,
        "color": "#ff4081",
        "label": "ZONE B",
        "active": True,
    },
    {
        "center": (0.8, 0.2),
        "radius": 0.25,
        "min_radius": 0.10,
        "shrink_rate": 0.006,
        "color": "#66ff66",
        "label": "ZONE C",
        "active": True,
    },
    # --- DANGER ZONE 1: Vertical (Up/Down) within Anchors ---
    {
        "center": [0.5, 0.5],
        "radius": 0.10,
        "color": "#ff0000",
        "label": "DANGER-V",
        "active": True,
        "is_danger": True,
        "velocity": [0.0, 0.015], 
    },
    # --- DANGER ZONE 2: Horizontal (Left/Right) within Anchors ---
    {
        "center": [0.5, 0.5],
        "radius": 0.10,
        "color": "#ff0000",
        "label": "DANGER-H",
        "active": True,
        "is_danger": True,
        "velocity": [0.015, 0.0], 
    },
]

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
# MATH HELPER: Analytical Circle Lens Overlap Percentage
# ---------------------------------------------------------------------------
def calculate_circle_overlap_percentage(p1, r1, p2, r2):
    """
    Computes what fraction of Circle 1 (the Tag) is intersected by Circle 2 (Danger Zone).
    """
    dx, dy = p1[0] - p2[0], p1[1] - p2[1]
    d = math.sqrt(dx * dx + dy * dy)
    
    if d >= r1 + r2:    # Case 1: Completely separated circles
        return 0.0
    if d <= r2 - r1:    # Case 2: Tag is completely inside Danger Zone
        return 1.0
    if d <= r1 - r2:    # Case 3: Danger zone is entirely inside the tag
        tag_area = math.pi * (r1 ** 2)
        danger_area = math.pi * (r2 ** 2)
        return danger_area / tag_area

    # Case 4: Circles intersect forming an asymmetrical circular lens
    tag_area = math.pi * (r1 ** 2)
    part1 = r1 ** 2 * math.acos((d ** 2 + r1 ** 2 - r2 ** 2) / (2 * d * r1))
    part2 = r2 ** 2 * math.acos((d ** 2 + r2 ** 2 - r1 ** 2) / (2 * d * r2))
    part3 = 0.5 * math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
    
    intersection_area = part1 + part2 - part3
    return intersection_area / tag_area

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
    
    # --- ADD THIS LINE TO GIVE THE TAG A RADIUS SIZE ---
    radius: float = 0.05

class SharedState:
    def __init__(self, n_tags):
        self.n_tags = n_tags
        self.tags   = [TagState() for _ in range(n_tags)]
        self.row_color_index = list(range(n_tags))
        self.lock   = threading.Lock()
        self.frame_count = 0
        self.start_time  = time.time()
        self.stop = False

# ---------------------------------------------------------------------------
# Zone Update (Movement & Shrinking)
# ---------------------------------------------------------------------------
def update_zones(state):
    # Anchor Boundaries (0.0 to 1.0)
    L_X_MIN, L_X_MAX = 0.0, 1.0
    L_Y_MIN, L_Y_MAX = 0.0, 1.0
    
    for zone in ZONES:
        if not zone["active"]:
            continue

        if zone.get("is_danger"):
            cx, cy = zone["center"]
            vx, vy = zone["velocity"]
            
            new_x, new_y = cx + vx, cy + vy
            
            # Bounce logic at Anchor edges
            if new_x - zone["radius"] < L_X_MIN or new_x + zone["radius"] > L_X_MAX:
                vx = -vx
            if new_y - zone["radius"] < L_Y_MIN or new_y + zone["radius"] > L_Y_MAX:
                vy = -vy
                
            zone["center"] = (cx + vx, cy + vy)
            zone["velocity"] = [vx, vy]
            
          # ---------------------------------------------------------------
            # NEW COMPONENT: 40% RECTILINEAR INTERSECTION LIMIT
            # ---------------------------------------------------------------
            AREA_THRESHOLD = 0.75
            
            for tag_id, tag in enumerate(state.tags):
                if tag.filt_position:
                    # Run the mathematical lens overlap equation
                    overlap_fraction = calculate_circle_overlap_percentage(
                        tag.filt_position, tag.radius,
                        zone["center"], zone["radius"]
                    )
                    
                    # Stop game execution instantly if overlap >= 40%
                    if overlap_fraction >= AREA_THRESHOLD:
                        print(f"!!! GAME OVER - {zone['label']} CLASH ({overlap_fraction * 100:.1f}% Tag Encroachment) !!!")
                        state.stop = True
        
        else:
            occupied = zone_is_occupied(zone, state.tags)
            if not occupied:
                if zone["radius"] > zone["min_radius"]:
                    zone["radius"] -= zone["shrink_rate"]
                    if zone["radius"] < zone["min_radius"]:
                        zone["radius"] = zone["min_radius"]

def zone_is_occupied(zone, tags):
    for tag in tags:
        if tag.filt_position is None:
            continue
        if point_in_zone(tag.filt_position, zone):
            return True
    return False

# ---------------------------------------------------------------------------
# OSC handler
# ---------------------------------------------------------------------------
def make_osc_handler(state: SharedState, anchor_ids, anchor_positions_list,
                    csv_writer=None):
    def handle_distances(address, *args):
        if state.stop: return 

        if len(args) < 9:
            print(f"[osc] malformed message (got {len(args)} args)")
            return

        tag_id    = int(args[0])
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
                    print(f"[ZONE] Tag {tag_id} ENTERED {ZONES[zi]['label']}")
                for zi in exited:
                    print(f"[ZONE] Tag {tag_id} EXITED {ZONES[zi]['label']}")

                tag.zones_inside = current_zones
            else:
                tag.kalman.predict()
            
            update_zones(state)
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
            {"text": "1. Welcome to Red zones and Green zones, click next to view how to play the game.", "img": "Assets/step1.png"},
            {"text": "2. The objective of this game is to capture all safe zones for three rounds.", "img": "Assets/step2.png"},
            {"text": "3. However, there will be two moving danger zones trying to eliminate you. AVOID THEM AT ALL COST!", "img": "Assets/step3.png"},
            {"text": "4. Upon reaching the safe zones, you have to stay in them until you've captured 100% of the zone!", "img": "Assets/step4.png"},
            {"text": "5. Once all safe zones have been captured successfully, you will progress to the next round.", "img": "Assets/step5.png"},
            {"text": "6. There will be three rounds in total. With every zone cleared, the speed of the moving danger zones increases.", "img": "Assets/step6.png"},
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
        self.img_frame = tk.Frame(self.top, bg="#222222", width=700, height=400)
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
        """Destroys the tutorial overlay completely and launches tracker interface."""
        self.top.destroy()

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
        if self.state.stop:
            self.hud.set_text("!!! GAME OVER - DANGER ZONE CLASH !!!")
            self.hud.set_color("red")
            self.canvas.draw_idle()
            return

        with self.state.lock:
            snapshot = [{"filt": t.filt_position, "dists": list(t.last_distances), "last": t.last_update} for t in self.state.tags]
            total, elapsed = self.state.frame_count, time.time() - self.state.start_time
            color_indices = list(self.state.row_color_index)

        now = time.time()

        for patch, txt, zone_data in self.zone_patches:
            patch.center = zone_data["center"]
            patch.set_radius(zone_data["radius"])
            txt.set_position(zone_data["center"])

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", type=int, default=2)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--csv", type=str, default=None)
    ap.add_argument("--windowed", action="store_true")
    args = ap.parse_args()

    state = SharedState(n_tags=args.tags)
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