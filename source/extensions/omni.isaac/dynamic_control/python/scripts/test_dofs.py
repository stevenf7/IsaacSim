from ..bindings import _dynamic_control


def test_dofs(dc):

    ar_path = "/panda"
    print("Registering articulation '%s'" % ar_path)

    ar = dc.get_articulation(ar_path)
    print("Got articulation:", ar)
    if ar == _dynamic_control.INVALID_HANDLE:
        return

    # set default states
    all_states = dc.get_articulation_dof_states(ar, _dynamic_control.STATE_NONE)
    all_states["pos"].fill(0)
    all_states["vel"].fill(0)

    # bend panda_joint4 90 degrees
    dof_idx = dc.find_articulation_dof_index(ar, "panda_joint4")
    all_states["pos"][dof_idx] = -1.57

    dc.set_articulation_dof_states(ar, all_states, _dynamic_control.STATE_ALL)

    # put all drives in position control mode by default
    all_props = dc.get_articulation_dof_properties(ar)
    print(all_props)
    all_props["driveMode"].fill(_dynamic_control.DRIVE_POS)
    all_props["stiffness"].fill(1e5)
    all_props["damping"].fill(1e3)
    dc.set_articulation_dof_properties(ar, all_props)
    # print(dc.get_articulation_dof_properties(ar))

    # set position targets to hold current positions
    dc.set_articulation_dof_position_targets(ar, all_states["pos"])

    # override panda_joint6 position target
    j6 = dc.find_articulation_dof(ar, "panda_joint6")
    dc.set_dof_position_target(j6, 1.57)

    # set velocity drive and target for panda_joint3
    j3 = dc.find_articulation_dof(ar, "panda_joint3")
    vel_props = _dynamic_control.DofProperties()
    vel_props.drive_mode = _dynamic_control.DRIVE_VEL
    vel_props.stiffness = 0
    vel_props.damping = 1e3
    dc.set_dof_properties(j3, vel_props)
    dc.set_dof_velocity_target(j3, 1.57)

    print(dc.get_articulation_dof_properties(ar))

    print("Done")
