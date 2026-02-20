def make_decider_network(robot):
    return DfNetwork(Dispatch(), context=BinStackingContext(robot))
