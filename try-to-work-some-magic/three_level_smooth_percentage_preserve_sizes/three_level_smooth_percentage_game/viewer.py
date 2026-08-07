import time
import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from constants import *
from shared_state import SharedState


class ViewerApp:
    def __init__(
        self,
        root,
        state: SharedState,
        simulate,
        fullscreen,
        game_manager,
        return_to_lobby_callback,
    ):
        self.root = root
        self.state = state
        self.simulate = simulate
        self.game_manager = game_manager
        self.return_to_lobby_callback = return_to_lobby_callback
        self.last_game_state = None

        root.title("Three-Level Zone Survival")
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

        xmin, xmax, ymin, ymax = VIEW_BOUNDS
        self.ax_plot.set_xlim(xmin, xmax)
        self.ax_plot.set_ylim(ymin, ymax)
        self.ax_plot.set_aspect("equal")
        self.ax_plot.set_facecolor("#000000")

        for anchor_id, (x, y) in ANCHORS.items():
            self.ax_plot.plot(
                x,
                y,
                marker="^",
                markersize=14,
                color="#ffeb3b",
                markeredgecolor="white",
            )
            self.ax_plot.annotate(
                f"A{anchor_id}",
                (x, y),
                xytext=(8, 8),
                textcoords="offset points",
                color="#ffeb3b",
            )

        self.zone_patches = []
        for zone in ALL_ZONES:
            danger = zone.get("is_danger", False)
            circle = mpatches.Circle(
                zone["center"],
                zone["radius"],
                fill=danger,
                linewidth=3,
                linestyle="-" if danger else "--",
                edgecolor=zone["color"],
                facecolor=zone["color"] if danger else "none",
                alpha=0.7 if danger else 1.0,
            )
            self.ax_plot.add_patch(circle)

            label = self.ax_plot.text(
                zone["center"][0],
                zone["center"][1],
                zone["label"],
                color="white" if danger else zone["color"],
                ha="center",
                va="center",
                weight="bold",
            )
            self.zone_patches.append((circle, label, zone))

        self.row_dots = []
        for index in range(state.n_tags):
            dot, = self.ax_plot.plot(
                [],
                [],
                marker="o",
                markersize=10,
                color=TAG_COLORS[index % len(TAG_COLORS)],
                markeredgecolor="white",
            )
            self.row_dots.append(dot)

        self.hud = self.ax_plot.text(
            0.02,
            0.98,
            "",
            transform=self.ax_plot.transAxes,
            va="top",
            color="white",
            family="monospace",
            fontsize=13,
            bbox=dict(facecolor="black", alpha=0.6),
        )

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.overlay_bg = Rectangle(
            (0, 0),
            1,
            1,
            transform=self.ax_plot.transAxes,
            facecolor="black",
            alpha=0.55,
            zorder=90,
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
                boxstyle="round,pad=1.0",
            ),
            zorder=100,
        )
        self.overlay_box.set_visible(False)

        if self.state.simulate:
            self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
            print("[SIM] Mouse simulation enabled")
        else:
            print("[SIM] Mouse simulation disabled")

        table = tk.Frame(root, bg="#000000")
        table.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.id_labels = []
        self.x_labels = []
        self.y_labels = []

        for row in range(state.n_tags):
            id_label = tk.Label(
                table,
                text=f"T{row}",
                bg="#111111",
                fg=TAG_COLORS[row % len(TAG_COLORS)],
                font=("Helvetica", 14, "bold"),
            )
            id_label.grid(row=row, column=0, padx=2)
            self.id_labels.append(id_label)

            x_label = tk.Label(
                table,
                text="—",
                bg="#111111",
                fg="white",
                width=12,
            )
            x_label.grid(row=row, column=1, padx=2)
            self.x_labels.append(x_label)

            y_label = tk.Label(
                table,
                text="—",
                bg="#111111",
                fg="white",
                width=12,
            )
            y_label.grid(row=row, column=2, padx=2)
            self.y_labels.append(y_label)

        self.tutorial_button = tk.Button(
            table,
            text="NEXT",
            bg="#00e5ff",
            fg="black",
            font=("Helvetica", 14, "bold"),
            command=self.on_tutorial_button,
        )
        self.tutorial_button.grid(
            row=0,
            column=4,
            rowspan=max(1, state.n_tags),
            padx=30,
        )

        self.game_master_button = tk.Button(
            table,
            text="CLASH DANGER ZONE",
            bg="#cc0000",
            fg="white",
            activebackground="#ff3333",
            activeforeground="white",
            font=("Helvetica", 14, "bold"),
            padx=20,
            pady=10,
            command=self.on_game_master_button,
        )
        self.game_master_button.grid(
            row=0,
            column=5,
            rowspan=max(1, state.n_tags),
            padx=20,
        )

        self.return_lobby_button = tk.Button(
            self.root,
            text="Return to Lobby",
            font=("Arial", 20, "bold"),
            command=self.game_manager.return_to_lobby,
        )
        self.return_lobby_button.place_forget()

        root.bind("<KeyPress-q>", lambda event: self.shutdown())

        if fullscreen:
            root.attributes("-fullscreen", True)

        self.root.after(100, self.update_loop)

    def update_loop(self):
        if not self.root.winfo_exists():
            return

        if not self.state.stop:
            with self.state.lock:
                self.game_manager.update()

        if (
            self.game_manager.game_state == STATE_GAME_WON
            and self.game_manager.game_end_sequence_complete
        ):
            if not self.return_lobby_button.winfo_ismapped():
                self.return_lobby_button.place(
                    relx=0.5,
                    rely=0.85,
                    anchor="center",
                )
        elif self.return_lobby_button.winfo_ismapped():
            self.return_lobby_button.place_forget()

        self.draw_gameplay()
        self.update_overlay()
        self.root.after(66, self.update_loop)

    def shutdown(self):
        self.state.stop = True
        self.root.destroy()

    def on_mouse_move(self, event):
        if (
            self.game_manager.game_state not in {STATE_TUTORIAL, STATE_PLAYING}
            or not self.state.game_started
        ):
            return

        if event.xdata is None or event.ydata is None:
            return

        with self.state.lock:
            tag = self.state.tags[0]
            tag.raw_position = (float(event.xdata), float(event.ydata))
            tag.filt_position = tag.raw_position
            tag.last_update = time.time()

    def on_tutorial_button(self):
        self.game_manager.next_tutorial_step()

    def on_game_master_button(self):
        if self.game_manager.game_state == STATE_PLAYING:
            self.game_manager.trigger_danger_clash()
        elif self.game_manager.game_state == STATE_GAME_OVER:
            self.game_manager.retry_game()

    def draw_gameplay(self):
        with self.state.lock:
            snapshot = [
                (tag.filt_position, tag.last_update)
                for tag in self.state.tags
            ]

        now = time.time()
        game_state = self.game_manager.game_state

        if game_state == STATE_TUTORIAL:
            self.draw_tutorial_hud()
            self.game_master_button.grid_remove()

        elif game_state == STATE_PLAYING:
            remaining = self.game_manager.get_survival_time_remaining()
            required_count = len(
                LEVEL_CONFIGS[self.game_manager.current_level]["zone_labels"]
            )

            self.hud.set_text(
                f"LEVEL {self.game_manager.current_level}\n"
                f"Protect {required_count} zones\n"
                f"Time remaining: {remaining:.1f}s"
            )
            self.hud.set_color("white")
            self.tutorial_button.grid_remove()
            self.game_master_button.grid()
            self.game_master_button.configure(
                text="CLASH DANGER ZONE",
                bg="#cc0000",
                fg="white",
                state="normal",
            )

        elif game_state == STATE_GAME_OVER:
            self.hud.set_text(
                f"LEVEL {self.game_manager.current_level}\n"
                "A safe zone reached minimum."
            )
            self.hud.set_color("red")
            self.tutorial_button.grid_remove()
            self.game_master_button.grid()
            self.game_master_button.configure(
                text="RETRY FROM LEVEL 1",
                bg="#ffb300",
                fg="black",
                state="normal",
            )

        elif game_state == STATE_GAME_WON:
            self.hud.set_text(
                "YOU WIN!\n"
                "All three survival levels are complete."
            )
            self.hud.set_color("lime")
            self.tutorial_button.grid_remove()
            self.game_master_button.grid_remove()

        for patch, label, zone in self.zone_patches:
            visible = zone.get("active", True)
            patch.set_visible(visible)
            label.set_visible(visible)

            if not visible:
                continue

            patch.center = zone["center"]
            patch.set_radius(zone["radius"])
            label.set_position(zone["center"])

            if zone.get("safe"):
                patch.set_linestyle("--")
                patch.set_linewidth(3)

        for index, (position, last_update) in enumerate(snapshot):
            stale = (now - last_update > 1.0) if last_update else True

            if position and not stale:
                self.row_dots[index].set_data([position[0]], [position[1]])
                self.x_labels[index].configure(text=f"{position[0]:.3f}")
                self.y_labels[index].configure(text=f"{position[1]:.3f}")
            else:
                self.row_dots[index].set_data([], [])
                self.x_labels[index].configure(text="—")
                self.y_labels[index].configure(text="—")

        self.canvas.draw_idle()

    def draw_tutorial_hud(self):
        step = self.game_manager.tutorial_step
        self.tutorial_button.grid()

        if step == TUTORIAL_EXPAND:
            done = self.game_manager.tutorial_expand_done

            if done:
                self.hud.set_text(
                    "STEP 1 COMPLETE\n"
                    "Standing inside a zone refills it.\n"
                    "Press NEXT."
                )
                self.tutorial_button.configure(text="NEXT", state="normal")
            else:
                self.hud.set_text(
                    "TUTORIAL — STEP 1\n"
                    "The full zones are already shrinking.\n"
                    "Step into either zone and make it grow again."
                )
                self.tutorial_button.configure(
                    text="REFILL A ZONE",
                    state="disabled",
                )

            self.hud.set_color("#00e5ff")

        elif step == TUTORIAL_SHRINK:
            done = self.game_manager.tutorial_shrink_done

            if done:
                self.hud.set_text(
                    "STEP 2 COMPLETE\n"
                    "An empty zone keeps shrinking.\n"
                    "Press NEXT."
                )
                self.tutorial_button.configure(text="NEXT", state="normal")
            else:
                self.hud.set_text(
                    "TUTORIAL — STEP 2\n"
                    "Step out of the zone.\n"
                    "Watch it shrink."
                )
                self.tutorial_button.configure(
                    text="STEP OUT",
                    state="disabled",
                )

            self.hud.set_color("#ffb300")

        elif step == TUTORIAL_SURVIVE:
            remaining = self.game_manager.get_tutorial_survival_remaining()
            done = self.game_manager.tutorial_survival_complete

            if done:
                self.hud.set_text(
                    "STEP 3 COMPLETE\n"
                    "You kept both zones alive.\n"
                    "Press NEXT."
                )
                self.tutorial_button.configure(text="NEXT", state="normal")
            else:
                self.hud.set_text(
                    "TUTORIAL — STEP 3\n"
                    "Keep both zones above minimum.\n"
                    f"Time remaining: {remaining:.1f}s"
                )
                self.tutorial_button.configure(
                    text="SURVIVE",
                    state="disabled",
                )

            self.hud.set_color("#66ff66")

        elif step == TUTORIAL_DANGER:
            self.hud.set_text(
                "TUTORIAL — STEP 4\n"
                "Beware of danger zones.\n"
                "Press START GAME when ready."
            )
            self.hud.set_color("#ff1744")
            self.tutorial_button.configure(
                text="START GAME",
                state="normal",
            )

    def update_overlay(self):
        game_state = self.game_manager.game_state

        if game_state == self.last_game_state:
            return

        self.last_game_state = game_state

        if game_state == STATE_GAME_OVER:
            self.show_overlay(
                "GAME OVER\n\n"
                "A safe zone reached minimum.\n\n"
                "Game Master: press RETRY FROM LEVEL 1",
                "red",
            )
        elif game_state == STATE_GAME_WON:
            self.show_overlay(
                "YOU WIN!\n\n"
                "All three levels are complete.",
                "lime",
            )
        else:
            self.hide_overlay()

    def show_overlay(self, text, colour="white"):
        self.overlay_bg.set_visible(True)
        self.overlay_box.set_text(text)
        self.overlay_box.set_color(colour)
        self.overlay_box.set_visible(True)
        self.canvas.draw_idle()

    def hide_overlay(self):
        self.overlay_bg.set_visible(False)
        self.overlay_box.set_visible(False)
