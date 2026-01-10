# Launch Isaac Sim before any other imports
# Default first two lines in any standalone application
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})  # we can also run as headless

# Now import Isaac Sim modules
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.timeline
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.storage.native import get_assets_root_path

# Add ground plane
ground_plane = stage_utils.add_reference_to_stage(
    usd_path=get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd",
    path="/World/ground",
)

# Create a blue visual material for the cube
visual_material = PreviewSurfaceMaterial("/World/Materials/blue")
visual_material.set_input_values("diffuseColor", [0.0, 0.0, 1.0])

# Create the cube geometry
cube_shape = Cube(
    paths="/World/fancy_cube",
    positions=np.array([[0.0, 0.0, 1.0]]),
    sizes=[1.0],
    scales=np.array([[0.5, 0.5, 0.5]]),
    reset_xform_op_properties=True,
)

# Apply collision and rigid body
GeomPrim(paths=cube_shape.paths, apply_collision_apis=True)
cube = RigidPrim(paths=cube_shape.paths)
cube_shape.apply_visual_materials(visual_material)

# Start the timeline (physics simulation)
omni.timeline.get_timeline_interface().play()
simulation_app.update()

# Run the simulation loop
for i in range(50):
    # Only query when physics is actively simulating
    if SimulationManager.is_simulating():
        positions, orientations = cube.get_world_poses()
        linear_velocities, angular_velocities = cube.get_velocities()

        # Will be shown on terminal
        print("Cube position is : " + str(positions.numpy()[0]))
        print("Cube's orientation is : " + str(orientations.numpy()[0]))
        print("Cube's linear velocity is : " + str(linear_velocities.numpy()[0]))

    # Step the app (physics + rendering)
    simulation_app.update()

simulation_app.close()  # close Isaac Sim
