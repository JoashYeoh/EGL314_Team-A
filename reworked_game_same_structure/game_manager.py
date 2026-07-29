from threading import Timer
from constants import *
from zones import *
from osc_sender import send_start_game, send_game_over, send_game_end_default_lighting, send_game_end_finale


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

        # Game-end Sequence
        self.game_end_sequence_started = False
        self.return_to_lobby_callback = None


    def start_tutorial(self):
        reset_zones(self.state)

        # Hide all game zones and danger zones.
        for zone in ZONES:
            zone["active"] = False

        # Start with Tutorial Zone 1 visible.
        for index, zone in TUTORIAL_ZONES:
            zone["radius"] = zone["min_radius"]
            zone["captured"] = False
            zone["expanded_sent"] = False
            zone["active"] = True

        # Tutorial danger appears only in Step 3.
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


    def start_game(self):
        reset_zones(self.state)
        initialise_danger_zones()

        # Activate game zones and danger zones.
        for zone in ZONES:
            zone["active"] = True

        # Tutorial zones must not appear in the game.
        for zone in TUTORIAL_ZONES:
            zone["active"] = False

        self.game_state = STATE_PLAYING
        self.game_running = True
        self.game_end_sequence_started = False

        self.state.game_started = True
        self.state.stop = False
        self.state.game_won = False

        send_start_game() # OSC


    def update(self):
        if not self.game_running:
            return
        
        # Process enter/exit events
        for tag_id,tag in enumerate(self.state.tags):
            if tag.filt_position is not None:
                self.process_zone_transitions(tag_id,tag)

        # Process win condition (if all zones captured)
        self.update_fn(self.state)
        if self.game_state==STATE_PLAYING:
            update_danger_zones(self.state)
            if all_safe_zones_captured():
                self.start_game_end_sequence()


    def process_zone_transitions(self,tag_id,tag):
        entered,exited=self.transition_fn(tag_id,tag)

        if self.game_state != STATE_TUTORIAL:
            return

        if (self.tutorial_step == TUTORIAL_ENTER and "TUTORIAL ZONE 1" in entered):
            self.tutorial_enter_done = True

        if (self.tutorial_step == TUTORIAL_EXIT and "TUTORIAL ZONE 2" in exited):
            self.tutorial_exit_done = True
            self.tutorial_zone_2_entered = True

        if (self.tutorial_step == TUTORIAL_EXIT and self.tutorial_zone_2_entered and "TUTORIAL ZONE 2" in exited):
            self.tutorial_exit_done = True

        """if self.game_state==STATE_TUTORIAL:

            if self.tutorial_step==TUTORIAL_ENTER and 0 in entered:
                self.tutorial_enter_done = True

            if self.tutorial_step==TUTORIAL_EXIT and 0 in exited:
                self.tutorial_exit_done = True"""


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
        if (self.tutorial_step == TUTORIAL_ENTER and self.tutorial_enter_done):
            # Hide the first tutorial zone.
            TUTORIAL_ZONES[0]["active"] = False

            # Reset and show the second tutorial zone.
            TUTORIAL_ZONES[1]["radius"] = (TUTORIAL_ZONES[1]["min_radius"])
            TUTORIAL_ZONES[1]["captured"] = False
            TUTORIAL_ZONES[1]["active"] = True

            # Clear old zone membership so the new zone gets
            # a fresh enter event.
            for tag in self.state.tags:
                tag.zones_inside.clear()

            self.tutorial_step = TUTORIAL_EXIT

        elif (self.tutorial_step == TUTORIAL_EXIT and self.tutorial_exit_done):
            TUTORIAL_ZONES[1]["active"] = False
            self.tutorial_step = TUTORIAL_COMPLETE

        elif self.tutorial_step == TUTORIAL_COMPLETE:
            self.start_game()


    def start_game_end_sequence(self):
        if self.game_end_sequence_started:
            return
        
        self.game_end_sequence_started = True   # state changed when win condition met (all zones captured)
        self.game_state = STATE_GAME_WON
        self.game_running = False
        self.state.game_started = False
        self.state.game_won = True

        for z in ZONES:
            if z.get('is_danger'):
                z['active']=False

        send_game_end_default_lighting()
        timer=Timer(GAME_END_SEQUENCE_DELAY,self.complete_game_end_sequence)
        timer.daemon=True; timer.start()


    def complete_game_end_sequence(self):
        send_game_end_finale()  # OSC
        if self.return_to_lobby_callback:
            self.return_to_lobby_callback() # go back to lobby page


    def enter_lobby(self):
        self.game_state = STATE_LOBBY
        self.game_running = False
        self.state.game_started = False
        self.state.game_won = False
        reset_zones(self.state)
