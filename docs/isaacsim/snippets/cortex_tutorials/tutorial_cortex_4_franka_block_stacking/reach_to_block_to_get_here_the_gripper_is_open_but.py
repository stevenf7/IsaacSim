open_gripper_rd = OpenGripperRd(dist_thresh_for_open=0.15)
reach_to_block_rd = ReachToBlockRd()
choose_block = ChooseNextBlock()
approach_grasp = DfApproachGrasp()

reach_to_block_rd.link_to("choose_block", choose_block)
choose_block.link_to("approach_grasp", approach_grasp)
