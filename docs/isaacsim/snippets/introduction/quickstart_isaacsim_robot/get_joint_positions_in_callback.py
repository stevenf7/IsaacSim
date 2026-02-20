from isaacsim.core.simulation_manager import IsaacEvents, SimulationManager


def print_joint_positions_callback(dt, context):
    positions = arm_handle.get_dof_positions()
    print("Joint positions:", positions)


# Store callback_id to remove later if needed
callback_id = SimulationManager.register_callback(print_joint_positions_callback, IsaacEvents.POST_PHYSICS_STEP)
