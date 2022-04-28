# Copyright (c) 2021, NVIDIA  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import argparse
from collections import OrderedDict
import time

from cli import CliTests, run_cli_option
from df import *


class TalkingDfAction(DfAction):
    def enter(self):
        print(self.name, "<enter>")

    def exit(self):
        print(self.name, "<exit>")

    def step(self):
        print(self.name, "<step>")


class TalkingDfDecider(DfDecider):
    def enter(self):
        print(self.name, "<enter>")

    def exit(self):
        print(self.name, "<exit>")

    def decide(self):
        print(self.name, "<decide>")


class MockAction1(TalkingDfAction):
    def step(self):
        print(self.name, "taking action 1")


class MockAction2(TalkingDfAction):
    def step(self):
        print(self.name, "taking action 2")


class MockDeciderChild1(TalkingDfDecider):
    def __init__(self):
        super().__init__()
        self.add_child("act1", MockAction1())
        self.add_child("act2", MockAction2())

    def decide(self):
        print(self.name, "deciding to take the provided action")
        return DfDecision("act1")


class MockDeciderChild2(TalkingDfDecider):
    def __init__(self):
        super().__init__()
        self.add_child("act2", MockAction2())

    def decide(self):
        print(self.name, "deciding to take the provided action")
        return DfDecision("act2")


class MockDecider(TalkingDfDecider):
    def __init__(self, flip=False):
        super().__init__()
        self.add_child("child1", MockDeciderChild1())
        self.add_child("child2", MockDeciderChild2())
        self.flip = flip

    def decide(self):
        if self.flip:
            print(self.name, "choosing decider child 2")
            return DfDecision("child2")
        else:
            print(self.name, "choosing decider child 1")
            return DfDecision("child1")


def test_build_df_network():
    mock_decider = MockDecider()

    child1_name = mock_decider.children["child1"].name
    child2_name = mock_decider.children["child2"].name
    print("child1 name:", child1_name)
    print("child2 name:", child2_name)

    child1_child1 = mock_decider.children["child1"].children["act1"]
    child1_child2 = mock_decider.children["child1"].children["act2"]
    print("child1_child1.name (act1):", child1_child1.name)
    print("child1_child2.name (act2):", child1_child2.name)

    child2_child1 = mock_decider.children["child2"].children["act2"]
    print("child2_child1.name (act2):", child2_child1.name)


def test_df_descent(flip=False):
    root = MockDecider(flip=flip)

    params = None
    context = None
    prev_stack = None
    stack = df_descend(root, params, context, prev_stack)

    print("Decision stack:")
    for i, node in enumerate(stack):
        print("%d) node name: %s" % (i, node.name))


def test_df_descent_flipped():
    test_df_descent(flip=True)


def test_enter(flip):
    root = MockDecider()

    params = None
    context = None
    prev_stack = None
    print("\ndecending first time")
    stack = df_descend(root, params, context, prev_stack)

    prev_stack = stack
    print("\ndecending second time")
    stack = df_descend(root, params, context, prev_stack)

    prev_stack = stack
    print("\ndecending third time")
    stack = df_descend(root, params, context, prev_stack)


def test_enter_new_and_exit_old():
    root = MockDecider()

    params = None
    context = None
    prev_stack = None
    print("\ndecending first time")
    stack = df_descend(root, params, context, prev_stack)

    prev_stack = stack
    root.flip = not root.flip  # Switch top-level choice.
    print("\ndecending second time, but with a different decision")
    stack = df_descend(root, params, context, prev_stack)

    prev_stack = stack
    print("\ndecending third time")
    stack = df_descend(root, params, context, prev_stack)


def test_tick_df_network():
    root = MockDecider()
    behavior = DfNetwork(root, params=None)

    context = None

    print("\ntick 1")
    behavior.tick(context)

    print("\ntick 2")
    behavior.tick(context)

    print("\nchanging action; tick 3")
    root.flip = not root.flip  # Switch top-level choice.
    behavior.tick(context)

    print("\ntick 4")
    behavior.tick(context)


class MockContext:
    def __init__(self):
        self.count1 = 0
        self.count2 = 0

    def monitor1(self):
        self.count1 += 1
        print("<count1> %d" % self.count1)

    def monitor2(self):
        self.count2 += 2
        print("<count2> %d" % self.count2)


def test_monitors():
    root = MockDecider()
    behavior = DfNetwork(root, params=None)

    context = MockContext()
    behavior.add_monitor(MockContext.monitor1)
    behavior.add_monitor(MockContext.monitor2)

    for i in range(3):
        behavior.tick(context)


class SimpleState(DfState):
    def __init__(self, index):
        self.index = index

    def enter(self):
        print("index: %d," % self.index, "enter()")
        self.counter = 0

    def step(self):
        print("index: %d, counter: %d" % (self.index, self.counter), "step()")
        self.counter += 1
        if self.counter <= self.index:
            return self
        else:
            return None

        return None

    def exit(self):
        print("index: %d," % self.index, "exit()")


class SimpleRate:
    def __init__(self, rate_hz):
        self.sleep_time = 1.0 / rate_hz

    def sleep(self):
        time.sleep(self.sleep_time)


def test_state_sequence():
    sequence = DfStateSequence([SimpleState(i + 1) for i in range(4)], loop=False)
    run_state_machine(sequence, SimpleRate(100), is_shutdown_cb=lambda: False)


class MockPick(DfAction):
    def enter(self):
        print(" Enter MockPick")

    def step(self):
        print("  <pick>")

    def exit(self):
        print(" Exit MockPick")


class MockPlace(DfAction):
    def enter(self):
        print(" Enter MockPlace")

    def step(self):
        print(" <place>")

    def exit(self):
        print(" Exit MockPlace")


class BuildUpTower(DfDecider):
    def __init__(self):
        super().__init__()
        self.add_child(
            "pick_and_place",
            DfStateMachineDecider(
                DfStateSequence(
                    [DfTimedDeciderState(MockPick(), 0.2), DfTimedDeciderState(MockPlace(), 0.2)], loop=True
                )
            ),
        )

    def enter(self):
        print("Entering build up tower")

    def decide(self):
        print("Building up tower")
        return DfDecision("pick_and_place")

    def exit(self):
        print("Exiting build up tower")


class TearDownTower(DfDecider):
    def enter(self):
        print("Entering tear down tower")
        self.add_child(
            "pick_and_place",
            DfStateMachineDecider(
                DfStateSequence(
                    [DfTimedDeciderState(MockPick(), 0.5), DfTimedDeciderState(MockPlace(), 0.5)], loop=True
                )
            ),
        )

    def decide(self):
        print("Tearing down tower")
        return DfDecision("pick_and_place")

    def exit(self):
        print("Exiting tear down tower")


class GoHome(DfAction):
    def enter(self):
        print("Entering go home")

    def step(self):
        print("Going home")

    def exit(self):
        print("Exiting go home")


def make_mixed_decider():
    build_up_sequence = []
    build_up_sequence.append(DfTimedDeciderState(BuildUpTower(), 1.0))
    build_up_sequence.append(DfTimedDeciderState(GoHome(), 1.0))

    tear_down_sequence = []
    tear_down_sequence.append(DfTimedDeciderState(TearDownTower(), 1.0))
    tear_down_sequence.append(DfTimedDeciderState(GoHome(), 1.0))

    sequence = [DfStateSequence(build_up_sequence), DfStateSequence(tear_down_sequence)]
    return DfStateMachineDecider(DfStateSequence(sequence, loop=True))


def test_mixed_decider():
    behavior = DfNetwork(make_mixed_decider())
    context = None
    while True:
        behavior.tick(context)
        time.sleep(0.2)


class RldsContext:
    """ A simple context for the RLDS demo. The model is that we have someone with a limited amount
    of energy who's tasked with grabbing objects and tossing them. Periodically, after a certain
    number of tosses, the person has to go home and recharge for a spell.

    RLDS states:
    - go home: return home to recharge
    - leave home: exit the house
    - reach to pick: reach out, get into position to pick
    - grasp object: get the object into the hand
    - toss object: toss it

    The context can be set up to either lose energy after the third toss so the RLDS always runs in
    sequence: reach to pick, grasp, toss, repeat. Or it can be set to lose energy after tossing
    three objects and picking up the fourth. In that case, the agent goes home to recharge with the
    fourth object inhand. Then once recharged, it's able to immediately toss since it remembers the
    object is in hand.
    """

    def __init__(self, lose_energy_on_pick=False):
        self.lose_energy_on_pick = lose_energy_on_pick

        self.is_home = True
        self.home_entry_time = None
        self.has_energy = False
        self.at_obj = False
        self.obj_in_hand = False
        self.prev_obj_in_hand = None
        self.toss_count = 0

        self.monitors = [RldsContext.monitor_is_home, RldsContext.monitor_toss, RldsContext.monitor_energy]

    def monitor_is_home(self):
        print("  <is_home: %s>" % str(self.is_home))
        if self.is_home:
            if self.home_entry_time is None:
                # Entering home
                self.home_entry_time = time.time()
                self.toss_count = 0
            else:
                if time.time() - self.home_entry_time > 2.0:
                    self.has_energy = True
        else:  # We're not home
            self.home_entry_time = None

    def is_toss_detected(self):
        return self.prev_obj_in_hand is not None and (self.prev_obj_in_hand and not self.obj_in_hand)

    def monitor_toss(self):
        if self.is_toss_detected():
            self.toss_count += 1
        print("  <toss count: %d>" % self.toss_count)

        self.prev_obj_in_hand = self.obj_in_hand

    def monitor_energy(self):
        # If we're set to lose energy on pick, then lose energy only after tossing three and picking
        # up the next one.
        if self.lose_energy_on_pick:
            if self.toss_count >= 3 and self.obj_in_hand:
                self.has_energy = False
        else:
            if self.toss_count >= 3:
                self.has_energy = False


# Fallback state
class GoHomeRd(DfRldsNode):
    def is_runnable(self):
        return True

    def enter(self):
        print("going home")
        self.context.is_home = True


class LeaveHomeRd(DfRldsNode):
    def is_runnable(self):
        return self.context.has_energy and self.context.is_home

    def enter(self):
        print("leaving home")
        self.context.is_home = False


# This one can be run only if the system has energy
class ReachToPickRd(DfRldsNode):
    def is_runnable(self):
        if self.context.is_home:
            return False

        return self.context.has_energy

    def enter(self):
        print("reaching to pick")
        self.context.at_obj = True
        self.context.is_home = False


class GraspObjRd(DfRldsNode):
    def is_runnable(self):
        if self.context.is_home:
            return False

        return self.context.has_energy and self.context.at_obj

    def enter(self):
        print("grasping obj")
        self.context.obj_in_hand = True


class TossObjRd(DfRldsNode):
    def is_runnable(self):
        if self.context.is_home:
            return False

        return self.context.has_energy and self.context.obj_in_hand

    def enter(self):
        print("tossing obj")
        self.context.obj_in_hand = False
        self.context.at_obj = False


def test_rlds():
    context = RldsContext(lose_energy_on_pick=True)

    rlds_decider = DfRldsDecider()
    rlds_decider.append_rlds_node("go_home", GoHomeRd())
    rlds_decider.append_rlds_node("leave_home", LeaveHomeRd())
    rlds_decider.append_rlds_node("reach_to_pick", ReachToPickRd())
    rlds_decider.append_rlds_node("grasp_obj", GraspObjRd())
    rlds_decider.append_rlds_node("toss_obj", TossObjRd())

    behavior = DfNetwork(rlds_decider)
    behavior.add_monitors(context.monitors)
    behavior.run(context, SimpleRate(rate_hz=2.0))


if __name__ == "__main__":
    tests = CliTests()
    tests["test_build_df_network"] = test_build_df_network
    tests["test_df_descent"] = test_df_descent
    tests["test_df_descent_flipped"] = test_df_descent_flipped
    tests["test_enter"] = lambda: test_enter(flip=False)
    tests["test_enter_flipped"] = lambda: test_enter(flip=True)
    tests["test_enter_new_and_exit_old"] = test_enter_new_and_exit_old
    tests["test_tick_df_network"] = test_tick_df_network
    tests["test_monitors"] = test_monitors
    tests["test_state_sequence"] = test_state_sequence
    tests["test_mixed_decider"] = test_mixed_decider
    tests["test_rlds"] = test_rlds

    parser = argparse.ArgumentParser("df_tests")
    tests.setup_flags(parser)
    args = parser.parse_args()

    tests.run_choice(args)
