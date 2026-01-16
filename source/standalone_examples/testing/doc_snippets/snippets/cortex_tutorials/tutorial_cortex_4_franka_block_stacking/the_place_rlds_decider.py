def make_place_rlds():
    rlds = DfRldsDecider()
    rlds.append_rlds_node("reach_to_placement", ReachToPlacementRd())
    rlds.append_rlds_node("place_block", PlaceBlockRd())
    return rlds
