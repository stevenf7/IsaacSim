import numpy as np
from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import carb
import omni
from isaacsim.core.api.world import World
from isaacsim.core.experimental.objects import Cube, GroundPlane
from isaacsim.core.utils.extensions import enable_extension
from pxr import Sdf, UsdLux, UsdPhysics

# Set up scene
world = World()
GroundPlane("/World/GroundPlane")

# Add lighting
stage = omni.usd.get_context().get_stage()
distantLight = UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight"))
distantLight.CreateIntensityAttr(500)

# Add cubes with collision and rigid body for physics simulation
cube_1 = Cube("/cube_1", sizes=1.0, positions=np.array([0.4, 0, 5.0]), colors=np.array([1.0, 0, 0]))
UsdPhysics.CollisionAPI.Apply(cube_1.prims[0])
UsdPhysics.RigidBodyAPI.Apply(cube_1.prims[0])

cube_2 = Cube("/cube_2", sizes=1.0, positions=np.array([-0.4, 0, 5.0]), colors=np.array([0, 0, 1.0]))
UsdPhysics.CollisionAPI.Apply(cube_2.prims[0])
UsdPhysics.RigidBodyAPI.Apply(cube_2.prims[0])

# Enable isaacsim.sensors.physx extension
enable_extension("isaacsim.sensors.physx")
simulation_app.update()

# Attach sensor to cube 1
from isaacsim.sensors.physx import ProximitySensor, clear_sensors, register_sensor

s = ProximitySensor(cube_1.prims[0])
register_sensor(s)


# Add callback to print proximity sensor data
def print_proximity_sensor_data_on_update(_):
    data = s.get_data()
    if "/cube_2" in data:
        # /cube_1 is colliding with /cube_2
        distance = data["/cube_2"]["distance"]
        duration = data["/cube_2"]["duration"]
        carb.log_warn(f"distance: {distance}, duration: {duration}")


# Play simulation
world.add_physics_callback("print_sensor_data", print_proximity_sensor_data_on_update)
simulation_app.update()
simulation_app.update()
world.play()

for i in range(100):
    # Run with a fixed step size
    world.step(render=True)
