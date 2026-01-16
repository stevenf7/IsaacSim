def open_gripper_franka(self, articulation):
    open_gripper_action = ArticulationAction(np.array([0.04, 0.04]), joint_indices=np.array([7, 8]))
    articulation.apply_action(open_gripper_action)

    # Check in once a frame until the gripper has been successfully opened.
    while not np.allclose(articulation.get_joint_positions()[7:], np.array([0.04, 0.04]), atol=0.001):
        yield ()

    return True
