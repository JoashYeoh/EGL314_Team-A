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
from matplotlib.patches import Rectangle


from constants import *
from shared_state import SharedState



# ---------------------------------------------------------------------------
# Viewer  (Tkinter + matplotlib)
# ---------------------------------------------------------------------------
class ViewerApp:
    def __init__(self, root, state: SharedState, simulate, fullscreen, game_manager):
        self.root         = root
        self.state        = state
        self.simulate     = simulate
        self.anchor_ids   = sorted(ANCHORS.keys())
        self.n_anchors    = len(self.anchor_ids)

        self.game_manager = game_manager
        self.last_game_state = None

        #for debug prints
        #self.last_debug_state = None
        #self.last_overlay_text = None

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

        # Create zone patches
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

        # Create FigureCanvasTkAgg
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # ---------------- Overlay ----------------
        self.overlay_bg = Rectangle(
            (0, 0),
            1,
            1,
            transform=self.ax_plot.transAxes,
            facecolor="black",
            alpha=0.55,
            zorder=90
        )

        self.overlay_bg.set_visible(False)
        self.ax_plot.add_patch(self.overlay_bg)

        self.overlay_box = self.ax_plot.text(
            0.5,
            0.5,
            "",
            transform=self.ax_plot.transAxes,
            ha="center",
            va="center",
            fontsize=22,
            color="white",
            bbox=dict(
                facecolor="#222222",
                edgecolor="white",
                boxstyle="round,pad=1.0"
            ),
            zorder=100
        )

        self.overlay_box.set_visible(False)


        if self.state.simulate: #-- if on simulate mode, 
            self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
            print("[SIM] Mouse simulation enabled")

        self.root.bind("<space>", self.on_space_pressed) # bind space keypress

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
                self.game_manager.update()

        self.draw_gameplay()
        self.update_overlay()

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
        if self.game_manager.game_state != STATE_PLAYING:
            return

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

            self.game_manager.process_zone_transitions(0, tag)


    #space key-bind
    def on_space_pressed(self, event):
        self.game_manager.handle_space()
    

# ---------------------------------------------------------------------------
# In Game Overlays (for differnt states)
# ---------------------------------------------------------------------------
    def draw_gameplay(self):
        with self.state.lock:
            snapshot = [{"filt": t.filt_position, "dists": list(t.last_distances), "last": t.last_update} for t in self.state.tags]
            total, elapsed = self.state.frame_count, time.time() - self.state.start_time
            color_indices = list(self.state.row_color_index)

        now = time.time()

        # ----- TIMER HUD -----
        if self.game_manager.level_running:
            remaining = self.game_manager.get_remaining_time()
            self.hud.set_text(
                f"LEVEL {self.game_manager.current_level}\n"
                f"Time Left: {remaining:.0f}s"
            )
            self.hud.set_color("white")

        # ----- DRAW ZONES -----
        for patch, txt, zone_data in self.zone_patches:
            # Hide inactive zones
            if not zone_data.get("active", True):
                patch.set_visible(False)
                txt.set_visible(False)
                continue
            # Show active zones
            patch.set_visible(True)
            txt.set_visible(True)
            patch.center = zone_data["center"]
            patch.set_radius(zone_data["radius"])
            txt.set_position(zone_data["center"])
            # Hide destroyed zones
            if zone_data.get("destroyed"):
                patch.set_visible(False)
                txt.set_visible(False)

        # ----- DRAW TAGS -----
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

        pass
    

    def draw_game_over(self):
        self.show_overlay(
            "GAME OVER\n\n"
            #"A Safe Zone Was Lost\n\n"
            "Press SPACE",
            "red"
        )
        pass


    def draw_level_complete(self):
        next_level = self.game_manager.current_level
        self.show_overlay(
            f"LEVEL {next_level - 1} COMPLETE!\n\n"
            f"Press SPACE to Begin Level {next_level}",
            "cyan"
        )
        pass


    def draw_game_win(self):
        self.show_overlay(
            "YOU WIN!\n\n"
            "All Levels Complete\n\n Final sequence starting...",
            "lime"
        )
        pass

    
    def update_overlay(self):
        state = self.game_manager.game_state

        if state == self.last_game_state:
            return

        print(f"[VIEWER] State changed -> {state}")

        self.last_game_state = state

        if state == STATE_PLAYING:
            self.hide_overlay()

        elif state == STATE_LEVEL_COMPLETE:
            self.draw_level_complete()

        elif state == STATE_GAME_OVER:
            self.draw_game_over()

        elif state == STATE_GAME_WON:
            self.draw_game_win()


# ---------------------------------------------------------------------------
# Helper Functions (to call overlay)
# ---------------------------------------------------------------------------
    def show_overlay(self, text, colour="white"):
        self.overlay_bg.set_visible(True)
        self.overlay_box.set_text(text)
        self.overlay_box.set_color(colour)
        self.overlay_box.set_visible(True)
        self.canvas.draw_idle()
    

    def hide_overlay(self):
        self.overlay_bg.set_visible(False)
        self.overlay_box.set_visible(False)