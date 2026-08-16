import threading
import time

from dataclasses import dataclass, field

from reworked_game_same_structure.game.kalman import Kalman2D


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

class SharedState:
    def __init__(self,n_tags,simulate=False):
        self.n_tags = n_tags
        self.tags   = [TagState() for _ in range(n_tags)]
        self.row_color_index = list(range(n_tags))

        self.lock=threading.Lock()

        self.frame_count = 0
        self.start_time  = time.time()

        self.game_started = False
        self.stop = False
        self.simulate = simulate
        self.game_won = False
