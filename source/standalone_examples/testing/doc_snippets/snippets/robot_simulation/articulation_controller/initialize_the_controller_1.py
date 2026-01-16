from isaacsim.core.prims import Articulation

# Create the articulation view
articulation_view = Articulation(prim_paths_expr="/World/envs/env_0/panda", name="franka_panda_view")
# Initialize the articulation controller
articulation_controller.initialize(articulation_view)
