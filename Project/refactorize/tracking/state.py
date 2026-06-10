from dataclasses import dataclass, field
import threading
import time

from tracking.kalman import Kalman2D


@dataclass
class TagState:
    """
    Runtime state for a single tracked tag.
    """

    last_distances: list[float] = field(
        default_factory=lambda: [0.0] * 8
    )

    raw_position: tuple[float, float] | None = None

    filt_position: tuple[float, float] | None = None

    last_update: float = 0.0

    kalman: Kalman2D = field(
        default_factory=Kalman2D
    )

    zones_inside: set[int] = field(
        default_factory=set
    )



class SharedState:

    def __init__(self, n_tags: int):

        self.n_tags = n_tags

        self.tags = [
            TagState()
            for _ in range(n_tags)
        ]

        self.row_color_index = list(
            range(n_tags)
        )

        self.frame_count = 0

        self.start_time = time.time()

        self.stop = False

        self.lock = threading.Lock()
    


    def snapshot(self):

        with self.lock:

            return {
                "frame_count": self.frame_count,
                "start_time": self.start_time,
                "stop": self.stop,
                "row_color_index": list(self.row_color_index),
                "tags": [
                    {
                        "filt_position": tag.filt_position,
                        "raw_position": tag.raw_position,
                        "last_update": tag.last_update,
                        "distances": list(tag.last_distances),
                    }
                    for tag in self.tags
                ],
            }
    


    def update_tag_position(self, tag_id: int, raw_position, filtered_position, distances):

        with self.lock:

            tag = self.tags[tag_id]

            tag.raw_position = raw_position

            tag.filt_position = filtered_position

            tag.last_distances = list(
                distances
            )

            tag.last_update = time.time()

            self.frame_count += 1

    

    def set_tag_color(self, tag_id: int, color_index: int):

        with self.lock:
            self.row_color_index[tag_id] = color_index

    

    def stop_game(self):

        with self.lock:
            self.stop = True