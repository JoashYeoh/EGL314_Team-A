import sys
import tkinter as tk

from reworked_game_same_structure.game.osc_sender import send_start_lobby


#----------------------------------------------------------------------------
# Tutorial/Instructions for game
#----------------------------------------------------------------------------
class TutorialWindow:
    def __init__(self,parent,state,fullscreen,viewer_class,start_game_bgm,game_manager,show_viewer_callback):
        self.parent = parent
        self.state = state
        self.game_manager = game_manager

        self.show_viewer_callback = show_viewer_callback
        self.top = tk.Toplevel(parent)

        # Create a Toplevel pop-up container (in this case the lobby screen)
        self.top.title('Zone Capturing Lobby')
        self.top.configure(bg='#111111')

        # Make window fullscreen
        if fullscreen:
            self.top.attributes('-fullscreen',True)
        # In windowed mode
        else:
            self.top.geometry('1100x700')

        # Enforce target exit routine if window closed via Alt+F4 or system keys
        self.top.protocol('WM_DELETE_WINDOW',self.on_close)

        # OSC
        send_start_lobby()

        tk.Label(self.top,text='ZONE CAPTURING',bg='#111111',fg='white',font=('Helvetica',42,'bold')).pack(pady=(100,25))
        tk.Label(self.top,text='Enter a zone to expand it. Exit before completion and it shrinks.\nCapture all five zones to win.',bg='#111111',fg='#cccccc',font=('Helvetica',20),justify='center').pack(pady=20)
        tk.Button(self.top,text='PLAY TUTORIAL',width=20,bg='#00e5ff',fg='black',font=('Helvetica',18,'bold'),command=self.start_tutorial).pack(pady=15)
        tk.Button(self.top,text='INSTANT PLAY',width=20,bg='#66ff66',fg='black',font=('Helvetica',18,'bold'),command=self.start_game).pack(pady=15)
        tk.Button(self.top,text='EXIT',width=20,bg='#333333',fg='white',font=('Helvetica',14,'bold'),command=self.on_close).pack(pady=30)
        self.top.bind('<Escape>',lambda e:self.on_close())


    def start_tutorial(self):
        self.game_manager.start_tutorial(); self.open_viewer()

    def start_game(self):
        self.game_manager.start_game(); self.open_viewer()


    def open_viewer(self):
        self.top.destroy(); self.parent.deiconify(); self.show_viewer_callback()


    def on_close(self):
        self.parent.destroy(); sys.exit(0)
