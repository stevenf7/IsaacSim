class PeckState(DfState):
    ...

    def enter(self):
        # On entry, sample a target.
        target_p = self.sample_target_p_away_from_obs()
        target_q = make_target_rotation(target_p)
        self.target = PosePq(target_p, target_q)
        approach_params = ApproachParams(direction=np.array([0.0, 0.0, -0.1]), std_dev=0.04)
        self.context.robot.arm.send_end_effector(self.target, approach_params=approach_params)

    def step(self):
        target_dist = np.linalg.norm(self.context.robot.arm.get_fk_p() - self.target.p)
        if target_dist < 0.01:
            return None  # Exit
        return self  # Keep going


def make_decider_network(robot):
    root = DfStateMachineDecider(
        DfStateSequence(
            [DfCloseGripper(width=0.0), PeckState(), DfTimedDeciderState(DfLift(height=0.05), activity_duration=0.25)],
            loop=True,
        )
    )
    return DfNetwork(root, context=PeckContext(robot))
