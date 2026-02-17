class PickBlockRd(DfStateMachineDecider, DfRldsNode):
    def __init__(self):
        # This behavior uses the locking feature of the decision framework to run a state machine
        # sequence as an atomic unit.
        super().__init__(
            DfStateSequence(
                [
                    DfSetLockState(set_locked_to=True, decider=self),
                    DfTimedDeciderState(DfCloseGripper(), activity_duration=0.5),
                    DfTimedDeciderState(Lift(0.1), activity_duration=0.25),
                    DfWriteContextState(lambda ctx: ctx.mark_block_in_gripper()),
                    DfSetLockState(set_locked_to=False, decider=self),
                ]
            )
        )

    ...
