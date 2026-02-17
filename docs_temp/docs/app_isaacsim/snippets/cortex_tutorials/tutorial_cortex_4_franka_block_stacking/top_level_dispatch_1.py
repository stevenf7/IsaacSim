class BlockPickAndPlaceDispatch(DfDecider):
    def __init__(self):
        super().__init__()
        self.add_child("pick", make_pick_rlds())
        self.add_child("place", make_place_rlds())
        self.add_child("go_home", GoHome())

    def decide(self):
        ct = self.context
        if ct.block_tower.is_complete:
            return DfDecision("go_home")

        if ct.is_gripper_clear:
            return DfDecision("pick")
        else:
            return DfDecision("place")
