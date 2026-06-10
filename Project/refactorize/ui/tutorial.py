# ui/tutorial.py

import os
import sys
import tkinter as tk

from ui.viewer import ViewerApp


TUTORIAL_PAGES = [
    {
        "text": "1. Welcome to Red zones and Green zones, click next to view how to play the game.",
        "img": "Assets/step1.png",
    },
    {
        "text": "2. The objective of this game is to capture all safe zones for three rounds.",
        "img": "Assets/step2.png",
    },
    {
        "text": "3. However, there will be two moving danger zones trying to eliminate you. AVOID THEM AT ALL COST!",
        "img": "Assets/step3.png",
    },
    {
        "text": "4. Upon reaching the safe zones, you have to stay in them until you've captured 100% of the zone!",
        "img": "Assets/step4.png",
    },
    {
        "text": "5. Once all safe zones have been captured successfully, you will progress to the next round.",
        "img": "Assets/step5.png",
    },
    {
        "text": "6. There will be three rounds in total. With every zone cleared, the speed of the moving danger zones increases.",
        "img": "Assets/step6.png",
    },
    {
        "text": "7. Leaving the safe zones will cause the safe zones to shrink. STAY ON IT!",
        "img": "Assets/step7.png",
    },
    {
        "text": "8. That's it! Are you ready to take on the challenge explorer? If you are, click Start Game.",
        "img": "Assets/step8.png",
    },
]


class TutorialWindow:

    def __init__(self, parent, state, engine, fullscreen):

        self.parent = parent
        self.state = state
        self.engine = engine
        self.fullscreen = fullscreen

        self.current_page = 0
        self.current_image = None

        self.top = tk.Toplevel(parent)
        self.top.title("Game Tutorial")
        self.top.configure(bg="#111111")
        self.top.attributes("-fullscreen", True)

        self.top.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        self.build_ui()

        self.top.bind(
            "<Escape>",
            lambda e: self.on_close()
        )

        self.update_page()

    def build_ui(self):

        self.top.grid_rowconfigure(0, weight=1)
        self.top.grid_rowconfigure(1, weight=3)
        self.top.grid_rowconfigure(2, weight=1)

        self.top.grid_columnconfigure(0, weight=1)

        # Instruction text

        self.text_label = tk.Label(
            self.top,
            text="",
            bg="#111111",
            fg="white",
            font=("Helvetica", 24, "bold"),
            justify="center",
            wraplength=1000,
        )

        self.text_label.grid(
            row=0,
            column=0,
            sticky="nsew",
            pady=(50, 20),
        )

        # Image area

        self.image_frame = tk.Frame(
            self.top,
            bg="#222222",
            width=700,
            height=400,
        )

        self.image_frame.grid(
            row=1,
            column=0,
            padx=50,
            pady=20,
        )

        self.image_frame.pack_propagate(False)

        self.image_label = tk.Label(
            self.image_frame,
            bg="#222222",
            fg="#777777",
        )

        self.image_label.pack(
            expand=True,
            fill="both",
        )

        # Navigation

        nav_frame = tk.Frame(
            self.top,
            bg="#111111",
        )

        nav_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(20, 50),
        )

        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)

        self.prev_button = tk.Button(
            nav_frame,
            text="Previous",
            command=self.previous_page,
            font=("Helvetica", 14, "bold"),
        )

        self.prev_button.grid(
            row=0,
            column=0,
            padx=40,
            sticky="w",
        )

        self.next_button = tk.Button(
            nav_frame,
            text="Next",
            command=self.next_page,
            font=("Helvetica", 14, "bold"),
        )

        self.next_button.grid(
            row=0,
            column=1,
            padx=40,
            sticky="e",
        )

    def update_page(self):

        page = TUTORIAL_PAGES[self.current_page]

        self.text_label.config(
            text=page["text"]
        )

        self.load_image(
            page["img"]
        )

        # First page

        if self.current_page == 0:
            self.prev_button.grid_remove()
        else:
            self.prev_button.grid()

        # Last page

        if self.current_page == len(TUTORIAL_PAGES) - 1:
            self.next_button.config(
                text="Start Game",
                command=self.start_game,
            )
        else:
            self.next_button.config(
                text="Next",
                command=self.next_page,
            )

    def load_image(self, relative_path):

        try:
            script_dir = os.path.dirname(
                os.path.abspath(__file__)
            )

            project_root = os.path.dirname(
                script_dir
            )

            image_path = os.path.join(
                project_root,
                relative_path,
            )

            self.current_image = tk.PhotoImage(
                file=image_path
            )

            self.image_label.config(
                image=self.current_image,
                text="",
            )

        except Exception:
            self.image_label.config(
                image="",
                text=f"Missing image:\n{relative_path}",
            )

    def next_page(self):

        if self.current_page < len(TUTORIAL_PAGES) - 1:
            self.current_page += 1
            self.update_page()

    def previous_page(self):

        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def start_game(self):

        self.engine.start_game()

        self.top.destroy()

        ViewerApp(
            root=self.parent,
            state=self.state,
            engine=self.engine,
            fullscreen=self.fullscreen
        )

        self.parent.deiconify()
        self.parent.lift()
        self.parent.focus_force()

    def on_close(self):

        self.parent.destroy()
        sys.exit(0)