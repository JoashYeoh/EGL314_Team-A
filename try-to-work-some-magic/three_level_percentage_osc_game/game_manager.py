import time

from constants import *
from zones import *
from osc_sender import (
    send_game_end_finale,
    send_game_over,
    send_game_win,
    send_level_complete,
    send_level_start,
    send_off_all,
    send_start_game,
    send_start_tutorial,
    send_tutorial_danger_zone,
    send_tutorial_survival_start,
)


class GameManager:
    def __init__(self, state, update_fn, transition_fn):
        self.state = state
        self.update_fn = update_fn
        self.transition_fn = transition_fn

        self.game_state = STATE_LOBBY
        self.game_running = False

        self.current_level = LEVEL_1
        self.survival_start_time = None
        self.survival_duration = 0.0

        self.tutorial_step = TUTORIAL_EXPAND
        self.tutorial_expand_done = False
        self.tutorial_shrink_done = False
        self.tutorial_survival_complete = False
        self.tutorial_survival_start_time = None
        self.tutorial_smallest_radii = {}
        self.tutorial_step_2_start_radii = {}

        self.game_end_sequence_started = False
        self.game_end_sequence_complete = False
        self.return_to_lobby_callback = None

        send_off_all()

    # -----------------------------------------------------------------------
    # Tutorial
    # -----------------------------------------------------------------------
    def start_tutorial(self):
        reset_zones(self.state)
        send_start_tutorial()

        for zone in ZONES:
            zone["active"] = False

        # Tutorial starts full and immediately shrinks.
        configure_tutorial_survival_zones()
        TUTORIAL_DANGER_ZONE["active"] = False

        self.tutorial_step = TUTORIAL_EXPAND
        self.tutorial_expand_done = False
        self.tutorial_shrink_done = False
        self.tutorial_survival_complete = False
        self.tutorial_survival_start_time = None
        self.tutorial_smallest_radii = {
            zone["label"]: zone["radius"]
            for zone in TUTORIAL_ZONES
        }
        self.tutorial_step_2_start_radii = {}

        for tag in self.state.tags:
            tag.zones_inside.clear()

        self.game_state = STATE_TUTORIAL
        self.game_running = True
        self.state.game_started = True
        self.state.stop = False
        self.state.game_won = False

        self.game_end_sequence_started = False
        self.game_end_sequence_complete = False

    def update_tutorial(self):
        if self.tutorial_step == TUTORIAL_EXPAND:
            self._update_tutorial_expand_step()

        elif self.tutorial_step == TUTORIAL_SHRINK:
            self._update_tutorial_shrink_step()

        elif self.tutorial_step == TUTORIAL_SURVIVE:
            self._update_tutorial_survive_step()

    def _update_tutorial_expand_step(self):
        for zone in TUTORIAL_ZONES:
            previous_smallest = self.tutorial_smallest_radii.get(
                zone["label"], zone["radius"]
            )

            self.tutorial_smallest_radii[zone["label"]] = min(
                previous_smallest,
                zone["radius"],
            )

            if (
                zone["radius"]
                >= self.tutorial_smallest_radii[zone["label"]] + 0.05
            ):
                self.tutorial_expand_done = True

    def _update_tutorial_shrink_step(self):
        for zone in TUTORIAL_ZONES:
            start_radius = self.tutorial_step_2_start_radii.get(
                zone["label"], zone["radius"]
            )

            if start_radius - zone["radius"] >= 0.10:
                self.tutorial_shrink_done = True

    def _update_tutorial_survive_step(self):
        if any_tutorial_zone_at_minimum():
            print("[TUTORIAL] A zone reached minimum. Restarting survival example.")
            configure_tutorial_survival_zones()
            self.tutorial_survival_start_time = time.monotonic()
            return

        if self.tutorial_survival_start_time is None:
            self.tutorial_survival_start_time = time.monotonic()

        elapsed = time.monotonic() - self.tutorial_survival_start_time
        self.tutorial_survival_complete = elapsed >= TUTORIAL_SURVIVAL_TIME

    def get_tutorial_survival_remaining(self):
        if self.tutorial_survival_start_time is None:
            return TUTORIAL_SURVIVAL_TIME

        elapsed = time.monotonic() - self.tutorial_survival_start_time
        return max(0.0, TUTORIAL_SURVIVAL_TIME - elapsed)

    def next_tutorial_step(self):
        if self.game_state != STATE_TUTORIAL:
            return

        if self.tutorial_step == TUTORIAL_EXPAND:
            if not self.tutorial_expand_done:
                return

            self.tutorial_step = TUTORIAL_SHRINK
            self.tutorial_shrink_done = False
            self.tutorial_step_2_start_radii = {
                zone["label"]: zone["radius"]
                for zone in TUTORIAL_ZONES
            }
            return

        if self.tutorial_step == TUTORIAL_SHRINK:
            if not self.tutorial_shrink_done:
                return

            configure_tutorial_survival_zones()
            self.tutorial_step = TUTORIAL_SURVIVE
            self.tutorial_survival_start_time = time.monotonic()
            self.tutorial_survival_complete = False
            send_tutorial_survival_start()
            return

        if self.tutorial_step == TUTORIAL_SURVIVE:
            if not self.tutorial_survival_complete:
                return

            for zone in TUTORIAL_ZONES:
                zone["active"] = False

            TUTORIAL_DANGER_ZONE["active"] = True
            self.tutorial_step = TUTORIAL_DANGER
            send_tutorial_danger_zone()
            return

        if self.tutorial_step == TUTORIAL_DANGER:
            self.start_game()

    # -----------------------------------------------------------------------
    # Three-level survival game
    # -----------------------------------------------------------------------
    def start_game(self):
        reset_zones(self.state)
        initialise_danger_zones()

        for zone in TUTORIAL_ZONES:
            zone["active"] = False
        TUTORIAL_DANGER_ZONE["active"] = False

        self.current_level = LEVEL_1
        self.game_state = STATE_PLAYING
        self.game_running = True
        self.state.game_started = True
        self.state.stop = False
        self.state.game_won = False

        self.game_end_sequence_started = False
        self.game_end_sequence_complete = False

        send_start_game()
        self.start_level(self.current_level)

    def start_level(self, level_number):
        self.current_level = level_number
        configure_zones_for_level(level_number)

        for tag in self.state.tags:
            tag.zones_inside.clear()

        self.survival_duration = LEVEL_CONFIGS[level_number]["survival_time"]
        self.survival_start_time = time.monotonic()

        send_level_start(level_number)
        print(
            f"[LEVEL {level_number}] START — "
            f"survive for {self.survival_duration:.0f}s"
        )

    def update(self):
        if not self.game_running:
            return

        current_level = self.current_level if self.game_state == STATE_PLAYING else None

        for tag_id, tag in enumerate(self.state.tags):
            if tag.filt_position is not None:
                self.process_zone_transitions(tag_id, tag, current_level)

        if self.game_state == STATE_TUTORIAL:
            update_tutorial_zones(self.state)
            self.update_tutorial()
            return

        if self.game_state == STATE_PLAYING:
            update_survival_zones(self.state, self.current_level)
            update_danger_zones(self.state)
            self.update_level_survival()

    def process_zone_transitions(self, tag_id, tag, current_level=None):
        return self.transition_fn(
            self.state,
            tag_id,
            tag,
            current_level,
        )

    def update_level_survival(self):
        if any_level_zone_at_minimum(self.current_level):
            self.trigger_survival_loss()
            return

        if self.survival_start_time is None:
            return

        elapsed = time.monotonic() - self.survival_start_time
        if elapsed >= self.survival_duration:
            self.complete_current_level()

    def get_survival_time_remaining(self):
        if self.survival_start_time is None:
            return 0.0

        elapsed = time.monotonic() - self.survival_start_time
        return max(0.0, self.survival_duration - elapsed)

    def complete_current_level(self):
        completed_level = self.current_level
        send_level_complete(completed_level)
        print(f"[LEVEL {completed_level}] COMPLETE")

        if completed_level >= LEVEL_3:
            self.start_game_end_sequence()
            return

        self.start_level(completed_level + 1)

    def trigger_survival_loss(self):
        print(
            f"[LEVEL {self.current_level}] GAME OVER — "
            "a safe zone reached minimum radius"
        )
        self._enter_game_over()

    def trigger_danger_clash(self):
        if self.game_state != STATE_PLAYING:
            return

        print("[GAME MASTER] DANGER ZONE CLASH TRIGGERED")
        self._enter_game_over()

    def _enter_game_over(self):
        self.game_state = STATE_GAME_OVER
        self.game_running = False
        self.state.game_started = False
        self.state.stop = False

        for zone in ZONES:
            zone["active"] = False

        send_game_over()

    def retry_game(self):
        if self.game_state != STATE_GAME_OVER:
            return

        print("[GAME MASTER] RETRYING FROM LEVEL 1")
        self.start_game()

    # -----------------------------------------------------------------------
    # Win and lobby
    # -----------------------------------------------------------------------
    def start_game_end_sequence(self):
        if self.game_end_sequence_started:
            return

        self.game_end_sequence_started = True
        self.game_end_sequence_complete = True
        self.game_state = STATE_GAME_WON
        self.game_running = False
        self.state.game_started = False
        self.state.game_won = True

        for zone in ZONES:
            if zone.get("is_danger"):
                zone["active"] = False

        send_game_win()
        send_game_end_finale()
        print("[GAME] Level 3 complete. Final sequence triggered.")

    def return_to_lobby(self):
        if self.game_state != STATE_GAME_WON:
            return

        self.enter_lobby()
        if self.return_to_lobby_callback:
            self.return_to_lobby_callback()

    def enter_lobby(self):
        self.game_state = STATE_LOBBY
        self.game_running = False
        self.state.game_started = False
        self.state.game_won = False
        self.state.stop = False
        self.game_end_sequence_started = False
        self.game_end_sequence_complete = False
        self.survival_start_time = None

        reset_zones(self.state)
        print("[GAME] Entered lobby")
