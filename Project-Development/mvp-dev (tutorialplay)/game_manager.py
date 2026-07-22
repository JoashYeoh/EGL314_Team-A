import time
from threading import Timer

from level_config import LEVELS
from constants import (
    ZONES,
    STATE_PLAYING,
    STATE_TUTORIAL,
    STATE_WAITING_TO_START,
    STATE_LEVEL_COMPLETE,
    STATE_GAME_OVER,
    STATE_GAME_WON,
    TUTORIAL_CUE_NONE,
    TUTORIAL_CUE_ZONE_INTRO,
    TUTORIAL_CUE_MINIMUM,
    TUTORIAL_CUE_MULTIPLE_ZONES,
    TUTORIAL_CUE_READY,
    TUTORIAL_ZONE_A_START_PERCENT,
    TUTORIAL_MINIMUM_BUFFER,
    GAME_OVER_DELAY,
)
from zones import *

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

        # ------------------------------------------------------------------
        # Tutorial state
        # ------------------------------------------------------------------
        self.tutorial_running = False
        self.tutorial_cue = TUTORIAL_CUE_NONE
        self.tutorial_cue_started_at = None

        self.tutorial_zone_a_target = None
        self.tutorial_zone_b_target = None

        self.waiting_for_game_master = False

        # self.start_level(1)

        # Game-end Sequence
        self.game_end_timer = None
        self.game_end_sequence_started = False
        self.game_end_finale_sent = False



# ------------------------------------------------------------------
# Tutorial Funtions
# ------------------------------------------------------------------
        def get_safe_zone(self, label):
            """
            Return a safe zone by its label.
            """

            for zone in ZONES:
                if (
                    zone.get("safe")
                    and zone.get("label") == label
                ):
                    return zone

            return None


        def get_danger_zones(self):
            """
            Return all danger zones.
            """

            return [
                zone
                for zone in ZONES
                if zone.get("is_danger")
            ]


        def get_safe_zones(self):
            """
            Return all safe zones.
            """

            return [
                zone
                for zone in ZONES
                if zone.get("safe")
            ]



    # ------------------------------------------------------------------
    # Reset All Zones
    # ------------------------------------------------------------------
    def reset_all_zones(self):
        """
        Reset all zones into a neutral, inactive state.

        This does not start a level.
        """

        for zone in ZONES:

            # --------------------------------------------------
            # Safe zones
            # --------------------------------------------------
            if zone.get("safe"):
                zone["active"] = False
                zone["radius"] = zone["max_radius"]

                zone["captured"] = False
                zone["expanded_sent"] = False
                zone["destroyed"] = False

                zone["current_cue"] = 1
                zone["last_direction"] = None
                zone["hysteresis_active"] = False

            # --------------------------------------------------
            # Danger zones
            # --------------------------------------------------
            elif zone.get("is_danger"):
                zone["active"] = False
                zone["center"] = tuple(zone["start_center"])

                zone["movement_target"] = "max"
                zone["current_osc_cue"] = None


    def reset_gameplay_flags(self):
        """
        Clear flags that could accidentally trigger normal lose conditions.
        """

        self.state.stop = False
        self.state.game_won = False

        self.state.safe_zone_lost = False
        self.state.danger_zone_hit = False

        self.state.game_over_delay = None
        self.state.game_over_sent = False



# ------------------------------------------------------------------
# Starting Tutorial
# ------------------------------------------------------------------
    def start_tutorial(self):
        """
        Enter playable tutorial mode.

        Normal level timing and lose conditions are disabled.
        """

        print("[TUTORIAL] Starting playable tutorial")

        self.level_running = False
        self.level_completed = False
        self.pause_between_levels = False

        self.tutorial_running = True
        self.waiting_for_game_master = False

        self.game_state = STATE_TUTORIAL
        self.tutorial_cue = TUTORIAL_CUE_ZONE_INTRO
        self.tutorial_cue_started_at = time.time()

        self.reset_gameplay_flags()
        self.reset_all_zones()

        # Clear old enter/exit history.
        for tag in self.state.tags:
            tag.zones_inside.clear()

        self.setup_tutorial_cue_1()



    def setup_tutorial_cue_1(self):
        """
        Cue 1:
        Show Zone A at 50%, with all other zones hidden.
        """

        print("[TUTORIAL] Cue 1 - Zone A at 50%")

        self.reset_all_zones()

        zone_a = self.get_safe_zone("ZONE A")

        if zone_a is None:
            raise RuntimeError(
                "Tutorial could not find ZONE A"
            )

        zone_a["active"] = True
        zone_a["destroyed"] = False

        zone_a["radius"] = percentage_to_radius(
            zone_a,
            TUTORIAL_ZONE_A_START_PERCENT
        )

        cue = percentage_to_cue(
            TUTORIAL_ZONE_A_START_PERCENT
        )

        zone_a["current_cue"] = cue
        zone_a["last_direction"] = None
        zone_a["hysteresis_active"] = False

        send_zone_cue(zone_a, cue)

        print(
            f"[TUTORIAL] {zone_a['label']} "
            f"radius={zone_a['radius']:.3f}, "
            f"cue={cue}"
        )








# ------------------------------------------------------------------
# Starting Game
# ------------------------------------------------------------------
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
            send_start_game_bgm()


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
        # --------------------------------------------------
        # Playable tutorial
        # --------------------------------------------------
        if self.game_state == STATE_TUTORIAL:
            self.update_tutorial()
            return

        # --------------------------------------------------
        # Level is prepared but waiting for Game Master
        # --------------------------------------------------
        if self.game_state == STATE_WAITING_TO_START:
            return

        # --------------------------------------------------
        # Ignore updates for overlays and end states
        # --------------------------------------------------
        if self.game_state != STATE_PLAYING:
            return

        if not self.level_running:
            return

        # --------------------------------------------------
        # Normal gameplay enter/exit events
        # --------------------------------------------------
        for tag_id, tag in enumerate(self.state.tags):
            if tag.filt_position is not None:
                self.process_zone_transitions(
                    tag_id,
                    tag
                )

        # --------------------------------------------------
        # Normal gameplay world update
        # --------------------------------------------------
        update_shrinking_zones(self.state)
        update_danger_zones(self.state)

        # --------------------------------------------------
        # Safe-zone loss
        # --------------------------------------------------
        if self.state.safe_zone_lost:
            self.state.safe_zone_lost = False

            self.trigger_game_over(
                "Safe zone destroyed"
            )
            return

        # --------------------------------------------------
        # Danger-zone collision
        # --------------------------------------------------
        if self.state.danger_zone_hit:
            self.state.danger_zone_hit = False

            self.trigger_game_over(
                "Danger zone collision"
            )
            return

        # --------------------------------------------------
        # Delayed game-over transition
        # --------------------------------------------------
        if self.state.game_over_delay is not None:
            if time.time() >= self.state.game_over_delay:
                self.game_state = STATE_GAME_OVER
                self.level_running = False
                self.state.stop = True

            return

        # --------------------------------------------------
        # Normal level completion
        # --------------------------------------------------
        if self.get_remaining_time() <= 0:
            self.finish_level()



    def update_tutorial(self):
        """
        Route tutorial updates according to the active cue.
        """

        if not self.tutorial_running:
            return

        # Keep tag enter/exit processing available during tutorial.
        for tag_id, tag in enumerate(self.state.tags):
            if tag.filt_position is not None:
                self.process_zone_transitions(
                    tag_id,
                    tag
                )

        # Cue 1 is intentionally static.
        if self.tutorial_cue == TUTORIAL_CUE_ZONE_INTRO:
            return

        """
        # These will be implemented in the next checkpoints.
        if self.tutorial_cue == TUTORIAL_CUE_MINIMUM:
            self.update_tutorial_cue_2()
            return

        if self.tutorial_cue == TUTORIAL_CUE_MULTIPLE_ZONES:
            self.update_tutorial_cue_3()
            return

        if self.tutorial_cue == TUTORIAL_CUE_READY:
            return
        """





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