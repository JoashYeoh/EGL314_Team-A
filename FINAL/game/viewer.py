import time
import tkinter as tk
# ^^^ Standard GUI library. It creates 'plot_frame', which acts as the 
# physical container holding your game arena and the moving danger zones.

from tkinter import ttk

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
    def __init__(self,root,state:SharedState,simulate,fullscreen,game_manager,return_to_lobby_callback):
        self.root           = root
        self.state          = state
        self.simulate       = simulate
        self.game_manager   = game_manager

        self.return_to_lobby_callback = return_to_lobby_callback
        self.last_game_state = None
        
        root.title('Zone Capturing Game')
        root.configure(bg='#000000')

        root.grid_rowconfigure(0,weight=5)
        root.grid_rowconfigure(1,weight=1)
        root.grid_columnconfigure(0,weight=1)

        plot_frame=tk.Frame(root,bg='#000000')
        plot_frame.grid(row=0,column=0,sticky='nsew')

        plt.style.use('dark_background')
        self.fig=Figure(figsize=(14,8)); self.fig.patch.set_facecolor('#000000')
        self.ax_plot=self.fig.add_subplot(111)

        xmin,xmax,ymin,ymax=VIEW_BOUNDS
        self.ax_plot.set_xlim(xmin,xmax); self.ax_plot.set_ylim(ymin,ymax)
        self.ax_plot.set_aspect('equal'); self.ax_plot.set_facecolor('#000000')

        for aid,(x,y) in ANCHORS.items():
            self.ax_plot.plot(x,y,marker='^',markersize=14,color='#ffeb3b',markeredgecolor='white')
            self.ax_plot.annotate(f'A{aid}',(x,y),xytext=(8,8),textcoords='offset points',color='#ffeb3b')
        self.zone_patches=[]

        for z in ALL_ZONES:
            danger=z.get('is_danger',False)
            circle=mpatches.Circle(z['center'],z['radius'],fill=danger,linewidth=3,linestyle='-' if danger else '--',edgecolor=z['color'],facecolor=z['color'] if danger else 'none',alpha=.7 if danger else 1)
            self.ax_plot.add_patch(circle)
            txt=self.ax_plot.text(z['center'][0],z['center'][1],z['label'],color='white' if danger else z['color'],ha='center',va='center',weight='bold')
            self.zone_patches.append((circle,txt,z))
        self.row_dots=[]

        for i in range(state.n_tags):
            dot,=self.ax_plot.plot([],[],marker='o',markersize=10,color=TAG_COLORS[i],markeredgecolor='white')
            self.row_dots.append(dot)

        self.hud=self.ax_plot.text(.02,.98,'',transform=self.ax_plot.transAxes,va='top',color='white',family='monospace',fontsize=13,bbox=dict(facecolor='black',alpha=.6))

        self.canvas=FigureCanvasTkAgg(self.fig,master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both',expand=True)

        self.overlay_bg=Rectangle((0,0),1,1,transform=self.ax_plot.transAxes,facecolor='black',alpha=.55,zorder=90)
        self.overlay_bg.set_visible(False); self.ax_plot.add_patch(self.overlay_bg)
        self.overlay_box=self.ax_plot.text(.5,.5,'',transform=self.ax_plot.transAxes,ha='center',va='center',fontsize=22,color='white',bbox=dict(facecolor='#222222',edgecolor='white',boxstyle='round,pad=1.0'),zorder=100)
        self.overlay_box.set_visible(False)

        if self.state.simulate:
            self.canvas.mpl_connect('motion_notify_event',self.on_mouse_move)
            print('[SIM] Mouse simulation enabled')
        else:
            print('[SIM] Mouse simulation disabled')

        table=tk.Frame(root,bg='#000000')
        table.grid(row=1,column=0,sticky='nsew',padx=10,pady=10)
        self.id_labels=[]; self.x_labels=[]
        self.y_labels=[]

        for r in range(state.n_tags):
            a=tk.Label(table,text=f'T{r}',bg='#111111',fg=TAG_COLORS[r],font=('Helvetica',14,'bold'))
            a.grid(row=r,column=0,padx=2)
            self.id_labels.append(a)

            x=tk.Label(table,text='—',bg='#111111',fg='white',width=12)
            x.grid(row=r,column=1,padx=2)
            self.x_labels.append(x)

            y=tk.Label(table,text='—',bg='#111111',fg='white',width=12)
            y.grid(row=r,column=2,padx=2); self.y_labels.append(y)

        self.tutorial_button=tk.Button(table,text='NEXT',bg='#00e5ff',fg='black',font=('Helvetica',14,'bold'),command=self.on_tutorial_button)
        self.tutorial_button.grid(row=0,column=4,rowspan=max(1,state.n_tags),padx=30)

        # -----------------------------------------------------------------------
        # Game Master control button
        # -----------------------------------------------------------------------
        # danger zone clash
        self.game_master_button = tk.Button(table, text="CLASH DANGER ZONE", bg="#cc0000", fg="white", activebackground="#ff3333", activeforeground="white", font=("Helvetica", 14, "bold"), padx=20, pady=10, command=self.on_game_master_button,)
        self.game_master_button.grid(row=0, column=5, rowspan=max(1, state.n_tags), padx=20,)

        # manual zone E
        self.zone_e_button = tk.Button(table, text="EXPAND ZONE E", bg="#ffb74d", fg="black", activebackground="#ffd180", font=("Helvetica", 14, "bold"), padx=20, pady=10, command=self.on_zone_e_button,)
        self.zone_e_button.grid(row=0, column=6, rowspan=max(1, state.n_tags), padx=20,)

        # -----------------------------------------------------------------------
        # Return To Lobby Button
        # -----------------------------------------------------------------------
        self.return_lobby_button = tk.Button(self.root, text="Return to Lobby", font=("Arial", 20, "bold"), command=self.game_manager.return_to_lobby,)
        self.return_lobby_button.place_forget()

        root.bind('<KeyPress-q>',lambda e:self.shutdown())  # keybind to shutdown game when keypress 'Q'

        if fullscreen:
            root.attributes('-fullscreen',True) # fullscreen viewer when in fullscreen mode
        self.root.after(100,self.update_loop)


    def update_loop(self):
        if not self.root.winfo_exists():
            return
        if not self.state.stop:
            with self.state.lock:self.game_manager.update()

        if (self.game_manager.game_state == STATE_GAME_WON and self.game_manager.game_end_sequence_complete):
            if not self.return_lobby_button.winfo_ismapped():
                self.return_lobby_button.place(relx=0.5,rely=0.85,anchor="center",)
        else:
            if self.return_lobby_button.winfo_ismapped():
                self.return_lobby_button.place_forget()

        self.draw_gameplay(); self.update_overlay()
        self.root.after(66,self.update_loop)


    def shutdown(self):
        self.state.stop=True
        self.root.destroy()


    def on_mouse_move(self,event):  # for tag position simulation based on mouse position
        if self.game_manager.game_state not in {STATE_TUTORIAL,STATE_PLAYING} or not self.state.game_started:
            return
        if event.xdata is None or event.ydata is None:
            return
        with self.state.lock:
            tag=self.state.tags[0]
            tag.raw_position=(float(event.xdata),float(event.ydata))
            tag.filt_position=tag.raw_position
            tag.last_update=time.time()


    def on_tutorial_button(self):
        self.game_manager.next_tutorial_step()


    def on_game_master_button(self):
        """
        The button performs different actions depending on
        the current game state.
        """

        if self.game_manager.game_state == STATE_PLAYING:
            self.game_manager.trigger_danger_clash()

            if self.game_manager.game_phase == GAME_PHASE_CAPTURE_ABCD:
                completed = sum(
                    1
                    for zone in ZONES
                    if zone.get("label") in {
                        "ZONE A",
                        "ZONE B",
                        "ZONE C",
                        "ZONE D",
                    }
                    and zone.get("captured")
                )

                self.hud.set_text(
                    "PHASE 1 — CAPTURE ZONES A-D\n"
                    f"Completed: {completed} / 4"
                )

            else:
                self.hud.set_text(
                    "PHASE 2 — ZONE E UNLOCKED\n"
                    "Game Master: start Zone E expansion."
                )

        elif self.game_manager.game_state == STATE_GAME_OVER:
            self.game_manager.retry_game()


    def on_zone_e_button(self):
        self.game_manager.trigger_zone_e_expansion()


    def draw_gameplay(self):
        snapshot=[]
        with self.state.lock:
            for t in self.state.tags:
                snapshot.append((t.filt_position,t.last_update))

        now=time.time()
        state=self.game_manager.game_state

        zone_e = next((zone for zone in ZONES if zone.get("label") == "ZONE E"), None,)

        if state==STATE_TUTORIAL:
            self.draw_tutorial_hud()
            self.game_master_button.grid_remove()
            self.zone_e_button.grid_remove()

        elif state==STATE_PLAYING:
            completed=sum(1 for z in ZONES if z.get('safe') and z.get('captured'))
            self.hud.set_text(f'CAPTURE ALL FIVE ZONES\nCompleted: {completed} / 5')
            self.hud.set_color('white')
            self.tutorial_button.grid_remove()
            self.game_master_button.grid()
            self.game_master_button.configure(text="CLASH DANGER ZONE", bg="#cc0000", fg="white", state="normal",)

            # -----------------------------------------
            # Zone E manual button state
            # -----------------------------------------
            self.zone_e_button.grid()
            if zone_e is None:
                self.zone_e_button.configure(text="ZONE E NOT FOUND", state="disabled")

            elif zone_e.get("captured", False):
                self.zone_e_button.configure(text="ZONE E CAPTURED", bg="#66bb6a", fg="black", state="disabled")

            elif zone_e.get("manual_expanding", False):
                self.zone_e_button.configure( text="ZONE E EXPANDING", bg="#ffcc80", fg="black", state="disabled")

            else:
                self.zone_e_button.configure(text="EXPAND ZONE E", bg="#ffb74d", fg="black", state="normal")

        elif state == STATE_GAME_OVER:
            self.hud.set_text("DANGER ZONE CLASH\n Game stopped.")
            self.hud.set_color("red")
            self.tutorial_button.grid_remove()
            self.game_master_button.configure(text="RETRY GAME", bg="#ffb300", fg="black", state="normal",)
            self.zone_e_button.configure(text="EXPAND ZONE E", state="disabled")

        elif state==STATE_GAME_WON:
            self.hud.set_text('YOU WIN!\nFinal sequence is running.')
            self.hud.set_color('lime')
            self.tutorial_button.grid_remove()
            self.game_master_button.configure(state="disabled",)

        # ----- DRAW ZONES -----
        for patch,txt,z in self.zone_patches:
            visible=z.get('active',True)
            patch.set_visible(visible)
            txt.set_visible(visible)

            if not visible:
                continue
            patch.center=z['center']
            patch.set_radius(z['radius']); txt.set_position(z['center'])

            if z.get('safe'):
                patch.set_linestyle('-' if z.get('captured') else '--')
            patch.set_linewidth(5 if z.get('captured') else 3)

        # ----- DRAW TAGS -----
        for i,(pos,last) in enumerate(snapshot):
            stale=(now-last>1.0) if last else True
            if pos and not stale:
                self.row_dots[i].set_data([pos[0]],[pos[1]])
                self.x_labels[i].configure(text=f'{pos[0]:.3f}')
                self.y_labels[i].configure(text=f'{pos[1]:.3f}')
            else:
                self.row_dots[i].set_data([],[])
                self.x_labels[i].configure(text='—')
                self.y_labels[i].configure(text='—')

        self.canvas.draw_idle()


    def draw_tutorial_hud(self):
        step = self.game_manager.tutorial_step

        self.tutorial_button.grid()

        if step == TUTORIAL_EXPAND:
            done = self.game_manager.tutorial_expand_done

            if done:
                self.hud.set_text(
                    "STEP 1 COMPLETE\n"
                    "Safe zones expand while occupied.\n"
                    "Press NEXT to continue."
                )

                self.tutorial_button.configure(
                    text="NEXT",
                    state="normal",
                )
            else:
                self.hud.set_text(
                    "TUTORIAL — STEP 1\n"
                    "Step into either safe zone.\n"
                    "Watch the zone expand."
                )

                self.tutorial_button.configure(
                    text="STEP INTO A ZONE",
                    state="disabled",
                )

            self.hud.set_color("#00e5ff")

        elif step == TUTORIAL_SHRINK:
            done = self.game_manager.tutorial_shrink_done

            if done:
                self.hud.set_text(
                    "STEP 2 COMPLETE\n"
                    "Safe zones shrink when unoccupied.\n"
                    "Press NEXT to continue."
                )

                self.tutorial_button.configure(
                    text="NEXT",
                    state="normal",
                )
            else:
                self.hud.set_text(
                    "TUTORIAL — STEP 2\n"
                    "Now step out of the zone.\n"
                    "Watch the zone shrink."
                )

                self.tutorial_button.configure(
                    text="STEP OUT OF THE ZONE",
                    state="disabled",
                )

            self.hud.set_color("#ffb300")

        elif step == TUTORIAL_DANGER:
            self.hud.set_text(
                "TUTORIAL — STEP 3\n"
                "Beware of danger zones!\n"
                "Avoid the red area."
            )

            self.hud.set_color("#ff1744")

            self.tutorial_button.configure(
                text="START GAME",
                state="normal",
            )


    def update_overlay(self):
        state=self.game_manager.game_state
        if state==self.last_game_state:
            return
        self.last_game_state=state

        if state == STATE_GAME_OVER:
            self.show_overlay(
                "DANGER ZONE CLASH!\n\n"
                "GAME OVER\n\n"
                "Game Master: press RETRY GAME",
                "red",
            )
        elif state==STATE_GAME_WON:
            self.show_overlay('YOU WIN!\n\nAll five zones are complete.\n\nFinal sequence starting...','lime')
        else:
            self.hide_overlay()


# ---------------------------------------------------------------------------
# Helper Functions (to call overlay)
# ---------------------------------------------------------------------------
    def show_overlay(self,text,colour='white'):
        self.overlay_bg.set_visible(True)
        self.overlay_box.set_text(text)
        self.overlay_box.set_color(colour)
        self.overlay_box.set_visible(True); self.canvas.draw_idle()


    def hide_overlay(self):
        self.overlay_bg.set_visible(False)
        self.overlay_box.set_visible(False)
