#!/usr/bin/env python3
import argparse,threading,tkinter as tk
from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server
from constants import *
from shared_state import SharedState
from viewer import ViewerApp
from tutorial import TutorialWindow
from game_manager import GameManager
from zones import update_zones,process_zone_transitions
from osc_handler import make_osc_handler
from osc_sender import send_start_game

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--tags',type=int,default=2)
    ap.add_argument('--port',type=int,default=DEFAULT_PORT)
    ap.add_argument('--csv',type=str,default=None)
    ap.add_argument('--windowed',action='store_true')
    ap.add_argument('--simulate',action='store_true')

    args=ap.parse_args()
    state=SharedState(args.tags,args.simulate)

    game_manager=GameManager(state,update_zones,process_zone_transitions)
    disp=osc_dispatcher.Dispatcher(); ids=sorted(ANCHORS.keys())
    handler=make_osc_handler(state,ids,[ANCHORS[i] for i in ids])
    disp.map('/distances',handler)

    server=osc_server.ThreadingOSCUDPServer(('0.0.0.0',args.port),disp)
    threading.Thread(target=server.serve_forever,daemon=True).start()

    print(f'[OSC] Listening on port {args.port}')
    root=tk.Tk()
    root.withdraw()

    def clear_root():
        for widget in root.winfo_children():
            if not isinstance(widget,tk.Toplevel):widget.destroy()

    def show_viewer():
        clear_root(); ViewerApp(root,state,args.simulate,not args.windowed,game_manager,return_to_lobby)

    def show_lobby():
        clear_root()
        root.withdraw()
        TutorialWindow(root,state,not args.windowed,ViewerApp,send_start_game,game_manager,show_viewer)

    def return_to_lobby(): 
        root.after(0,finish_return)

    def finish_return():
        game_manager.enter_lobby()
        show_lobby()

    game_manager.return_to_lobby_callback = return_to_lobby
    show_lobby()
    root.mainloop()
    server.shutdown()
    server.server_close()


if __name__=='__main__':main()
