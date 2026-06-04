import time
import tkinter as tk
from tkinter import ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from config import (
    ANCHORS,
    VIEW_BOUNDS,
    TAG_COLORS,
    COLOR_NAMES
)


class ViewerApp:

    def __init__(
        self,
        root,
        state,
        engine,
        show_circles=True,
        fullscreen=True
    ):
        self.root = root
        self.state = state
        self.engine = engine
        self.show_circles = show_circles

        self.anchor_ids = sorted(ANCHORS.keys())

        self.build_window()
        self.build_plot()
        self.build_table()

        if fullscreen:
            root.attributes("-fullscreen", True)

        root.bind(
            "<KeyPress-q>",
            lambda e: self.shutdown()
        )

        self.root.after(
            100,
            self.update_loop
        )


    def build_window(self):

        self.root.title("BU03 Live Tracker")

        self.root.configure(
            bg="#000000"
        )

        self.root.grid_rowconfigure(
            0,
            weight=5
        )

        self.root.grid_rowconfigure(
            1,
            weight=1
        )

        self.root.grid_columnconfigure(
            0,
            weight=1
        )

        self.plot_frame = tk.Frame(
            self.root,
            bg="#000000"
        )

        self.plot_frame.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.table_frame = tk.Frame(
            self.root,
            bg="#000000"
        )

        self.table_frame.grid(
            row=1,
            column=0,
            sticky="nsew"
        )



    def build_plot(self):

        plt.style.use("dark_background")

        self.fig = Figure(
            figsize=(14, 8)
        )

        self.ax = self.fig.add_subplot(111)

        x_min, x_max, y_min, y_max = VIEW_BOUNDS

        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)

        self.ax.set_aspect("equal")

        self.draw_anchors()
        self.draw_zones()
        self.create_tag_markers()

        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=self.plot_frame
        )

        self.canvas.draw()

        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )



    def draw_anchors(self):

        for aid, (x, y) in ANCHORS.items():

            self.ax.plot(
                x,
                y,
                marker="^",
                markersize=14
            )

            self.ax.annotate(
                f"A{aid}",
                (x, y)
            )



    def draw_zones(self):

        self.zone_patches = []

        all_zones = (
            self.engine.zone_manager.safe_zones
            +
            self.engine.zone_manager.danger_zones
        )

        for zone in all_zones:

            patch = plt.Circle(
                zone.center,
                zone.radius,
                fill=False,
                color=zone.color
            )

            self.ax.add_patch(patch)

            label = self.ax.text(
                zone.center[0],
                zone.center[1],
                zone.label,
                ha="center",
                va="center"
            )

            self.zone_patches.append(
                (patch, label, zone)
            )


    def create_tag_markers(self):

        self.tag_markers = []

        for i in range(self.state.n_tags):

            marker, = self.ax.plot(
                [],
                [],
                marker="o",
                markersize=10,
                color=TAG_COLORS[i]
            )

            self.tag_markers.append(marker)

        self.hud = self.ax.text(
            0.02,
            0.98,
            "",
            transform=self.ax.transAxes
        )



    def build_table(self):

        self.id_labels = []
        self.x_labels = []
        self.y_labels = []

        self.color_combos = []
        self.color_swatches = []

        for row in range(self.state.n_tags):

            self.add_tag_row(
                row
            )



    def add_tag_row(self, row):

        id_label = tk.Label(
            self.table_frame,
            text=f"T{row}"
        )

        id_label.grid(
            row=row + 1,
            column=0,
            padx=5,
            pady=2
        )

        self.id_labels.append(id_label)

        x_label = tk.Label(
            self.table_frame,
            text="0.00"
        )

        x_label.grid(
            row=row + 1,
            column=1,
            padx=5
        )

        self.x_labels.append(x_label)

        y_label = tk.Label(
            self.table_frame,
            text="0.00"
        )

        y_label.grid(
            row=row + 1,
            column=2,
            padx=5
        )

        self.y_labels.append(y_label)
    

    def render_tags(self):

        for i, tag in enumerate(self.state.tags):

            pos = tag.filt_position

            if pos is None:
                continue

            x, y = pos

            self.tag_markers[i].set_data(
                [x],
                [y]
            )

            self.x_labels[i].config(
                text=f"{x:.2f}"
            )

            self.y_labels[i].config(
                text=f"{y:.2f}"
            )


    def render_zones(self):

        for patch, label, zone in self.zone_patches:

            patch.center = zone.center

            patch.set_radius(
                zone.radius
            )

            label.set_position(
                zone.center
            )



    def render_hud(self):

        phase = self.engine.phase.name

        self.hud.set_text(
            f"Phase: {phase}"
        )

        if phase == "GAME_OVER":

            self.hud.set_color("red")

        elif phase == "WIN":

            self.hud.set_color("lime")

        else:

            self.hud.set_color("white")



    def update_loop(self):

        self.render_zones()

        self.render_tags()

        self.render_hud()

        self.canvas.draw_idle()

        if not self.state.stop:

            self.root.after(
                66,
                self.update_loop
            )



    def shutdown(self):

        self.state.stop = True

        self.root.destroy()