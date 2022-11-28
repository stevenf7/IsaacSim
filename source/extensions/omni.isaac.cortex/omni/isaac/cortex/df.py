# Copyright (c) 2021, NVIDIA  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

""" The decision framework. Decider networks and state machines are implemented here.

Conceptually, a decider network is a mapping from world and logical state to a choice of action.
That mapping often has intuitive structure to it; decider networks make it easy to design many of
these mappings by hand. The world and logical state is stored in a user defined context object which
is simply passed around within the framework and made available to the decider nodes and state
machines to aid in making decisions and taking action.

A decider network is an acyclic graph of decider nodes, each of which has a simple enter(),
decide(), and exit() interface. The decide() method makes the decision by choosing a child. In a
leaf, that child can be None, in which case, the node typically acts to step an action. Leaves, for
that reason, are called actions. See DfDecider, DfDecision. DfNetwork is a good entry point in
reading through the code. It shows how the decider network is created and stepped.

The basic descent algorithm for tracing from the root of the decider network down to an action
choice is implemented by df_descend(). Importantly, when the system reaches a given DfDecider node
for the first time along a given path it calls enter() on that node, followed by decide(). While it
continues to trace the same path from the root to the node, it calls only decide() on that node. But
once that node is no longer reached, it calls exit() on the node.  This is implemented by keeping
track of the path trace through the network from cycle to cycle and observing whether the new path
trace is branching relative to the previous. See df_descend() for details.

These calls to enter() and exit() give the decider nodes a notion of statefulness allowing them to
setup and tear down local memory to affect their decisions. The methods parallel the API to state
machines (see DfState), which have the API enter(), step(), and exit(). That means state machines
can be used inside decider nodes to help make decisions. Likewise, decider networks can be used
inside state machines to help define the state behavior.

The decider network is fundamentally reactive. It's constantly making decisions from the root to the
choice of action leaf with each tick, and will change its mind as needed if the world or logical
state changes. But sometimes it's important to be able to lock the decider network to prevent it
from changing its mind at critical points (especially for atomic actions implemented as chain state
machines). Setting the decider's is_locked attribute will lock the path from the root to that
decider node and prevent the descent algorithm from deviating from it. See DfSetLockState for a
state that will lock and unlock the path.

A collection of useful classes:
- DfNetwork, df_descend, DfDecider, DfDecision DfAction form the basic implementation of decider
  networks. DfHsmAction uses a hierarchical state machine to define an action.
- DfState is the basic interface for a state machine. DfBindableState is a version of a state
  machine that presents context and params to the state in the same way decider nodes do (see
  DfDecider). DfStateSequence is a simple chain state machine that's easy to construct from
  individual states which execute and ultimately return None when done. Likewise, a
  DfHierarchicalState abstracts a hierarchical state of a hierarchical state machine. The
  run_state_machine() method takes a state and runs it until its step() method returns None.
- DfDeciderState is a state machine that internally runs a decider network inside its step method,
  never exiting.  Likewise, a DfTimedDeciderState is a decider state which as a time limit. Once
  that time limit has passed, it exits. DfWaitState is a simple state that just waits for a
  prespecified duration.
- DfStateMachineDecider is a DfDecider node which internally has a state machine which is stepped
  during each decide() call.
- DfSetLockState locks or unlocks the decider path to accommodate temporally extended atomic
  actions. And DfWriteContextState provides a way to write into the context when the state is
  entered.
- The DfRldsDecider is an important DfDecider type implementing the Robust Logical Dynamical
  Systems model of reactive decision making.
"""

import time


class DfLogicalState:
    def __init__(self):
        self.monitors = []

    def add_monitors(self, monitors):
        self.monitors.extend(monitors)

    def reset(self):
        """ This method is left unimplemented in the base class because it's important that deriving classes
        implement it to reset the logical state when the simulation is reset.
        """
        raise NotImplementedError()


class DfDecision:
    """ Represents a decision made by the decider. It names the child to take and provides it
    parameters.
    """

    def __init__(self, name, params=None):
        self.name = name
        self.params = params


class DfBindable(object):
    def bind(self, context, params):
        self.context = context
        self.params = params


class DfDecider(DfBindable):
    """ A decider node of a decider network. The descent algorithm handles automatically setting the
    internal context member and passing down the parameters both of which can be accessed from
    enter(), decide() and exit() through self.{context,params}.

    Derived classes should override enter(), decide() and exit() as needed. decide() should make the
    decision (accessing the internal context and passed parameters) and return a DfDecision() object
    encapsulating its choice.
    """

    def __init__(self):
        self.name = "root"
        self.context = None
        self.params = None
        self.children = {}

    def add_child(self, name, child):
        child.name = name
        self.children[name] = child

    def enter(self):
        pass

    def decide(self):
        pass

    def exit(self):
        pass


class DfAction(DfDecider):
    """ A decider node that represents a leaf action that makes no additional decisions of its own.
    """

    @staticmethod
    def empty():
        return DfAction()

    def step(self):
        pass

    def decide(self):
        self.step()
        return None


class DfHsmAction(DfAction):
    """ Interfaces a Hierarchical State Machine (HSM) to a decision framework action so it can be
    used as a DfAction leaf in the decider network.

    On enter, step, and exit, the HSM calls its own enter, step, and exit methods. Note that if the
    state machine exits (such as a hierarchical state's internal state machine finishes), it will
    keep calling step (and do nothing) until a higher-level decider decides not to run this action
    any more.
    """

    def __init__(self, hsm):
        """ Create with state machine.

        The state machine is anything that's stepped until completion. E.g. HierarchicalState or
        SequenceState.
        """
        super(DfHsmAction, self).__init__()
        self.hsm = hsm

    def enter(self):
        self.hsm.enter()

    def step(self):
        self.hsm.step()

    def exit(self):
        self.hsm.exit()


def df_descend(root, root_params, context, prev_stack):
    """ Descend the decider network to a leaf starting at the root. Uses the prev_stack to check
    when or if branches occure. Returns the current stack representing the path from the root to the
    leaf.

    When a branch is detected, nodes are popped off the previous stack from the leaf to first child
    of the the joining node and exit() is called on each. Then enter() is called on all nodes in the
    new branch. If there is no previoius stack, a first stack is created and enter() is called on
    the entire path to the leaf. 
    """

    stack = [root]
    if prev_stack is not None:
        # Step through the stack in reverse order from the leaf to the root checking for the most
        # distal locked node. If one's found, we'll start the algorithm from that node and just
        # descend from there.
        for i, node in enumerate(reversed(prev_stack)):
            if hasattr(node, "is_locked") and node.is_locked:
                root = node
                root_params = node.params
                stack = prev_stack[0 : (len(prev_stack) - i)]

    root.bind(context, root_params)
    node = root

    is_branched = False
    while True:
        if prev_stack is None:
            is_branched = True
        elif not is_branched and (len(prev_stack) < len(stack) or prev_stack[len(stack) - 1] != node):
            # If we detect branching here, then mark it and handle exiting from the previous branch.
            is_branched = True
            for i in range(len(prev_stack) - 1, -1, -1):  # Iterate backward from end.
                # Exit up through the current index because this node is the first verified divergence.
                prev_stack[i].exit()
                if i == len(stack) - 1:
                    break

        if is_branched:
            node.enter()

        decision = node.decide()
        if decision is None:  # Is leaf
            return stack

        node = node.children[decision.name]
        node.bind(context, decision.params)
        stack.append(node)


class DfState(DfBindable):
    """ Interface for a state in a state machine. The main work of the state is done by step(). That
    method should also return the next state to be executed (which could be self for a self
    transition).
    """

    def enter(self):
        pass

    def step(self):
        pass

    def exit(self):
        pass


class DfStateSequence(DfState):
    """ A hierarchical state internally representing a chain of states to be executed (given by
    sequence). Each state in the sequence should be terminating. The sequence machine transitions to
    the next state when the current state terminates.

    If loop is set to True, it loops back to the beginning once the final state has terminated.
    Otherwise, the higher level sequence state will terminate once it's finished a single pass
    through the sequence.
    """

    def __init__(self, sequence, loop=False):
        self.sequence = sequence
        self.loop = loop
        self.state = None

    def bind(self, context, params):
        """ This method can be used to bind the underlying state to the given context and params.
        Both states the support bind() and those that don't can be used in a DfStateSequence. If
        it's supported, then bind() is called, otherwise it's ignored.
        """
        self.context = context
        self.params = params
        for state in self.sequence:
            if hasattr(state, "bind"):
                state.bind(context, params)

    def enter(self):
        if len(self.sequence) == 0:
            self.active_index = None
            self.state = None
            return

        self.active_index = 0
        self.state = self.sequence[self.active_index]
        self.state.enter()

    def step(self):
        if self.state is None:
            return None

        next_state = self.state.step()
        if next_state is None:
            self.state.exit()

            self.active_index += 1
            if self.loop and self.active_index == len(self.sequence):
                self.active_index = 0

            if self.active_index < len(self.sequence):
                next_state = self.sequence[self.active_index]
                next_state.enter()

        self.state = next_state

        if self.state is not None:
            return self
        else:
            return None

    def exit(self):
        if self.state is not None:
            self.state.exit()


class DfHierarchicalState(DfState):
    """ A state that internally runs a separate state machine.
    
    The state machine resets back to the initial state every time enter() is called. Then calls to
    step() step the internal state machine making any needed transitions. On exit(), the active
    state is exited if there is one. Once the internal state machine ends (transitions to None),
    there is no longer an active state and calls to step() return None as well.
    """

    def __init__(self, init_state):
        self.init_state = init_state
        self.active_state = None

    def enter(self):
        if self.init_state is not None:
            if self.active_state is not None:
                self.active_state.exit()

            self.active_state = self.init_state
            self.active_state.enter()

    def step(self):
        # If there's no active state transition to None (stop)
        if self.active_state is None:
            return None

        # Step the active state. Step returns the next state the internal machine is transitioning
        # to. If it has transitioned to a different state, then handle the enter() and exit() calls
        # properly.
        next_state = self.active_state.step()
        if next_state != self.active_state:
            self.active_state.exit()
            if next_state is None:
                self.active_state = None
                return None
            else:
                self.active_state = next_state
                self.active_state.enter()

        # The higher level state never transitions out of itself. It's just running the internal
        # machine. We indicate that we're finished with this internal machine by returning None
        # (see above).
        return self

    def exit(self):
        if self.active_state is not None:
            self.active_state.exit()


def run_state_machine(state, rate, cb=None, is_shutdown_cb=None):
    """ Run the given state machine. Exits when there are no more transitions.
    """
    hstate = DfHierarchicalState(init_state=state)
    hstate.enter()
    while is_shutdown_cb is None or not is_shutdown_cb():
        if hstate is None:
            return

        hstate = hstate.step()
        if cb:
            cb()
        rate.sleep()


class DfDeciderState(DfState):
    """ A decider state is a state that's internally running a decider every tick.
    """

    def __init__(self, decider):
        self.decider = decider

    def bind(self, context, params):
        self.decider.bind(context, params)

    def enter(self):
        self.stack = None

    def step(self):
        self.stack = df_descend(self.decider, self.decider.params, self.decider.context, self.stack)
        return self

    def exit(self):
        if self.stack is not None:
            for node in reversed(self.stack):
                node.exit()


class DfTimedDeciderState(DfDeciderState):
    """ A state which ticks a decider network from its step() method for a predefined
    activity_duration number of seconds.
    """

    def __init__(self, decider, activity_duration):
        super().__init__(decider)
        self.activity_duration = activity_duration

    def enter(self):
        super().enter()
        self.entry_time = time.time()

    def step(self):
        next_state = super().step()
        elapse_time = time.time() - self.entry_time

        # If we're within the activity duration, then return the next state as usual. Otherwise,
        # return None to exit
        if elapse_time < self.activity_duration:
            return next_state
        else:
            return None

    def exit(self):
        super().exit()


class DfWaitState(DfState):
    """ This state waits a specified length of time before exiting.
    """

    def __init__(self, wait_time):
        self.wait_time = wait_time

    def enter(self):
        self.entry_time = time.time()

    def step(self):
        if time.time() - self.entry_time < self.wait_time:
            return self
        else:
            return None

    def exit(self):
        self.entry_time = None


class DfStateMachineDecider(DfDecider):
    """ This decider steps a state machine each tick. The state machine can be any state machine,
    but if it has a bind() method, bind() will be called to give the state access to the context
    and current params.
    """

    def __init__(self, state):
        self.init_state = state

    def bind_state(self):
        if hasattr(self.state, "bind"):
            self.state.bind(self.context, self.params)

    def enter(self):
        self.state = self.init_state
        if self.state is not None:
            self.bind_state()
            self.state.enter()

    def decide(self):
        if self.state == None:
            return None

        self.bind_state()
        self.state = self.state.step()
        return None

    def exit(self):
        if self.state is not None:
            self.bind_state()
            self.state.exit()


class DfSetLockState(DfState):
    """ On entry, this state sets the given decider node's is_locked attribute to the specified
    value.
    """

    def __init__(self, set_locked_to, decider):
        self.set_locked_to = set_locked_to
        self.decider = decider

    def enter(self):
        self.decider.is_locked = self.set_locked_to


class DfWriteContextState(DfState):
    """ On entry, this state calls the specified write method, passing in the bound context.
    """

    def __init__(self, write_method):
        self.write_method = write_method

    def enter(self):
        self.write_method(self.context)


class DfNetwork:
    """ Represents the decider network defined by a root decider. Provides methods for adding
    context monitors (i.e. functions f(ct) of the context ct) called before each step of the decider
    descent algorithm.

    Each tick, all monitors are called in the order they're added and the decider network is descended
    to the leaf using df_descend(). The descent algorithm is the same as that used in
    DfDeciderState, so state machines that internally use deciders as DfDeciderState objects will
    process the subnetwork in the same way. Additionally, a DfStateMachineDecider whose internal state
    machine consists of DfDeciderState objects can be thought of as extending the decider network
    conditionally as a function of which state it's in.
    """

    def __init__(self, decider, params=None, monitors=None, context=None):
        self._decider = decider
        self._params = params

        self._monitors = monitors
        self._bound_context = context

        self.reset()

    def reset(self):
        self._decider_state = DfDeciderState(self._decider)
        self._decider_state.enter()

    def bind_context(self, context):
        self._bound_context = context

    @property
    def context(self):
        return self._bound_context

    def process_monitors(self, context):
        if self._monitors is not None:
            for monitor in self._monitors:
                monitor(context)

    def step(self, context=None):
        if context is None:
            if self._bound_context is not None:
                context = self._bound_context

        # Note the monitors are only processed if they're provided on construction.
        self.process_monitors(context)
        self._decider_state.bind(context, self._params)
        self._decider_state.step()

    def run(self, context, rate, is_shutdown_cb=None):
        while is_shutdown_cb is None or not is_shutdown_cb():
            self.step(context)
            rate.sleep()


class DfRldsNode(DfDecider):
    """ Represents a RLDS decision state. bind() is called from the DfRldsDecider before
    is_runnable() or is_enterable() are queried, so those methods have access to the decider node's
    context and current params.
    """

    def is_runnable(self):
        pass

    def is_enterable(self):
        # Defaults to being equivalent to is_runnable().
        return self.is_runnable()


class DfRldsDecider(DfDecider):
    """ A decider node implementing the Robust Logical Dynamical System (RLDS) decision protocol.

    The RLDS node has a sequence of child nodes, ordered in order of increasing priority, each of
    which are DfRldsNode objects with is_runnable() and is_enterable() methods. A call to decide()
    steps from the highest priority node to the lowest, checking is_enterable() on each (or
    is_runnable() if it's already running the decision), and simply chooses the first that returns
    true.
    """

    class NamedRldsNode:
        def __init__(self, name, rlds_node):
            self.name = name
            self.rlds_node = rlds_node

    def __init__(self):
        super().__init__()
        self.sequence = []

    def append_rlds_node(self, name, rlds_node):
        self.sequence.append(DfRldsDecider.NamedRldsNode(name, rlds_node))
        self.add_child(name, rlds_node)

    def enter(self):
        self.prev_node = None

    def decide(self):
        for named_rlds_node in reversed(self.sequence):
            rlds_node = named_rlds_node.rlds_node
            rlds_node.bind(self.context, self.params)
            if rlds_node == self.prev_node:
                is_active = rlds_node.is_runnable
            else:
                is_active = rlds_node.is_enterable
            self.prev_node = rlds_node

            if is_active():
                return DfDecision(named_rlds_node.name)

        return None
