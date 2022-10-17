from omni.isaac.kit import SimulationApp

kit = SimulationApp()

import omni
import omni.physx
from pxr import UsdPhysics, PhysxSchema

kit.update()

stage = omni.usd.get_context().get_stage()
scene = UsdPhysics.Scene.Define(stage, "/physicsScene")
physx_scene_api = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())

kit.update()


def test_callback(step):
    print("callback")


print("Start test")
physx_interface = omni.physx.acquire_physx_interface()
physx_sim_interface = omni.physx.get_physx_simulation_interface()
# Commenting out the following line will prevent the deadlock
physics_timer_callback = physx_interface.subscribe_physics_step_events(test_callback)

# In Isaac Sim we run the following to "warm up" physics without simulating forward in time
physx_interface.start_simulation()
physx_interface.force_load_physics_from_usd()
physx_sim_interface.simulate(1.0 / 60.0, 0.0)
print("Fetch results")
physx_sim_interface.fetch_results()

print("Finish Test")
kit.update()
kit.close()  # Cleanup application
