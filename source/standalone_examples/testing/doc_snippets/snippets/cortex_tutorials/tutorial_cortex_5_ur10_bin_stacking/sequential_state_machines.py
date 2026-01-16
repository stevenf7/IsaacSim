class PickBin(DfStateMachineDecider):
    def __init__(self):
        super().__init__(
            DfStateSequence(
                [
                    ReachToPick(),
                    DfWaitState(wait_time=0.5),
                    DfSetLockState(set_locked_to=True, decider=self),
                    CloseSuctionGripper(),
                    DfTimedDeciderState(DfLift(0.3), activity_duration=0.4),
                    DfSetLockState(set_locked_to=False, decider=self),
                ],
            )
        )


class FlipBin(DfStateMachineDecider):
    def __init__(self):
        super().__init__(
            DfStateSequence(
                [
                    LiftAndTurn(),
                    MoveToFlipStation(),
                    DfSetLockState(set_locked_to=True, decider=self),
                    OpenSuctionGripper(),
                    ReleaseFlipStationBin(duration=0.65),
                    DfSetLockState(set_locked_to=False, decider=self),
                ]
            )
        )


class PlaceBin(DfStateMachineDecider):
    def __init__(self):
        super().__init__(
            DfStateSequence(
                [
                    ReachToPlace(),
                    DfWaitState(wait_time=0.5),
                    DfSetLockState(set_locked_to=True, decider=self),
                    OpenSuctionGripper(),
                    DfTimedDeciderState(DfLift(0.1), activity_duration=0.25),
                    DfWriteContextState(lambda ctx: ctx.mark_active_bin_as_complete()),
                    DfSetLockState(set_locked_to=False, decider=self),
                ],
            )
        )
