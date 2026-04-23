from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import numpy as np
import omni
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.rtx import CameraSensor, RtxCamera

# Create a simple scene with cubes
Cube("/World/cube_1", sizes=1.0, positions=np.array([5.0, 3.0, 1.0]), colors=[1, 0, 0])
Cube("/World/cube_2", sizes=1.0, positions=np.array([-5.0, 1.0, 3.0]), colors=[0, 0, 1])

# Create a camera with the RTX sensor API
cam = RtxCamera(
    "/World/camera",
    tick_rate=20.0,
    positions=np.array([0.0, 0.0, 25.0]),
)
cam.camera.set_focal_lengths(24.0)
cam.camera.set_clipping_ranges(0.01, 1000.0)

# Create sensor with RGB and motion vectors annotators
sensor = CameraSensor(
    cam,
    resolution=(256, 256),
    annotators=["rgb", "motion_vectors"],
)

# Run simulation and retrieve data
timeline = omni.timeline.get_timeline_interface()
timeline.play()

for i in range(101):
    simulation_app.update()
    if i == 100:
        rgb_data, _ = sensor.get_data("rgb")
        mv_data, _ = sensor.get_data("motion_vectors")
        if rgb_data is not None:
            print(f"RGB shape: {rgb_data.shape}")
        if mv_data is not None:
            print(f"Motion vectors shape: {mv_data.shape}")

timeline.stop()
simulation_app.close()
