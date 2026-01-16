# It used to have context=DfContext(robot). Now we use the custom FollowContext class.
world.add_decider_network(DfNetwork(DfStateMachineDecider(FollowState()), context=FollowContext(robot)))
