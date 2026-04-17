import asyncio  # Used to run sample asynchronously to not block rendering thread

import omni  # Provides the core omniverse APIs
from isaacsim.sensors.physx import _range_sensor  # Imports the python bindings to interact with Lidar sensor
from pxr import Gf, Semantics, UsdGeom, UsdPhysics  # pxr usd imports used to create cube

stage = omni.usd.get_context().get_stage()  # Used to access Geometry
timeline = omni.timeline.get_timeline_interface()  # Used to interact with simulation
lidarInterface = _range_sensor.acquire_lidar_sensor_interface()  # Used to interact with the LIDAR
# These commands are the Python-equivalent of the first half of this tutorial
omni.kit.commands.execute("AddPhysicsSceneCommand", stage=stage, path="/World/PhysicsScene")
lidarPath = "/LidarName"
# Create Lidar prim
result, prim = omni.kit.commands.execute(
    "RangeSensorCreateLidar",
    path=lidarPath,
    parent="/World",
    min_range=0.4,
    max_range=100.0,
    draw_points=True,
    draw_lines=False,
    horizontal_fov=360.0,
    vertical_fov=60.0,
    horizontal_resolution=0.4,
    vertical_resolution=0.4,
    rotation_rate=0.0,
    high_lod=True,
    yaw_offset=0.0,
    enable_semantics=True,
)
UsdGeom.XformCommonAPI(stage.GetPrimAtPath("/World" + lidarPath)).SetTranslate((2.0, 0.0, 0.0))

# Create a cube, sphere, add collision and different semantic labels
primType = ["Cube", "Sphere"]
for i in range(2):
    prim = stage.DefinePrim("/World/" + primType[i], primType[i])
    UsdGeom.XformCommonAPI(prim).SetTranslate((-2.0, -2.0 + i * 4.0, 0.0))
    UsdGeom.XformCommonAPI(prim).SetScale((1, 1, 1))
    collisionAPI = UsdPhysics.CollisionAPI.Apply(prim)

    # Add semantic label
    sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
    sem.CreateSemanticTypeAttr()
    sem.CreateSemanticDataAttr()
    sem.GetSemanticTypeAttr().Set("class")
    sem.GetSemanticDataAttr().Set(primType[i])


# Get point cloud and semantic id for Lidar hit points
async def get_lidar_param():
    await asyncio.sleep(1.0)
    timeline.pause()
    pointcloud = lidarInterface.get_point_cloud_data("/World" + lidarPath)
    semantics = lidarInterface.get_prim_data("/World" + lidarPath)

    print("Point Cloud", pointcloud)
    print("Semantic ID", semantics)


timeline.play()  # Start the Simulation
asyncio.ensure_future(get_lidar_param())  # Only ask for data after sweep is complete
