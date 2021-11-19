# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"renderer": "RayTracedLighting", "headless": True})

import omni
from omni.isaac.contact_sensor import _contact_sensor
from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid

# enable ROS bridge extension
enable_extension("omni.isaac.ros_bridge")

# check if rosmaster node is running
# this is to prevent this sample from waiting indefinetly if roscore is not running
# can be removed in regular usage
simulation_app.update()
result, check = omni.kit.commands.execute("RosBridgeRosMasterCheck")
if not check:
    carb.log_error("Please run roscore before executing this script")
    simulation_app.close()
    exit()

# Note that this is not the system level rospy, but one compiled for omniverse
import numpy as np
import rospy
from isaac_tutorials.msg import ContactSensor


rospy.init_node("contact_sample", anonymous=True, disable_signals=True, log_level=rospy.ERROR)

timeline = omni.timeline.get_timeline_interface()
contact_pub = rospy.Publisher("/contact_report", ContactSensor, queue_size=0)
cs = _contact_sensor.acquire_contact_sensor_interface()

meters_per_unit = 0.01
ros_world = World(stage_units_in_meters=meters_per_unit)

# add a cube in the world
cube_path = "/cube"
cube_1 = ros_world.scene.add(
    DynamicCuboid(
        prim_path=cube_path, name="cube_1", position=np.array([0, 0, 1.5]) * 100, size=np.array([1, 1, 1]) * 100
    )
)
# Add a plane for cube to collide with
ros_world.scene.add_default_ground_plane()

# putting contact sensor in the ContactSensor Message format
def format_contact(c_out, contact):
    c_out.time = float(contact["time"])
    c_out.value = float(contact["value"] * meters_per_unit)
    c_out.in_contact = bool(contact["inContact"])
    return c_out


# Setup contact sensor on cube
props = _contact_sensor.SensorProperties()
props.radius = -1  # Cover the entire body
props.minThreshold = 0
props.maxThreshold = 1000000000000
props.sensorPeriod = 1.0 / 60.0
body_path = cube_path
sensor_handle = cs.add_sensor_on_body(body_path, props)

# initiate the message handle
c_out = ContactSensor()

# start simulation
timeline.play()
for frame in range(10000):
    ros_world.step(render=False)

    # Get processed contact data
    reading = cs.get_sensor_readings(sensor_handle)
    if reading.shape[0]:
        for r in reading:
            print(r)
            # pack the raw data into ContactSensor format and publish it
            c = format_contact(c_out, r)
            contact_pub.publish(c)


# Cleanup
contact_pub.unregister()
rospy.signal_shutdown("contact_sample complete")
timeline.stop()
simulation_app.close()
