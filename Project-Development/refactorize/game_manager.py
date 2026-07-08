import time
from threading import Timer


from level_config import LEVELS
from constants import (
    ZONES,
    STATE_PLAYING,
    STATE_LEVEL_COMPLETE,
    STATE_GAME_OVER,
    STATE_GAME_WON,
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

        self.start_level(1)


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
                    zone["velocity"] = list(zone["start_velocity"])
            
            for zone in safe_zones:
                zone["active"] = False

            for zone in safe_zones[:safe_zone_count]:
                zone["active"] = True
                zone["captured"] = False
                zone["expanded_sent"] = False
                zone["destroyed"] = False
                zone["radius"] = zone["max_radius"]
            
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
        self.pause_between_levels = True
        self.game_state = STATE_LEVEL_COMPLETE

        if self.current_level < len(LEVELS):
            self.current_level += 1
            print(f"Waiting to start Level {self.current_level}")

        else:
            print("GAME WON!")
            self.game_state = STATE_GAME_WON
            self.state.game_won = True
            self.state.stop = True
        
        send_game_win()
        Timer(2.0, send_pause_reaper).start()
    

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
        elif self.state.danger_zone_hit:
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
            self.new_game()


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