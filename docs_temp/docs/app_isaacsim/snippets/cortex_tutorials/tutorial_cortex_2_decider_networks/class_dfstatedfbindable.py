state = DfStateSequence([State1(), State2(), State3()], loop=True)
decider_network = DfNetwork(DfStateMachineDecider(state), context=DfContext(robot))
