"""Conceptual sketch of the differential IK pattern used by UR10/Franka wrappers.

This is a pattern template, not a runnable script. The live implementation
is in isaacsim.robot.experimental.manipulators.examples.{ur10,franka}.
"""


def differential_ik_step(
    arm,
    target_pos,
    target_quat,
    arm_dofs,
    method="damped-least-squares",
    damping=0.05,
    scale=1.0,
    min_singular_value=1e-5,
):
    """Compute and apply one IK step toward (target_pos, target_quat).

    arm: robot Articulation wrapper with get_jacobian_matrices(),
         end_effector_link_index, differential_inverse_kinematics(),
         set_dof_position_targets().
    Returns joint delta (dq) applied this step.
    """
    ee = arm.end_effector_link
    J = arm.get_jacobian_matrices().numpy()[:, arm.end_effector_link_index - 1, :, :arm_dofs]
    cur_pos, cur_q = ee.get_world_poses()
    dq = arm.differential_inverse_kinematics(
        jacobian_end_effector=J,
        current_position=cur_pos.numpy(),
        current_orientation=cur_q.numpy(),
        goal_position=target_pos,
        goal_orientation=target_quat,
        method=method,
        method_cfg={"scale": scale, "damping": damping, "min_singular_value": min_singular_value},
    )
    cur_dofs = arm.get_dof_position_targets()
    arm.set_dof_position_targets(cur_dofs[:, :arm_dofs] + dq, dof_indices=list(range(arm_dofs)))
    return dq
