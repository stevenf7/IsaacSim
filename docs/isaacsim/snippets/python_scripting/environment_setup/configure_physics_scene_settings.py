# -- Test setup --
from isaacsim.core.simulation_manager import PhysxScene

physics_scene = PhysxScene("/World/physicsScene")
physics_scene.set_gravity([0.0, 0.0, -9.81])
# -- End test setup --

from isaacsim.core.simulation_manager import PhysxScene, SimulationManager

physics_scene = PhysxScene("/World/physicsScene")
physics_scene.set_gravity([0.0, 0.0, -9.81])

SimulationManager.set_device("cpu")
physics_scene.set_enabled_ccd(True)
physics_scene.set_enabled_stabilization(True)
physics_scene.set_enabled_gpu_dynamics(False)
physics_scene.set_broadphase_type("MBP")
physics_scene.set_solver_type("TGS")
