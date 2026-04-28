# -- Test setup --
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.storage.native import get_assets_root_path

asset_path = get_assets_root_path() + "/Isaac/Robots/Unitree/H1/h1.usd"
stage_utils.add_reference_to_stage(asset_path, path="/h1")
SimulationManager.initialize_physics()
# -- End test setup --
from isaacsim.core.experimental.prims import Articulation

prim = Articulation("/h1")
print(prim.dof_names)
lower, upper = prim.get_dof_limits()
stiffnesses, dampings = prim.get_dof_gains()
max_velocities = prim.get_dof_max_velocities()
max_efforts = prim.get_dof_max_efforts()
for i, name in enumerate(prim.dof_names):
    print(
        f"  {name}: lower={lower.numpy()[0][i]:.4f}, upper={upper.numpy()[0][i]:.4f}, "
        f"maxVelocity={max_velocities.numpy()[0][i]:.2f}, maxEffort={max_efforts.numpy()[0][i]:.0f}, "
        f"stiffness={stiffnesses.numpy()[0][i]:.2f}, damping={dampings.numpy()[0][i]:.2f}"
    )
