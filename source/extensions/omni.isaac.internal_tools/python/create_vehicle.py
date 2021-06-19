# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import gc
import omni.ext
import omni.usd
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import omni.kit.utils
import omni.kit.commands
from pxr import Usd, UsdGeom, Sdf, UsdShade, UsdPhysics, Gf, PhysxSchema, UsdLux
import weakref
from omni.physx.scripts import utils
from omni.physxvehicle.scripts.wizards.physxVehicleWizard import VehicleData, DRIVE_TYPE_NONE
import asyncio

EXTENSION_NAME = "Vehicle Config Tool"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._usd_context = omni.usd.get_context()
        self._selected_prim = None
        self._selection = self._usd_context.get_selection()
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        self._menu_items = [
            MenuItemDescription(
                "Misc",
                sub_menu=[
                    MenuItemDescription(
                        name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
                    )
                ],
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")

        with self._window.frame:
            with ui.VStack(spacing=10):
                with ui.HStack(height=0, spacing=10):
                    ui.Label("Enable all debug sensor viz", width=0)
                    self._debug_viz = ui.CheckBox().model
                    self._debug_viz.set_value(True)
                with ui.HStack(height=0, spacing=10):
                    ui.Label("Enable REB components", width=0)
                    self._reb = ui.CheckBox().model
                    self._reb.set_value(True)
                ui.Button("Create Vehicle", clicked_fn=self.create_vehicle)
        pass

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def setup(self):
        self._usdContext = omni.usd.get_context()
        self._stage = self._usdContext.get_stage()
        UsdGeom.SetStageUpAxis(self._stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(self._stage, 1.0)
        self._metersPerUnit = UsdGeom.GetStageMetersPerUnit(self._stage)
        self._lengthScale = 1.0 / self._metersPerUnit

    async def create_env(self):

        omni.kit.commands.execute(
            "AddGroundPlaneCommand",
            stage=self._stage,
            planePath="/groundPlane",
            axis="Z",
            size=1500.0,
            position=Gf.Vec3f(0, 0, 0.0),
            color=Gf.Vec3f(0.5),
        )
        gravityScale = 9.81 * self._lengthScale
        scene = UsdPhysics.Scene.Define(self._stage, "/physics/scene")
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(gravityScale)

        PhysxSchema.PhysxSceneAPI.Apply(self._stage.GetPrimAtPath("/physics/scene"))
        physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(self._stage, "/physics/scene")
        physxSceneAPI.CreateEnableCCDAttr(True)
        physxSceneAPI.CreateEnableStabilizationAttr(True)
        physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
        physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
        physxSceneAPI.CreateSolverTypeAttr("TGS")

        await omni.kit.app.get_app().next_update_async()
        omni.kit.commands.execute("DeletePrimsCommand", paths=["/World/defaultLight"])
        await omni.kit.app.get_app().next_update_async()
        omni.kit.commands.execute(
            "CreatePrimCommand",
            prim_path="/World/dometLight",
            prim_type="DomeLight",
            select_new_prim=False,
            attributes={
                UsdLux.Tokens.intensity: 1000,
                UsdLux.Tokens.specular: 1,
                UsdLux.Tokens.textureFile: "omniverse://ov-isaac-dev.nvidia.com/Library/Materials/HDR/aircraft_workshop_01_2k.hdr",
                UsdLux.Tokens.textureFormat: UsdLux.Tokens.latlong,
                UsdGeom.Tokens.visibility: "inherited",
            },
        )
        await omni.kit.app.get_app().next_update_async()
        pass

    def create_vehicle(self):
        # Create a simple env that the vehicle can drive on
        self.setup()
        asyncio.ensure_future(self.create_env())

        data = VehicleData()
        # set paths for where vehicle prims are created
        data.rootVehiclePath = "/vehicle"
        data.rootSharedPath = data.rootVehiclePath + "/shared"

        # Set vehicle as z up x forward
        data.up = Gf.Vec3f(0, 0, 1)
        data.forward = Gf.Vec3f(1, 0, 0)
        data.side = data.forward.GetCross(data.up)

        # units are in meters, and then scaled by the stage units
        data.chassisLength = 4.7 * self._lengthScale
        data.chassisWidth = 0.87749 * 2.0 * self._lengthScale
        data.chassisHeight = 1.0 * self._lengthScale
        data.chassisMass = 1711.1156  # KG
        # set the radius scale which is multiplied by the chassis length inside of the reset_axles function
        data._defaultRadiusScale = 0.4051 / data.chassisLength
        data._defaultWidthScale = 0.29608 / (data._defaultRadiusScale * data.chassisLength)
        # we need to set this if sdk control is enabled, by default the vehicle can be driven by keyboard
        if self._reb.get_value_as_bool():
            data.driveTypeIndex = DRIVE_TYPE_NONE

        data.reset_axles()
        # reset_axels also resets steering and drive, so do it after
        data.maxSteerAngle[0] = 30.0  # in degrees
        data.maxSteerAngle[1] = 0.0  # rear axle doesn't have steering
        data.driven[0] = True
        data.driven[1] = False  # Rear axle is not driven
        # data.weightDistribution[0]=100
        # data.weightDistribution[1]=0

        # Made the initialization part async so we can run updates between steps to make sure everything is initialized properly in usd
        async def _task():
            parent_path = data.rootVehiclePath + "/Vehicle"

            await omni.kit.app.get_app().next_update_async()
            omni.kit.commands.execute("PhysXVehicleWizardCreateCommand", vehicleData=data)
            await omni.kit.app.get_app().next_update_async()
            self._stage.SetDefaultPrim(self._stage.GetPrimAtPath(data.rootVehiclePath))

            # TODO: Add code for custom wheel alignments and offsets
            # move the chassis rigid body to origin of vehicle, all sensors are placed with this assumption

            vehicle_chassis = self._stage.GetPrimAtPath(parent_path)
            vehicle_chassis.GetPrim().GetAttribute("xformOp:translate").Set((0, 0, 0))

            self._timeline.play()
            await omni.kit.app.get_app().next_update_async()
            self._timeline.stop()
            await omni.kit.app.get_app().next_update_async()
            # recompute offsets because chassis moved
            omni.kit.commands.execute("PhysXVehicleWheelSimTransformsAutocomputeCommand", primPath=parent_path)
            await omni.kit.app.get_app().next_update_async()

            mass_api = UsdPhysics.MassAPI.Get(self._stage, Sdf.Path(parent_path))
            mass_api.GetCenterOfMassAttr().Set(Gf.Vec3d(1.54077, 0, 0.45238))
            chassis_prim = self._stage.GetPrimAtPath(parent_path + "/ChassisCollision")
            chassis_prim.GetPrim().GetAttribute("xformOp:translate").Set((1.63374, 0, 0.75185))

            wheel_path = ""
            chassis_path = ""
            chassis_lights_path = ""
            omni.kit.commands.execute("DeletePrimsCommand", paths=[parent_path + "/ChassisRender"])
            chassis_prim = self._stage.DefinePrim(parent_path + "/ChassisRender", "Xform")
            chassis_prim.GetReferences().AddReference(chassis_path)
            chassis_prim.GetPrim().GetAttribute("xformOp:translate").Set((1.63374, 0, 0))
            chassis_prim.SetInstanceable(False)

            chassis_lights = self._stage.DefinePrim(parent_path + "/ChassisLights", "Xform")
            chassis_lights.GetReferences().AddReference(chassis_lights_path)
            chassis_lights.GetPrim().GetAttribute("xformOp:translate").Set((0, 0, 0))
            chassis_lights.SetInstanceable(False)

            wheel_prim = self._stage.GetPrimAtPath(parent_path + "/LeftWheel1References")
            wheel_prim.GetAttribute("xformOp:translate").Set((3.26394, 0.87749, 0.40457))

            wheel_prim = self._stage.GetPrimAtPath(parent_path + "/RightWheel1References")
            wheel_prim.GetAttribute("xformOp:translate").Set((3.26394, -0.87749, 0.40457))

            wheel_prim = self._stage.GetPrimAtPath(parent_path + "/LeftWheel2References")
            wheel_prim.GetAttribute("xformOp:translate").Set((0, 0.87749, 0.40457))

            wheel_prim = self._stage.GetPrimAtPath(parent_path + "/RightWheel2References")
            wheel_prim.GetAttribute("xformOp:translate").Set((0, -0.87749, 0.40457))

            # Delete existing wheel visuals
            omni.kit.commands.execute("DeletePrimsCommand", paths=[parent_path + "/LeftWheel1References/Render"])
            omni.kit.commands.execute("DeletePrimsCommand", paths=[parent_path + "/RightWheel1References/Render"])
            omni.kit.commands.execute("DeletePrimsCommand", paths=[parent_path + "/LeftWheel2References/Render"])
            omni.kit.commands.execute("DeletePrimsCommand", paths=[parent_path + "/RightWheel2References/Render"])

            wheel_prim = self._stage.DefinePrim(parent_path + "/LeftWheel1References/Render", "Xform")
            wheel_prim.GetReferences().AddReference(wheel_path)
            wheel_prim.GetPrim().GetAttribute("xformOp:rotateXYZ").Set((0, 0, 90))
            wheel_prim.SetInstanceable(False)

            wheel_prim = self._stage.DefinePrim(parent_path + "/RightWheel1References/Render", "Xform")
            wheel_prim.GetReferences().AddReference(wheel_path)
            wheel_prim.GetPrim().GetAttribute("xformOp:rotateXYZ").Set((0, 0, -90))
            wheel_prim.SetInstanceable(False)

            wheel_prim = self._stage.DefinePrim(parent_path + "/LeftWheel2References/Render", "Xform")
            wheel_prim.GetReferences().AddReference(wheel_path)
            wheel_prim.GetPrim().GetAttribute("xformOp:rotateXYZ").Set((0, 0, 90))
            wheel_prim.SetInstanceable(False)

            wheel_prim = self._stage.DefinePrim(parent_path + "/RightWheel2References/Render", "Xform")
            wheel_prim.GetReferences().AddReference(wheel_path)
            wheel_prim.GetPrim().GetAttribute("xformOp:rotateXYZ").Set((0, 0, -90))
            wheel_prim.SetInstanceable(False)

            # Set wheel physics parameters
            for wheel_path in ["/LeftWheel1", "/RightWheel1", "/LeftWheel2", "/RightWheel2"]:
                wheel_prim = PhysxSchema.PhysxVehicleWheel(self._stage.GetPrimAtPath(data.rootVehiclePath + wheel_path))
                wheel_prim.GetMoiAttr().Set(34.34439)
                wheel_prim.GetDampingRateAttr().Set(7.00906)
                wheel_prim.GetMaxBrakeTorqueAttr().Set(100930.4375)
                wheel_prim.GetMaxHandBrakeTorqueAttr().Set(0)

            # Set suspension parameters
            suspension_prim = PhysxSchema.PhysxVehicleSuspension(
                self._stage.GetPrimAtPath(data.rootVehiclePath + "/Suspension1")
            )
            suspension_prim.GetSpringStrengthAttr().Set(42857.14062)
            suspension_prim.GetSpringDamperRateAttr().Set(2634.93018)
            suspension_prim.GetMaxCompressionAttr().Set(0.52949)
            suspension_prim.GetMaxDroopAttr().Set(0.52949)

            suspension_prim = PhysxSchema.PhysxVehicleSuspension(
                self._stage.GetPrimAtPath(data.rootVehiclePath + "/Suspension2")
            )
            suspension_prim.GetSpringStrengthAttr().Set(42857.14062)
            suspension_prim.GetSpringDamperRateAttr().Set(2634.93018)
            suspension_prim.GetMaxCompressionAttr().Set(0.52949)
            suspension_prim.GetMaxDroopAttr().Set(0.52949)

            # because we moved the wheels and chassis com, recompute everything
            omni.kit.commands.execute("PhysXVehicleWheelSimTransformsAutocomputeCommand", primPath=parent_path)
            # 1.63374 offset from origin
            # 0/1 3.26394, +/- 0.87749, 0.40457
            # 2/3 0, +/- 0.87749, 0.40457
            reb_root = parent_path + "/REB"
            sensor_root = parent_path + "/Sensors"
            camera_root = parent_path + "/Cameras"
            if self._reb.get_value_as_bool():
                result, prim = omni.kit.commands.execute(
                    "RobotEngineBridgeCreateVehicle",
                    path="/REB_Vehicle",
                    parent=reb_root,
                    input_component="input",
                    input_channel="vehicle_command",
                    output_component="output",
                    output_channel="vehicle_state",
                    vehicle_prim_rel=[parent_path],
                    history_length=5,
                    use_pid=True,
                    controller_pid_values=(2.0, 0.5, 1.0),
                )
            await self.create_imu(reb_root)
            await self.create_cameras(reb_root, camera_root, Gf.Vec3d(1.63374, 0, 0))
            await self.create_lidars(
                reb_root, sensor_root, data.chassisLength * 0.5, data.chassisWidth * 0.5, Gf.Vec3d(1.63374, 0, 0)
            )
            await self.create_ultrasonic(reb_root, sensor_root, Gf.Vec3d(1.63374, 0, 0))

            # move camera to location vehicle will be created at
            self._viewport.set_camera_position(
                "/OmniverseKit_Persp", data.chassisLength * 1.5, data.chassisWidth * 2, data.chassisHeight * 2, True
            )
            self._viewport.set_camera_target("/OmniverseKit_Persp", 2.0, 0, 0, True)

        asyncio.ensure_future(_task())

    async def create_imu(self, parent):
        if self._reb.get_value_as_bool():
            result, prim = omni.kit.commands.execute(
                "RobotEngineBridgeCreatePoseTree",
                path="/REB_PoseTree",
                parent=parent,
                node_name="atlas",
                output_component="",
                output_channel="frontend",
                prims_rel=[parent],
                depth_limits=[1],
                prim_regex="",
            )
        # TODO add IMU rigid body + joint
        pass

    async def create_cameras(self, reb_parent, sensor_parent, offset):
        cameras = [
            ("/BEV_Camera", Gf.Vec3d(0, 0, 5), (0, 0, 90), 74, "orthographic"),
            ("/FOV120_frontcenter", Gf.Vec3d(0.162, 0, 1.47), (90, 0, -90), 83.04, "perspective"),
            ("/FOV120_backcenter", Gf.Vec3d(-1.77, 0, 1.47), (90, 0.0, 90), 83.04, "perspective"),
        ]
        reb_data = [("/REB_BEV_Camera", True), ("/REB_FOV120_frontcenter", False), ("/REB_FOV120_backcenter", False)]
        for i in range(len(cameras)):
            camera = cameras[i]
            camera_prim = UsdGeom.Camera(self._stage.DefinePrim(sensor_parent + camera[0], "Camera"))
            xform_api = UsdGeom.XformCommonAPI(camera_prim)
            xform_api.SetRotate(camera[2], UsdGeom.XformCommonAPI.RotationOrderXYZ)
            xform_api.SetTranslate(camera[1] + offset)
            # camera_prim.GetFocalLengthAttr().Set(FOCAL_LENGTH)
            camera_prim.GetHorizontalApertureAttr().Set(camera[3])
            camera_prim.GetProjectionAttr().Set(camera[4])
            # camera_prim.GetVerticalApertureAttr().Set(VERTICAL_APERTURE)

            if self._reb.get_value_as_bool():
                result, camera_prim = omni.kit.commands.execute(
                    "RobotEngineBridgeCreateCamera",
                    path=reb_data[i][0],
                    parent=reb_parent,
                    rgb_output_component="output",
                    rgb_output_channel="color",
                    depth_output_component="output",
                    depth_output_channel="depth",
                    segmentation_output_component="output",
                    segmentation_output_channel="segmentation",
                    bbox2d_output_component="output",
                    bbox2d_output_channel="bbox",
                    bbox2d_class_list="",
                    bbox3d_output_component="output",
                    bbox3d_output_channel="bbox3d",
                    bbox3d_class_list="",
                    rgb_enabled=True,
                    depth_enabled=False,
                    segmentaion_enabled=False,
                    bbox2d_enabled=False,
                    bbox3d_enabled=False,
                    camera_prim_rel=[camera_prim.GetPrim().GetPrimPath()],
                    resolution=Gf.Vec2i(800, 600),
                )
        pass

    async def create_lidars(self, reb_parent, sensor_parent, chassis_length, chassis_width, sensor_offset):
        await omni.kit.app.get_app().next_update_async()
        # Sensor paths
        names = ["/Lidar_FrontLeft", "/Lidar_FrontRight", "/Lidar_RearLeft", "/Lidar_RearRight"]
        # specify the REB path, channel, timing offset
        reb_data = [
            ("/REB_Lidar_FrontLeft", "output", "rangescan", 0.0),
            ("/REB_Lidar_FrontRight", "output", "rangescan_2", 100.0),
            ("/REB_Lidar_RearLeft", "output", "rangescan_3", 200.0),
            ("/REB_Lidar_RearRight", "output", "rangescan_4", 300.0),
        ]
        # move the lidar sensor out from the chassis by a fixed amount
        lidar_offset = 0.1 * self._lengthScale
        # specify poses and forward directions
        poses = [
            (Gf.Vec3d(chassis_length + lidar_offset, chassis_width + lidar_offset, 0.0), Gf.Vec3d(0, 0, 45)),
            (Gf.Vec3d(-(chassis_length + lidar_offset), chassis_width + lidar_offset, 0.0), Gf.Vec3d(0, 0, 135)),
            (Gf.Vec3d(chassis_length + lidar_offset, -(chassis_width + lidar_offset), 0.0), Gf.Vec3d(0, 0, 315)),
            (Gf.Vec3d(-(chassis_length + lidar_offset), -(chassis_width + lidar_offset), 0.0), Gf.Vec3d(0, 0, 255)),
        ]
        yaw_offsets = [0, 0, 0, 0]
        for i in range(len(poses)):
            result, lidar = omni.kit.commands.execute(
                "RangeSensorCreateLidar",
                path=names[i],
                parent=sensor_parent,
                min_range=0.4,
                max_range=100.0,
                draw_points=False,
                draw_lines=self._debug_viz.get_value_as_bool(),
                horizontal_fov=210.0,
                vertical_fov=30.0,
                horizontal_resolution=0.4,
                vertical_resolution=4.0,
                rotation_rate=0.0,
                high_lod=False,
                yaw_offset=yaw_offsets[i],
            )
            lidar.GetPrim().GetAttribute("xformOp:translate").Set(poses[i][0] + sensor_offset)
            lidar.GetPrim().GetAttribute("xformOp:rotateXYZ").Set(poses[i][1])
            if self._reb.get_value_as_bool():
                result, prim = omni.kit.commands.execute(
                    "RobotEngineBridgeCreateLidar",
                    path=reb_data[i][0],
                    parent=reb_parent,
                    output_component=reb_data[i][1],
                    output_channel=reb_data[i][2],
                    lidar_prim_rel=[lidar.GetPrim().GetPrimPath()],
                )
                prim.GetTimeOffsetAttr().Set(reb_data[i][3])
            await omni.kit.app.get_app().next_update_async()
            pass

    async def create_ultrasonic(self, reb_parent, sensor_parent, emitter_offset):
        await omni.kit.app.get_app().next_update_async()
        # position units are in meters, and then scaled by stage units
        emitter_poses = [
            (Gf.Vec3d(0, 0, 76.3), Gf.Vec3d(1.886, 0.886, 0.55)),
            (Gf.Vec3d(0, 0, 41.5), Gf.Vec3d(2.163, 0.716, 0.55)),
            (Gf.Vec3d(0, 0, 8.5), Gf.Vec3d(2.325, 0.311, 0.55)),
            (Gf.Vec3d(0, 0, -8.5), Gf.Vec3d(2.326, -0.311, 0.55)),
            (Gf.Vec3d(0, 0, -41.5), Gf.Vec3d(2.163, -0.716, 0.55)),
            (Gf.Vec3d(0, 0, -76.3), Gf.Vec3d(1.886, -0.886, 0.55)),
            (Gf.Vec3d(0, 0, 101.0), Gf.Vec3d(-1.769, 0.875, 0.55)),
            (Gf.Vec3d(0, 0, 154.0), Gf.Vec3d(-2.244, 0.65, 0.55)),
            (Gf.Vec3d(0, 0, 178.0), Gf.Vec3d(-2.311, 0.311, 0.55)),
            (Gf.Vec3d(0, 0, -178.0), Gf.Vec3d(-2.311, -0.311, 0.55)),
            (Gf.Vec3d(0, 0, -154.0), Gf.Vec3d(-2.244, -0.65, 0.55)),
            (Gf.Vec3d(0, 0, -101.0), Gf.Vec3d(-1.769, -0.875, 0.55)),
        ]

        result, group_0 = omni.kit.commands.execute(
            "RangeSensorCreateUltrasonicFiringGroup",
            path="/UltrasonicFiringGroup_0",
            parent=sensor_parent,
            emitter_modes=[(0, 1), (3, 0), (4, 1), (7, 0), (8, 1), (11, 0)],
            receiver_modes=[
                (0, 1),
                (1, 1),
                (2, 0),
                (3, 0),
                (3, 1),
                (4, 0),
                (4, 1),
                (5, 1),
                (6, 0),
                (7, 0),
                (7, 1),
                (8, 0),
                (8, 1),
                (9, 1),
                (10, 0),
                (11, 0),
            ],
        )

        result, group_1 = omni.kit.commands.execute(
            "RangeSensorCreateUltrasonicFiringGroup",
            path="/UltrasonicFiringGroup_1",
            parent=sensor_parent,
            emitter_modes=[(1, 1), (2, 0), (5, 1), (6, 0), (9, 1), (10, 0)],
            receiver_modes=[
                (0, 1),
                (1, 0),
                (1, 1),
                (2, 0),
                (2, 1),
                (3, 0),
                (4, 1),
                (5, 1),
                (6, 0),
                (7, 0),
                (8, 1),
                (9, 0),
                (9, 1),
                (10, 0),
                (10, 1),
                (11, 0),
            ],
        )
        adjacency = [
            [0, 1],
            [0, 1, 2],
            [1, 2, 3],
            [2, 3, 4],
            [3, 4, 5],
            [4, 5],
            [6, 7],
            [6, 7, 8],
            [7, 8, 9],
            [8, 9, 10],
            [9, 10, 11],
            [10, 11],
        ]
        emitters = []
        for i in range(len(emitter_poses)):
            pose = emitter_poses[i]
            adjacent = adjacency[i]
            result, emitter_prim = omni.kit.commands.execute(
                "RangeSensorCreateUltrasonicEmitter",
                path="/UltrasonicEmitter",
                parent=sensor_parent,
                per_ray_intensity=0.4,
                yaw_offset=0.0,
                adjacency_list=adjacent,
            )
            emitter_prim.GetPrim().GetAttribute("xformOp:translate").Set((pose[1] + emitter_offset) * self._lengthScale)
            emitter_prim.GetPrim().GetAttribute("xformOp:rotateXYZ").Set(pose[0])
            emitters.append(emitter_prim)
        emitter_paths = [emitter.GetPath() for emitter in emitters]

        # Add ultrasonic
        result, ultrasonic_array = omni.kit.commands.execute(
            "RangeSensorCreateUltrasonicArray",
            path="/UltrasonicArray",
            parent=sensor_parent,
            min_range=0.4,
            max_range=4.5,
            draw_points=False,
            draw_lines=self._debug_viz.get_value_as_bool(),
            horizontal_fov=75.0,
            vertical_fov=50.0,
            horizontal_resolution=0.5,
            vertical_resolution=5.0,
            num_bins=224,
            emitter_prims=emitter_paths,
            firing_group_prims=[group_0.GetPath(), group_1.GetPath()],
        )
        await omni.kit.app.get_app().next_update_async()

        if self._reb.get_value_as_bool():
            result, prim = omni.kit.commands.execute(
                "RobotEngineBridgeCreateUltrasonic",
                path="/REB_Ultrasonic",
                parent=reb_parent,
                output_component="output",
                output_channel="uss_envelopes",
                ultrasonic_prim_rel=[ultrasonic_array.GetPrim().GetPrimPath()],
            )
        pass

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        pass
