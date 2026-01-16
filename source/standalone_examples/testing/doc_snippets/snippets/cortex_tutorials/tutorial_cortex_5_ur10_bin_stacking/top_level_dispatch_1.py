class Dispatch(DfDecider):
    def __init__(self):
        super().__init__()

        self.add_child("flip_bin", FlipBin())
        self.add_child("pick_bin", PickBin())
        self.add_child("place_bin", PlaceBin())
        self.add_child("go_home", make_go_home())
        self.add_child("do_nothing", DfStateMachineDecider(DoNothing()))

    def decide(self):
        if self.context.stack_complete:
            return DfDecision("go_home")

        if self.context.has_active_bin:
            if not self.context.active_bin.is_attached:
                return DfDecision("pick_bin")
            elif self.context.active_bin.needs_flip:
                return DfDecision("flip_bin")
            else:
                return DfDecision("place_bin")
        else:
            return DfDecision("go_home")
