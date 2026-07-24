import sys

import tkinter as tk

from MVP.game.constants import *
from MVP.game.osc_sender import *


# ---------------------------------------------------------------------------
# Tutorial/Instructions for game
#----------------------------------------------------------------------------
class TutorialWindow: #defines class handling intruction window
    def __init__(self, parent, state, fullscreen, viewer_class, start_game_bgm, game_manager): #initialization and take parent and app to communicate with main game
        self.parent = parent #Saves these window references as object variables so any function inside this class can access them later.
        self.state = state
        self.fullscreen = fullscreen

        self.viewer_class = viewer_class
        self.start_game_bgm = start_game_bgm
        self.game_manager = game_manager
                
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
            {"text": "1. Welcome to Zone Capturing. click next to view how to play the game.", "img": "/Assets/media/image1.jpg"},
            {"text": "2. This is safe zone", "img": "/Assets/media/image2.jpg"},
            {"text": "3. This is danger zone", "img": "/Assets/media/image3.jpg"},
            {"text": "4. Ready to play?", "img": "/Assets/media/image4.jpg"},
        ]
        self.current_page = 0

        send_start_sequence()
        send_bgm()

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
            send_tutorial_cue()

    def show_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_view()

    def start_game(self):
        """Destroys the tutorial overlay completely and launches tracker interface."""
        
        self.game_manager.start_level(1)

        self.top.destroy()
        self.state.game_started = True # toggles the start state of game

        # Only after Tutorial Window is destroyed would the ViewerApp (game) run
        self.viewer_class(self.parent, self.state, True, self.fullscreen, self.game_manager)

        self.parent.deiconify() #show the game window after the instruction page closes
        self.parent.lift()
        self.parent.focus_force() #pull focus onto the game application so keybinds work immediately at the game window

        send_tutorial_cue()

    def on_close(self):
        # Force clean terminate on early cancellation exit routines
        self.parent.destroy()
        sys.exit(0)