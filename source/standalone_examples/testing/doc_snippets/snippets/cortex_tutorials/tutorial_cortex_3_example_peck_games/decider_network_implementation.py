class PeckContext(DfContext):
    def __init__(self, robot):
        super().__init__(robot)
        self.robot = robot
        self.reset()
        self.add_monitors([PeckContext.monitor_active_target_p])

        def reset(self):
            self.is_done = True
            self.active_target_p = None

        # Monitor whether a block is too close to the active target.
        def monitor_active_target_p(self):
            if self.active_target_p is not None and self.is_near_obs(self.active_target_p):
                self.is_done = True

        # Called by a special state at the end of the peck behavior.
        def set_is_done(self):
            self.is_done = True

    ...


class PeckState(DfState):
    def enter(self):
        target_p = self.context.active_target_p
        target_q = make_target_rotation(target_p)
        self.target = PosePq(target_p, target_q)
        approach_params = ApproachParams(direction=np.array([0.0, 0.0, -0.1]), std_dev=0.04)
        self.context.robot.arm.send_end_effector(self.target, approach_params=approach_params)

    def step(self):
        # Send the command each cycle so exponential smoothing will converge.
        target_dist = np.linalg.norm(self.context.robot.arm.get_fk_p() - self.target.p)
        if target_dist < 0.01:
            return None  # Exit
        return self  # Keep going


class Dispatch(DfDecider):
    def __init__(self):
        super().__init__()

        self.add_child("choose_target", ChooseTarget())
        self.add_child(
            "peck",
            DfStateMachineDecider(
                DfStateSequence(
                    [
                        CloseGripper(),
                        PeckState(),
                        DfTimedDeciderState(DfLift(height=0.05), activity_duration=0.25),
                        DfWriteContextState(lambda context: context.set_is_done()),
                    ]
                )
            ),
        )

    def decide(self):
        if self.context.is_done:
            return DfDecision("choose_target")
        else:
            return DfDecision("peck")


def make_decider_network(robot):
    return DfNetwork(Dispatch(), context=PeckContext(robot))
