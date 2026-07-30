from threading import Timer
from constants import *
from zones import *
from osc_sender import send_tutorial_danger_zone, send_start_game, send_game_over, send_game_win, send_game_end_finale, send_off_all


class GameManager:
    def __init__(self, state, update_fn, transition_fn):
        self.state = state

        self.update_fn = update_fn
        self.transition_fn = transition_fn

        self.game_state = STATE_LOBBY
        self.game_running = False

        self.tutorial_step = TUTORIAL_EXPAND
        self.tutorial_enter_done = False
        self.tutorial_exit_done = False
        self.tutorial_expanded_zones = set()
        self.tutorial_shrinking_zones = set()
        #self.tutorial_zone_2_entered = False
        self.tutorial_step_2_start_radii = {}

        # Game-end Sequence
        self.game_end_sequence_started = False
        self.return_to_lobby_callback = None
        send_off_all()


    def start_tutorial(self):
        reset_zones(self.state)

        # Hide normal game zones.
        for zone in ZONES:
            zone["active"] = False

        # Show both tutorial zones at minimum radius.
        for zone in TUTORIAL_ZONES:
            zone["radius"] = zone["min_radius"]
            zone["captured"] = False
            zone["expanded_sent"] = False
            zone["tutorial_max_sent"] = False
            zone["active"] = True

        # Hide tutorial danger zone until Step 3.
        TUTORIAL_DANGER_ZONE["active"] = False

        self.tutorial_step = TUTORIAL_EXPAND
        self.tutorial_enter_done = False
        self.tutorial_exit_done = False

        self.tutorial_expanded_zones.clear()
        self.tutorial_shrinking_zones.clear()

        for tag in self.state.tags:
            tag.zones_inside.clear()

        self.game_state = STATE_TUTORIAL
        self.game_running = True

        # UART/OSC tag positions must continue being processed.
        self.state.game_started = True
        self.state.stop = False
        self.state.game_won = False

        # flags for return to lobby button at end game
        self.game_end_sequence_started = False
        self.game_end_sequence_complete = False
        self.return_to_lobby_callback = None


    def update_tutorial(self):
        if self.tutorial_step == TUTORIAL_EXPAND:
            self._update_tutorial_expand_step()

        elif self.tutorial_step == TUTORIAL_SHRINK:
            self._update_tutorial_shrink_step()
    

    def _update_tutorial_expand_step(self):
        expansion_threshold = 0.10

        for zone in TUTORIAL_ZONES:
            if (zone["radius"] >= zone["min_radius"] + expansion_threshold):
                self.tutorial_expanded_zones.add(zone["label"])

        # Either tutorial zone can complete Step 1.
        self.tutorial_expand_done = bool(self.tutorial_expanded_zones)


    def _update_tutorial_shrink_step(self):
        shrink_threshold = 0.10

        for zone in TUTORIAL_ZONES:
            start_radius = self.tutorial_step_2_start_radii.get(
                zone["label"],
                zone["radius"],
            )

            if start_radius - zone["radius"] >= shrink_threshold:
                self.tutorial_shrinking_zones.add(
                    zone["label"]
                )

        self.tutorial_shrink_done = bool(
            self.tutorial_shrinking_zones
        )


#--------------------------------------------------------
# GAME
#--------------------------------------------------------
    def start_game(self):
        reset_zones(self.state)
        initialise_danger_zones()

        # Activate game zones and danger zones.
        for zone in ZONES:
            zone["active"] = True

        # Tutorial zones must not appear in the game.
        for zone in TUTORIAL_ZONES:
            zone["active"] = False

        TUTORIAL_DANGER_ZONE["active"] = False

        for tag in self.state.tags:
            tag.zones_inside.clear()

        self.game_state = STATE_PLAYING
        self.game_running = True
        self.game_end_sequence_started = False

        self.state.game_started = True
        self.state.stop = False
        self.state.game_won = False

        self.game_end_sequence_started = False
        self.game_end_sequence_complete = False

        send_start_game() # OSC


    def update(self):
        if not self.game_running:
            return
        
        # Process enter/exit events
        for tag_id,tag in enumerate(self.state.tags):
            if tag.filt_position is not None:
                self.process_zone_transitions(tag_id,tag)

        # Expand or shrink active zones.
        self.update_fn(self.state)

        # Tutorial-specific checks.
        if self.game_state == STATE_TUTORIAL:
            self.update_tutorial()
            return
        
        # Normal gameplay logic.
        if self.game_state == STATE_PLAYING:
            update_danger_zones(self.state)

            if all_safe_zones_captured():
                self.start_game_end_sequence() # OSC


    def process_zone_transitions(self, tag_id, tag):
        entered, exited = self.transition_fn(self.state, tag_id, tag,)

        if self.game_state == STATE_TUTORIAL:
            return

        # Any normal gameplay transition logic can remain below.


    def trigger_danger_clash(self):
        """
        Called manually by the Game Master.

        Stops the current game, hides every zone and changes
        the game state to STATE_GAME_OVER.
        """

        # Only allow the clash during the actual game.
        if self.game_state != STATE_PLAYING:
            print(
                "[GAME MASTER] Danger clash ignored because "
                "the game is not currently playing."
            )
            return

        print("[GAME MASTER] DANGER ZONE CLASH TRIGGERED")

        self.game_state = STATE_GAME_OVER
        self.game_running = False
        self.state.game_started = False
        self.state.stop = False

        for zone in ZONES:
            zone["active"] = False

        send_game_over() # OSC


    def retry_game(self):
        """
        Restarts the five-zone game after a game-over state.
        """

        if self.game_state != STATE_GAME_OVER:
            return

        print("[GAME MASTER] RETRYING GAME")

        self.start_game()


    def next_tutorial_step(self):
        if self.game_state != STATE_TUTORIAL:
            return

        # ------------------------------------------------------
        # Step 1 → Step 2
        # ------------------------------------------------------
        if self.tutorial_step == TUTORIAL_EXPAND:
            if not self.tutorial_expand_done:
                return

            self.tutorial_step = TUTORIAL_SHRINK
            self.tutorial_shrink_done = False
            self.tutorial_shrinking_zones.clear()

            # Record the current radius of both zones.
            self.tutorial_step_2_start_radii = {
                zone["label"]: zone["radius"]
                for zone in TUTORIAL_ZONES
            }

            return

        # ------------------------------------------------------
        # Step 2 → Step 3
        # ------------------------------------------------------
        if self.tutorial_step == TUTORIAL_SHRINK:
            if not self.tutorial_shrink_done:
                return

            # Hide both tutorial safe zones.
            for zone in TUTORIAL_ZONES:
                zone["active"] = False

            # Show one tutorial danger zone.
            TUTORIAL_DANGER_ZONE["active"] = True
            send_tutorial_danger_zone()

            for tag in self.state.tags:
                tag.zones_inside.clear()

            self.tutorial_step = TUTORIAL_DANGER
            return

        # ------------------------------------------------------
        # Step 3 → Normal game
        # ------------------------------------------------------
        if self.tutorial_step == TUTORIAL_DANGER:
            self.start_game()


    def start_game_end_sequence(self):
        if self.game_end_sequence_started:
            return
        
        self.game_end_sequence_started = True   # state changed when win condition met (all zones captured)
        self.game_end_sequence_complete = False

        self.game_state = STATE_GAME_WON
        self.game_running = False

        self.state.game_started = False
        self.state.game_won = True

        for z in ZONES:
            if z.get('is_danger'):
                z['active']=False

        send_game_win() # OSC
        timer=Timer(GAME_END_SEQUENCE_DELAY,self.complete_game_end_sequence)
        timer.daemon=True; timer.start()


    def complete_game_end_sequence(self):
        send_game_end_finale()  # OSC
        self.game_end_sequence_complete = True
        print(
            "[GAME] Final sequence completed. "
            "Waiting for Return to Lobby button."
        )


    def return_to_lobby(self):
        """
        Called when the player presses the Return to Lobby button.
        """

        if self.game_state != STATE_GAME_WON:
            print(
                "[GAME] Return to lobby ignored because "
                "the game is not in the won state."
            )
            return

        print("[GAME] Returning to lobby by button press")

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

        reset_zones(self.state)

        for tag in self.state.tags:
            tag.zones_inside.clear()

        print("[GAME] Entered lobby")
