def make_decider_network(robot):
    return DfNetwork(
        BlockPickAndPlaceDispatch(), context=BuildTowerContext(robot, tower_position=np.array([0.25, 0.3, 0.0]))
    )
