class GameManager:

    def __init__(self, state, update_fn, transition_fn):
        self.state = state

        self.update_fn = update_fn
        self.transition_fn = transition_fn

    def update(self):

        # Check zone transitions for every tag
        for tag_id, tag in enumerate(self.state.tags):
            if tag.filt_position is not None:
                self.process_zone_transitions(tag_id, tag)

        self.update_fn(self.state)

    def process_zone_transitions(self, tag_id, tag):
        self.transition_fn(tag_id, tag)