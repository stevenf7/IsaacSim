# provides the core omniverse APIs
# used to run sample asynchronously to not block rendering thread
import asyncio

import omni

# import the python bindings to interact with Lidar sensor
from isaacsim.sensors.physx import _range_sensor

# pxr usd imports used to create cube
from pxr import Gf, UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
lidarInterface = _range_sensor.acquire_lidar_sensor_interface()
timeline = omni.timeline.get_timeline_interface()
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

CubePath = "/World/CubeName"
cubeGeom = UsdGeom.Cube.Define(stage, CubePath)
cubePrim = stage.GetPrimAtPath(CubePath)
cubeGeom.AddTranslateOp().Set(Gf.Vec3f(2.0, 0.0, 0.0))
cubeGeom.CreateSizeAttr(1)
collisionAPI = UsdPhysics.CollisionAPI.Apply(cubePrim)


async def get_lidar_param():
    await omni.kit.app.get_app().next_update_async()
    timeline.pause()
    depth = lidarInterface.get_linear_depth_data("/World" + lidarPath)
    zenith = lidarInterface.get_zenith_data("/World" + lidarPath)
    azimuth = lidarInterface.get_azimuth_data("/World" + lidarPath)
    print("depth", depth)
    print("zenith", zenith)
    print("azimuth", azimuth)


timeline.play()
asyncio.ensure_future(get_lidar_param())
