class Dispatch(DfDecider):
    def enter(self):
        self.add_child("peck", PeckAction())
        self.add_child("lift", DfLift(height=0.1))
        self.add_child("go_home", make_go_home())

    def decide(self):
        if self.context.is_eff_close_to_inactive_block:
            return DfDecision("lift")

        if self.context.has_active_block:
            return DfDecision("peck")

        # If we aren't doing anything else, always just go home.
        return DfDecision("go_home")
