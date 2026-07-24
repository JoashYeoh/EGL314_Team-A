import time
from threading import Timer

from MVP.game.level_config import LEVELS
from MVP.game.constants import (
    ZONES,
    STATE_PLAYING,
    STATE_LEVEL_COMPLETE,
    STATE_GAME_OVER,
    STATE_GAME_WON,
    GAME_OVER_DELAY,
)
from MVP.game.zones import *

class GameManager:

    def __init__(self, state, update_fn, transition_fn):
        self.state = state

        self.update_fn = update_fn
        self.transition_fn = transition_fn

        self.current_level = 1
        self.level_running = False
        self.level_completed = False
        self.level_start_time = None
        self.pause_between_levels = False
        self.level_data = LEVELS
        self.game_state = STATE_PLAYING

        # self.start_level(1)

        # Game-end Sequence
        self.game_end_timer = None
        self.game_end_sequence_started = False
        self.game_end_finale_sent = False


    def start_level(self, level):
            self.current_level = level
            level_data = LEVELS[level]
            safe_zone_count = level_data["safe_zones"]

            self.level_running = True
            self.game_state = STATE_PLAYING
            self.level_completed = False
            self.pause_between_levels = False

            # refresh lose condition states whenever start
            self.state.safe_zone_lost = False
            self.state.danger_zone_hit = False
            self.state.game_over_delay = None
            self.state.game_over_sent = False

            # reset all tags
            for tag in self.state.tags:
                tag.zones_inside.clear()
                tag.raw_position = None
                tag.filt_position = None

            self.level_start_time = time.time()

            safe_zones = []
            for zone in ZONES:
                if zone.get("safe"):
                    safe_zones.append(zone)
                if zone.get("is_danger"):
                    zone["center"] = zone["start_center"]
                    zone["velocity"] = list(zone["velocity"])
            
            for zone in safe_zones:
                zone["active"] = False

            for zone in safe_zones[:safe_zone_count]:
                zone["active"] = True
                zone["captured"] = False
                zone["expanded_sent"] = False
                zone["destroyed"] = False
                zone["radius"] = zone["max_radius"]
                zone["last_direction"] = None
                zone["hysteresis_active"] = False
                zone["current_cue"] = 1
            
            # ---------------------------------------------
            # Initialise danger-zone movement and OSC cues.
            # Call this once per level, after zone reset.
            # ---------------------------------------------
            initialise_danger_zones()

            print("------ ACTIVE ZONES ------")
            for zone in safe_zones:
                print(zone["label"], zone["active"])

            self.state.game_music_started = True
            send_start_game()


    def get_level_data(self):
        return LEVELS[self.current_level]


    def get_remaining_time(self):

        if self.level_start_time is None:
            return 0

        level_data = LEVELS[self.current_level]
        elapsed = time.time() - self.level_start_time
        remaining = level_data["survival_time"] - elapsed

        return max(0, remaining)


    def finish_level(self):

        print(f"Level {self.current_level} complete!")

        self.level_running = False
        self.level_completed = True

        # ---------------------------------------------
        # Levels 1 and 2
        # ---------------------------------------------
        if self.current_level < len(LEVELS):

            completed_level = self.current_level

            self.current_level += 1
            self.pause_between_levels = True
            self.game_state = STATE_LEVEL_COMPLETE

            print(
                f"Level {completed_level} complete. "
                f"Waiting to start Level {self.current_level}"
            )

            send_level_win()
            # Pause gameplay audio between levels.
            Timer(2.0, send_pause_reaper).start()
 
            return

        # ---------------------------------------------
        # Level 3 completed
        # ---------------------------------------------
        print("LEVEL 3 WON — STARTING GAME-END SEQUENCE")

        self.start_game_end_sequence()


    def update(self):
        if not self.level_running:
            return

        # Process enter/exit events
        for tag_id, tag in enumerate(self.state.tags):
            if tag.filt_position is not None:
                self.process_zone_transitions(tag_id, tag)

        # Update the game world
        update_shrinking_zones(self.state)
        update_danger_zones(self.state)

        # ---------- Events ----------
        if self.state.safe_zone_lost:
            self.state.safe_zone_lost = False
            self.trigger_game_over("Safe zone destroyed")
        if self.state.danger_zone_hit:
            self.state.safe_zone_hit = False
            self.trigger_game_over("Danger zone collision")

        # Lose condition
        if self.state.game_over_delay is not None:
            if time.time() >= self.state.game_over_delay:

                self.game_state = STATE_GAME_OVER
                self.level_running = False
                self.state.stop = True
                return

        # Win current level
        if self.get_remaining_time() <= 0:
            self.finish_level() 


    def process_zone_transitions(self, tag_id, tag):
        self.transition_fn(tag_id, tag)
    

    def trigger_game_over(self, reason="GAME OVER"):
        if self.game_state == STATE_GAME_OVER:
            return

        if self.state.game_over_delay is None:
            print(f"[GAME OVER] {reason}")
            self.state.game_over_delay = time.time() + GAME_OVER_DELAY
            send_game_over()
            Timer(2.0, send_pause_reaper).start()



#------------- Level 3 Game End Sequence --------------
    def start_game_end_sequence(self):
        """
        Runs once after Level 3 has been completed.

        Stage 1:
            Freeze gameplay and send default GrandMA lighting.

        Stage 2:
            After GAME_END_SEQUENCE_DELAY, send the final
            GrandMA and REAPER commands.
        """

        if self.game_end_sequence_started:
            return

        print("[GAME END] Starting game-end sequence")

        self.game_end_sequence_started = True
        self.game_end_finale_sent = False

        # ---------------------------------------------
        # Freeze gameplay
        # ---------------------------------------------
        self.level_running = False
        self.level_completed = True
        self.pause_between_levels = False

        self.game_state = STATE_GAME_WON

        self.state.game_won = True

        # Do not set state.stop=True here.
        #
        # ViewerApp only calls game_manager.update() when
        # state.stop is False. Keeping it False allows the
        # viewer and overlay to continue refreshing.
        self.state.stop = False

        # ---------------------------------------------
        # Stop all zone movement
        # ---------------------------------------------
        for zone in ZONES:
            if zone.get("is_danger"):
                zone["active"] = False

        # ---------------------------------------------
        # Stage 1: default GrandMA lighting
        # ---------------------------------------------
        send_game_end_default_lighting()

        # ---------------------------------------------
        # Stage 2: delayed finale
        # ---------------------------------------------
        self.game_end_timer = Timer(
            GAME_END_SEQUENCE_DELAY,
            self.complete_game_end_sequence
        )

        self.game_end_timer.daemon = True
        self.game_end_timer.start()

        print(
            f"[GAME END] Finale scheduled in "
            f"{GAME_END_SEQUENCE_DELAY:.1f} seconds"
        )
    

    def complete_game_end_sequence(self):
        """
        Called once after the game-end delay.
        """

        if self.game_end_finale_sent:
            return

        self.game_end_finale_sent = True

        print("[GAME END] Triggering final GrandMA and REAPER sequence")

        send_game_end_finale()



# ---------------------------------------------------------------------------
# game progression (during overlays)
# ---------------------------------------------------------------------------

    def handle_space(self):
        state = self.game_state
        next_level = self.current_level

        if state == STATE_LEVEL_COMPLETE:
            self.start_level(next_level)

        elif state == STATE_GAME_OVER:
            self.retry_level()

        elif state == STATE_GAME_WON:
            # The game has ended.
            # Do not automatically return to Level 1.
            print(
                "[GAME END] SPACE ignored — "
                "game-end sequence is active"
            )


    def retry_level(self):

        print(f"Retrying Level {self.current_level}")

        self.game_state = STATE_PLAYING

        self.level_running = True
        self.level_completed = False
        self.pause_between_levels = False

        self.state.stop = False
        self.state.game_won = False

        self.state.game_over_delay = None
        self.state.game_over_sent = False

        self.state.safe_zone_lost = False
        self.state.danger_zone_hit = False

        self.start_level(self.current_level)


    def new_game(self):
        self.current_level = 1
        self.retry_level()