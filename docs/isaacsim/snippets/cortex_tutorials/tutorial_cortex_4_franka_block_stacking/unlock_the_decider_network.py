class PlaceBlockRd(DfStateMachineDecider, DfRldsNode):
    def __init__(self):
        # This behavior uses the locking feature of the decision framework to run a state machine
        # sequence as an atomic unit.
        super().__init__(
            DfStateSequence(
                [
                    DfSetLockState(set_locked_to=True, decider=self),
                    DfTimedDeciderState(DfOpenGripper(), activity_duration=0.5),
                    DfTimedDeciderState(Lift(0.15), activity_duration=0.35),
                    DfWriteContextState(lambda ctx: ctx.clear_gripper()),
                    DfWriteContextState(set_top_block_aligned),
                    DfTimedDeciderState(DfCloseGripper(), activity_duration=0.25),
                    DfSetLockState(set_locked_to=False, decider=self),
                ]
            )
        )
