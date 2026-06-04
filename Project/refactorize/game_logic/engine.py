from enum import Enum
from time import time

from tracking.trilateration import trilaterate_2d
from game_logic.zone_manager import ZoneManager


class GamePhase(Enum):

    TUTORIAL = 0

    ROUND_1 = 1
    ROUND_2 = 2
    ROUND_3 = 3

    WIN = 4

    GAME_OVER = 5


# Game Engine
class GameEngine:

    def __init__(
        self,
        state,
        anchors,
        safe_zones,
        danger_zones
    ):

        self.state = state

        self.phase = GamePhase.TUTORIAL

        self.current_round = 1

        self.anchor_ids = sorted(
            anchors.keys()
        )

        self.anchor_positions = [
            anchors[i]
            for i in self.anchor_ids
        ]

        self.zone_manager = ZoneManager(
            safe_zones,
            danger_zones
        )
    

# Start Game
    def start_game(self):

        self.phase = GamePhase.ROUND_1
    

# Main Update Function
    def update_tag(self, tag_id, distances):

        if tag_id >= self.state.n_tags:
            return

        tag = self.state.tags[tag_id]

        trilat_distances = [
            distances[i]
            for i in self.anchor_ids
        ]

        raw_pos = trilaterate_2d(
            self.anchor_positions,
            trilat_distances
        )

        if raw_pos:

            tag.kalman.predict()

            filt_pos = tag.kalman.update(
                raw_pos[0],
                raw_pos[1]
            )

        else:

            tag.kalman.predict()

            filt_pos = tag.filt_position

        with self.state.lock:

            tag.last_distances = distances
            tag.raw_position = raw_pos
            tag.filt_position = filt_pos
            tag.last_update = time()

            self.state.frame_count += 1

        event = self.zone_manager.update(
            self.state.tags
        )

        if event == "GAME_OVER":

            self.game_over()

        elif event == "ROUND_COMPLETE":

            self.advance_round()


# Round Logic
    def check_game_state(self):

        if self.zone_manager.game_over:

            self.phase = GamePhase.GAME_OVER

            self.state.stop_game()

            return

        if self.zone_manager.all_zones_captured():

            self.advance_round()


# Round Advancement
    def advance_round(self):

        if self.current_round == 1:

            self.current_round = 2
            self.phase = GamePhase.ROUND_2

            self.increase_danger_speed()

        elif self.current_round == 2:

            self.current_round = 3
            self.phase = GamePhase.ROUND_3

            self.increase_danger_speed()

        elif self.current_round == 3:

            self.phase = GamePhase.WIN


# Danger Speed Increase
    def increase_danger_speed(self):

        for zone in self.zone_manager.danger_zones:

            zone.increase_speed(1.5)


# Game Over Method
    def game_over(self):

        if self.phase == GamePhase.GAME_OVER:
            return

        self.phase = GamePhase.GAME_OVER

        self.state.stop_game()

        print("GAME OVER")





# -------------------- Mouse Simulation for Tag ----------------------
    def update_virtual_tag(
        self,
        tag_id,
        position
    ):

        if tag_id >= self.state.n_tags:
            return

        tag = self.state.tags[tag_id]

        with self.state.lock:

            tag.raw_position = position
            tag.filt_position = position

        event = self.zone_manager.update(
            self.state.tags
        )

        if event == "GAME_OVER":
            self.game_over()

        elif event == "ROUND_COMPLETE":
            self.advance_round()