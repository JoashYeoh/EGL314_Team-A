import threading
import time

from dataclasses import dataclass, field

from kalman import Kalman2D
from constants import ROUND_EXPAND


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
    def __init__(self, n_tags, simulate=False):
        self.n_tags = n_tags
        self.tags   = [TagState() for _ in range(n_tags)]
        self.row_color_index = list(range(n_tags))
        
        self.lock   = threading.Lock()
        
        self.frame_count = 0
        self.start_time  = time.time()
        
        self.game_started = False
        self.stop = False
        self.game_over_sent = False # to check if game over state has been sent out on osc (so it doesn't spam)
                
        self.simulate = simulate # tag simulation state
        self.game_won = False   

        self.round = ROUND_EXPAND
        self.survival_start_time = None