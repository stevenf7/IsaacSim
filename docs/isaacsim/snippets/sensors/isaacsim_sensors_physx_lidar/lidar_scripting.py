# isort: skip_file
# -- Test setup --
from isaacsim.sensors.physx import _range_sensor

# -- End test setup --

# [imports]
import asyncio  # Used to run sample asynchronously to not block rendering thread

import omni  # Provides the core omniverse APIs
from isaacsim.sensors.physx import _range_sensor  # Imports the python bindings to interact with Lidar sensor
from pxr import Gf, UsdGeom, UsdPhysics  # pxr usd imports used to create the cube

# [/imports]

# [setup]
import omni

stage = omni.usd.get_context().get_stage()  # Used to access Geometry
timeline = omni.timeline.get_timeline_interface()  # Used to interact with simulation
lidarInterface = _range_sensor.acquire_lidar_sensor_interface()  # Used to interact with the LIDAR

# These commands are the Python-equivalent of the first half of this tutorial
omni.kit.commands.execute("AddPhysicsSceneCommand", stage=stage, path="/World/PhysicsScene")
lidarPath = "/LidarName"
result, prim = omni.kit.commands.execute(
    "RangeSensorCreateLidar",
    path=lidarPath,
    parent="/World",
    min_range=0.4,
    max_range=100.0,
    draw_points=False,
    draw_lines=True,
    horizontal_fov=360.0,
    vertical_fov=30.0,
    horizontal_resolution=0.4,
    vertical_resolution=4.0,
    rotation_rate=0.0,
    high_lod=False,
    yaw_offset=0.0,
    enable_semantics=False,
)
# [/setup]

# [create-obstacle]
from isaacsim.core.experimental.utils.stage import get_current_stage
from pxr import Gf, UsdGeom, UsdPhysics

stage = get_current_stage()
CubePath = "/World/CubeName"  # Create a Cube
cubeGeom = UsdGeom.Cube.Define(stage, CubePath)
cubePrim = stage.GetPrimAtPath(CubePath)
cubeGeom.AddTranslateOp().Set(Gf.Vec3f(2.0, 0.0, 0.0))  # Move it away from the LIDAR
cubeGeom.CreateSizeAttr(1)  # Scale it appropriately
collisionAPI = UsdPhysics.CollisionAPI.Apply(cubePrim)  # Add a Physics Collider to it
# [/create-obstacle]

# [get-lidar-data]
import asyncio

import omni.timeline


async def get_lidar_param():  # Function to retrieve data from the LIDAR
    await omni.kit.app.get_app().next_update_async()  # wait one frame for data
    timeline.pause()  # Pause the simulation to populate the LIDAR's depth buffers
    depth = lidarInterface.get_linear_depth_data("/World" + lidarPath)
    zenith = lidarInterface.get_zenith_data("/World" + lidarPath)
    azimuth = lidarInterface.get_azimuth_data("/World" + lidarPath)
    print("depth", depth)  # Print the data
    print("zenith", zenith)
    print("azimuth", azimuth)


timeline = omni.timeline.get_timeline_interface()
timeline.play()  # Start the Simulation
asyncio.ensure_future(get_lidar_param())  # Only ask for data after sweep is complete
# [/get-lidar-data]
