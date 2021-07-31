# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.ext
import carb
import omni.usd
from pxr import Usd, Gf
from omni.physx import get_physx_interface, get_physx_scene_query_interface


class Sensor:
    def __init__(self, extent: carb.Float3, parent: Usd.Prim):
        self.extent = extent
        self.parent = parent
        self.overlapping = False
        self.distance = 0
        self.stage = omni.usd.get_context().get_stage()

    def update(self):
        self.parent_pose = omni.usd.utils.get_world_transform_matrix(self.parent)
        origin = self.parent_pose.ExtractTranslation()
        rot = self.parent_pose.ExtractRotation().GetQuat()
        self.overlapping = False
        get_physx_scene_query_interface().overlap_box(
            self.extent,
            carb.Float3(origin[0], origin[1], origin[2]),
            carb.Float4(rot.GetImaginary()[0], rot.GetImaginary()[1], rot.GetImaginary()[2], rot.GetReal()),
            self.compute,
            False,
        )
        pass

    def status(self):
        return (self.overlapping, self.distance)

    def compute(self, hit):
        overlap_prim = self.stage.GetPrimAtPath(hit.rigid_body)
        hit_pose = omni.usd.utils.get_world_transform_matrix(overlap_prim)
        dist = Gf.Vec3d(hit_pose.ExtractTranslation() - self.parent_pose.ExtractTranslation()).GetLength()
        self.overlapping = True
        print("overlap: ", overlap_prim, "distance: ", dist)
        # we stop processing after the first overlap by returning false
        return False
        # TODO, process closest overlap instead of first


class SensorManager(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SensorManager, cls).__new__(cls)
            cls.sensors = []
        return cls._instance

    def register_sensor(self, sensor: Sensor):
        self.sensors.append(sensor)

    def clear_sensors(self):
        self.sensors = []

    def update(self):
        for sensor in self.sensors:
            sensor.update()


# Public API:
def register_sensor(sensor: Sensor):
    SensorManager().register_sensor(sensor)


def clear_sensors():
    SensorManager().clear_sensors()


class Extension(omni.ext.IExt):
    def on_startup(self):
        # step the sensor every physics step
        self._sub = get_physx_interface().subscribe_physics_step_events(self._on_update)
        self._sm = SensorManager()  # Store instance to sensor manager singleton

    def on_shutdown(self):
        self._sub = None  # clear subscription
        clear_sensors()  # clear sensors on shutdown
        self._sm = None

    def _on_update(self, dt):
        self._sm.update()
        pass


# Example usage, create a physics scene and a Cube first
# from omni.isaac.proximity_sensor import Sensor, register_sensor, clear_sensors
# import carb
# import omni
# half_extent = carb.Float3(25,25,25)
# stage = omni.usd.get_context().get_stage()
# parent = stage.GetPrimAtPath("/World/Cube")
# s = Sensor(half_extent, parent)
# register_sensor(s)
