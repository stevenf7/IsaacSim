# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import json
import carb
from omni.isaac.kit import SimulationApp

# Example ROS bridge sample showing rospy and rosclock interaction
kit = SimulationApp({"renderer": "RayTracedLighting", "headless": True})
import omni
from omni.isaac.contact_sensor import _contact_sensor
from pxr import UsdGeom, UsdPhysics, Gf, PhysicsSchemaTools
from omni.isaac.kit.utils import enable_extension

# enable ROS bridge extension
enable_extension("omni.isaac.ros_bridge")
# check if rosmaster node is running
# this is to prevent this sample from waiting indefinetly if roscore is not running
# can be removed in regular usage
kit.update()
result, check = omni.kit.commands.execute("RosBridgeRosMasterCheck")
if not check:
    carb.log_error("Please run roscore before executing this script")
    kit.close()
    exit()
# Note that this is not the system level rospy, but one compiled for omniverse
from std_msgs.msg import String
import rospy

rospy.init_node("contact_sample", anonymous=True, disable_signals=True, log_level=rospy.ERROR)

timeline = omni.timeline.get_timeline_interface()
ros_pub = rospy.Publisher("contact_report", String, queue_size=0)
cs = _contact_sensor.acquire_contact_sensor_interface()
stage = omni.usd.get_context().get_stage()
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)

# Add physics
scene = UsdPhysics.Scene.Define(stage, "/physics/scene")
scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
scene.CreateGravityMagnitudeAttr().Set(9.81)

cube_path = "/cube"
cube_geom = UsdGeom.Cube.Define(stage, cube_path)
cubePrim = stage.GetPrimAtPath(cube_path)

cube_geom.CreateSizeAttr(1)
cube_geom.AddTranslateOp().Set((0, 0, 1.5))
rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
rigid_api.CreateRigidBodyEnabledAttr(True)
# Prim that we are detecting collision events for must have collision API
UsdPhysics.CollisionAPI.Apply(cubePrim)
# Add a plane for cube to collide with
PhysicsSchemaTools.addGroundPlane(stage, "/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, 0), Gf.Vec3f(0.5))
kit.update()


def serialize(contact):
    c = {}
    c["time"] = float(contact["time"])
    c["value"] = float(contact["value"] * meters_per_unit)
    c["in_contact"] = bool(contact["inContact"])
    return json.dumps(c)


def serialize_raw(contact):
    c = {}
    c["time"] = float(contact["time"])
    c["body0"] = str(cs.decode_body_name(contact["body0"]))
    c["body1"] = str(cs.decode_body_name(contact["body1"]))
    c["position"] = [
        float(contact["position"][0]) * meters_per_unit,
        float(contact["position"][1]) * meters_per_unit,
        float(contact["position"][2]) * meters_per_unit,
    ]
    c["normal"] = [float(contact["normal"][0]), float(contact["normal"][1]), float(contact["normal"][2])]
    c["impulse"] = [
        float(contact["impulse"][0]) * meters_per_unit,
        float(contact["impulse"][1]) * meters_per_unit,
        float(contact["impulse"][2]) * meters_per_unit,
    ]
    return json.dumps(c)


# Setup contact sensor on cube
props = _contact_sensor.SensorProperties()
props.radius = -1  # Cover the entire body
props.minThreshold = 0
props.maxThreshold = 1000000000000
props.sensorPeriod = 1.0 / 60.0
body_path = cube_path
sensor_handle = cs.add_sensor_on_body(body_path, props)
# start simulation
omni.timeline.get_timeline_interface().play()
for frame in range(60):
    kit.update()
    # Get processed contact data
    reading = cs.get_sensor_readings(sensor_handle)
    if reading.shape[0]:
        for r in reading:
            print(serialize(r))
            ros_pub.publish(serialize(r))
    # Get raw contact data
    raw_readings = cs.get_body_contact_raw_data(cube_path)
    if raw_readings.shape[0]:
        for r in raw_readings:
            print(serialize_raw(r))
            ros_pub.publish(serialize_raw(r))
# Cleanup
ros_pub.unregister()
rospy.signal_shutdown("contact_sample complete")
omni.timeline.get_timeline_interface().stop()
kit.close()
