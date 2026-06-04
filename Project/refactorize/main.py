#!/usr/bin/env python3

import argparse
import threading
import tkinter as tk

from pythonosc import dispatcher
from pythonosc import osc_server

from config import ANCHORS, DEFAULT_PORT

from tracking.state import SharedState

from game_logic.engine import GameEngine
from game_logic.zones import create_default_safe_zones
from game_logic.danger_zones import create_default_danger_zones

from osc.receiver import make_osc_handler

from ui.tutorial import TutorialWindow


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--tags",
        type=int,
        default=2,
        help="Number of tags"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="OSC listen port"
    )

    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Disable fullscreen"
    )


#---------- Mouse simulation of Tags -----------
    parser.add_argument(
        "--simulate",
        action="store_true"
    )
#-----------------------------------------------

    return parser.parse_args()


# OSC Server Startup
def start_osc_server(state, engine, port):

    disp = dispatcher.Dispatcher()

    handler = make_osc_handler(
        state=state,
        engine=engine
    )

    disp.map(
        "/distances",
        handler
    )

    server = osc_server.ThreadingOSCUDPServer(
        ("0.0.0.0", port),
        disp
    )
    
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )

    thread.start()

    print(
        f"OSC Listening on port {port}"
    )

    return server


# Main Function
def main():

    args = parse_args()

    #
    # Shared State
    #

    state = SharedState(
        n_tags=args.tags
    )

    #
    # Zones
    #

    safe_zones = (
        create_default_safe_zones()
    )

    danger_zones = (
        create_default_danger_zones()
    )

    #
    # Game Engine
    #

    engine = GameEngine(
        state=state,
        anchors=ANCHORS,
        safe_zones=safe_zones,
        danger_zones=danger_zones
    )

    #
    # OSC
    #

    start_osc_server(
        state=state,
        engine=engine,
        port=args.port
    )

    #
    # UI
    #

    root = tk.Tk()

    root.withdraw()

    TutorialWindow(
        parent=root,
        state=state,
        engine=engine,
        fullscreen=not args.windowed
    )

    root.mainloop()


#Entry point
if __name__ == "__main__":
    main()