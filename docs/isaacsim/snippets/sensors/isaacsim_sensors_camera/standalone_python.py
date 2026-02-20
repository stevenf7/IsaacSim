from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import isaacsim.core.utils.numpy.rotations as rot_utils
import matplotlib.pyplot as plt
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.sensors.camera import Camera

my_world = World(stage_units_in_meters=1.0)

# Add two cubes to the scene
cube_1 = my_world.scene.add(
    DynamicCuboid(
        prim_path="/new_cube_1",
        name="cube_1",
        position=np.array([5.0, 3, 1.0]),
        scale=np.array([0.6, 0.5, 0.2]),
        size=1.0,
        color=np.array([255, 0, 0]),
    )
)

cube_2 = my_world.scene.add(
    DynamicCuboid(
        prim_path="/new_cube_2",
        name="cube_2",
        position=np.array([-5, 1, 3.0]),
        scale=np.array([0.1, 0.1, 0.1]),
        size=1.0,
        color=np.array([0, 0, 255]),
        linear_velocity=np.array([0, 0, 0.4]),
    )
)

# Add a camera to the scene, facing the cubes
camera = Camera(
    prim_path="/World/camera",
    position=np.array([0.0, 0.0, 25.0]),
    frequency=20,
    resolution=(256, 256),
    orientation=rot_utils.euler_angles_to_quats(np.array([0, 90, 0]), degrees=True),
)

# Add a ground plane to the scene
my_world.scene.add_default_ground_plane()

# Reset the world and initialize the camera
my_world.reset()
camera.initialize()

i = 0
# Collect motion vectors for each object in view of the camera
camera.add_motion_vectors_to_frame()

# Run indefinitely, until the simulation is stopped (eg. via Ctrl+C)
for _ in range(101):
    my_world.step(render=True)
    if i == 100:
        # Find the 2D coordinates of the cubes in the image
        points_2d = camera.get_image_coords_from_world_points(
            np.array([cube_1.get_world_pose()[0], cube_2.get_world_pose()[0]])
        )
        # Project the 2D coordinates of the cubes in the image back to 3D world coordinates,
        # taking depth as z-position of the camera
        points_3d = camera.get_world_points_from_image_coords(points_2d, np.array([24.94, 24.9]))
        # Print both sets, demonstrating reprojection errors when comparing points_3D to the
        print(points_2d)
        print(points_3d)
        # Plot the RGB image
        plt.imsave("camera.png", camera.get_rgba()[:, :, :3])
        # Print the motion vectors collected by the camera
        print(camera.get_current_frame()["motion_vectors"])
    if my_world.is_playing():
        if my_world.current_time_step_index == 0:
            my_world.reset()
    i += 1


simulation_app.close()
