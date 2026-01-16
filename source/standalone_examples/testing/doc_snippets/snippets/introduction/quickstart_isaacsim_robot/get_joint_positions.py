import asyncio

from isaacsim.core.api.simulation_context import SimulationContext


async def test():
    def print_state(dt):
        joint_positions = arm_handle.get_joint_positions()
        print("Joint positions: ", joint_positions)

    simulation_context = SimulationContext()
    await simulation_context.initialize_simulation_context_async()
    await simulation_context.reset_async()
    simulation_context.add_physics_callback("printing_state", print_state)


asyncio.ensure_future(test())
